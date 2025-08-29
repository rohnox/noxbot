from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def store_list_keyboard(items):
    rows = []
    for pid, title in items:
        rows.append([InlineKeyboardButton(f"{title}", callback_data=f"VIEW_{pid}")])
    return InlineKeyboardMarkup(rows)

def product_keyboard(pid: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("خرید 🛒", callback_data=f"BUY_{pid}")],
        [InlineKeyboardButton("بازگشت ⬅️", callback_data="STORE_BACK")]
    ])

def admin_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Dashboard", callback_data="ADM_DASH"),
         InlineKeyboardButton("Orders", callback_data="ADM_ORDERS"),
         InlineKeyboardButton("Products", callback_data="ADM_PRODUCTS")],
    ])

def orders_list_keyboard(order_pairs, page: int, has_next: bool):
    rows = []
    for oid, code in order_pairs:
        rows.append([InlineKeyboardButton(f"#{code}", callback_data=f"ADM_ORDER_{oid}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"ADM_ORDERS_PAGE_{page-1}"))
    if has_next:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"ADM_ORDERS_PAGE_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("Back", callback_data="ADM_DASH")])
    return InlineKeyboardMarkup(rows)

def order_detail_keyboard(oid: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("پرداخت شد", callback_data=f"ADM_SET_PAID_{oid}"),
         InlineKeyboardButton("درحال پردازش", callback_data=f"ADM_SET_PROC_{oid}")],
        [InlineKeyboardButton("تحویل شد", callback_data=f"ADM_SET_DELIV_{oid}"),
         InlineKeyboardButton("لغو شد", callback_data=f"ADM_SET_CANCEL_{oid}")],
        [InlineKeyboardButton("عودت شد", callback_data=f"ADM_SET_REF_{oid}")],
        [InlineKeyboardButton("ارسال مجدد کالا", callback_data=f"ADM_SEND_AGAIN_{oid}")],
        [InlineKeyboardButton("Back", callback_data="ADM_ORDERS")]
    ])

def products_list_keyboard(prod_pairs):
    rows = []
    for pid, title in prod_pairs:
        rows.append([InlineKeyboardButton(f"{title}", callback_data=f"ADM_PROD_{pid}")])
    rows.append([InlineKeyboardButton("➕ افزودن محصول", callback_data="ADM_ADD_PROD")])
    rows.append([InlineKeyboardButton("Back", callback_data="ADM_DASH")])
    return InlineKeyboardMarkup(rows)

def product_admin_keyboard(pid: int, active: bool):
    label = "غیرفعال‌کردن" if active else "فعال‌کردن"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=f"ADM_TOGGLE_{pid}")],
        [InlineKeyboardButton("افزودن کد لایسنس", callback_data=f"ADM_ADD_CODES_{pid}")],
        [InlineKeyboardButton("Back", callback_data="ADM_PRODUCTS")]
    ])
