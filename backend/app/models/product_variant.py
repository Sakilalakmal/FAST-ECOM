from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from app.models.base import ORMModel
from app.models.mixins import ActiveMixin

if TYPE_CHECKING:
    from app.models.inventory import Inventory
    from app.models.product import Product
    from app.models.variant_selection import VariantSelection


class ProductVariant(ActiveMixin, ORMModel):
    __tablename__ = "product_variants"
    __table_args__ = (
        Index(
            "uq_product_variants_sku_active",
            "sku",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "uq_product_variants_barcode_active",
            "barcode",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND barcode IS NOT NULL"),
        ),
        Index(
            "uq_product_variants_product_id_combination_signature_active",
            "product_id",
            "combination_signature",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    barcode: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    variant_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    price_override: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    compare_at_price_override: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    image_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    combination_signature: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    product: Mapped[Product] = relationship(back_populates="variants")
    selections: Mapped[list[VariantSelection]] = relationship(
        back_populates="variant",
        cascade="all, delete-orphan",
    )
    inventory: Mapped[Inventory | None] = relationship(
        back_populates="variant",
        cascade="all, delete-orphan",
        uselist=False,
    )
