from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, Boolean, JSON, Float, Enum
from sqlalchemy.sql import func
from .db import Base
import enum

class Role(enum.Enum):
    user = "user"
    admin = "admin"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    joined_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.user)

    orders: Mapped[list["Order"]] = relationship(back_populates="user")

class Setting(Base):
    __tablename__ = "settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    support_username: Mapped[str | None] = mapped_column(String(64), default=None)
    channel_username: Mapped[str | None] = mapped_column(String(64), default=None)
    card_number: Mapped[str | None] = mapped_column(String(32), default=None)

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)

    parent: Mapped["Category | None"] = relationship(remote_side=[id])
    products: Mapped[list["Product"]] = relationship(back_populates="category")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    required_fields: Mapped[list[str] | None] = mapped_column(JSON, default=[])

    category: Mapped["Category | None"] = relationship(back_populates="products")
    plans: Mapped[list["ProductPlan"]] = relationship(back_populates="product")

class ProductPlan(Base):
    __tablename__ = "product_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    title: Mapped[str] = mapped_column(String(128))
    price: Mapped[float] = mapped_column(Float)

    product: Mapped["Product"] = relationship(back_populates="plans")

class PaymentMethod(enum.Enum):
    card_to_card = "card_to_card"
    zarinpal = "zarinpal"
    idpay = "idpay"

class OrderStatus(enum.Enum):
    pending = "pending"
    awaiting_manual_review = "awaiting_manual_review"
    paid = "paid"
    canceled = "canceled"
    failed = "failed"

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("product_plans.id"))
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.pending)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(Enum(PaymentMethod), nullable=True)
    gateway: Mapped[str | None] = mapped_column(String(32), nullable=True)
    gateway_authority: Mapped[str | None] = mapped_column(String(128), nullable=True)
    gateway_track_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped["DateTime | None"] = mapped_column(DateTime(timezone=True), nullable=True)

    meta: Mapped[list["OrderMeta"]] = relationship(back_populates="order", cascade="all, delete")
    user: Mapped["User"] = relationship(back_populates="orders")
    product: Mapped["Product"] = relationship()
    plan: Mapped["ProductPlan | None"] = relationship()

class OrderMeta(Base):
    __tablename__ = "order_meta"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    key: Mapped[str] = mapped_column(String(64))
    value: Mapped[str] = mapped_column(Text)

    order: Mapped["Order"] = relationship(back_populates="meta")

class ManualProof(Base):
    __tablename__ = "manual_proofs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    text: Mapped[str | None] = mapped_column(Text, nullable=True)  # توضیحات کاربر (شماره پیگیری/چهار رقم آخر)
    photo_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
