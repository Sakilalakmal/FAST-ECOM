from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from math import ceil
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models.order import OrderStatus, PaymentStatus
from app.models.payment import PaymentMethod

OptionalPaymentTextStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
]
OptionalPaymentRefStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
OptionalProviderNameStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class PaymentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_method: PaymentMethod
    provider_name: OptionalProviderNameStr | None = None
    provider_reference: OptionalPaymentRefStr | None = None
    external_reference: OptionalPaymentRefStr | None = None
    notes: OptionalPaymentTextStr | None = None

    @field_validator(
        "provider_name",
        "provider_reference",
        "external_reference",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_optional_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class PaymentListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    order_id: int | None = Field(default=None, gt=0)


class AdminPaymentStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: PaymentStatus
    provider_name: OptionalProviderNameStr | None = None
    provider_transaction_id: OptionalPaymentRefStr | None = None
    provider_reference: OptionalPaymentRefStr | None = None
    notes: OptionalPaymentTextStr | None = None

    @field_validator(
        "status",
        "provider_name",
        "provider_transaction_id",
        "provider_reference",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_optional_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: PaymentStatus) -> PaymentStatus:
        if value == PaymentStatus.UNPAID:
            raise ValueError("unpaid is not a valid payment record status.")
        return value


class PaymentOrderSummary(BaseModel):
    id: int
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    total_amount: Decimal
    currency_code: str
    placed_at: datetime


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    user_id: int
    attempt_number: int
    payment_method: PaymentMethod
    status: PaymentStatus
    amount: Decimal
    currency_code: str
    provider_name: str | None = None
    provider_transaction_id: str | None = None
    provider_reference: str | None = None
    external_reference: str | None = None
    notes: str | None = None
    initiated_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    order: PaymentOrderSummary


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        *,
        items: list[PaymentResponse],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaymentListResponse":
        total_pages = ceil(total / page_size) if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
