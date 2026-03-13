from __future__ import annotations

from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.repositories.cart_repository import CartRepository
from app.schemas.cart import (
    AddCartItemRequest,
    CartItemProductSummary,
    CartItemResponse,
    CartItemVariantSummary,
    CartResponse,
    UpdateCartItemRequest,
)
from app.schemas.variant import VariantSelectedOptionResponse


class CartServiceError(Exception):
    pass


class CartItemNotFoundError(CartServiceError):
    pass


class CartVariantNotFoundError(CartServiceError):
    pass


class CartVariantUnavailableError(CartServiceError):
    pass


class CartValidationError(CartServiceError):
    pass


class CartService:
    def __init__(self, repository: CartRepository | None = None) -> None:
        self.repository = repository or CartRepository()

    def get_current_cart(self, db: Session, *, current_user: User) -> CartResponse:
        cart = self.repository.get_active_cart_by_user_id(db, user_id=current_user.id)
        if cart is None:
            try:
                cart = self.repository.create_cart(db, user_id=current_user.id)
                db.commit()
            except IntegrityError as exc:
                db.rollback()
                raise CartServiceError("Unable to create the active cart.") from exc
            cart = self.repository.get_active_cart_by_user_id(db, user_id=current_user.id) or cart

        return self.build_cart_response(cart)

    def add_item(
        self,
        db: Session,
        *,
        current_user: User,
        payload: AddCartItemRequest,
    ) -> CartResponse:
        cart = self.repository.get_active_cart_by_user_id(db, user_id=current_user.id)
        if cart is None:
            cart = self.repository.create_cart(db, user_id=current_user.id)

        variant = self.repository.get_variant_for_cart(db, variant_id=payload.variant_id)
        if variant is None:
            raise CartVariantNotFoundError("Variant not found.")

        existing_item = self.repository.get_cart_item_by_variant_id_and_cart_id(
            db,
            variant_id=variant.id,
            cart_id=cart.id,
        )
        target_quantity = payload.quantity
        if existing_item is not None:
            target_quantity += existing_item.quantity

        self._validate_requested_quantity(
            variant=variant,
            requested_quantity=target_quantity,
        )

        unit_price_snapshot = self._resolve_effective_price(variant)

        try:
            if existing_item is not None:
                self.repository.update_cart_item(
                    db,
                    cart_item=existing_item,
                    update_data={
                        "quantity": target_quantity,
                        "unit_price_snapshot": unit_price_snapshot,
                    },
                )
            else:
                self.repository.create_cart_item(
                    db,
                    cart_id=cart.id,
                    item_data={
                        "product_id": variant.product_id,
                        "variant_id": variant.id,
                        "quantity": payload.quantity,
                        "unit_price_snapshot": unit_price_snapshot,
                    },
                )
            self.repository.touch_cart(db, cart=cart)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise CartServiceError("Unable to add the item to the cart.") from exc

        refreshed_cart = self.repository.get_active_cart_by_user_id(db, user_id=current_user.id)
        if refreshed_cart is None:
            raise CartServiceError("Unable to load the active cart.")
        return self.build_cart_response(refreshed_cart)

    def update_item_quantity(
        self,
        db: Session,
        *,
        current_user: User,
        item_id: int,
        payload: UpdateCartItemRequest,
    ) -> CartResponse:
        cart = self.repository.get_active_cart_by_user_id(db, user_id=current_user.id)
        if cart is None:
            raise CartItemNotFoundError("Cart item not found.")

        cart_item = self.repository.get_cart_item_by_id_and_cart_id(
            db,
            item_id=item_id,
            cart_id=cart.id,
        )
        if cart_item is None:
            raise CartItemNotFoundError("Cart item not found.")

        if payload.quantity == 0:
            try:
                self.repository.remove_cart_item(db, cart_item=cart_item)
                self.repository.touch_cart(db, cart=cart)
                db.commit()
            except IntegrityError as exc:
                db.rollback()
                raise CartServiceError("Unable to remove the cart item.") from exc

            refreshed_cart = self.repository.get_active_cart_by_user_id(db, user_id=current_user.id)
            if refreshed_cart is None:
                raise CartServiceError("Unable to load the active cart.")
            return self.build_cart_response(refreshed_cart)

        variant = self.repository.get_variant_for_cart(db, variant_id=cart_item.variant_id)
        if variant is None:
            raise CartVariantNotFoundError("Variant not found.")

        self._validate_requested_quantity(
            variant=variant,
            requested_quantity=payload.quantity,
        )

        try:
            self.repository.update_cart_item(
                db,
                cart_item=cart_item,
                update_data={
                    "quantity": payload.quantity,
                    "unit_price_snapshot": self._resolve_effective_price(variant),
                },
            )
            self.repository.touch_cart(db, cart=cart)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise CartServiceError("Unable to update the cart item.") from exc

        refreshed_cart = self.repository.get_active_cart_by_user_id(db, user_id=current_user.id)
        if refreshed_cart is None:
            raise CartServiceError("Unable to load the active cart.")
        return self.build_cart_response(refreshed_cart)

    def remove_item(
        self,
        db: Session,
        *,
        current_user: User,
        item_id: int,
    ) -> CartResponse:
        cart = self.repository.get_active_cart_by_user_id(db, user_id=current_user.id)
        if cart is None:
            raise CartItemNotFoundError("Cart item not found.")

        cart_item = self.repository.get_cart_item_by_id_and_cart_id(
            db,
            item_id=item_id,
            cart_id=cart.id,
        )
        if cart_item is None:
            raise CartItemNotFoundError("Cart item not found.")

        try:
            self.repository.remove_cart_item(db, cart_item=cart_item)
            self.repository.touch_cart(db, cart=cart)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise CartServiceError("Unable to remove the cart item.") from exc

        refreshed_cart = self.repository.get_active_cart_by_user_id(db, user_id=current_user.id)
        if refreshed_cart is None:
            raise CartServiceError("Unable to load the active cart.")
        return self.build_cart_response(refreshed_cart)

    def clear_cart(self, db: Session, *, current_user: User) -> CartResponse:
        cart = self.repository.get_active_cart_by_user_id(db, user_id=current_user.id)
        if cart is None:
            try:
                cart = self.repository.create_cart(db, user_id=current_user.id)
                db.commit()
            except IntegrityError as exc:
                db.rollback()
                raise CartServiceError("Unable to create the active cart.") from exc
            cart = self.repository.get_active_cart_by_user_id(db, user_id=current_user.id) or cart
            return self.build_cart_response(cart)

        try:
            self.repository.clear_cart_items(db, cart=cart)
            self.repository.touch_cart(db, cart=cart)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise CartServiceError("Unable to clear the cart.") from exc

        refreshed_cart = self.repository.get_active_cart_by_user_id(db, user_id=current_user.id)
        if refreshed_cart is None:
            raise CartServiceError("Unable to load the active cart.")
        return self.build_cart_response(refreshed_cart)

    def build_cart_response(self, cart: Cart) -> CartResponse:
        items = [self.build_cart_item_response(item) for item in cart.items]
        subtotal = sum((item.line_subtotal for item in items), Decimal("0.00"))
        total_quantity = sum(item.quantity for item in items)
        currency_code = items[0].product.currency_code if items else None
        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=items,
            item_count=len(items),
            total_quantity=total_quantity,
            subtotal=subtotal,
            currency_code=currency_code,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
        )

    def build_cart_item_response(self, cart_item: CartItem) -> CartItemResponse:
        line_subtotal = cart_item.unit_price_snapshot * cart_item.quantity
        return CartItemResponse(
            id=cart_item.id,
            product_id=cart_item.product_id,
            variant_id=cart_item.variant_id,
            quantity=cart_item.quantity,
            unit_price_snapshot=cart_item.unit_price_snapshot,
            line_subtotal=line_subtotal,
            product=self._build_product_summary(cart_item.product),
            variant=self._build_variant_summary(cart_item.variant, requested_quantity=cart_item.quantity),
            created_at=cart_item.created_at,
            updated_at=cart_item.updated_at,
        )

    def _validate_requested_quantity(
        self,
        *,
        variant: ProductVariant,
        requested_quantity: int,
    ) -> None:
        if requested_quantity <= 0:
            raise CartValidationError("quantity must be greater than zero.")

        available_quantity = self._available_quantity(variant)
        if available_quantity <= 0:
            raise CartVariantUnavailableError("Variant is out of stock.")
        if requested_quantity > available_quantity:
            raise CartVariantUnavailableError(
                "Requested quantity exceeds available stock for the variant."
            )

    def _build_product_summary(self, product: Product) -> CartItemProductSummary:
        return CartItemProductSummary(
            id=product.id,
            name=product.name,
            slug=product.slug,
            currency_code=product.currency_code,
            image_url=self._select_primary_image_url(product.images),
        )

    def _build_variant_summary(
        self,
        variant: ProductVariant,
        *,
        requested_quantity: int,
    ) -> CartItemVariantSummary:
        available_quantity = self._available_quantity(variant)
        is_available = (
            variant.deleted_at is None
            and variant.is_active
            and variant.product.deleted_at is None
            and variant.product.is_active
            and available_quantity >= requested_quantity
        )
        return CartItemVariantSummary(
            id=variant.id,
            sku=variant.sku,
            display_label=self._build_display_label(variant),
            image_url=variant.image_url or self._select_primary_image_url(variant.product.images),
            selected_options=self._build_selected_option_responses(variant),
            is_available=is_available,
            available_quantity=available_quantity,
        )

    def _build_selected_option_responses(
        self,
        variant: ProductVariant,
    ) -> list[VariantSelectedOptionResponse]:
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
        return [
            VariantSelectedOptionResponse(
                option_id=selection.option_id,
                option_name=selection.option.name,
                option_value_id=selection.option_value_id,
                option_value=selection.option_value.value,
            )
            for selection in selections
        ]

    def _build_display_label(self, variant: ProductVariant) -> str:
        if variant.variant_name:
            return variant.variant_name
        selected_options = self._build_selected_option_responses(variant)
        if selected_options:
            return " / ".join(option.option_value for option in selected_options)
        return variant.sku

    def _resolve_effective_price(self, variant: ProductVariant) -> Decimal:
        return (
            variant.price_override
            if variant.price_override is not None
            else variant.product.base_price
        )

    def _available_quantity(self, variant: ProductVariant) -> int:
        if variant.inventory is None:
            return 0
        return max(variant.inventory.quantity_on_hand - variant.inventory.quantity_reserved, 0)

    def _select_primary_image_url(self, images: list[ProductImage]) -> str | None:
        if not images:
            return None
        primary_image = next((image for image in images if image.is_primary), None)
        if primary_image is not None:
            return primary_image.image_url
        return images[0].image_url
