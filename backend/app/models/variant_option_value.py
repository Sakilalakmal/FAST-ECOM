from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ORMModel

if TYPE_CHECKING:
    from app.models.variant_option import VariantOption
    from app.models.variant_selection import VariantSelection


class VariantOptionValue(ORMModel):
    __tablename__ = "variant_option_values"
    __table_args__ = (
        Index(
            "uq_variant_option_values_option_id_normalized_value_active",
            "option_id",
            "normalized_value",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    option_id: Mapped[int] = mapped_column(
        ForeignKey("variant_options.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    value: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    normalized_value: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    option: Mapped[VariantOption] = relationship(back_populates="values")
    selections: Mapped[list[VariantSelection]] = relationship(back_populates="option_value")
