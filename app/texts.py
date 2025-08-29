WELCOME = (
    "سلام! به فروشگاه ما خوش آمدید.\n"
    "از منوی زیر یکی را انتخاب کنید:"
)

MENU_STORE = "ورود به فروشگاه 🛍️"
MENU_ACCOUNT = "حساب کاربری 👤"
MENU_SUPPORT = "پشتیبانی 🛟"
MENU_CHANNEL = "کانال ما 📣"

ACCOUNT_TEMPLATE = (
    "مشخصات حساب شما:\n"
    "• شناسه: <code>{tg_id}</code>\n"
    "• نام: {name}\n"
    "• نام‌کاربری: @{username}\n"
    "• تاریخ عضویت: {joined_at}"
)

NO_CHANNEL = "کانالی ثبت نشده است."
SUPPORT_TEXT_TEMPLATE = "برای ارتباط با پشتیبانی به @{support} پیام بدهید."

ASK_CATEGORY = "یکی از دسته‌ها را انتخاب کنید:"
ASK_PRODUCT = "یکی از محصولات را انتخاب کنید:"
ASK_PLAN = "پلن مورد نظر را انتخاب کنید:"
PRODUCT_DESC = "توضیحات: {desc}"

ASK_REQUIRED_FIELD = "لطفاً مقدار «{field}» را ارسال کنید:"
ASK_PAYMENT_METHOD = "روش پرداخت را انتخاب کنید:"
PAY_CARD_TO_CARD = "کارت به کارت 💳"
PAY_ZARINPAL = "زرین‌پال"
PAY_IDPAY = "آیدی‌پی"

CARD_TO_CARD_INSTRUCTION = (
    "لطفاً مبلغ <b>{amount}</b> تومان را به کارت زیر واریز کنید و سپس <b>شماره پیگیری و چهار رقم آخر کارت مبدا</b> را برای بررسی ارسال کنید.\n"
    "<code>{card}</code>"
)

SEND_PROOF_TEXT = "شماره پیگیری و چهار رقم آخر کارت را ارسال کنید:"
SEND_PROOF_PHOTO = "در صورت تمایل تصویر رسید را هم ارسال کنید یا /skip را بزنید."

ADMIN_ONLY = "این بخش مخصوص ادمین است."
ADMIN_PANEL = "پنل ادمین را انتخاب کنید:"
ADMIN_MANAGE_CATS = "مدیریت دسته‌ها"
ADMIN_MANAGE_PRODUCTS = "مدیریت محصولات"
ADMIN_MANAGE_ORDERS = "سفارش‌ها"
ADMIN_SETTINGS = "تنظیمات"
ADMIN_BACK = "بازگشت"

ADMIN_SUPPORT = "تنظیم پشتیبانی/کانال/کارت"
ADMIN_SET_SUPPORT = "تنظیم یوزرنیم پشتیبانی"
ADMIN_SET_CHANNEL = "تنظیم یوزرنیم کانال"
ADMIN_SET_CARD = "تنظیم شماره کارت"

ADMIN_PROMPT_SUPPORT = "یوزرنیم پشتیبانی را بدون @ ارسال کنید:"
ADMIN_PROMPT_CHANNEL = "یوزرنیم کانال را بدون @ ارسال کنید:"
ADMIN_PROMPT_CARD = "شماره کارت را ارسال کنید:"
ADMIN_SAVED = "ذخیره شد ✅"

ADMIN_CATS_LIST = "لیست دسته‌ها:"
ADMIN_PRODUCTS_LIST = "لیست محصولات:"
ADMIN_ADD = "➕ افزودن"
ADMIN_DELETE = "🗑️ حذف"
ADMIN_TOGGLE = "فعال/غیرفعال"
ADMIN_ADD_CATEGORY_PROMPT = "عنوان دسته جدید را ارسال کنید:"
ADMIN_ADD_PRODUCT_PROMPT = "عنوان محصول جدید را ارسال کنید:"
ADMIN_SET_PRODUCT_DESC_PROMPT = "توضیحات محصول را ارسال کنید (یا /skip):"
ADMIN_SET_PRODUCT_CATEGORY_PROMPT = "شناسه دسته را برای انتساب محصول ارسال کنید (یا /skip):"
ADMIN_ADD_PLAN_PROMPT = "برای افزودن پلن، به صورت «عنوان - قیمت» ارسال کنید. پایان: /done"
ADMIN_SET_REQUIRED_FIELDS_PROMPT = (
    "فهرست فیلدهای لازم را به شکل JSON لیست ارسال کنید، مثل: \n"
    "<code>[\"username_receiver\", \"note\"]</code>\n"
    "یا /skip برای خالی."
)

ADMIN_SET_ZARINPAL = "تنظیم زرین‌پال"
ADMIN_SET_IDPAY = "تنظیم آیدی‌پی"
ADMIN_PROMPT_ZP_MID = "MerchantID زرین‌پال را ارسال کنید:"
ADMIN_PROMPT_ZP_SB  = "Sandbox زرین‌پال؟ 1 یا 0 ارسال کنید:"
ADMIN_PROMPT_IDPAY_KEY = "API Key آیدی‌پی را ارسال کنید:"
ADMIN_PROMPT_IDPAY_SB  = "Sandbox آیدی‌پی؟ 1 یا 0 ارسال کنید:"


ORDERS_PENDING = "سفارش‌های در انتظار بررسی:"
ORDER_ROW = "سفارش #{oid} | کاربر {uid} | مبلغ {amount} | روش {pm} | وضعیت {st}"
ORDER_APPROVE = "تایید پرداخت ✅"
ORDER_REJECT = "رد ❌"
ORDER_APPROVED = "سفارش تایید شد ✅"
ORDER_REJECTED = "سفارش رد شد ❌"

ERROR = "خطایی رخ داد. دوباره تلاش کنید."
