# -*- coding: utf-8 -*-
MAIN_HELP = (
    "منوی اصلی:\n"
    "• 🛍️ فروشگاه\n"
    "• 👤 حساب\n"
    "• 🆘 پشتیبانی\n"
)
ACCOUNT_TEXT = "👤 حساب کاربری شما:\nID: {id}\nنام: {name}\nیوزرنیم: @{username}\nسفارش‌ها: {orders_total} (تاییدشده: {orders_ok}, در انتظار: {orders_review})"
SUPPORT_TEXT = "برای ارتباط با پشتیبانی به @{username} پیام دهید."
EMPTY_LIST = "هیچ موردی یافت نشد."
CANCELLED = "لغو شد."

ADMIN_PANEL_TITLE = "پنل مدیریت 🛠️"
ADMIN_MENU_TEXT = "به پنل مدیریت خوش آمدید.\nیک گزینه را انتخاب کنید:"
ADMIN_NEED = "این بخش مخصوص مدیر است."
BROADCAST_COPY_PROMPT = "پیام یا رسانه‌ای که می‌خواهید \"کپی همگانی\" شود را ارسال کنید."
BROADCAST_FORWARD_PROMPT = "پیام را از جایی فوروارد کنید تا به همه ارسال شود."
BROADCAST_DONE = "ارسال به {n} کاربر انجام شد."
SET_WELCOME_PROMPT = "متن جدید خوش‌آمدگویی را ارسال کنید."
SET_SUPPORT_PROMPT = "یوزرنیم پشتیبانی (بدون @) را ارسال کنید."
SET_CARD_PROMPT = "شماره کارت جدید را ارسال کنید."
SET_CHANNEL_PROMPT = "یوزرنیم/آیدی کانال سفارش‌ها را ارسال کنید (مثال: @my_orders یا -100...)"

WELCOME_FALLBACK = "سلام! به فروشگاه خوش اومدی ✨"
STORE_CHOOSE_CATEGORY = "یک دسته را انتخاب کنید:"
STORE_CHOOSE_PRODUCT = "یک محصول را انتخاب کنید:"
STORE_CHOOSE_PLAN = "یک پلن را انتخاب کنید:"
STORE_SUMMARY = (
    "خلاصه سفارش:\n"
    "محصول: {product}\n"
    "پلن: {plan}\n"
    "قیمت: {price:,} تومان\n\n"
    "برای ادامه پرداخت، روی «پرداخت کارت به کارت 💳» بزنید."
)
CARD_INFO = "لطفاً مبلغ {price:,} تومان را به کارت زیر واریز کنید و سپس رسید را ارسال کنید:\n\n{card}\n\nسپس روی «ارسال رسید» بزنید."
SEND_PROOF_PROMPT = "رسید پرداخت را به صورت عکس یا متن ارسال کنید."
PROOF_SAVED = "رسید دریافت شد و سفارش شما در حال بررسی است. نتیجه به شما اطلاع داده می‌شود."
ORDER_APPROVED_USER = "✅ سفارش شما تایید شد. سپاس از خرید شما."
ORDER_REJECTED_USER = "❌ سفارش شما رد شد. لطفاً با پشتیبانی در ارتباط باشید."

MAIN_CHANNEL_BTN = "📣 کانال ما"

ADD_NOTE_PROMPT = "توضیح/درخواست اضافه خود را ارسال کنید (اختیاری). برای رد شدن از این مرحله /skip بزنید."
NOTE_SAVED = "توضیح شما ذخیره شد."
CONTINUE_TO_PAY = "برای ادامه پرداخت، روی «ادامه پرداخت 💳» بزنید."

ORDERS_MINE_TITLE = "📦 سفارشات من (۵ مورد اخیر):"
ORDER_ITEM_LINE = "• #{id} | کد پیگیری: {trk} | وضعیت: {status}"
ORDER_DETAIL = (
    "جزئیات سفارش #{id}\n"
    "کد پیگیری: {trk}\n"
    "محصول: {product}\n"
    "پلن: {plan}\n"
    "توضیح پلن: {desc}\n"
    "قیمت: {price:,} تومان\n"
    "وضعیت: {status}"
)

TRACKING_ASSIGNED = "✅ سفارش شما ثبت شد. کد پیگیری: {trk}\nبرای ادامه پرداخت، روی «ارسال رسید» بزنید."
ORDER_PROCESSING_USER = "🔧 سفارش شما با کد پیگیری {trk} در حال انجام است."
ORDER_COMPLETED_USER = "🎉 سفارش شما با کد پیگیری {trk} انجام شد. سپاس از شما!"
ORDER_REJECTED_USER = "❌ سفارش شما با کد پیگیری {trk} رد شد. لطفاً با پشتیبانی در ارتباط باشید."

SUPPORT_BTN = "🆘 ارتباط با پشتیبانی"
MY_ORDERS_BTN = "📦 سفارشات من"
VIEW_DETAILS_BTN = "🔎 جزئیات"
