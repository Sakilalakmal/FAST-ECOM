from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.address import Address
from app.models.user import User
from app.repositories.address_repository import AddressRepository
from app.schemas.address import AddressCreateRequest, AddressResponse, AddressUpdateRequest


class AddressServiceError(Exception):
    pass


class AddressNotFoundError(AddressServiceError):
    pass


class AddressValidationError(AddressServiceError):
    pass


class AddressService:
    def __init__(self, repository: AddressRepository | None = None) -> None:
        self.repository = repository or AddressRepository()

    def list_user_addresses(self, db: Session, *, user_id: int) -> list[AddressResponse]:
        addresses = self.repository.list_addresses_by_user_id(db, user_id=user_id)
        return [self.build_address_response(address) for address in addresses]

    def get_user_address(
        self,
        db: Session,
        *,
        user_id: int,
        address_id: int,
    ) -> AddressResponse:
        address = self.repository.get_address_by_id_and_user_id(
            db,
            address_id=address_id,
            user_id=user_id,
        )
        if address is None:
            raise AddressNotFoundError("Address not found.")

        return self.build_address_response(address)

    def create_user_address(
        self,
        db: Session,
        *,
        current_user: User,
        payload: AddressCreateRequest,
    ) -> AddressResponse:
        has_existing_addresses = (
            self.repository.count_addresses_by_user_id(db, user_id=current_user.id) > 0
        )
        should_set_default = payload.is_default or not has_existing_addresses
        address_data = payload.model_dump()
        address_data["is_default"] = should_set_default

        try:
            if should_set_default:
                self.repository.unset_default_addresses(db, user_id=current_user.id)

            address = self.repository.create_address(
                db,
                user_id=current_user.id,
                address_data=address_data,
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise AddressServiceError("Unable to create the address.") from exc

        return self.build_address_response(address)

    def update_user_address(
        self,
        db: Session,
        *,
        current_user: User,
        address_id: int,
        payload: AddressUpdateRequest,
    ) -> AddressResponse:
        if not payload.model_fields_set:
            raise AddressValidationError("At least one address field must be provided.")

        address = self.repository.get_address_by_id_and_user_id(
            db,
            address_id=address_id,
            user_id=current_user.id,
        )
        if address is None:
            raise AddressNotFoundError("Address not found.")

        update_data = payload.model_dump(exclude_unset=True)
        should_set_default = False
        required_fields = {
            "recipient_name",
            "phone_number",
            "address_line_1",
            "city",
            "postal_code",
            "country",
        }
        for required_field in required_fields:
            if required_field in update_data and update_data[required_field] is None:
                raise AddressValidationError(f"{required_field} cannot be null.")

        if "is_default" in update_data:
            requested_is_default = bool(update_data.pop("is_default"))
            if requested_is_default:
                should_set_default = True
            elif address.is_default:
                raise AddressValidationError(
                    "Default address cannot be unset directly. Set another address as default instead."
                )

        try:
            if update_data:
                self.repository.update_address(
                    db,
                    address=address,
                    update_data=update_data,
                )

            if should_set_default:
                self.repository.unset_default_addresses(
                    db,
                    user_id=current_user.id,
                    exclude_address_id=address.id,
                )
                self.repository.set_address_as_default(db, address=address)

            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise AddressServiceError("Unable to update the address.") from exc

        return self.build_address_response(address)

    def delete_user_address(
        self,
        db: Session,
        *,
        current_user: User,
        address_id: int,
    ) -> None:
        address = self.repository.get_address_by_id_and_user_id(
            db,
            address_id=address_id,
            user_id=current_user.id,
        )
        if address is None:
            raise AddressNotFoundError("Address not found.")

        was_default = address.is_default

        try:
            self.repository.soft_delete_address(db, address=address)

            if was_default:
                fallback_address = self.repository.get_default_candidate_for_user(
                    db,
                    user_id=current_user.id,
                    exclude_address_id=address.id,
                )
                if fallback_address is not None:
                    self.repository.set_address_as_default(db, address=fallback_address)

            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise AddressServiceError("Unable to delete the address.") from exc

    def set_default_user_address(
        self,
        db: Session,
        *,
        current_user: User,
        address_id: int,
    ) -> AddressResponse:
        address = self.repository.get_address_by_id_and_user_id(
            db,
            address_id=address_id,
            user_id=current_user.id,
        )
        if address is None:
            raise AddressNotFoundError("Address not found.")

        try:
            self.repository.unset_default_addresses(
                db,
                user_id=current_user.id,
                exclude_address_id=address.id,
            )
            self.repository.set_address_as_default(db, address=address)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise AddressServiceError("Unable to set the default address.") from exc

        return self.build_address_response(address)

    def build_address_response(self, address: Address) -> AddressResponse:
        return AddressResponse.model_validate(address)
