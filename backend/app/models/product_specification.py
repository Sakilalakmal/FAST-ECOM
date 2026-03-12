from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.product import Product


class ProductSpecification(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "product_specifications"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    spec_key: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    spec_value: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    product: Mapped[Product] = relationship(back_populates="specifications")
