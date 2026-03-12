from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SqlEnum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from app.models.base import ORMModel

if TYPE_CHECKING:
    from app.models.user import User


class AddressType(str, Enum):
    HOME = "home"
    WORK = "work"
    OTHER = "other"


class Address(ORMModel):
    __tablename__ = "addresses"
    __table_args__ = (
        Index("ix_addresses_user_id", "user_id"),
        Index("ix_addresses_user_id_is_default", "user_id", "is_default"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    recipient_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    phone_number: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    address_line_1: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    address_line_2: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    city: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    state_or_province: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    postal_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    landmark: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    address_type: Mapped[AddressType | None] = mapped_column(
        SqlEnum(
            AddressType,
            name="address_type_enum",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=True,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=expression.false(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="addresses")
