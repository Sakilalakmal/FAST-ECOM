from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.variant import VariantSelectedOptionResponse


class AddCartItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: int = Field(gt=0)
    quantity: int = Field(ge=1)


class UpdateCartItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: int = Field(ge=0)


class CartItemProductSummary(BaseModel):
    id: int
    name: str
    slug: str
    currency_code: str
    image_url: str | None = None


class CartItemVariantSummary(BaseModel):
    id: int
    sku: str
    display_label: str
    image_url: str | None = None
    selected_options: list[VariantSelectedOptionResponse]
    is_available: bool
    available_quantity: int


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    variant_id: int
    quantity: int
    unit_price_snapshot: Decimal
    line_subtotal: Decimal
    product: CartItemProductSummary
    variant: CartItemVariantSummary
    created_at: datetime
    updated_at: datetime


class CartSummaryResponse(BaseModel):
    item_count: int
    total_quantity: int
    subtotal: Decimal
    currency_code: str | None = None


class CartResponse(CartSummaryResponse):
    id: int
    user_id: int
    items: list[CartItemResponse]
    created_at: datetime
    updated_at: datetime
