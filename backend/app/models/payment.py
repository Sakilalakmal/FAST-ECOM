from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ORMModel
from app.models.order import PaymentStatus

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User


class PaymentMethod(str, Enum):
    CASH_ON_DELIVERY = "cash_on_delivery"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    WALLET = "wallet"


class Payment(ORMModel):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_order_id_status", "order_id", "status"),
        Index("ix_payments_user_id_created_at", "user_id", "created_at"),
        Index("uq_payments_order_id_attempt_number", "order_id", "attempt_number", unique=True),
        Index("ix_payments_provider_transaction_id", "provider_transaction_id"),
        Index("ix_payments_external_reference", "external_reference"),
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SqlEnum(
            PaymentMethod,
            name="payment_method_enum",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SqlEnum(
            PaymentStatus,
            name="payment_status_enum",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    provider_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    provider_transaction_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    provider_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    initiated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    failed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    order: Mapped[Order] = relationship(back_populates="payments")
    user: Mapped[User] = relationship(back_populates="payments")
