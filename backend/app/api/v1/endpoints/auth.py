from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.dependencies.auth import (
    get_auth_service,
    get_current_active_user,
    get_current_admin_user,
    get_current_verified_user,
)
from app.dependencies.db import get_db_session
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LogoutRequest,
    MessageResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    RefreshTokenRequest,
)
from app.schemas.user import UserProfileResponse
from app.services.auth_service import (
    AuthService,
    AuthServiceError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    RefreshTokenNotFoundError,
    RefreshTokenRevokedError,
    UserAlreadyExistsError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register_user(
    payload: UserRegisterRequest,
    db: Annotated[Session, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserProfileResponse:
    try:
        return auth_service.register_user(db, payload=payload)
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except AuthServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to register user.",
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate a user and issue tokens",
)
def login_user(
    payload: UserLoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        return auth_service.login_user(
            db,
            payload=payload,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except AuthServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to complete login.",
        ) from exc


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Issue a new access token using a refresh token",
)
def refresh_access_token(
    payload: RefreshTokenRequest,
    db: Annotated[Session, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AccessTokenResponse:
    try:
        return auth_service.refresh_access_token(
            db,
            refresh_token=payload.refresh_token.get_secret_value(),
        )
    except (
        InvalidRefreshTokenError,
        RefreshTokenNotFoundError,
        RefreshTokenRevokedError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get the currently authenticated user",
)
def get_authenticated_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserProfileResponse:
    return auth_service.build_user_profile_response(current_user)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke a refresh token and end the session",
)
def logout_user(
    payload: LogoutRequest,
    db: Annotated[Session, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    try:
        auth_service.logout_user(
            db,
            refresh_token=payload.refresh_token.get_secret_value(),
        )
        return MessageResponse(message="Logout completed successfully.")
    except (
        InvalidRefreshTokenError,
        RefreshTokenNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.get(
    "/verified-me",
    response_model=UserProfileResponse,
    summary="Get the currently authenticated verified user",
)
def get_verified_authenticated_user(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserProfileResponse:
    return auth_service.build_user_profile_response(current_user)


@router.get(
    "/admin-check",
    response_model=MessageResponse,
    summary="Verify admin-only access",
)
def admin_only_check(
    current_user: Annotated[User, Depends(get_current_admin_user)],
) -> MessageResponse:
    return MessageResponse(message=f"Admin access granted for user {current_user.id}.")
