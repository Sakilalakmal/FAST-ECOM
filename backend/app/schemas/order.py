from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from math import ceil
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models.order import OrderStatus, PaymentStatus

OptionalOrderNoteStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
]


class PlaceOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shipping_address_id: int = Field(gt=0)
    notes: OptionalOrderNoteStr | None = None

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_notes(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class OrderListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class AdminOrderStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: OrderStatus


class AdminPaymentStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_status: PaymentStatus


class OrderShippingAddressSnapshot(BaseModel):
    full_name: str
    phone_number: str
    address_line_1: str
    address_line_2: str | None = None
    city: str
    state_or_province: str | None = None
    postal_code: str
    country: str
    landmark: str | None = None


class OrderItemResponse(BaseModel):
    id: int
    product_id: int | None = None
    variant_id: int | None = None
    product_name_snapshot: str
    product_slug_snapshot: str | None = None
    variant_sku_snapshot: str
    variant_label_snapshot: str | None = None
    quantity: int
    unit_price_snapshot: Decimal
    line_subtotal: Decimal
    created_at: datetime
    updated_at: datetime


class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int
    shipping_address_id: int | None = None
    billing_address_id: int | None = None
    status: OrderStatus
    payment_status: PaymentStatus
    subtotal_amount: Decimal
    discount_amount: Decimal
    shipping_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency_code: str
    notes: str | None = None
    shipping_address: OrderShippingAddressSnapshot
    items: list[OrderItemResponse]
    placed_at: datetime
    created_at: datetime
    updated_at: datetime


class OrderListItemResponse(BaseModel):
    id: int
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    total_amount: Decimal
    currency_code: str
    item_count: int
    shipping_full_name: str
    placed_at: datetime
    created_at: datetime


class OrderListResponse(BaseModel):
    items: list[OrderListItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        *,
        items: list[OrderListItemResponse],
        total: int,
        page: int,
        page_size: int,
    ) -> "OrderListResponse":
        total_pages = ceil(total / page_size) if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
