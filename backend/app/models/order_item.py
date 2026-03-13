from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order


class OrderItem(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="order_item_quantity_positive"),
        CheckConstraint(
            "unit_price_snapshot >= 0",
            name="order_item_unit_price_snapshot_non_negative",
        ),
        CheckConstraint("line_subtotal >= 0", name="order_item_line_subtotal_non_negative"),
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_name_snapshot: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    product_slug_snapshot: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    variant_sku_snapshot: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    variant_label_snapshot: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    quantity: Mapped[int] = mapped_column(
        nullable=False,
    )
    unit_price_snapshot: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    line_subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    order: Mapped[Order] = relationship(back_populates="items")
