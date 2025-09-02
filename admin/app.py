# admin/app.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from common.db import SessionLocal
from common.models import Order, Product
from common.settings import Settings

settings = Settings()

# SessionMiddleware را هنگام ساخت اپ اضافه می‌کنیم تا جلوتر از میدل‌ویرهای تابعی اجرا شود
middleware = [
    Middleware(
        SessionMiddleware,
        secret_key=settings.ADMIN_SECRET,
        same_site="lax",
        https_only=False,     # اگر SSL داری True کن
        max_age=60 * 60 * 8,  # 8 ساعت
    )
]
app = FastAPI(middleware=middleware)

# Static & Templates
app.mount('/static', StaticFiles(directory='admin/static'), name='static')
templates = Jinja2Templates(directory='admin/templates')

# ... بالای فایل همان import ها ...

EXEMPT_PREFIXES = ("/static",)
EXEMPT_EXACT = ("/favicon.ico", "/login")  # توجه: login هم پشت گیت می‌ره، ولی بعد از gate_ok

@app.middleware("http")
async def gate_guard(request: Request, call_next):
    """
    اگر ADMIN_GATE_TOKEN ست شده باشد:
      - تا وقتی session['gate_ok']=True نشده، همه مسیرها 404 می‌دهند
      - فقط وقتی ?<ADMIN_GATE_PARAM>=<ADMIN_GATE_TOKEN> در URL باشد، gate_ok می‌شود
      - سپس برای جلوگیری از لو رفتن توکن، ریدایرکت می‌کنیم به همان URL بدون پارامتر
    اگر ADMIN_GATE_TOKEN خالی باشد: گیت غیرفعال است.
    """
    if not settings.ADMIN_GATE_TOKEN:
        return await call_next(request)

    # اجازه‌ی درخواست‌هایی که کوششی برای فعال‌سازی گیت دارند
    qp = dict(request.query_params)
    token = qp.get(settings.ADMIN_GATE_PARAM)

    session = request.scope.get("session") or {}
    if session.get("gate_ok") is True:
        return await call_next(request)

    if token == settings.ADMIN_GATE_TOKEN:
        # فعال‌سازی گِیت برای این سشن
        request.session["gate_ok"] = True
        # ریدایرکت به همان آدرس بدون پارامترِ gate
        from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
        parts = urlsplit(str(request.url))
        q = dict(parse_qsl(parts.query))
        q.pop(settings.ADMIN_GATE_PARAM, None)
        new_query = urlencode(q)
        clean_url = urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))
        return RedirectResponse(url=clean_url, status_code=303)

    # در غیر این صورت، هیچ چیزی لو نده: 404
    from fastapi import Response
    return Response(status_code=404)

# (حالا auth_guard بعد از gate_guard قرار بگیرد)
@app.middleware("http")
async def auth_guard(request: Request, call_next):
    path = request.url.path
    if path in ("/login", "/favicon.ico") or any(path.startswith(p) for p in ("/static",)):
        # حتی /login هم باید از گیت عبور کرده باشد؛ اما اگر gate_ok شده باشد، اجازه می‌دهیم
        session = request.scope.get("session") or {}
        if not session.get("gate_ok"):
            from fastapi import Response
            return Response(status_code=404)
        # در صورت گذشتن از گیت، اجازه بدهد ادامه دهد
        return await call_next(request)

    # برای بقیه مسیرها هم ابتدا gate_ok لازم است
    session = request.scope.get("session") or {}
    if not session.get("gate_ok"):
        from fastapi import Response
        return Response(status_code=404)

    # سپس بررسی لاگین
    if not session.get("auth", False):
        return RedirectResponse(url="/login", status_code=303)

    return await call_next(request)

