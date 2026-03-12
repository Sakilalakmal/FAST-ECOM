from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from math import ceil
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
SlugStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
OptionalShortTextStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]
OptionalLongTextStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=5000),
]
OptionalUrlStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)]
OptionalSkuStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
CurrencyCodeStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=3)]
SpecKeyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
SpecValueStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class ProductSortOption(str, Enum):
    DEFAULT = "default"
    NEWEST = "newest"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"


class ProductImageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_url: OptionalUrlStr
    alt_text: OptionalShortTextStr | None = None
    sort_order: int = Field(default=0, ge=0)
    is_primary: bool = False

    @field_validator("alt_text", mode="before")
    @classmethod
    def normalize_alt_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class ProductImageUpdateRequest(ProductImageCreateRequest):
    pass


class ProductSpecificationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec_key: SpecKeyStr
    spec_value: SpecValueStr
    sort_order: int = Field(default=0, ge=0)


class ProductSpecificationUpdateRequest(ProductSpecificationCreateRequest):
    pass


class ProductCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NameStr
    slug: SlugStr | None = None
    short_description: OptionalShortTextStr | None = None
    description: OptionalLongTextStr | None = None
    category_id: int = Field(gt=0)
    brand_id: int | None = Field(default=None, gt=0)
    base_price: Decimal = Field(ge=0)
    compare_at_price: Decimal | None = Field(default=None, ge=0)
    currency_code: CurrencyCodeStr = "USD"
    sku: OptionalSkuStr | None = None
    is_active: bool = True
    is_featured: bool = False
    sort_order: int = Field(default=0, ge=0)
    images: list[ProductImageCreateRequest] = Field(default_factory=list)
    specifications: list[ProductSpecificationCreateRequest] = Field(default_factory=list)

    @field_validator(
        "slug",
        "short_description",
        "description",
        "sku",
        mode="before",
    )
    @classmethod
    def normalize_optional_text_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value

    @field_validator("currency_code", mode="before")
    @classmethod
    def normalize_currency_code(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value


class ProductUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NameStr | None = None
    slug: SlugStr | None = None
    short_description: OptionalShortTextStr | None = None
    description: OptionalLongTextStr | None = None
    category_id: int | None = Field(default=None, gt=0)
    brand_id: int | None = Field(default=None, gt=0)
    base_price: Decimal | None = Field(default=None, ge=0)
    compare_at_price: Decimal | None = Field(default=None, ge=0)
    currency_code: CurrencyCodeStr | None = None
    sku: OptionalSkuStr | None = None
    is_active: bool | None = None
    is_featured: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)
    images: list[ProductImageUpdateRequest] | None = None
    specifications: list[ProductSpecificationUpdateRequest] | None = None

    @field_validator(
        "slug",
        "short_description",
        "description",
        "sku",
        mode="before",
    )
    @classmethod
    def normalize_optional_text_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value

    @field_validator("currency_code", mode="before")
    @classmethod
    def normalize_currency_code(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
            return value.upper()
        return value


class ProductCategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class ProductBrandSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    alt_text: str | None = None
    sort_order: int
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class ProductSpecificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    spec_key: str
    spec_value: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ProductListItemResponse(BaseModel):
    id: int
    name: str
    slug: str
    short_description: str | None = None
    base_price: Decimal
    compare_at_price: Decimal | None = None
    currency_code: str
    is_active: bool
    is_featured: bool
    sort_order: int
    category: ProductCategorySummary
    brand: ProductBrandSummary | None = None
    primary_image: ProductImageResponse | None = None
    created_at: datetime
    updated_at: datetime


class ProductResponse(BaseModel):
    id: int
    name: str
    slug: str
    short_description: str | None = None
    description: str | None = None
    category: ProductCategorySummary
    brand: ProductBrandSummary | None = None
    base_price: Decimal
    compare_at_price: Decimal | None = None
    currency_code: str
    sku: str | None = None
    is_active: bool
    is_featured: bool
    sort_order: int
    images: list[ProductImageResponse]
    specifications: list[ProductSpecificationResponse]
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    items: list[ProductListItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        *,
        items: list[ProductListItemResponse],
        total: int,
        page: int,
        page_size: int,
    ) -> "ProductListResponse":
        total_pages = ceil(total / page_size) if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class PublicProductListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    search: str | None = None
    category_id: int | None = Field(default=None, gt=0)
    brand_id: int | None = Field(default=None, gt=0)
    featured: bool | None = None
    sort: ProductSortOption = ProductSortOption.DEFAULT

    @field_validator("search", mode="before")
    @classmethod
    def normalize_search(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class AdminProductListQuery(PublicProductListQuery):
    is_active: bool | None = None
