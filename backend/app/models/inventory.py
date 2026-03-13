from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.product_variant import ProductVariant


class Inventory(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventories"
    __table_args__ = (
        UniqueConstraint("variant_id"),
        CheckConstraint("quantity_on_hand >= 0", name="quantity_on_hand_non_negative"),
        CheckConstraint("quantity_reserved >= 0", name="quantity_reserved_non_negative"),
        CheckConstraint(
            "low_stock_threshold IS NULL OR low_stock_threshold >= 0",
            name="low_stock_threshold_non_negative",
        ),
    )

    variant_id: Mapped[int] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity_on_hand: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    quantity_reserved: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    low_stock_threshold: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    last_stock_update_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    variant: Mapped[ProductVariant] = relationship(back_populates="inventory")
