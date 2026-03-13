from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.variant_selection import VariantSelection


class CartRepository:
    def get_active_cart_by_user_id(self, db: Session, *, user_id: int) -> Cart | None:
        stmt = (
            select(Cart)
            .options(*self._cart_load_options())
            .where(Cart.user_id == user_id, Cart.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def create_cart(self, db: Session, *, user_id: int) -> Cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.flush()
        return cart

    def get_cart_item_by_id_and_cart_id(
        self,
        db: Session,
        *,
        item_id: int,
        cart_id: int,
    ) -> CartItem | None:
        stmt = (
            select(CartItem)
            .options(*self._cart_item_load_options())
            .where(CartItem.id == item_id, CartItem.cart_id == cart_id)
        )
        return db.scalar(stmt)

    def get_cart_item_by_variant_id_and_cart_id(
        self,
        db: Session,
        *,
        variant_id: int,
        cart_id: int,
    ) -> CartItem | None:
        stmt = (
            select(CartItem)
            .options(*self._cart_item_load_options())
            .where(CartItem.variant_id == variant_id, CartItem.cart_id == cart_id)
        )
        return db.scalar(stmt)

    def create_cart_item(
        self,
        db: Session,
        *,
        cart_id: int,
        item_data: dict[str, object],
    ) -> CartItem:
        cart_item = CartItem(cart_id=cart_id, **item_data)
        db.add(cart_item)
        db.flush()
        return cart_item

    def update_cart_item(
        self,
        db: Session,
        *,
        cart_item: CartItem,
        update_data: dict[str, object],
    ) -> CartItem:
        for field_name, value in update_data.items():
            setattr(cart_item, field_name, value)

        db.add(cart_item)
        db.flush()
        return cart_item

    def remove_cart_item(self, db: Session, *, cart_item: CartItem) -> None:
        db.delete(cart_item)
        db.flush()

    def clear_cart_items(self, db: Session, *, cart: Cart) -> None:
        for item in list(cart.items):
            db.delete(item)
        db.flush()

    def touch_cart(self, db: Session, *, cart: Cart) -> Cart:
        cart.updated_at = datetime.now(UTC)
        db.add(cart)
        db.flush()
        return cart

    def get_variant_for_cart(self, db: Session, *, variant_id: int) -> ProductVariant | None:
        stmt = (
            select(ProductVariant)
            .join(Product, Product.id == ProductVariant.product_id)
            .options(*self._variant_load_options())
            .where(
                ProductVariant.id == variant_id,
                ProductVariant.deleted_at.is_(None),
                ProductVariant.is_active.is_(True),
                Product.deleted_at.is_(None),
                Product.is_active.is_(True),
            )
        )
        return db.scalar(stmt)

    def _cart_load_options(self):
        return (
            selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.images),
            selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product),
            selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.inventory),
            selectinload(Cart.items)
            .selectinload(CartItem.variant)
            .selectinload(ProductVariant.selections)
            .selectinload(VariantSelection.option),
            selectinload(Cart.items)
            .selectinload(CartItem.variant)
            .selectinload(ProductVariant.selections)
            .selectinload(VariantSelection.option_value),
        )

    def _cart_item_load_options(self):
        return (
            selectinload(CartItem.product).selectinload(Product.images),
            selectinload(CartItem.variant).selectinload(ProductVariant.product),
            selectinload(CartItem.variant).selectinload(ProductVariant.inventory),
            selectinload(CartItem.variant)
            .selectinload(ProductVariant.selections)
            .selectinload(VariantSelection.option),
            selectinload(CartItem.variant)
            .selectinload(ProductVariant.selections)
            .selectinload(VariantSelection.option_value),
        )

    def _variant_load_options(self):
        return (
            selectinload(ProductVariant.product).selectinload(Product.images),
            selectinload(ProductVariant.inventory),
            selectinload(ProductVariant.selections).selectinload(VariantSelection.option),
            selectinload(ProductVariant.selections).selectinload(VariantSelection.option_value),
        )
