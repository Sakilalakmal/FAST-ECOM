from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import ORMModel
from app.models.mixins import ActiveMixin


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
