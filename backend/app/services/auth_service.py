from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_token_jti,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest
from app.schemas.user import RoleResponse, UserProfileResponse


class AuthServiceError(Exception):
    pass


class UserAlreadyExistsError(AuthServiceError):
    pass


class RoleNotFoundError(AuthServiceError):
    pass


class InvalidCredentialsError(AuthServiceError):
    pass


class InactiveUserError(AuthServiceError):
    pass


class RefreshTokenNotFoundError(AuthServiceError):
    pass


class AuthService:
    def __init__(self, repository: AuthRepository | None = None) -> None:
        self.repository = repository or AuthRepository()

    def register_user(
        self,
        db: Session,
        *,
        payload: UserRegisterRequest,
        default_role_name: str = "customer",
    ) -> UserProfileResponse:
        existing_user = self.repository.get_user_by_email(db, email=str(payload.email))
        if existing_user:
            raise UserAlreadyExistsError("A user with this email already exists.")

        if payload.phone_number:
            existing_phone = self.repository.get_user_by_phone_number(
                db,
                phone_number=payload.phone_number,
            )
            if existing_phone:
                raise UserAlreadyExistsError("A user with this phone number already exists.")

        role = self.repository.get_role_by_name(db, name=default_role_name)
        if role is None:
            raise RoleNotFoundError(f"Role '{default_role_name}' was not found.")

        try:
            user = self.repository.create_user(
                db,
                email=str(payload.email),
                hashed_password=get_password_hash(payload.password.get_secret_value()),
                first_name=payload.first_name,
                last_name=payload.last_name,
                phone_number=payload.phone_number,
            )
            self.repository.attach_role_to_user(db, user=user, role=role)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise UserAlreadyExistsError("User registration violates a uniqueness constraint.") from exc

        persisted_user = self.repository.get_user_by_id(db, user_id=user.id)
        return self._build_user_profile_response(persisted_user or user)

    def authenticate_user(self, db: Session, *, payload: UserLoginRequest) -> User:
        user = self.repository.get_user_by_email(db, email=str(payload.email))
        if user is None:
            raise InvalidCredentialsError("Invalid email or password.")

        if not verify_password(payload.password.get_secret_value(), user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password.")

        if not user.is_active:
            raise InactiveUserError("The user account is inactive.")

        return user

    def login_user(
        self,
        db: Session,
        *,
        payload: UserLoginRequest,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenResponse:
        user = self.authenticate_user(db, payload=payload)
        self.repository.update_last_login(
            db,
            user=user,
            last_login_at=datetime.now(UTC),
        )

        try:
            token_response = self.issue_tokens_for_user(
                db,
                user=user,
                user_agent=user_agent,
                ip_address=ip_address,
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise AuthServiceError("Unable to persist authentication state.") from exc

        return token_response

    def issue_tokens_for_user(
        self,
        db: Session,
        *,
        user: User,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenResponse:
        access_token = create_access_token(subject=str(user.id))
        refresh_jti = generate_token_jti()
        refresh_token = create_refresh_token(subject=str(user.id), jti=refresh_jti)

        self.repository.store_refresh_token(
            db,
            user_id=user.id,
            jti=refresh_jti,
            expires_at=refresh_token.expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        return TokenResponse(
            access_token=access_token.token,
            refresh_token=refresh_token.token,
            token_type="bearer",
            expires_in=int((access_token.expires_at - datetime.now(UTC)).total_seconds()),
            refresh_expires_in=int(
                (refresh_token.expires_at - datetime.now(UTC)).total_seconds()
            ),
        )

    def get_user_profile(self, db: Session, *, user_id: int) -> UserProfileResponse:
        user = self.repository.get_user_by_id(db, user_id=user_id)
        if user is None:
            raise InvalidCredentialsError("User not found.")
        return self._build_user_profile_response(user)

    def revoke_refresh_token(self, db: Session, *, jti: str) -> None:
        refresh_token = self.repository.find_refresh_token_by_jti(db, jti=jti)
        if refresh_token is None:
            raise RefreshTokenNotFoundError("Refresh token not found.")

        if refresh_token.revoked_at is None:
            self.repository.revoke_refresh_token(db, refresh_token=refresh_token)
            db.commit()

    def _build_user_profile_response(self, user: User) -> UserProfileResponse:
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
