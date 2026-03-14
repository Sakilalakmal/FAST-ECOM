from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from app.models.base import ORMModel
from app.models.mixins import ActiveMixin

if TYPE_CHECKING:
    from app.models.cart_item import CartItem
    from app.models.brand import Brand
    from app.models.category import Category
    from app.models.product_image import ProductImage
    from app.models.product_specification import ProductSpecification
    from app.models.product_variant import ProductVariant
    from app.models.variant_option import VariantOption
    from app.models.wishlist_item import WishlistItem


class Product(ActiveMixin, ORMModel):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    short_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    brand_id: Mapped[int | None] = mapped_column(
        ForeignKey("brands.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    base_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    compare_at_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        server_default="USD",
        nullable=False,
    )
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    is_featured: Mapped[bool] = mapped_column(
        default=False,
        server_default=expression.false(),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    category: Mapped[Category] = relationship(back_populates="products")
    brand: Mapped[Brand | None] = relationship(back_populates="products")
    images: Mapped[list[ProductImage]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order",
    )
    specifications: Mapped[list[ProductSpecification]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductSpecification.sort_order",
    )
    variants: Mapped[list[ProductVariant]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVariant.sort_order",
    )
    variant_options: Mapped[list[VariantOption]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="VariantOption.sort_order",
    )
    cart_items: Mapped[list[CartItem]] = relationship(back_populates="product")
    wishlist_items: Mapped[list[WishlistItem]] = relationship(back_populates="product")
