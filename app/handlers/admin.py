from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ..texts import *
from ..keyboards import admin_panel_kb, admin_settings_kb, categories_kb, products_kb, orders_actions_kb
from ..utils import IsAdmin, get_or_create_settings
from ..models import Category, Product, ProductPlan, Setting, Order, OrderStatus

router = Router(name="admin")
router.message.filter(IsAdmin())

class AdminStates(StatesGroup):
    adding_category = State()
    adding_product = State()
    setting_desc = State()
    setting_category_for_product = State()
    adding_plan = State()
    setting_required_fields = State()
    set_support = State()
    set_channel = State()
    set_card = State()
    set_zp_mid = State()
    set_zp_sb  = State()
    set_idpay_key = State()
    set_idpay_sb  = State()

@router.callback_query(F.data == "set:zp")
async def set_zp(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer(ADMIN_PROMPT_ZP_MID); await state.set_state(AdminStates.set_zp_mid)

@router.message(AdminStates.set_zp_mid)
async def save_zp_mid(message: Message, db: AsyncSession, state: FSMContext):
    s = await get_or_create_settings(db); s.zarinpal_merchant_id = message.text.strip(); await db.commit()
    await message.answer(ADMIN_PROMPT_ZP_SB); await state.set_state(AdminStates.set_zp_sb)

@router.message(AdminStates.set_zp_sb)
async def save_zp_sb(message: Message, db: AsyncSession, state: FSMContext):
    s = await get_or_create_settings(db); s.zarinpal_sandbox = (message.text.strip() in ("1","true","True")); await db.commit()
    await message.answer(ADMIN_SAVED); await state.clear()

@router.callback_query(F.data == "set:idpay")
async def set_idpay(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer(ADMIN_PROMPT_IDPAY_KEY); await state.set_state(AdminStates.set_idpay_key)

@router.message(AdminStates.set_idpay_key)
async def save_idpay_key(message: Message, db: AsyncSession, state: FSMContext):
    s = await get_or_create_settings(db); s.idpay_api_key = message.text.strip(); await db.commit()
    await message.answer(ADMIN_PROMPT_IDPAY_SB); await state.set_state(AdminStates.set_idpay_sb)

@router.message(AdminStates.set_idpay_sb)
async def save_idpay_sb(message: Message, db: AsyncSession, state: FSMContext):
    s = await get_or_create_settings(db); s.idpay_sandbox = (message.text.strip() in ("1","true","True")); await db.commit()
    await message.answer(ADMIN_SAVED); await state.clear()
    
@router.message(F.text == "/admin")
async def admin_start(message: Message):
    await message.answer(ADMIN_PANEL, reply_markup=admin_panel_kb())

@router.message(F.text == ADMIN_SETTINGS)
async def admin_settings(message: Message, db: AsyncSession):
    s = await get_or_create_settings(db)
    txt = (f"یوزرنیم پشتیبانی: @{s.support_username}\n" if s.support_username else "پشتیبانی: تنظیم نشده\n")
    txt += (f"کانال: @{s.channel_username}\n" if s.channel_username else "کانال: تنظیم نشده\n")
    txt += (f"کارت: {s.card_number}" if s.card_number else "کارت: تنظیم نشده")
    await message.answer(txt, reply_markup=admin_settings_kb())

@router.callback_query(F.data == "set:support")
async def set_support(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer(ADMIN_PROMPT_SUPPORT)
    await state.set_state(AdminStates.set_support)

@router.message(AdminStates.set_support)
async def set_support_save(message: Message, db: AsyncSession, state: FSMContext):
    s = await get_or_create_settings(db)
    s.support_username = message.text.strip().lstrip("@")
    await db.commit()
    await message.answer(ADMIN_SAVED)
    await state.clear()

@router.callback_query(F.data == "set:channel")
async def set_channel(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer(ADMIN_PROMPT_CHANNEL)
    await state.set_state(AdminStates.set_channel)

@router.message(AdminStates.set_channel)
async def set_channel_save(message: Message, db: AsyncSession, state: FSMContext):
    s = await get_or_create_settings(db)
    s.channel_username = message.text.strip().lstrip("@")
    await db.commit()
    await message.answer(ADMIN_SAVED)
    await state.clear()

@router.callback_query(F.data == "set:card")
async def set_card(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer(ADMIN_PROMPT_CARD)
    await state.set_state(AdminStates.set_card)

@router.message(AdminStates.set_card)
async def set_card_save(message: Message, db: AsyncSession, state: FSMContext):
    s = await get_or_create_settings(db)
    s.card_number = message.text.strip().replace(" ", "")
    await db.commit()
    await message.answer(ADMIN_SAVED)
    await state.clear()

@router.message(F.text == ADMIN_MANAGE_CATS)
async def manage_cats(message: Message, db: AsyncSession, state: FSMContext):
    res = await db.execute(select(Category))
    cats = res.scalars().all()
    txt = ADMIN_CATS_LIST + "\n" + "\n".join([f"#{c.id} - {c.title}" for c in cats]) if cats else "هیچ دسته‌ای نیست."
    await message.answer(txt, reply_markup=None)
    await message.answer("برای افزودن دسته، متن «/addcat» را بفرستید. برای حذف: «/delcat <id>».")

@router.message(F.text == "/addcat")
async def add_category_prompt(message: Message, state: FSMContext):
    await message.answer(ADMIN_ADD_CATEGORY_PROMPT)
    await state.set_state(AdminStates.adding_category)

@router.message(AdminStates.adding_category)
async def add_category_save(message: Message, db: AsyncSession, state: FSMContext):
    db.add(Category(title=message.text.strip()))
    await db.commit()
    await message.answer(ADMIN_SAVED)
    await state.clear()

@router.message(F.text.startswith("/delcat"))
async def delete_category(message: Message, db: AsyncSession):
    try:
        _, cid = message.text.split()
        cid = int(cid)
    except:
        await message.answer("فرمت صحیح: /delcat <id>")
        return
    await db.execute(delete(Category).where(Category.id==cid))
    await db.commit()
    await message.answer("حذف شد.")

@router.message(F.text == ADMIN_MANAGE_PRODUCTS)
async def manage_products(message: Message, db: AsyncSession):
    res = await db.execute(select(Product))
    products = res.scalars().all()
    if not products:
        await message.answer("محصولی وجود ندارد. با /addproduct اضافه کنید.")
        return
    await message.answer(ADMIN_PRODUCTS_LIST)
    await message.answer("برای افزودن: /addproduct \nبرای حذف: /delproduct <id>\nبرای تنظیم توضیح: /setdesc <id>\nبرای انتساب دسته: /setcat <id>\nبرای افزودن پلن: /addplan <id>\nبرای فیلدهای لازم: /setfields <id>")

@router.message(F.text == "/addproduct")
async def add_product_prompt(message: Message, state: FSMContext):
    await message.answer(ADMIN_ADD_PRODUCT_PROMPT)
    await state.set_state(AdminStates.adding_product)

@router.message(AdminStates.adding_product)
async def add_product_save(message: Message, db: AsyncSession, state: FSMContext):
    p = Product(title=message.text.strip(), is_active=True)
    db.add(p)
    await db.commit()
    await message.answer(ADMIN_SAVED + " اکنون /setdesc و /addplan را اجرا کنید.")
    await state.clear()

@router.message(F.text.startswith("/delproduct"))
async def delete_product(message: Message, db: AsyncSession):
    try:
        _, pid = message.text.split()
        pid = int(pid)
    except:
        await message.answer("فرمت صحیح: /delproduct <id>")
        return
    await db.execute(delete(Product).where(Product.id==pid))
    await db.commit()
    await message.answer("حذف شد.")

@router.message(F.text.startswith("/setdesc"))
async def set_desc_prompt(message: Message, state: FSMContext):
    try:
        _, pid = message.text.split()
        await state.update_data(pid=int(pid))
        await message.answer(ADMIN_SET_PRODUCT_DESC_PROMPT)
        await state.set_state(AdminStates.setting_desc)
    except:
        await message.answer("فرمت صحیح: /setdesc <id>")

@router.message(AdminStates.setting_desc)
async def set_desc_save(message: Message, db: AsyncSession, state: FSMContext):
    data = await state.get_data()
    pid = data["pid"]
    res = await db.execute(select(Product).where(Product.id==pid))
    p = res.scalar_one()
    if message.text != "/skip":
        p.description = message.text
    await db.commit()
    await message.answer(ADMIN_SAVED)
    await state.clear()

@router.message(F.text.startswith("/setcat"))
async def set_cat_prompt(message: Message, state: FSMContext):
    try:
        _, pid = message.text.split()
        await state.update_data(pid=int(pid))
        await message.answer(ADMIN_SET_PRODUCT_CATEGORY_PROMPT)
        await state.set_state(AdminStates.setting_category_for_product)
    except:
        await message.answer("فرمت صحیح: /setcat <id>")

@router.message(AdminStates.setting_category_for_product)
async def set_cat_save(message: Message, db: AsyncSession, state: FSMContext):
    data = await state.get_data()
    pid = data["pid"]
    res = await db.execute(select(Product).where(Product.id==pid))
    p = res.scalar_one()
    if message.text != "/skip":
        p.category_id = int(message.text)
    await db.commit()
    await message.answer(ADMIN_SAVED)
    await state.clear()

@router.message(F.text.startswith("/addplan"))
async def add_plan_prompt(message: Message, state: FSMContext):
    try:
        _, pid = message.text.split()
        await state.update_data(pid=int(pid))
        await message.answer(ADMIN_ADD_PLAN_PROMPT)
        await state.set_state(AdminStates.adding_plan)
    except:
        await message.answer("فرمت صحیح: /addplan <id>")

@router.message(AdminStates.adding_plan)
async def add_plan_save(message: Message, db: AsyncSession, state: FSMContext):
    if message.text == "/done":
        await message.answer("اتمام افزودن پلن‌ها.")
        await state.clear()
        return
    try:
        title, price = [x.strip() for x in message.text.split("-")]
        price = float(price.replace(",", ""))
    except:
        await message.answer("فرمت صحیح: «عنوان - قیمت». مثال: سه‌ماهه - 150000")
        return
    data = await state.get_data()
    pid = data["pid"]
    db.add(ProductPlan(product_id=pid, title=title, price=price))
    await db.commit()
    await message.answer("پلن ثبت شد. مورد بعدی یا /done")

@router.message(F.text.startswith("/setfields"))
async def set_fields_prompt(message: Message, state: FSMContext):
    try:
        _, pid = message.text.split()
        await state.update_data(pid=int(pid))
        await message.answer(ADMIN_SET_REQUIRED_FIELDS_PROMPT)
        await state.set_state(AdminStates.setting_required_fields)
    except:
        await message.answer("فرمت صحیح: /setfields <id>")

@router.message(AdminStates.setting_required_fields)
async def set_fields_save(message: Message, db: AsyncSession, state: FSMContext):
    import json
    data = await state.get_data()
    pid = data["pid"]
    res = await db.execute(select(Product).where(Product.id==pid))
    p = res.scalar_one()
    if message.text != "/skip":
        try:
            arr = json.loads(message.text)
            if not isinstance(arr, list):
                raise ValueError("not a list")
            p.required_fields = arr
        except Exception as e:
            await message.answer("JSON نامعتبر. نمونه صحیح: [\"username_receiver\", \"note\"]")
            return
    await db.commit()
    await message.answer(ADMIN_SAVED)
    await state.clear()

@router.message(F.text == ADMIN_MANAGE_ORDERS)
async def manage_orders(message: Message, db: AsyncSession):
    res = await db.execute(select(Order).where(Order.status==OrderStatus.awaiting_manual_review))
    orders = res.scalars().all()
    if not orders:
        await message.answer("سفارش در انتظار بررسی وجود ندارد.")
        return
    await message.answer(ORDERS_PENDING)
    for o in orders:
        await message.answer(
            ORDER_ROW.format(oid=o.id, uid=o.user_id, amount=int(o.amount), pm=o.payment_method, st=o.status),
            reply_markup=orders_actions_kb(o.id)
        )

@router.callback_query(F.data.startswith("order:approve:"))
async def approve_order(cb: CallbackQuery, db: AsyncSession):
    oid = int(cb.data.split(":")[2])
    res = await db.execute(select(Order).where(Order.id==oid))
    o = res.scalar_one_or_none()
    if not o:
        await cb.answer("پیدا نشد.", show_alert=True)
        return
    o.status = OrderStatus.paid
    await db.commit()
    await cb.message.edit_text(ORDER_APPROVED)

@router.callback_query(F.data.startswith("order:reject:"))
async def reject_order(cb: CallbackQuery, db: AsyncSession):
    oid = int(cb.data.split(":")[2])
    res = await db.execute(select(Order).where(Order.id==oid))
    o = res.scalar_one_or_none()
    if not o:
        await cb.answer("پیدا نشد.", show_alert=True)
        return
    o.status = OrderStatus.canceled
    await db.commit()
    await cb.message.edit_text(ORDER_REJECTED)
