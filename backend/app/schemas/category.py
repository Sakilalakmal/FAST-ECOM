from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
SlugStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
OptionalTextStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
OptionalUrlStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)]


class CategoryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NameStr
    slug: SlugStr | None = None
    description: OptionalTextStr | None = None
    image_url: OptionalUrlStr | None = None
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0)
    parent_id: int | None = Field(default=None, gt=0)

    @field_validator("slug", "description", "image_url", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class CategoryUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NameStr | None = None
    slug: SlugStr | None = None
    description: OptionalTextStr | None = None
    image_url: OptionalUrlStr | None = None
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)
    parent_id: int | None = Field(default=None, gt=0)

    @field_validator("slug", "description", "image_url", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None = None
    image_url: str | None = None
    is_active: bool
    sort_order: int
    parent_id: int | None = None
    created_at: datetime
    updated_at: datetime
