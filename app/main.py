from fastapi import FastAPI
from .handlers.payments import router as payments_router
from .db import engine, Base
import asyncio

app = FastAPI(title="Shop Bot Payments")

@app.on_event("startup")
async def on_startup():
    # init db
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(payments_router)
