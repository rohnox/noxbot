from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from common.db import SessionLocal
from common.models import Order, Product

app = FastAPI()
app.mount('/static', StaticFiles(directory='admin/static'), name='static')
templates = Jinja2Templates(directory='admin/templates')

@app.get('/', response_class=HTMLResponse)
async def dashboard(request: Request):
    with SessionLocal() as s:
        orders_count = s.query(Order).count()
        products_count = s.query(Product).count()
    return templates.TemplateResponse('dashboard.html', { 'request': request, 'orders_count': orders_count, 'products_count': products_count })

@app.get('/orders', response_class=HTMLResponse)
async def orders_list(request: Request):
    with SessionLocal() as s:
        orders = s.query(Order).order_by(Order.id.desc()).limit(100).all()
    return templates.TemplateResponse('orders_list.html', { 'request': request, 'orders': orders })

@app.post('/orders/{oid}/status')
async def update_status(oid: int, status: str = Form(...)):
    with SessionLocal() as s:
        o = s.get(Order, oid)
        if o:
            o.status = status
            s.commit()
    return RedirectResponse(url=f'/orders', status_code=303)
