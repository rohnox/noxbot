from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, Numeric
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(Integer, index=True, unique=True)
    first_name: Mapped[str] = mapped_column(String(100), default="")
    username: Mapped[str] = mapped_column(String(100), default="")
    lang: Mapped[str] = mapped_column(String(8), default="fa")
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(16))  # premium | stars
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(512), default="")
    price: Mapped[int] = mapped_column(Integer)    # IRR by default
    currency: Mapped[str] = mapped_column(String(8), default="IRR")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_tg_id: Mapped[int] = mapped_column(Integer, index=True)
    product_id: Mapped[int] = mapped_column(Integer)  # FK simplified for starter
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8), default="IRR")
    status: Mapped[str] = mapped_column(String(24), default="created")  # created|pending_payment|paid|in_progress|done|canceled
    note_internal: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer)
    provider: Mapped[str] = mapped_column(String(32), default="offline")
    method: Mapped[str] = mapped_column(String(32), default="receipt")
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8), default="IRR")
    status: Mapped[str] = mapped_column(String(16), default="init")  # init|awaiting|confirmed|failed
    tx_id: Mapped[str] = mapped_column(String(64), default="")
    receipt_url: Mapped[str] = mapped_column(String(256), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
