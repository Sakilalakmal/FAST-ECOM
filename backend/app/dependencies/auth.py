from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_token
from app.dependencies.db import get_db_session
from app.models.user import User
from app.services.auth_service import (
    AuthService,
    InactiveUserError,
    InvalidCredentialsError,
    UnverifiedUserError,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().API_V1_STR}/auth/login",
)


def get_auth_service() -> AuthService:
    return AuthService()


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload.sub)
    except (InvalidTokenError, ValueError, TypeError):
        raise credentials_exception from None

    try:
        return auth_service.get_user_entity(db, user_id=user_id)
    except InvalidCredentialsError:
        raise credentials_exception from None


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    try:
        return auth_service.ensure_active_user(current_user)
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


def get_current_verified_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    try:
        return auth_service.ensure_verified_user(current_user)
    except UnverifiedUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


def require_roles(*role_names: str):
    normalized_roles = {role_name.lower() for role_name in role_names}

    def role_dependency(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        user_roles = {
            user_role.role.name.lower()
            for user_role in current_user.user_roles
            if user_role.role is not None and user_role.role.deleted_at is None
        }
        if normalized_roles and user_roles.isdisjoint(normalized_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role.",
            )
        return current_user

    return role_dependency


def get_current_admin_user(
    current_user: Annotated[User, Depends(require_roles("admin"))],
) -> User:
    return current_user
