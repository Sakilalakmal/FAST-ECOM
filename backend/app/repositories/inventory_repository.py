from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory


class InventoryRepository:
    def get_inventory_by_variant_id(self, db: Session, *, variant_id: int) -> Inventory | None:
        stmt = select(Inventory).where(Inventory.variant_id == variant_id)
        return db.scalar(stmt)

    def create_inventory(
        self,
        db: Session,
        *,
        variant_id: int,
        inventory_data: dict[str, object],
    ) -> Inventory:
        inventory = Inventory(variant_id=variant_id, **inventory_data)
        db.add(inventory)
        db.flush()
        return inventory

    def update_inventory(
        self,
        db: Session,
        *,
        inventory: Inventory,
        update_data: dict[str, object],
        stock_fields_changed: bool,
    ) -> Inventory:
        for field_name, value in update_data.items():
            setattr(inventory, field_name, value)

        if stock_fields_changed:
            inventory.last_stock_update_at = datetime.now(UTC)

        db.add(inventory)
        db.flush()
        return inventory
