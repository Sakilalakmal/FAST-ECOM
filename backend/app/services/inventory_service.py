from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.variant_repository import VariantRepository
from app.schemas.inventory import InventoryResponse, InventoryUpdateRequest


class InventoryServiceError(Exception):
    pass


class InventoryVariantNotFoundError(InventoryServiceError):
    pass


class InventoryValidationError(InventoryServiceError):
    pass


class InventoryService:
    def __init__(
        self,
        repository: InventoryRepository | None = None,
        variant_repository: VariantRepository | None = None,
    ) -> None:
        self.repository = repository or InventoryRepository()
        self.variant_repository = variant_repository or VariantRepository()

    def get_variant_inventory(self, db: Session, *, variant_id: int) -> InventoryResponse:
        variant = self.variant_repository.get_variant_by_id(db, variant_id=variant_id)
        if variant is None:
            raise InventoryVariantNotFoundError("Variant not found.")
        if variant.inventory is None:
            raise InventoryServiceError("Inventory record not found for the variant.")
        return self.build_inventory_response(variant.inventory)

    def update_variant_inventory(
        self,
        db: Session,
        *,
        variant_id: int,
        payload: InventoryUpdateRequest,
    ) -> InventoryResponse:
        if not payload.model_fields_set:
            raise InventoryValidationError("At least one inventory field must be provided.")

        variant = self.variant_repository.get_variant_by_id(db, variant_id=variant_id)
        if variant is None:
            raise InventoryVariantNotFoundError("Variant not found.")
        if variant.inventory is None:
            raise InventoryServiceError("Inventory record not found for the variant.")

        update_data = payload.model_dump(exclude_unset=True)
        if "quantity_on_hand" in update_data and update_data["quantity_on_hand"] is None:
            raise InventoryValidationError("quantity_on_hand cannot be null.")
        if "quantity_reserved" in update_data and update_data["quantity_reserved"] is None:
            raise InventoryValidationError("quantity_reserved cannot be null.")

        quantity_on_hand = int(update_data.get("quantity_on_hand", variant.inventory.quantity_on_hand))
        quantity_reserved = int(update_data.get("quantity_reserved", variant.inventory.quantity_reserved))
        if quantity_reserved > quantity_on_hand:
            raise InventoryValidationError(
                "quantity_reserved cannot be greater than quantity_on_hand."
            )

        stock_fields_changed = any(
            field_name in update_data for field_name in {"quantity_on_hand", "quantity_reserved"}
        )

        try:
            inventory = self.repository.update_inventory(
                db,
                inventory=variant.inventory,
                update_data=update_data,
                stock_fields_changed=stock_fields_changed,
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise InventoryServiceError("Unable to update inventory.") from exc

        return self.build_inventory_response(inventory)

    def build_inventory_response(self, inventory: Inventory) -> InventoryResponse:
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
