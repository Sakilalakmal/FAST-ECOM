from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ORMModel

if TYPE_CHECKING:
    from app.models.order_item import OrderItem
    from app.models.payment import Payment


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PENDING = "pending"
    REQUIRES_ACTION = "requires_action"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order(ORMModel):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_user_id_status", "user_id", "status"),
        Index("ix_orders_user_id_payment_status", "user_id", "payment_status"),
        Index("ix_orders_placed_at", "placed_at"),
    )

    order_number: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    shipping_address_id: Mapped[int | None] = mapped_column(
        ForeignKey("addresses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    billing_address_id: Mapped[int | None] = mapped_column(
        ForeignKey("addresses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[OrderStatus] = mapped_column(
        SqlEnum(
            OrderStatus,
            name="order_status_enum",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        default=OrderStatus.PENDING,
        server_default=OrderStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SqlEnum(
            PaymentStatus,
            name="payment_status_enum",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        default=PaymentStatus.UNPAID,
        server_default=PaymentStatus.UNPAID.value,
        nullable=False,
        index=True,
    )
    subtotal_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False,
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False,
    )
    shipping_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        server_default="USD",
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    shipping_full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    shipping_phone_number: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    shipping_address_line_1: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    shipping_address_line_2: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    shipping_city: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    shipping_state_or_province: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    shipping_postal_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    shipping_country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    shipping_landmark: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    placed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderItem.created_at",
    )
    payments: Mapped[list[Payment]] = relationship(
        back_populates="order",
        order_by="Payment.attempt_number",
    )
