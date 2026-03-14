from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductBrandSummary, ProductCategorySummary


class AddWishlistItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(gt=0)


class WishlistProductImageSummary(BaseModel):
    id: int
    image_url: str
    alt_text: str | None = None


class WishlistProductSummary(BaseModel):
    id: int
    name: str
    slug: str
    short_description: str | None = None
    base_price: Decimal
    compare_at_price: Decimal | None = None
    currency_code: str
    is_active: bool
    category: ProductCategorySummary
    brand: ProductBrandSummary | None = None
    primary_image: WishlistProductImageSummary | None = None


class WishlistItemResponse(BaseModel):
    id: int
    product: WishlistProductSummary
    created_at: datetime
    updated_at: datetime


class WishlistResponse(BaseModel):
    id: int
    user_id: int
    item_count: int
    items: list[WishlistItemResponse]
    created_at: datetime
    updated_at: datetime
