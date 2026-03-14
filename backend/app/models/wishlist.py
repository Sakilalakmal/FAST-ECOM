from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ORMModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.wishlist_item import WishlistItem


class Wishlist(ORMModel):
    __tablename__ = "wishlists"
    __table_args__ = (
        Index(
            "uq_wishlists_user_id_active",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user: Mapped[User] = relationship(back_populates="wishlists")
    items: Mapped[list[WishlistItem]] = relationship(
        back_populates="wishlist",
        cascade="all, delete-orphan",
        order_by="WishlistItem.created_at.desc()",
    )
