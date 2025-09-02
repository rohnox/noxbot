# admin/app.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from common.db import SessionLocal
from common.models import Order, Product
from common.settings import Settings

settings = Settings()

# 1) SessionMiddleware را موقع ساخت اپ اضافه کن تا قبل از میدل‌ویرهای تابعی اجرا شود
middleware = [
    Middleware(
        SessionMiddleware,
        secret_key=settings.ADMIN_SECRET,
        same_site="lax",
        https_only=False,     # اگر SSL داری True کن
        max_age=60 * 60 * 8,  # 8h
    )
]
app = FastAPI(middleware=middleware)

app.mount('/static', StaticFiles(directory='admin/static'), name='static')
templates = Jinja2Templates(directory='admin/templates')

EXEMPT_PATHS = ("/login", "/static", "/favicon.ico")

# 2) از scope برای دسترسی به سشن استفاده کن تا اگر هنوز نبود Assert نشود
@app.middleware("http")
async def auth_guard(request: Request, call_next):
    path = request.url.path
    if path == "/" or any(path.startswith(p) for p in EXEMPT_PATHS):
        return await call_next(request)
    session = request.scope.get("session")  # ممکن است None باشد اگر SessionMiddleware نرسیده باشد
    if not (session and session.get("auth", False)):
        return RedirectResponse(url="/login", status_code=303)
    return await call_next(request)

# --- login/logout ---
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # در اینجا SessionMiddleware تا این لحظه اجرا شده و request.session امن است
    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        request.session["auth"] = True
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "نام کاربری یا رمز عبور اشتباه است."})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

# --- dashboard ---
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    with SessionLocal() as s:
        orders_count = s.query(Order).count()
        products_count = s.query(Product).count()
    return templates.TemplateResponse('dashboard.html', {
        'request': request,
        'orders_count': orders_count,
        'products_count': products_count
    })

# --- orders ---
@app.get('/orders', response_class=HTMLResponse)
async def orders_list(request: Request):
    with SessionLocal() as s:
        orders = s.query(Order).order_by(Order.id.desc()).limit(100).all()
    return templates.TemplateResponse('orders_list.html', {'request': request, 'orders': orders})

@app.post('/orders/{oid}/status')
async def update_status(oid: int, status: str = Form(...)):
    with SessionLocal() as s:
        o = s.get(Order, oid)
        if o:
            o.status = status
            s.commit()
    return RedirectResponse(url='/orders', status_code=303)

# --- products (CRUD) ---
@app.get('/products', response_class=HTMLResponse)
async def products_list(request: Request):
    with SessionLocal() as s:
        products = s.query(Product).order_by(Product.id.desc()).all()
    return templates.TemplateResponse('products.html', {'request': request, 'products': products})

@app.post('/products/create')
async def products_create(kind: str = Form(...), name: str = Form(...), price: int = Form(...), currency: str = Form("IRR"), is_active: str = Form("on")):
    active = True if is_active == "on" else False
    with SessionLocal() as s:
        p = Product(kind=kind, name=name, price=price, currency=currency, is_active=active)
        s.add(p)
        s.commit()
    return RedirectResponse(url='/products', status_code=303)

@app.post('/products/{pid}/update')
async def products_update(pid: int, name: str = Form(...), price: int = Form(...), currency: str = Form(...)):
    with SessionLocal() as s:
        p = s.get(Product, pid)
        if p:
            p.name = name
            p.price = price
            p.currency = currency
            s.commit()
    return RedirectResponse(url='/products', status_code=303)

@app.post('/products/{pid}/toggle')
async def products_toggle(pid: int):
    with SessionLocal() as s:
        p = s.get(Product, pid)
        if p:
            p.is_active = not p.is_active
            s.commit()
    return RedirectResponse(url='/products', status_code=303)

@app.post('/products/{pid}/delete')
async def products_delete(pid: int):
    with SessionLocal() as s:
        p = s.get(Product, pid)
        if p:
            s.delete(p)
            s.commit()
    return RedirectResponse(url='/products', status_code=303)
