from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
SlugStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
OptionalTextStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
OptionalUrlStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)]


class BrandCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NameStr
    slug: SlugStr | None = None
    description: OptionalTextStr | None = None
    logo_url: OptionalUrlStr | None = None
    website_url: OptionalUrlStr | None = None
    is_active: bool = True

    @field_validator("slug", "description", "logo_url", "website_url", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class BrandUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NameStr | None = None
    slug: SlugStr | None = None
    description: OptionalTextStr | None = None
    logo_url: OptionalUrlStr | None = None
    website_url: OptionalUrlStr | None = None
    is_active: bool | None = None

    @field_validator("slug", "description", "logo_url", "website_url", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
