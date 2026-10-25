from __future__ import annotations

from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class MemberLevel(Base):
    __tablename__ = "member_levels"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(32))
    min_points: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    openid: Mapped[str] = mapped_column(String(64), unique=True)
    nickname: Mapped[str] = mapped_column(String(20), default="猫友1234")
    avatar_path: Mapped[str] = mapped_column(String(255), default="/static/images/avatar.jpg")
    level_code: Mapped[str] = mapped_column(
        String(8),
        ForeignKey("member_levels.code", onupdate="CASCADE", ondelete="RESTRICT"),
        default="V1",
    )
    points: Mapped[int] = mapped_column(Integer, default=0)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    created_at: Mapped[int] = mapped_column(BigInteger)

    level: Mapped[MemberLevel] = relationship(lazy="joined")


class ProductLine(Base):
    __tablename__ = "product_lines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    tag: Mapped[str] = mapped_column(String(16))
    en: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255), default="")
    color: Mapped[str] = mapped_column(String(7), default="#8B5E3C")
    bg: Mapped[str] = mapped_column(String(7), default="#F3EAE0")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    line_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("product_lines.id", onupdate="CASCADE", ondelete="RESTRICT"),
    )
    name: Mapped[str] = mapped_column(String(64))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    orig_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    paws: Mapped[int] = mapped_column(Integer, default=3)
    is_hot: Mapped[bool] = mapped_column(Boolean, default=False)
    is_new: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(String(255), default="")
    image_path: Mapped[str] = mapped_column(String(255))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    on_sale: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    line: Mapped[ProductLine] = relationship(lazy="joined")


class Topping(Base):
    __tablename__ = "toppings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64))
    area: Mapped[str] = mapped_column(String(64))
    address: Mapped[str] = mapped_column(String(255))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    distance: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="open")
    business_hours: Mapped[str] = mapped_column(String(32), default="10:00-22:00")
    making_cups: Mapped[int] = mapped_column(Integer, default=0)
    pack_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1.00"))
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("4.00"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class CouponTemplate(Base):
    __tablename__ = "coupon_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(128), default="")
    cut: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    min_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    valid_days: Mapped[int] = mapped_column(Integer, default=30)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class UserCoupon(Base):
    __tablename__ = "user_coupons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    template_id: Mapped[int] = mapped_column(
        ForeignKey("coupon_templates.id", onupdate="CASCADE", ondelete="RESTRICT")
    )
    title: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(128), default="")
    cut: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    min_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    status: Mapped[str] = mapped_column(String(16), default="unused")
    expire_at: Mapped[int] = mapped_column(BigInteger)
    locked_by: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[int] = mapped_column(BigInteger)


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(20))
    phone: Mapped[str] = mapped_column(String(20))
    detail: Mapped[str] = mapped_column(String(120))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[int] = mapped_column(BigInteger)

    product: Mapped[Product] = relationship(lazy="joined")


class Order(Base):
    __tablename__ = "orders"

    out_trade_no: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT")
    )
    state: Mapped[str] = mapped_column(String(16), default="pending_pay")
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", onupdate="CASCADE", ondelete="RESTRICT")
    )
    store_name: Mapped[str] = mapped_column(String(64))
    mode: Mapped[str] = mapped_column(String(16))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    pack_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    coupon_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_coupons.id", onupdate="CASCADE", ondelete="SET NULL")
    )
    coupon_cut: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    pick_code: Mapped[str | None] = mapped_column(String(16))
    address_id: Mapped[int | None] = mapped_column(
        ForeignKey("addresses.id", onupdate="CASCADE", ondelete="SET NULL")
    )
    address_name: Mapped[str | None] = mapped_column(String(20))
    address_phone: Mapped[str | None] = mapped_column(String(20))
    address_detail: Mapped[str | None] = mapped_column(String(120))
    address_is_default: Mapped[bool | None] = mapped_column(Boolean)
    remark: Mapped[str] = mapped_column(String(100), default="")
    create_time: Mapped[int] = mapped_column(BigInteger)
    pay_time: Mapped[int | None] = mapped_column(BigInteger)
    finish_time: Mapped[int | None] = mapped_column(BigInteger)
    review_rating: Mapped[int | None] = mapped_column(Integer)
    review_content: Mapped[str | None] = mapped_column(String(200))
    review_created_at: Mapped[int | None] = mapped_column(BigInteger)
    earning_points: Mapped[int] = mapped_column(Integer, default=0)
    transaction_id: Mapped[str | None] = mapped_column(String(64))

    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OrderItem.sort_order",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(
        ForeignKey("orders.out_trade_no", onupdate="CASCADE", ondelete="CASCADE")
    )
    product_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(64))
    image_path: Mapped[str] = mapped_column(String(255))
    line_id: Mapped[str] = mapped_column(String(32))
    ice: Mapped[str] = mapped_column(String(16))
    sugar: Mapped[str] = mapped_column(String(16))
    count: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    order: Mapped[Order] = relationship(back_populates="items")
    toppings: Mapped[list[OrderItemTopping]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OrderItemTopping.sort_order",
    )


class OrderItemTopping(Base):
    __tablename__ = "order_item_toppings"
    __table_args__ = (UniqueConstraint("order_item_id", "topping_id", name="uq_item_topping"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    topping_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(32))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    item: Mapped[OrderItem] = relationship(back_populates="toppings")


class PointsLog(Base):
    __tablename__ = "points_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(64))
    points: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[int] = mapped_column(BigInteger)


class ExchangeItem(Base):
    __tablename__ = "exchange_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(64))
    cost: Mapped[int] = mapped_column(Integer)
    item_type: Mapped[str] = mapped_column(String(16), default="coupon")
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("coupon_templates.id", onupdate="CASCADE", ondelete="RESTRICT")
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    template: Mapped[CouponTemplate | None] = relationship(lazy="joined")


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    idem_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    order_no: Mapped[str] = mapped_column(
        ForeignKey("orders.out_trade_no", onupdate="CASCADE", ondelete="CASCADE")
    )
    expires_at: Mapped[int] = mapped_column(BigInteger)
