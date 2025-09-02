# admin/app.py
from fastapi import FastAPI, APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from common.db import SessionLocal
from common.models import Order, Product
from common.settings import Settings

settings = Settings()

def _normalize_base(p: str) -> str:
    p = (p or "/").strip()
    if p == "/" or p == "":
        return ""  # روت
    if not p.startswith("/"):
        p = "/" + p
    return p.rstrip("/")

BASE = _normalize_base(settings.DASHBOARD_PATH)

middleware = [
    Middleware(
        SessionMiddleware,
        secret_key=settings.ADMIN_SECRET,
        same_site="lax",
        https_only=False,      # اگر SSL داری True
        max_age=60*60*8,       # 8h
    )
]
app = FastAPI(middleware=middleware)

# استاتیک‌ها زیر BASE
app.mount(f"{BASE}/static", StaticFiles(directory="admin/static"), name="static")
templates = Jinja2Templates(directory="admin/templates")

router = APIRouter(prefix=BASE)

EXEMPT_PREFIXES = (f"{BASE}/static",)
EXEMPT_EXACT = (f"{BASE}/favicon.ico", f"{BASE}/login")

REQUIRE_GATE = bool(getattr(settings, "ADMIN_GATE_TOKEN", ""))

@app.middleware("http")
async def gate_guard(request: Request, call_next):
    if not REQUIRE_GATE:
        return await call_next(request)

    session = request.scope.get("session") or {}
    if session.get("gate_ok"):
        return await call_next(request)

    # اگر پارامتر gate موجود و درست بود، gate_ok را ست کن
    param = getattr(settings, "ADMIN_GATE_PARAM", "gate")
    token = request.query_params.get(param)
    if token and token == getattr(settings, "ADMIN_GATE_TOKEN", ""):
        request.session["gate_ok"] = True
        # ریدایرکت به URL بدون پارامتر gate
        from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
        parts = urlsplit(str(request.url))
        q = dict(parse_qsl(parts.query))
        q.pop(param, None)
        new_query = urlencode(q)
        clean = urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))
        return RedirectResponse(url=clean, status_code=303)

    # هیچ چیزی لو نده
    return Response(status_code=404)

@app.middleware("http")
async def auth_guard(request: Request, call_next):
    path = request.url.path
    # اگر گیت فعاله، فقط بعد از gate_ok اجازه بده حتی به /login
    if REQUIRE_GATE and not (request.scope.get("session") or {}).get("gate_ok"):
        return Response(status_code=404)

    if path in EXEMPT_EXACT or any(path.startswith(p) for p in EXEMPT_PREFIXES):
        return await call_next(request)

    session = request.scope.get("session") or {}
    if not session.get("auth", False):
        return RedirectResponse(url=f"{BASE}/login", status_code=303)
    return await call_next(request)

@router.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)

# ---------- Login ----------
@router.get("/login", response_class=HTMLResponse, name="login")
async def login_form(request: Request):
    if (request.scope.get("session") or {}).get("auth"):
        return RedirectResponse(url=request.url_for("dashboard"), status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    from common.settings import Settings
    s = Settings()
    if username == s.ADMIN_USERNAME and password == s.ADMIN_PASSWORD:
        request.session["auth"] = True
        return RedirectResponse(url=request.url_for("dashboard"), status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "نام کاربری یا رمز عبور اشتباه است."})

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url=request.url_for("login"), status_code=303)

# ---------- Dashboard ----------
@router.get("/", response_class=HTMLResponse, name="dashboard")
async def dashboard(request: Request):
    with SessionLocal() as s:
        orders_count = s.query(Order).count()
        products_count = s.query(Product).count()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "orders_count": orders_count, "products_count": products_count},
    )

# ---------- Orders ----------
@router.get("/orders", response_class=HTMLResponse, name="orders_list")
async def orders_list(request: Request):
    with SessionLocal() as s:
        orders = s.query(Order).order_by(Order.id.desc()).limit(100).all()
    return templates.TemplateResponse("orders_list.html", {"request": request, "orders": orders})

@router.post("/orders/{oid}/status")
async def update_status(oid: int, status: str = Form(...)):
    with SessionLocal() as s:
        o = s.get(Order, oid)
        if o:
            o.status = status
            s.commit()
    return RedirectResponse(url=request.url_for("orders_list"), status_code=303)

# ---------- Products (CRUD) ----------
@router.get("/products", response_class=HTMLResponse, name="products_list")
async def products_list(request: Request):
    with SessionLocal() as s:
        products = s.query(Product).order_by(Product.id.desc()).all()
    return templates.TemplateResponse("products.html", {"request": request, "products": products})

@router.post("/products/create")
async def products_create(kind: str = Form(...), name: str = Form(...), price: int = Form(...),
                          currency: str = Form("IRR"), is_active: str = Form("on")):
    active = (is_active == "on")
    with SessionLocal() as s:
        s.add(Product(kind=kind, name=name, price=price, currency=currency, is_active=active))
        s.commit()
    return RedirectResponse(url=request.url_for("products_list"), status_code=303)

@router.post("/products/{pid}/update")
async def products_update(pid: int, name: str = Form(...), price: int = Form(...), currency: str = Form(...)):
    with SessionLocal() as s:
        p = s.get(Product, pid)
        if p:
            p.name = name
            p.price = price
            p.currency = currency
            s.commit()
    return RedirectResponse(url=request.url_for("products_list"), status_code=303)

@router.post("/products/{pid}/toggle")
async def products_toggle(pid: int):
    with SessionLocal() as s:
        p = s.get(Product, pid)
        if p:
            p.is_active = not p.is_active
            s.commit()
    return RedirectResponse(url=request.url_for("products_list"), status_code=303)

@router.post("/products/{pid}/delete")
async def products_delete(pid: int):
    with SessionLocal() as s:
        p = s.get(Product, pid)
        if p:
            s.delete(p)
            s.commit()
    return RedirectResponse(url=request.url_for("products_list"), status_code=303)

app.include_router(router)
