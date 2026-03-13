from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.product_variant import ProductVariant
    from app.models.variant_option import VariantOption
    from app.models.variant_option_value import VariantOptionValue


class VariantSelection(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "variant_selections"
    __table_args__ = (
        UniqueConstraint("variant_id", "option_id"),
        UniqueConstraint("variant_id", "option_value_id"),
    )

    variant_id: Mapped[int] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_id: Mapped[int] = mapped_column(
        ForeignKey("variant_options.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    option_value_id: Mapped[int] = mapped_column(
        ForeignKey("variant_option_values.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    variant: Mapped[ProductVariant] = relationship(back_populates="selections")
    option: Mapped[VariantOption] = relationship(back_populates="selections")
    option_value: Mapped[VariantOptionValue] = relationship(back_populates="selections")
