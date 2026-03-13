from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ORMModel

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.variant_option_value import VariantOptionValue
    from app.models.variant_selection import VariantSelection


class VariantOption(ORMModel):
    __tablename__ = "variant_options"
    __table_args__ = (
        Index(
            "uq_variant_options_product_id_normalized_name_active",
            "product_id",
            "normalized_name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    normalized_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    product: Mapped[Product] = relationship(back_populates="variant_options")
    values: Mapped[list[VariantOptionValue]] = relationship(
        back_populates="option",
        cascade="all, delete-orphan",
        order_by="VariantOptionValue.sort_order",
    )
    selections: Mapped[list[VariantSelection]] = relationship(back_populates="option")
