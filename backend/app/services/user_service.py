from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import RoleResponse, UserProfileResponse, UserProfileUpdateRequest


class UserServiceError(Exception):
    pass


class UserProfileValidationError(UserServiceError):
    pass


class UserPhoneNumberAlreadyExistsError(UserServiceError):
    pass


class UserService:
    def __init__(self, repository: UserRepository | None = None) -> None:
        self.repository = repository or UserRepository()

    def get_current_user_profile(self, *, current_user: User) -> UserProfileResponse:
        return self.build_user_profile_response(current_user)

    def update_current_user_profile(
        self,
        db: Session,
        *,
        current_user: User,
        payload: UserProfileUpdateRequest,
    ) -> UserProfileResponse:
        if not payload.model_fields_set:
            raise UserProfileValidationError("At least one profile field must be provided.")

        update_data = payload.model_dump(exclude_unset=True)
        for required_field in ("first_name", "last_name"):
            if required_field in update_data and update_data[required_field] is None:
                raise UserProfileValidationError(f"{required_field} cannot be null.")

        phone_number = update_data.get("phone_number")
        if isinstance(phone_number, str):
            existing_user = self.repository.get_user_by_phone_number(
                db,
                phone_number=phone_number,
            )
            if existing_user is not None and existing_user.id != current_user.id:
                raise UserPhoneNumberAlreadyExistsError(
                    "A user with this phone number already exists."
                )

        try:
            self.repository.update_user_profile(
                db,
                user=current_user,
                update_data=update_data,
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise UserServiceError("Unable to update the current user profile.") from exc

        persisted_user = self.repository.get_user_by_id(db, user_id=current_user.id) or current_user
        return self.build_user_profile_response(persisted_user)

    def build_user_profile_response(self, user: User) -> UserProfileResponse:
        roles = [
            RoleResponse.model_validate(user_role.role)
            for user_role in user.user_roles
            if user_role.role is not None and user_role.role.deleted_at is None
        ]

        return UserProfileResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=user.phone_number,
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=roles,
        )
