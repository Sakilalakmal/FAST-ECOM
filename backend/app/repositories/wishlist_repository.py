from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.brand import Brand
from app.models.category import Category
from app.models.product import Product
from app.models.wishlist import Wishlist
from app.models.wishlist_item import WishlistItem


class WishlistRepository:
    def get_active_wishlist_by_user_id(self, db: Session, *, user_id: int) -> Wishlist | None:
        stmt = (
            select(Wishlist)
            .options(*self._wishlist_load_options())
            .where(
                Wishlist.user_id == user_id,
                Wishlist.deleted_at.is_(None),
            )
        )
        return db.scalar(stmt)

    def create_wishlist(self, db: Session, *, user_id: int) -> Wishlist:
        wishlist = Wishlist(user_id=user_id)
        db.add(wishlist)
        db.flush()
        return wishlist

    def get_or_create_active_wishlist(self, db: Session, *, user_id: int) -> Wishlist:
        wishlist = self.get_active_wishlist_by_user_id(db, user_id=user_id)
        if wishlist is not None:
            return wishlist
        return self.create_wishlist(db, user_id=user_id)

    def get_wishlist_item_by_product_id(
        self,
        db: Session,
        *,
        wishlist_id: int,
        product_id: int,
    ) -> WishlistItem | None:
        stmt = (
            select(WishlistItem)
            .options(*self._wishlist_item_load_options())
            .where(
                WishlistItem.wishlist_id == wishlist_id,
                WishlistItem.product_id == product_id,
            )
        )
        return db.scalar(stmt)

    def create_wishlist_item(
        self,
        db: Session,
        *,
        wishlist_id: int,
        product_id: int,
    ) -> WishlistItem:
        wishlist_item = WishlistItem(
            wishlist_id=wishlist_id,
            product_id=product_id,
        )
        db.add(wishlist_item)
        db.flush()
        return wishlist_item

    def delete_wishlist_item(self, db: Session, *, wishlist_item: WishlistItem) -> None:
        db.delete(wishlist_item)
        db.flush()

    def clear_wishlist_items(self, db: Session, *, wishlist: Wishlist) -> None:
        for item in list(wishlist.items):
            db.delete(item)
        db.flush()

    def get_public_product_by_id(self, db: Session, *, product_id: int) -> Product | None:
        stmt = (
            select(Product)
            .options(*self._product_load_options())
            .join(Category, Product.category_id == Category.id)
            .outerjoin(Brand, Product.brand_id == Brand.id)
            .where(
                Product.id == product_id,
                Product.deleted_at.is_(None),
                Product.is_active.is_(True),
                Category.deleted_at.is_(None),
                Category.is_active.is_(True),
            )
        )
        return db.scalar(stmt)

    def _wishlist_load_options(self):
        return (
            selectinload(Wishlist.items)
            .selectinload(WishlistItem.product)
            .selectinload(Product.category),
            selectinload(Wishlist.items)
            .selectinload(WishlistItem.product)
            .selectinload(Product.brand),
            selectinload(Wishlist.items)
            .selectinload(WishlistItem.product)
            .selectinload(Product.images),
        )

    def _wishlist_item_load_options(self):
        return (
            selectinload(WishlistItem.product).selectinload(Product.category),
            selectinload(WishlistItem.product).selectinload(Product.brand),
            selectinload(WishlistItem.product).selectinload(Product.images),
        )

    def _product_load_options(self):
        return (
            selectinload(Product.category),
            selectinload(Product.brand),
            selectinload(Product.images),
        )
