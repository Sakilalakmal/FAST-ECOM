from __future__ import annotations

from hashlib import sha256
from typing import Iterable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.variant_option import VariantOption
from app.models.variant_option_value import VariantOptionValue
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.variant_repository import VariantRepository
from app.schemas.inventory import InventoryResponse
from app.schemas.variant import (
    ProductVariantCreateRequest,
    ProductVariantResponse,
    ProductVariantUpdateRequest,
    PublicProductVariantResponse,
    VariantOptionCreateRequest,
    VariantOptionResponse,
    VariantOptionUpdateRequest,
    VariantOptionValueCreateRequest,
    VariantOptionValueResponse,
    VariantOptionValueUpdateRequest,
    VariantSelectedOptionResponse,
    VariantSelectionRequest,
)


class VariantServiceError(Exception):
    pass


class VariantProductNotFoundError(VariantServiceError):
    pass


class ProductVariantNotFoundError(VariantServiceError):
    pass


class VariantOptionNotFoundError(VariantServiceError):
    pass


class VariantOptionValueNotFoundError(VariantServiceError):
    pass


class VariantConflictError(VariantServiceError):
    pass


class VariantValidationError(VariantServiceError):
    pass


class VariantService:
    def __init__(
        self,
        repository: VariantRepository | None = None,
        inventory_repository: InventoryRepository | None = None,
    ) -> None:
        self.repository = repository or VariantRepository()
        self.inventory_repository = inventory_repository or InventoryRepository()

    def list_variant_options(
        self,
        db: Session,
        *,
        product_id: int,
    ) -> list[VariantOptionResponse]:
        product = self.repository.get_product_by_id(db, product_id=product_id)
        if product is None:
            raise VariantProductNotFoundError("Product not found.")

        options = self.repository.list_variant_options_by_product(db, product_id=product_id)
        return [self.build_variant_option_response(option) for option in options]

    def create_variant_option(
        self,
        db: Session,
        *,
        product_id: int,
        payload: VariantOptionCreateRequest,
    ) -> VariantOptionResponse:
        product = self.repository.get_product_by_id(db, product_id=product_id)
        if product is None:
            raise VariantProductNotFoundError("Product not found.")
        if self.repository.count_variants_by_product(db, product_id=product_id) > 0:
            raise VariantConflictError(
                "Variant options cannot be changed after variants have been created."
            )

        normalized_name = self._normalize_lookup_value(payload.name)
        if self.repository.option_name_exists(
            db,
            product_id=product_id,
            normalized_name=normalized_name,
        ):
            raise VariantConflictError("A variant option with this name already exists for the product.")

        option_data = payload.model_dump()
        option_data["normalized_name"] = normalized_name

        try:
            option = self.repository.create_variant_option(
                db,
                product_id=product_id,
                option_data=option_data,
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise VariantServiceError("Unable to create the variant option.") from exc

        return self.build_variant_option_response(option)

    def update_variant_option(
        self,
        db: Session,
        *,
        option_id: int,
        payload: VariantOptionUpdateRequest,
    ) -> VariantOptionResponse:
        if not payload.model_fields_set:
            raise VariantValidationError("At least one option field must be provided.")

        option = self.repository.get_variant_option_by_id(db, option_id=option_id)
        if option is None:
            raise VariantOptionNotFoundError("Variant option not found.")

        update_data = payload.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] is None:
            raise VariantValidationError("name cannot be null.")
        if "sort_order" in update_data and update_data["sort_order"] is None:
            raise VariantValidationError("sort_order cannot be null.")

        if "name" in update_data:
            normalized_name = self._normalize_lookup_value(str(update_data["name"]))
            if self.repository.option_name_exists(
                db,
                product_id=option.product_id,
                normalized_name=normalized_name,
                exclude_option_id=option.id,
            ):
                raise VariantConflictError(
                    "A variant option with this name already exists for the product."
                )
            update_data["normalized_name"] = normalized_name

        try:
            option = self.repository.update_variant_option(db, option=option, update_data=update_data)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise VariantServiceError("Unable to update the variant option.") from exc

        return self.build_variant_option_response(option)

    def delete_variant_option(self, db: Session, *, option_id: int) -> None:
        option = self.repository.get_variant_option_by_id(db, option_id=option_id)
        if option is None:
            raise VariantOptionNotFoundError("Variant option not found.")
        if self.repository.count_variants_by_product(db, product_id=option.product_id) > 0:
            raise VariantConflictError(
                "Variant options cannot be deleted after variants have been created."
            )

        try:
            self.repository.soft_delete_variant_option(db, option=option)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise VariantServiceError("Unable to delete the variant option.") from exc

    def create_variant_option_value(
        self,
        db: Session,
        *,
        option_id: int,
        payload: VariantOptionValueCreateRequest,
    ) -> VariantOptionValueResponse:
        option = self.repository.get_variant_option_by_id(db, option_id=option_id)
        if option is None:
            raise VariantOptionNotFoundError("Variant option not found.")

        normalized_value = self._normalize_lookup_value(payload.value)
        if self.repository.option_value_exists(
            db,
            option_id=option_id,
            normalized_value=normalized_value,
        ):
            raise VariantConflictError("A value with this name already exists for the option.")

        value_data = payload.model_dump()
        value_data["normalized_value"] = normalized_value

        try:
            option_value = self.repository.create_option_value(
                db,
                option_id=option_id,
                value_data=value_data,
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise VariantServiceError("Unable to create the variant option value.") from exc

        return self.build_variant_option_value_response(option_value)

    def update_variant_option_value(
        self,
        db: Session,
        *,
        value_id: int,
        payload: VariantOptionValueUpdateRequest,
    ) -> VariantOptionValueResponse:
        if not payload.model_fields_set:
            raise VariantValidationError("At least one option value field must be provided.")

        option_value = self.repository.get_option_value_by_id(db, value_id=value_id)
        if option_value is None:
            raise VariantOptionValueNotFoundError("Variant option value not found.")

        update_data = payload.model_dump(exclude_unset=True)
        if "value" in update_data and update_data["value"] is None:
            raise VariantValidationError("value cannot be null.")
        if "sort_order" in update_data and update_data["sort_order"] is None:
            raise VariantValidationError("sort_order cannot be null.")

        if "value" in update_data:
            normalized_value = self._normalize_lookup_value(str(update_data["value"]))
            if self.repository.option_value_exists(
                db,
                option_id=option_value.option_id,
                normalized_value=normalized_value,
                exclude_value_id=option_value.id,
            ):
                raise VariantConflictError("A value with this name already exists for the option.")
            update_data["normalized_value"] = normalized_value

        try:
            option_value = self.repository.update_option_value(
                db,
                option_value=option_value,
                update_data=update_data,
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise VariantServiceError("Unable to update the variant option value.") from exc

        return self.build_variant_option_value_response(option_value)

    def delete_variant_option_value(self, db: Session, *, value_id: int) -> None:
        option_value = self.repository.get_option_value_by_id(db, value_id=value_id)
        if option_value is None:
            raise VariantOptionValueNotFoundError("Variant option value not found.")
        if self.repository.count_variant_assignments_by_option_value(
            db,
            option_value_id=option_value.id,
        ) > 0:
            raise VariantConflictError(
                "Variant option values that are used by variants cannot be deleted."
            )

        try:
            self.repository.soft_delete_option_value(db, option_value=option_value)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise VariantServiceError("Unable to delete the variant option value.") from exc

    def list_variants_by_product(
        self,
        db: Session,
        *,
        product_id: int,
    ) -> list[ProductVariantResponse]:
        product = self.repository.get_product_by_id(db, product_id=product_id)
        if product is None:
            raise VariantProductNotFoundError("Product not found.")

        variants = self.repository.list_variants_by_product(db, product_id=product_id)
        return [self.build_variant_response(variant) for variant in variants]

    def get_variant(self, db: Session, *, variant_id: int) -> ProductVariantResponse:
        variant = self.repository.get_variant_by_id(db, variant_id=variant_id)
        if variant is None:
            raise ProductVariantNotFoundError("Variant not found.")
        return self.build_variant_response(variant)

    def create_variant(
        self,
        db: Session,
        *,
        product_id: int,
        payload: ProductVariantCreateRequest,
    ) -> ProductVariantResponse:
        product = self.repository.get_product_by_id(db, product_id=product_id)
        if product is None:
            raise VariantProductNotFoundError("Product not found.")
        if self.repository.get_variant_by_sku(db, sku=payload.sku) is not None:
            raise VariantConflictError("A variant with this SKU already exists.")

        validated_selections, combination_signature = self._validate_selected_options(
            db,
            product=product,
            selected_options=payload.selected_options,
        )
        if self.repository.variant_combination_exists(
            db,
            product_id=product.id,
            combination_signature=combination_signature,
        ):
            raise VariantConflictError(
                "A variant with the same option combination already exists for this product."
            )

        self._validate_variant_prices(
            product=product,
            price_override=payload.price_override,
            compare_at_price_override=payload.compare_at_price_override,
        )

        variant_data = payload.model_dump(exclude={"selected_options"})
        variant_data["combination_signature"] = combination_signature

        try:
            variant = self.repository.create_variant(
                db,
                product_id=product.id,
                variant_data=variant_data,
            )
            self.repository.replace_variant_selections(
                db,
                variant=variant,
                selections_data=validated_selections,
            )
            self.inventory_repository.create_inventory(
                db,
                variant_id=variant.id,
                inventory_data={
                    "quantity_on_hand": 0,
                    "quantity_reserved": 0,
                    "low_stock_threshold": None,
                },
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise VariantServiceError("Unable to create the variant.") from exc

        created_variant = self.repository.get_variant_by_id(db, variant_id=variant.id)
        if created_variant is None:
            raise VariantServiceError("Unable to load the created variant.")
        return self.build_variant_response(created_variant)

    def update_variant(
        self,
        db: Session,
        *,
        variant_id: int,
        payload: ProductVariantUpdateRequest,
    ) -> ProductVariantResponse:
        if not payload.model_fields_set:
            raise VariantValidationError("At least one variant field must be provided.")

        variant = self.repository.get_variant_by_id(db, variant_id=variant_id)
        if variant is None:
            raise ProductVariantNotFoundError("Variant not found.")

        update_data = payload.model_dump(exclude_unset=True, exclude={"selected_options"})
        self._validate_non_nullable_variant_update_fields(update_data)

        if "sku" in update_data and update_data["sku"] is not None:
            if self.repository.get_variant_by_sku(
                db,
                sku=str(update_data["sku"]),
                exclude_variant_id=variant.id,
            ) is not None:
                raise VariantConflictError("A variant with this SKU already exists.")

        price_override = update_data.get("price_override", variant.price_override)
        compare_at_price_override = (
            update_data["compare_at_price_override"]
            if "compare_at_price_override" in update_data
            else variant.compare_at_price_override
        )
        self._validate_variant_prices(
            product=variant.product,
            price_override=price_override,
            compare_at_price_override=compare_at_price_override,
        )

        if payload.selected_options is not None:
            validated_selections, combination_signature = self._validate_selected_options(
                db,
                product=variant.product,
                selected_options=payload.selected_options,
            )
            if self.repository.variant_combination_exists(
                db,
                product_id=variant.product_id,
                combination_signature=combination_signature,
                exclude_variant_id=variant.id,
            ):
                raise VariantConflictError(
                    "A variant with the same option combination already exists for this product."
                )
            update_data["combination_signature"] = combination_signature
        else:
            validated_selections = None

        try:
            if update_data:
                self.repository.update_variant(db, variant=variant, update_data=update_data)
            if validated_selections is not None:
                self.repository.replace_variant_selections(
                    db,
                    variant=variant,
                    selections_data=validated_selections,
                )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise VariantServiceError("Unable to update the variant.") from exc

        updated_variant = self.repository.get_variant_by_id(db, variant_id=variant.id)
        if updated_variant is None:
            raise VariantServiceError("Unable to load the updated variant.")
        return self.build_variant_response(updated_variant)

    def delete_variant(self, db: Session, *, variant_id: int) -> None:
        variant = self.repository.get_variant_by_id(db, variant_id=variant_id)
        if variant is None:
            raise ProductVariantNotFoundError("Variant not found.")

        try:
            self.repository.soft_delete_variant(db, variant=variant)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise VariantServiceError("Unable to delete the variant.") from exc

    def build_variant_option_response(self, option: VariantOption) -> VariantOptionResponse:
        values = [
            self.build_variant_option_value_response(value)
            for value in self._sort_option_values(
                value for value in option.values if value.deleted_at is None
            )
        ]
        return VariantOptionResponse(
            id=option.id,
            product_id=option.product_id,
            name=option.name,
            sort_order=option.sort_order,
            values=values,
            created_at=option.created_at,
            updated_at=option.updated_at,
        )

    def build_variant_option_value_response(
        self,
        option_value: VariantOptionValue,
    ) -> VariantOptionValueResponse:
        return VariantOptionValueResponse(
            id=option_value.id,
            option_id=option_value.option_id,
            value=option_value.value,
            sort_order=option_value.sort_order,
            created_at=option_value.created_at,
            updated_at=option_value.updated_at,
        )

    def build_variant_response(self, variant: ProductVariant) -> ProductVariantResponse:
        return ProductVariantResponse(
            id=variant.id,
            product_id=variant.product_id,
            sku=variant.sku,
            barcode=variant.barcode,
            variant_name=variant.variant_name,
            display_label=self._build_display_label(variant),
            price_override=variant.price_override,
            compare_at_price_override=variant.compare_at_price_override,
            effective_price=self._resolve_effective_price(variant),
            effective_compare_at_price=self._resolve_effective_compare_at_price(variant),
            image_url=variant.image_url,
            is_active=variant.is_active,
            sort_order=variant.sort_order,
            selected_options=self._build_selected_option_responses(variant),
            inventory=(
                self._build_inventory_response(variant.inventory)
                if variant.inventory is not None
                else None
            ),
            created_at=variant.created_at,
            updated_at=variant.updated_at,
        )

    def build_public_variant_summaries(
        self,
        product: Product,
        *,
        public_view: bool,
    ) -> list[PublicProductVariantResponse]:
        variants = [variant for variant in product.variants if variant.deleted_at is None]
        if public_view:
            variants = [variant for variant in variants if variant.is_active]

        variants.sort(key=lambda item: (item.sort_order, item.id))
        return [self._build_public_variant_response(variant) for variant in variants]

    def _build_public_variant_response(
        self,
        variant: ProductVariant,
    ) -> PublicProductVariantResponse:
        available_quantity = self._available_quantity(variant)
        return PublicProductVariantResponse(
            id=variant.id,
            sku=variant.sku,
            display_label=self._build_display_label(variant),
            image_url=variant.image_url,
            effective_price=self._resolve_effective_price(variant),
            effective_compare_at_price=self._resolve_effective_compare_at_price(variant),
            selected_options=self._build_selected_option_responses(variant),
            is_active=variant.is_active,
            is_available=variant.is_active and available_quantity > 0,
            available_quantity=available_quantity,
        )

    def _validate_selected_options(
        self,
        db: Session,
        *,
        product: Product,
        selected_options: list[VariantSelectionRequest],
    ) -> tuple[list[dict[str, object]], str]:
        active_options = [option for option in product.variant_options if option.deleted_at is None]
        active_options.sort(key=lambda item: (item.sort_order, item.id))

        if not active_options:
            if selected_options:
                raise VariantValidationError(
                    "This product does not have variant options configured."
                )
            return [], self._build_combination_signature([])

        if len(selected_options) != len(active_options):
            raise VariantValidationError(
                "selected_options must include exactly one value for each product variant option."
            )

        expected_option_ids = {option.id for option in active_options}
        seen_option_ids: set[int] = set()
        value_ids: list[int] = []
        for selection in selected_options:
            if selection.option_id in seen_option_ids:
                raise VariantValidationError("Each variant option can only be selected once.")
            seen_option_ids.add(selection.option_id)
            value_ids.append(selection.option_value_id)

        if seen_option_ids != expected_option_ids:
            raise VariantValidationError(
                "selected_options must include exactly one value for each product variant option."
            )

        option_values = self.repository.get_option_values_by_ids(db, value_ids=value_ids)
        if len(option_values) != len(value_ids):
            raise VariantValidationError("One or more selected option values are invalid.")

        values_by_id = {value.id: value for value in option_values}
        validated_selections: list[dict[str, object]] = []
        signature_parts: list[tuple[int, int]] = []

        for selection in selected_options:
            option_value = values_by_id.get(selection.option_value_id)
            if option_value is None or option_value.option is None:
                raise VariantValidationError("One or more selected option values are invalid.")
            if option_value.option.product_id != product.id:
                raise VariantValidationError("Selected option values must belong to the product.")
            if option_value.option_id != selection.option_id:
                raise VariantValidationError("Selected option values do not match their option.")

            validated_selections.append(
                {
                    "option_id": selection.option_id,
                    "option_value_id": selection.option_value_id,
                }
            )
            signature_parts.append((selection.option_id, selection.option_value_id))

        return validated_selections, self._build_combination_signature(signature_parts)

    def _validate_variant_prices(
        self,
        *,
        product: Product,
        price_override,
        compare_at_price_override,
    ) -> None:
        effective_price = price_override if price_override is not None else product.base_price
        if compare_at_price_override is not None and compare_at_price_override < effective_price:
            raise VariantValidationError(
                "compare_at_price_override must be greater than or equal to the effective variant price."
            )

    def _validate_non_nullable_variant_update_fields(self, update_data: dict[str, object]) -> None:
        required_fields = {"sku", "is_active", "sort_order"}
        for required_field in required_fields:
            if required_field in update_data and update_data[required_field] is None:
                raise VariantValidationError(f"{required_field} cannot be null.")

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

    def _resolve_effective_price(self, variant: ProductVariant):
        return variant.price_override if variant.price_override is not None else variant.product.base_price

    def _resolve_effective_compare_at_price(self, variant: ProductVariant):
        candidate = (
            variant.compare_at_price_override
            if variant.compare_at_price_override is not None
            else variant.product.compare_at_price
        )
        effective_price = self._resolve_effective_price(variant)
        if candidate is not None and candidate >= effective_price:
            return candidate
        return None

    def _available_quantity(self, variant: ProductVariant) -> int:
        if variant.inventory is None:
            return 0
        return max(variant.inventory.quantity_on_hand - variant.inventory.quantity_reserved, 0)

    def _build_inventory_response(self, inventory: Inventory) -> InventoryResponse:
        available_quantity = max(inventory.quantity_on_hand - inventory.quantity_reserved, 0)
        low_stock_threshold = inventory.low_stock_threshold
        is_low_stock = low_stock_threshold is not None and available_quantity <= low_stock_threshold
        return InventoryResponse(
            id=inventory.id,
            variant_id=inventory.variant_id,
            quantity_on_hand=inventory.quantity_on_hand,
            quantity_reserved=inventory.quantity_reserved,
            available_quantity=available_quantity,
            low_stock_threshold=low_stock_threshold,
            is_low_stock=is_low_stock,
            last_stock_update_at=inventory.last_stock_update_at,
            created_at=inventory.created_at,
            updated_at=inventory.updated_at,
        )

    def _sort_option_values(
        self,
        values: Iterable[VariantOptionValue],
    ) -> list[VariantOptionValue]:
        return sorted(values, key=lambda item: (item.sort_order, item.id))

    def _normalize_lookup_value(self, value: str) -> str:
        return value.strip().lower()

    def _build_combination_signature(self, parts: list[tuple[int, int]]) -> str:
        raw_signature = "|".join(
            f"{option_id}:{option_value_id}"
            for option_id, option_value_id in sorted(parts, key=lambda item: item[0])
        )
        return sha256(raw_signature.encode("utf-8")).hexdigest()
