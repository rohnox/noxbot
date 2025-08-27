from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..texts import *
from ..keyboards import main_menu, categories_kb, products_kb, plans_kb, payment_methods_kb
from ..models import User, Category, Product, ProductPlan, Order, OrderStatus, PaymentMethod, OrderMeta
from ..utils import get_or_create_settings
from ..config import settings
from ..services.payments.zarinpal import ZarinpalGateway
from ..services.payments.idpay import IDPayGateway

router = Router(name="user")

class OrderFlow(StatesGroup):
    choosing_category = State()
    choosing_product = State()
    choosing_plan = State()
    filling_fields = State()
    choosing_payment = State()
    manual_proof_text = State()
    manual_proof_photo = State()

@router.message(F.text == "/start")
async def cmd_start(message: Message, db: AsyncSession):
    # register user if not exists
    q = await db.execute(select(User).where(User.tg_id == message.from_user.id))
    u = q.scalar_one_or_none()
    if not u:
        u = User(
            tg_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username
        )
        db.add(u)
        await db.commit()
    await message.answer(WELCOME, reply_markup=main_menu())

@router.message(F.text == MENU_ACCOUNT)
async def account_info(message: Message, db: AsyncSession):
    q = await db.execute(select(User).where(User.tg_id == message.from_user.id))
    u = q.scalar_one()
    text = ACCOUNT_TEMPLATE.format(
        tg_id=u.tg_id,
        name=u.first_name or "-",
        username=u.username or "-",
        joined_at=u.joined_at.strftime("%Y-%m-%d %H:%M")
    )
    await message.answer(text)

@router.message(F.text == MENU_SUPPORT)
async def support(message: Message, db: AsyncSession):
    s = await get_or_create_settings(db)
    if s.support_username:
        await message.answer(SUPPORT_TEXT_TEMPLATE.format(support=s.support_username))
    else:
        await message.answer("پشتیبانی هنوز تنظیم نشده است.")

@router.message(F.text == MENU_CHANNEL)
async def channel(message: Message, db: AsyncSession):
    s = await get_or_create_settings(db)
    if s.channel_username:
        await message.answer(f"عضویت در کانال: https://t.me/{s.channel_username}")
    else:
        await message.answer(NO_CHANNEL)

@router.message(F.text == MENU_STORE)
async def enter_store(message: Message, state: FSMContext, db: AsyncSession):
    # list categories (top-level)
    res = await db.execute(select(Category).where(Category.parent_id == None))
    cats = res.scalars().all()
    if not cats:
        await message.answer("هنوز دسته‌ای ثبت نشده است.", reply_markup=ReplyKeyboardRemove())
        return
    await message.answer(ASK_CATEGORY, reply_markup=ReplyKeyboardRemove())
    await message.answer(" ", reply_markup=None, reply_markup_inline=categories_kb(cats))
    await state.set_state(OrderFlow.choosing_category)

@router.callback_query(F.data.startswith("cat:"))
async def on_category(cb: CallbackQuery, state: FSMContext, db: AsyncSession):
    cat_id = int(cb.data.split(":")[1])
    # list products in category
    res = await db.execute(select(Product).where(Product.category_id == cat_id))
    products = res.scalars().all()
    if not products:
        await cb.message.edit_text("در این دسته محصولی وجود ندارد.")
        return
    await state.update_data(category_id=cat_id)
    await cb.message.edit_text(ASK_PRODUCT, reply_markup=products_kb(products))
    await state.set_state(OrderFlow.choosing_product)

@router.callback_query(F.data.startswith("prod:"))
async def on_product(cb: CallbackQuery, state: FSMContext, db: AsyncSession):
    pid = int(cb.data.split(":")[1])
    res = await db.execute(select(Product).where(Product.id == pid))
    p = res.scalar_one()
    if not p.is_active:
        await cb.answer("این محصول غیرفعال است.", show_alert=True)
        return
    # show desc (if any) and plans
    desc = PRODUCT_DESC.format(desc=p.description) if p.description else " "
    await state.update_data(product_id=pid)
    # plans
    res = await db.execute(select(ProductPlan).where(ProductPlan.product_id == pid))
    plans = res.scalars().all()
    if not plans:
        await cb.message.edit_text(f"{desc}\n(برای این محصول پلنی ثبت نشده است)")
        return
    await cb.message.edit_text(desc, reply_markup=plans_kb(plans))
    await state.set_state(OrderFlow.choosing_plan)

@router.callback_query(F.data.startswith("plan:"))
async def on_plan(cb: CallbackQuery, state: FSMContext, db: AsyncSession):
    plan_id = int(cb.data.split(":")[1])
    # save and start asking required fields
    data = await state.get_data()
    res = await db.execute(select(Product).where(Product.id == data["product_id"]))
    product = res.scalar_one()
    await state.update_data(plan_id=plan_id, required_fields=product.required_fields or [], collected={})
    # ask first field or move to payment
    fields = product.required_fields or []
    if fields:
        first = fields[0]
        await state.set_state(OrderFlow.filling_fields)
        await cb.message.edit_text(ASK_REQUIRED_FIELD.format(field=first))
    else:
        await ask_payment(cb.message, state, db)

