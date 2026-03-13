from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.order_item import OrderItem
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.repositories.order_repository import OrderRepository
from app.schemas.order import (
    AdminOrderStatusUpdateRequest,
    AdminPaymentStatusUpdateRequest,
    OrderItemResponse,
    OrderListItemResponse,
    OrderListQuery,
    OrderListResponse,
    OrderResponse,
    OrderShippingAddressSnapshot,
    PlaceOrderRequest,
)


class OrderServiceError(Exception):
    pass


class OrderNotFoundError(OrderServiceError):
    pass


class OrderAddressNotFoundError(OrderServiceError):
    pass


class OrderCartEmptyError(OrderServiceError):
    pass


class OrderValidationError(OrderServiceError):
    pass


class OrderInventoryError(OrderServiceError):
    pass


class OrderService:
    def __init__(self, repository: OrderRepository | None = None) -> None:
        self.repository = repository or OrderRepository()

    def place_order(
        self,
        db: Session,
        *,
        current_user: User,
        payload: PlaceOrderRequest,
    ) -> OrderResponse:
        try:
            with db.begin():
                shipping_address = self.repository.get_address_by_id_and_user_id(
                    db,
                    address_id=payload.shipping_address_id,
                    user_id=current_user.id,
                )
                if shipping_address is None:
                    raise OrderAddressNotFoundError("Shipping address not found.")

                cart = self.repository.get_active_cart_for_checkout(db, user_id=current_user.id)
                if cart is None or not cart.items:
                    raise OrderCartEmptyError("Your cart is empty.")

                variant_ids = [item.variant_id for item in cart.items]
                variants = self.repository.get_checkout_variants_by_ids(
                    db,
                    variant_ids=variant_ids,
                )
                variant_by_id = {variant.id: variant for variant in variants}
                if len(variant_by_id) != len(variant_ids):
                    raise OrderValidationError(
                        "One or more cart items reference unavailable products or variants."
                    )

                inventories = self.repository.get_locked_inventories_by_variant_ids(
                    db,
                    variant_ids=variant_ids,
                )
                inventory_by_variant_id = {
                    inventory.variant_id: inventory for inventory in inventories
                }

                subtotal_amount = Decimal("0.00")
                discount_amount = Decimal("0.00")
                shipping_amount = Decimal("0.00")
                tax_amount = Decimal("0.00")
                currency_code: str | None = None
                order_items_data: list[dict[str, object]] = []

                for cart_item in cart.items:
                    variant = variant_by_id.get(cart_item.variant_id)
                    if variant is None or variant.product is None:
                        raise OrderValidationError(
                            "One or more cart items reference unavailable products or variants."
                        )
                    if variant.product_id != cart_item.product_id:
                        raise OrderValidationError(
                            "Cart item product information is no longer valid."
                        )

                    inventory = inventory_by_variant_id.get(variant.id)
                    if inventory is None:
                        raise OrderValidationError(
                            "Inventory is not configured for one or more cart items."
                        )

                    available_quantity = max(
                        inventory.quantity_on_hand - inventory.quantity_reserved,
                        0,
                    )
                    if available_quantity < cart_item.quantity:
                        raise OrderInventoryError(
                            f"Insufficient stock for variant {variant.sku}."
                        )

                    item_currency_code = variant.product.currency_code.upper()
                    if currency_code is None:
                        currency_code = item_currency_code
                    elif currency_code != item_currency_code:
                        raise OrderValidationError(
                            "All cart items in the order must use the same currency."
                        )

                    unit_price_snapshot = self._resolve_effective_price(variant)
                    line_subtotal = unit_price_snapshot * cart_item.quantity
                    subtotal_amount += line_subtotal

                    order_items_data.append(
                        {
                            "product_id": cart_item.product_id,
                            "variant_id": cart_item.variant_id,
                            "product_name_snapshot": variant.product.name,
                            "product_slug_snapshot": variant.product.slug,
                            "variant_sku_snapshot": variant.sku,
                            "variant_label_snapshot": self._build_variant_label(variant),
                            "quantity": cart_item.quantity,
                            "unit_price_snapshot": unit_price_snapshot,
                            "line_subtotal": line_subtotal,
                        }
                    )

                if currency_code is None:
                    raise OrderCartEmptyError("Your cart is empty.")

                placed_at = datetime.now(UTC)
                total_amount = subtotal_amount - discount_amount + shipping_amount + tax_amount
                order_number = self._generate_unique_order_number(db, placed_at=placed_at)

                order = self.repository.create_order(
                    db,
                    order_data={
                        "order_number": order_number,
                        "user_id": current_user.id,
                        "shipping_address_id": shipping_address.id,
                        "billing_address_id": None,
                        "status": OrderStatus.PENDING,
                        "payment_status": PaymentStatus.UNPAID,
                        "subtotal_amount": subtotal_amount,
                        "discount_amount": discount_amount,
                        "shipping_amount": shipping_amount,
                        "tax_amount": tax_amount,
                        "total_amount": total_amount,
                        "currency_code": currency_code,
                        "notes": payload.notes,
                        "shipping_full_name": shipping_address.recipient_name,
                        "shipping_phone_number": shipping_address.phone_number,
                        "shipping_address_line_1": shipping_address.address_line_1,
                        "shipping_address_line_2": shipping_address.address_line_2,
                        "shipping_city": shipping_address.city,
                        "shipping_state_or_province": shipping_address.state_or_province,
                        "shipping_postal_code": shipping_address.postal_code,
                        "shipping_country": shipping_address.country,
                        "shipping_landmark": shipping_address.landmark,
                        "placed_at": placed_at,
                    },
                )
                self.repository.create_order_items(
                    db,
                    order_id=order.id,
                    items_data=order_items_data,
                )

                for cart_item in cart.items:
                    inventory = inventory_by_variant_id[cart_item.variant_id]
                    self.repository.decrement_inventory(
                        db,
                        inventory=inventory,
                        quantity=cart_item.quantity,
                    )

                self.repository.clear_cart_items(db, cart=cart)
                self.repository.touch_cart(db, cart=cart)
                order_id = order.id
        except (
            OrderAddressNotFoundError,
            OrderCartEmptyError,
            OrderValidationError,
            OrderInventoryError,
        ):
            raise
        except IntegrityError as exc:
            raise OrderServiceError("Unable to place the order.") from exc

        created_order = self.repository.get_order_by_id_and_user_id(
            db,
            order_id=order_id,
            user_id=current_user.id,
        )
        if created_order is None:
            raise OrderServiceError("Unable to load the created order.")
        return self.build_order_response(created_order)

    def list_user_orders(
        self,
        db: Session,
        *,
        current_user: User,
        filters: OrderListQuery,
    ) -> OrderListResponse:
        orders, total = self.repository.list_orders_by_user(
            db,
            user_id=current_user.id,
            filters=filters,
        )
        return OrderListResponse.create(
            items=[self.build_order_list_item_response(order) for order in orders],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    def get_user_order(
        self,
        db: Session,
        *,
        current_user: User,
        order_id: int,
    ) -> OrderResponse:
        order = self.repository.get_order_by_id_and_user_id(
            db,
            order_id=order_id,
            user_id=current_user.id,
        )
        if order is None:
            raise OrderNotFoundError("Order not found.")
        return self.build_order_response(order)

    def list_admin_orders(
        self,
        db: Session,
        *,
        filters: OrderListQuery,
    ) -> OrderListResponse:
        orders, total = self.repository.list_orders(db, filters=filters)
        return OrderListResponse.create(
            items=[self.build_order_list_item_response(order) for order in orders],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    def get_admin_order(self, db: Session, *, order_id: int) -> OrderResponse:
        order = self.repository.get_order_by_id(db, order_id=order_id)
        if order is None:
            raise OrderNotFoundError("Order not found.")
        return self.build_order_response(order)

    def update_order_status(
        self,
        db: Session,
        *,
        order_id: int,
        payload: AdminOrderStatusUpdateRequest,
    ) -> OrderResponse:
        order = self.repository.get_order_by_id(db, order_id=order_id)
        if order is None:
            raise OrderNotFoundError("Order not found.")

        try:
            self.repository.update_order_status(db, order=order, status_value=payload.status)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise OrderServiceError("Unable to update the order status.") from exc

        return self.build_order_response(order)

    def update_payment_status(
        self,
        db: Session,
        *,
        order_id: int,
        payload: AdminPaymentStatusUpdateRequest,
    ) -> OrderResponse:
        order = self.repository.get_order_by_id(db, order_id=order_id)
        if order is None:
            raise OrderNotFoundError("Order not found.")

        try:
            self.repository.update_payment_status(
                db,
                order=order,
                payment_status=payload.payment_status,
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise OrderServiceError("Unable to update the payment status.") from exc

        return self.build_order_response(order)

    def build_order_response(self, order: Order) -> OrderResponse:
        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            shipping_address_id=order.shipping_address_id,
            billing_address_id=order.billing_address_id,
            status=order.status,
            payment_status=order.payment_status,
            subtotal_amount=order.subtotal_amount,
            discount_amount=order.discount_amount,
            shipping_amount=order.shipping_amount,
            tax_amount=order.tax_amount,
            total_amount=order.total_amount,
            currency_code=order.currency_code,
            notes=order.notes,
            shipping_address=self._build_shipping_snapshot(order),
            items=[self._build_order_item_response(item) for item in order.items],
            placed_at=order.placed_at,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    def build_order_list_item_response(self, order: Order) -> OrderListItemResponse:
        return OrderListItemResponse(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            payment_status=order.payment_status,
            total_amount=order.total_amount,
            currency_code=order.currency_code,
            item_count=len(order.items),
            shipping_full_name=order.shipping_full_name,
            placed_at=order.placed_at,
            created_at=order.created_at,
        )

    def _build_order_item_response(self, item: OrderItem) -> OrderItemResponse:
        return OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            product_name_snapshot=item.product_name_snapshot,
            product_slug_snapshot=item.product_slug_snapshot,
            variant_sku_snapshot=item.variant_sku_snapshot,
            variant_label_snapshot=item.variant_label_snapshot,
            quantity=item.quantity,
            unit_price_snapshot=item.unit_price_snapshot,
            line_subtotal=item.line_subtotal,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _build_shipping_snapshot(self, order: Order) -> OrderShippingAddressSnapshot:
        return OrderShippingAddressSnapshot(
            full_name=order.shipping_full_name,
            phone_number=order.shipping_phone_number,
            address_line_1=order.shipping_address_line_1,
            address_line_2=order.shipping_address_line_2,
            city=order.shipping_city,
            state_or_province=order.shipping_state_or_province,
            postal_code=order.shipping_postal_code,
            country=order.shipping_country,
            landmark=order.shipping_landmark,
        )

    def _build_variant_label(self, variant: ProductVariant) -> str:
        if variant.variant_name:
            return variant.variant_name

        selections = [
            selection
            for selection in variant.selections
            if selection.option is not None
            and selection.option_value is not None
            and selection.option.deleted_at is None
            and selection.option_value.deleted_at is None
        ]
        selections.sort(
            key=lambda item: (
                item.option.sort_order,
                item.option.id,
                item.option_value.sort_order,
                item.option_value.id,
            )
        )
        if selections:
            return " / ".join(selection.option_value.value for selection in selections)
        return variant.sku

    def _resolve_effective_price(self, variant: ProductVariant) -> Decimal:
        if variant.price_override is not None:
            return variant.price_override
        return variant.product.base_price

    def _generate_unique_order_number(self, db: Session, *, placed_at: datetime) -> str:
        date_part = placed_at.strftime("%Y%m%d")
        for _ in range(10):
            candidate = f"ORD-{date_part}-{uuid4().hex[:6].upper()}"
            if not self.repository.order_number_exists(db, order_number=candidate):
                return candidate
        raise OrderServiceError("Unable to generate a unique order number.")
