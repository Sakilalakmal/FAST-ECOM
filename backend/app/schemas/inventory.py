from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventoryUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity_on_hand: int | None = Field(default=None, ge=0)
    quantity_reserved: int | None = Field(default=None, ge=0)
    low_stock_threshold: int | None = Field(default=None, ge=0)


class InventoryResponse(BaseModel):
    id: int
    variant_id: int
    quantity_on_hand: int
    quantity_reserved: int
    available_quantity: int
    low_stock_threshold: int | None = None
    is_low_stock: bool
    last_stock_update_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
