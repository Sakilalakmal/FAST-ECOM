from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ORMModel
from app.models.mixins import ActiveMixin

if TYPE_CHECKING:
    from app.models.product import Product


class Brand(ActiveMixin, ORMModel):
    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(
        String(160),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    logo_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    website_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    products: Mapped[list[Product]] = relationship(back_populates="brand")