@router.message(OrderFlow.filling_fields)
async def fill_fields(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    fields = data.get("required_fields", [])
    collected = data.get("collected", {})
    # determine which field we are on:
    for f in fields:
        if f not in collected:
            collected[f] = message.text
            break
    # find next field
    next_field = None
    for f in fields:
        if f not in collected:
            next_field = f
            break
    await state.update_data(collected=collected)
    if next_field:
        await message.answer(ASK_REQUIRED_FIELD.format(field=next_field))
    else:
        await ask_payment(message, state, db)

async def ask_payment(message: Message, state: FSMContext, db: AsyncSession):
    # show payment methods based on settings
    has_zp = bool(settings.ZARINPAL_MERCHANT_ID)
    has_idpay = bool(settings.IDPAY_API_KEY)
    await message.answer(ASK_PAYMENT_METHOD, reply_markup=payment_methods_kb(has_zp, has_idpay))
    await state.set_state(OrderFlow.choosing_payment)

@router.callback_query(F.data.startswith("pay:"), OrderFlow.choosing_payment)
async def choose_payment(cb: CallbackQuery, state: FSMContext, db: AsyncSession):
    method = cb.data.split(":")[1]
    data = await state.get_data()
    # load product & plan to get price
    from sqlalchemy import select
    from ..models import ProductPlan, Order
    res = await db.execute(select(ProductPlan).where(ProductPlan.id == data["plan_id"]))
    plan = res.scalar_one()
    amount = int(plan.price)
    # create order
    order = Order(
        user_id=(await db.execute(select(User).where(User.tg_id==cb.from_user.id))).scalar_one().id,
        product_id=data["product_id"],
        plan_id=data["plan_id"],
        amount=amount,
        status=OrderStatus.pending
    )
    db.add(order)
    await db.flush()
    # save meta fields
    for k, v in (data.get("collected") or {}).items():
        db.add(OrderMeta(order_id=order.id, key=k, value=v))
    await db.commit()

    if method == "c2c":
        await handle_card_to_card(cb, order, db)
    elif method == "zarinpal":
        await handle_zarinpal(cb, order, db)
    elif method == "idpay":
        await handle_idpay(cb, order, db)
    else:
        await cb.answer("روش ناشناخته.", show_alert=True)

async def handle_card_to_card(cb: CallbackQuery, order: Order, db: AsyncSession):
    from ..utils import get_or_create_settings
    s = await get_or_create_settings(db)
    card = s.card_number or "ثبت نشده"
    await cb.message.edit_text(CARD_TO_CARD_INSTRUCTION.format(amount=int(order.amount), card=card))
    await cb.message.answer(SEND_PROOF_TEXT)
    await cb.message.answer(SEND_PROOF_PHOTO)
    # move state to manual proof
    await OrderFlow.manual_proof_text.set()

@router.message(OrderFlow.manual_proof_text)
async def manual_proof_text(message: Message, state: FSMContext, db: AsyncSession):
    # attach to last pending order of user
    from sqlalchemy import select, desc
    from ..models import Order, ManualProof, OrderStatus, User
    u = (await db.execute(select(User).where(User.tg_id==message.from_user.id))).scalar_one()
    q = await db.execute(select(Order).where(Order.user_id==u.id).order_by(desc(Order.id)))
    order = q.scalars().first()
    if not order:
        await message.answer(ERROR)
        await state.clear()
        return
    db.add(ManualProof(order_id=order.id, text=message.text))
    order.status = OrderStatus.awaiting_manual_review
    await db.commit()
    await message.answer("اطلاعات شما ثبت شد. اگر رسید تصویری دارید ارسال کنید یا /skip بزنید.")
    await OrderFlow.manual_proof_photo.set()

@router.message(OrderFlow.manual_proof_photo, F.photo)
async def manual_proof_photo(message: Message, state: FSMContext, db: AsyncSession):
    from sqlalchemy import select, desc
    from ..models import Order, ManualProof, User
    u = (await db.execute(select(User).where(User.tg_id==message.from_user.id))).scalar_one()
    q = await db.execute(select(Order).where(Order.user_id==u.id).order_by(desc(Order.id)))
    order = q.scalars().first()
    if order:
        file_id = message.photo[-1].file_id
        # update latest proof row
        from sqlalchemy import select as sel
        res = await db.execute(sel(ManualProof).where(ManualProof.order_id==order.id).order_by(ManualProof.id.desc()))
        proof = res.scalars().first()
        if proof:
            proof.photo_file_id = file_id
            await db.commit()
    await message.answer("رسید تصویری ذخیره شد. در انتظار تایید ادمین باشید.")
    await state.clear()

@router.message(OrderFlow.manual_proof_photo, F.text == "/skip")
async def manual_proof_skip(message: Message, state: FSMContext):
    await message.answer("باشه. سفارش شما در صف بررسی دستی است.")
    await state.clear()

async def handle_zarinpal(cb: CallbackQuery, order: Order, db: AsyncSession):
    if not settings.ZARINPAL_MERCHANT_ID:
        await cb.answer("زرین‌پال تنظیم نشده.", show_alert=True)
        return
    zp = ZarinpalGateway()
    callback_url = f"{settings.BASE_URL}/payments/zarinpal/callback?oid={order.id}"
    link = await zp.create_payment(amount=int(order.amount), description=f"Order#{order.id}", callback_url=callback_url)
    order.payment_method = PaymentMethod.zarinpal
    order.gateway = "zarinpal"
    order.gateway_authority = link.authority
    await db.commit()
    await cb.message.edit_text(f"برای پرداخت روی لینک زیر بزنید:\n{link.url}")

async def handle_idpay(cb: CallbackQuery, order: Order, db: AsyncSession):
    if not settings.IDPAY_API_KEY:
        await cb.answer("آیدی‌پی تنظیم نشده.", show_alert=True)
        return
    gw = IDPayGateway()
    callback_url = f"{settings.BASE_URL}/payments/idpay/callback?oid={order.id}"
    link = await gw.create_payment(amount=int(order.amount), description=f"Order#{order.id}", callback_url=callback_url)
    order.payment_method = PaymentMethod.idpay
    order.gateway = "idpay"
    order.gateway_authority = link.authority
    await db.commit()
    await cb.message.edit_text(f"برای پرداخت روی لینک زیر بزنید:\n{link.url}")
