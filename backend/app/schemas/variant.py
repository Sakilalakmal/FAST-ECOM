from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.schemas.inventory import InventoryResponse

VariantNameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
VariantSkuStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
VariantBarcodeStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
VariantOptionNameStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
]
VariantOptionValueStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
]
VariantImageUrlStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=512),
]


class VariantSelectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    option_id: int = Field(gt=0)
    option_value_id: int = Field(gt=0)


class VariantOptionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: VariantOptionNameStr
    sort_order: int = Field(default=0, ge=0)


class VariantOptionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: VariantOptionNameStr | None = None
    sort_order: int | None = Field(default=None, ge=0)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_optional_name(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class VariantOptionValueCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: VariantOptionValueStr
    sort_order: int = Field(default=0, ge=0)


class VariantOptionValueUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: VariantOptionValueStr | None = None
    sort_order: int | None = Field(default=None, ge=0)

    @field_validator("value", mode="before")
    @classmethod
    def normalize_optional_value(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class ProductVariantCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: VariantSkuStr
    barcode: VariantBarcodeStr | None = None
    variant_name: VariantNameStr | None = None
    price_override: Decimal | None = Field(default=None, ge=0)
    compare_at_price_override: Decimal | None = Field(default=None, ge=0)
    image_url: VariantImageUrlStr | None = None
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0)
    selected_options: list[VariantSelectionRequest] = Field(default_factory=list)

    @field_validator("sku", mode="before")
    @classmethod
    def normalize_sku(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("barcode", "variant_name", "image_url", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class ProductVariantUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: VariantSkuStr | None = None
    barcode: VariantBarcodeStr | None = None
    variant_name: VariantNameStr | None = None
    price_override: Decimal | None = Field(default=None, ge=0)
    compare_at_price_override: Decimal | None = Field(default=None, ge=0)
    image_url: VariantImageUrlStr | None = None
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)
    selected_options: list[VariantSelectionRequest] | None = None

    @field_validator("sku", mode="before")
    @classmethod
    def normalize_optional_sku(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
            return value.upper()
        return value

    @field_validator("barcode", "variant_name", "image_url", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class VariantOptionValueResponse(BaseModel):
    id: int
    option_id: int
    value: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class VariantOptionResponse(BaseModel):
    id: int
    product_id: int
    name: str
    sort_order: int
    values: list[VariantOptionValueResponse]
    created_at: datetime
    updated_at: datetime


class VariantSelectedOptionResponse(BaseModel):
    option_id: int
    option_name: str
    option_value_id: int
    option_value: str


class PublicProductVariantResponse(BaseModel):
    id: int
    sku: str
    display_label: str
    image_url: str | None = None
    effective_price: Decimal
    effective_compare_at_price: Decimal | None = None
    selected_options: list[VariantSelectedOptionResponse]
    is_active: bool
    is_available: bool
    available_quantity: int


class ProductVariantResponse(BaseModel):
    id: int
    product_id: int
    sku: str
    barcode: str | None = None
    variant_name: str | None = None
    display_label: str
    price_override: Decimal | None = None
    compare_at_price_override: Decimal | None = None
    effective_price: Decimal
    effective_compare_at_price: Decimal | None = None
    image_url: str | None = None
    is_active: bool
    sort_order: int
    selected_options: list[VariantSelectedOptionResponse]
    inventory: InventoryResponse | None = None
    created_at: datetime
    updated_at: datetime
