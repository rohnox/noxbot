from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, PreCheckoutQueryHandler, ContextTypes, filters
)
from config import BOT_TOKEN, USE_WEBHOOK, WEBHOOK_URL, WEBHOOK_PATH, LISTEN_ADDR, PORT
from database import init_db
from utils.logger import setup_logging
from handlers.start import start
from handlers.help import help_cmd
from handlers.shop import store_cmd, store_cb
from handlers.payments import precheckout, successful_payment
from handlers.orders import my_orders
from handlers.admin_basic import stats_cmd, broadcast_start, broadcast_receive, broadcast_cancel
from handlers.admin_panel import admin_entry, admin_cb
from handlers.admin_codes_capture import capture_codes
from handlers.admin_add_product import (
    addproduct_start, addproduct_title, addproduct_price, addproduct_currency,
    addproduct_type, addproduct_asset, addproduct_cancel,
    TITLE, PRICE, CURRENCY, TYPE, ASSET
)

async def unknown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await (update.effective_message or update.effective_chat).reply_text("Unknown. See /help")

def main():
    setup_logging()
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # User
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("store", store_cmd))
    app.add_handler(CallbackQueryHandler(store_cb, pattern=r"^(VIEW_|BUY_|STORE_BACK)"))
    app.add_handler(CommandHandler("orders", my_orders))

    # Payments
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # Admin
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_receive)]},
        fallbacks=[CommandHandler("cancel", broadcast_cancel)]
    ))
    app.add_handler(CommandHandler("admin", admin_entry))
    app.add_handler(CallbackQueryHandler(admin_cb, pattern=r"^ADM_"))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("addproduct", addproduct_start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addproduct_title)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addproduct_price)],
            CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, addproduct_currency)],
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addproduct_type)],
            ASSET: [
                MessageHandler(filters.Document.ALL, addproduct_asset),
                MessageHandler(filters.TEXT & ~filters.COMMAND, addproduct_asset),
            ],
        },
        fallbacks=[CommandHandler("cancel", addproduct_cancel)]
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, capture_codes))

    # Unknown
    app.add_handler(MessageHandler(filters.COMMAND, unknown_cmd))

    if USE_WEBHOOK and WEBHOOK_URL:
        path = WEBHOOK_PATH
        app.run_webhook(
            listen=LISTEN_ADDR,
            port=PORT,
            url_path=path,
            webhook_url=(WEBHOOK_URL.rstrip("/") + ("/" + path if path else "")),
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
