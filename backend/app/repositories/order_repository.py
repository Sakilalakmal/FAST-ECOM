from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.address import Address
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.inventory import Inventory
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.variant_selection import VariantSelection
from app.schemas.order import OrderListQuery


class OrderRepository:
    def get_address_by_id_and_user_id(
        self,
        db: Session,
        *,
        address_id: int,
        user_id: int,
    ) -> Address | None:
        stmt = select(Address).where(
            Address.id == address_id,
            Address.user_id == user_id,
            Address.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    def get_active_cart_for_checkout(self, db: Session, *, user_id: int) -> Cart | None:
        stmt = (
            select(Cart)
            .options(*self._cart_load_options())
            .where(Cart.user_id == user_id, Cart.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def get_checkout_variants_by_ids(
        self,
        db: Session,
        *,
        variant_ids: list[int],
    ) -> list[ProductVariant]:
        if not variant_ids:
            return []

        stmt = (
            select(ProductVariant)
            .join(Product, Product.id == ProductVariant.product_id)
            .options(*self._variant_load_options())
            .where(
                ProductVariant.id.in_(variant_ids),
                ProductVariant.deleted_at.is_(None),
                ProductVariant.is_active.is_(True),
                Product.deleted_at.is_(None),
                Product.is_active.is_(True),
            )
        )
        return list(db.scalars(stmt).all())

    def get_locked_inventories_by_variant_ids(
        self,
        db: Session,
        *,
        variant_ids: list[int],
    ) -> list[Inventory]:
        if not variant_ids:
            return []

        stmt = (
            select(Inventory)
            .where(Inventory.variant_id.in_(variant_ids))
            .with_for_update()
        )
        return list(db.scalars(stmt).all())

    def order_number_exists(self, db: Session, *, order_number: str) -> bool:
        stmt = select(Order.id).where(
            Order.order_number == order_number,
            Order.deleted_at.is_(None),
        )
        return db.scalar(stmt) is not None

    def create_order(self, db: Session, *, order_data: dict[str, object]) -> Order:
        order = Order(**order_data)
        db.add(order)
        db.flush()
        return order

    def create_order_items(
        self,
        db: Session,
        *,
        order_id: int,
        items_data: list[dict[str, object]],
    ) -> list[OrderItem]:
        order_items = [OrderItem(order_id=order_id, **item_data) for item_data in items_data]
        db.add_all(order_items)
        db.flush()
        return order_items

    def decrement_inventory(
        self,
        db: Session,
        *,
        inventory: Inventory,
        quantity: int,
    ) -> Inventory:
        inventory.quantity_on_hand -= quantity
        inventory.last_stock_update_at = datetime.now(UTC)
        db.add(inventory)
        db.flush()
        return inventory

    def clear_cart_items(self, db: Session, *, cart: Cart) -> None:
        for item in list(cart.items):
            db.delete(item)
        db.flush()

    def touch_cart(self, db: Session, *, cart: Cart) -> Cart:
        cart.updated_at = datetime.now(UTC)
        db.add(cart)
        db.flush()
        return cart

    def get_order_by_id_and_user_id(
        self,
        db: Session,
        *,
        order_id: int,
        user_id: int,
    ) -> Order | None:
        stmt = (
            select(Order)
            .options(*self._order_load_options())
            .where(
                Order.id == order_id,
                Order.user_id == user_id,
                Order.deleted_at.is_(None),
            )
        )
        return db.scalar(stmt)

    def get_order_by_id(self, db: Session, *, order_id: int) -> Order | None:
        stmt = (
            select(Order)
            .options(*self._order_load_options())
            .where(Order.id == order_id, Order.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def list_orders_by_user(
        self,
        db: Session,
        *,
        user_id: int,
        filters: OrderListQuery,
    ) -> tuple[list[Order], int]:
        stmt = (
            select(Order)
            .options(*self._order_load_options())
            .where(Order.user_id == user_id, Order.deleted_at.is_(None))
            .order_by(Order.placed_at.desc(), Order.id.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        count_stmt = select(func.count(Order.id)).where(
            Order.user_id == user_id,
            Order.deleted_at.is_(None),
        )
        total = int(db.scalar(count_stmt) or 0)
        items = list(db.scalars(stmt).all())
        return items, total

    def list_orders(
        self,
        db: Session,
        *,
        filters: OrderListQuery,
    ) -> tuple[list[Order], int]:
        stmt = (
            select(Order)
            .options(*self._order_load_options())
            .where(Order.deleted_at.is_(None))
            .order_by(Order.placed_at.desc(), Order.id.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        count_stmt = select(func.count(Order.id)).where(Order.deleted_at.is_(None))
        total = int(db.scalar(count_stmt) or 0)
        items = list(db.scalars(stmt).all())
        return items, total

    def update_order_status(
        self,
        db: Session,
        *,
        order: Order,
        status_value: OrderStatus,
    ) -> Order:
        order.status = status_value
        db.add(order)
        db.flush()
        return order

    def _cart_load_options(self):
        return (
            selectinload(Cart.items).selectinload(CartItem.product),
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

    def _variant_load_options(self):
        return (
            selectinload(ProductVariant.product),
            selectinload(ProductVariant.inventory),
            selectinload(ProductVariant.selections).selectinload(VariantSelection.option),
            selectinload(ProductVariant.selections).selectinload(VariantSelection.option_value),
        )

    def _order_load_options(self):
        return (selectinload(Order.items),)
