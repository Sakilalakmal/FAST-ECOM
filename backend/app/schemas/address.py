from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.models.address import AddressType

RecipientNameStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=150),
]
PhoneNumberStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=32),
]
AddressLineStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
OptionalAddressLineStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
CityStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
]
StateStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
]
PostalCodeStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=32),
]
CountryStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=100),
]


class AddressCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipient_name: RecipientNameStr
    phone_number: PhoneNumberStr
    address_line_1: AddressLineStr
    address_line_2: OptionalAddressLineStr | None = None
    city: CityStr
    state_or_province: StateStr | None = None
    postal_code: PostalCodeStr
    country: CountryStr
    landmark: OptionalAddressLineStr | None = None
    address_type: AddressType | None = None
    is_default: bool = False

    @field_validator("address_line_2", "state_or_province", "landmark", mode="before")
    @classmethod
    def normalize_optional_text_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class AddressUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipient_name: RecipientNameStr | None = None
    phone_number: PhoneNumberStr | None = None
    address_line_1: AddressLineStr | None = None
    address_line_2: OptionalAddressLineStr | None = None
    city: CityStr | None = None
    state_or_province: StateStr | None = None
    postal_code: PostalCodeStr | None = None
    country: CountryStr | None = None
    landmark: OptionalAddressLineStr | None = None
    address_type: AddressType | None = None
    is_default: bool | None = None

    @field_validator(
        "address_line_2",
        "state_or_province",
        "landmark",
        mode="before",
    )
    @classmethod
    def normalize_optional_update_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    recipient_name: str
    phone_number: str
    address_line_1: str
    address_line_2: str | None = None
    city: str
    state_or_province: str | None = None
    postal_code: str
    country: str
    landmark: str | None = None
    address_type: AddressType | None = None
    is_default: bool
    created_at: datetime
    updated_at: datetime
