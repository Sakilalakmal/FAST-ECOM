from __future__ import annotations

from typing import Annotated, Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
PhoneNumberStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=32)]


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str | None = None
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    roles: list[RoleResponse] = Field(default_factory=list)


class UserProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: NameStr | None = None
    last_name: NameStr | None = None
    phone_number: PhoneNumberStr | None = None

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone_number(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value
