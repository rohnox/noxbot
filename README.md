# NoxShop Pro Bot (aiogram v3)
- پنل مدیریت خودکار برای ادمین‌ها
- سفارش با اعلان به کانال با هشتگ #سفارش_{ID}
- پیام/فوروارد همگانی
- تنظیمات از پنل: خوش‌آمدگویی، پشتیبانی، کارت، کانال سفارش‌ها، کانال اصلی

## Run
pip install -r requirements.txt
cp .env.example .env
python -m app.run_polling

### تنظیم کانال اصلی (اختیاری)
در `.env` مقدار `MAIN_CHANNEL=@your_channel` را بگذارید یا از پنل مدیریت ↦ تنظیمات ↦ «کانال اصلی» تنظیم کنید.
