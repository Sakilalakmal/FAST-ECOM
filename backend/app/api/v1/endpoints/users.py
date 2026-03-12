from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db_session
from app.models.user import User
from app.schemas.address import AddressCreateRequest, AddressResponse, AddressUpdateRequest
from app.schemas.user import UserProfileResponse, UserProfileUpdateRequest
from app.services.address_service import (
    AddressNotFoundError,
    AddressService,
    AddressServiceError,
    AddressValidationError,
)
from app.services.user_service import (
    UserPhoneNumberAlreadyExistsError,
    UserProfileValidationError,
    UserService,
    UserServiceError,
)

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service() -> UserService:
    return UserService()


def get_address_service() -> AddressService:
    return AddressService()


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get the current authenticated user profile",
)
def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserProfileResponse:
    return user_service.get_current_user_profile(current_user=current_user)


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    summary="Update the current authenticated user profile",
)
def update_current_user_profile(
    payload: UserProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserProfileResponse:
    try:
        return user_service.update_current_user_profile(
            db,
            current_user=current_user,
            payload=payload,
        )
    except UserProfileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except UserPhoneNumberAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the current user profile.",
        ) from exc


@router.get(
    "/addresses",
    response_model=list[AddressResponse],
    summary="List saved addresses for the current authenticated user",
)
def list_current_user_addresses(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    address_service: Annotated[AddressService, Depends(get_address_service)],
) -> list[AddressResponse]:
    return address_service.list_user_addresses(db, user_id=current_user.id)


@router.post(
    "/addresses",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a saved address for the current authenticated user",
)
def create_current_user_address(
    payload: AddressCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    address_service: Annotated[AddressService, Depends(get_address_service)],
) -> AddressResponse:
    try:
        return address_service.create_user_address(
            db,
            current_user=current_user,
            payload=payload,
        )
    except AddressServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the address.",
        ) from exc


@router.get(
    "/addresses/{address_id}",
    response_model=AddressResponse,
    summary="Get a saved address for the current authenticated user",
)
def get_current_user_address(
    address_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    address_service: Annotated[AddressService, Depends(get_address_service)],
) -> AddressResponse:
    try:
        return address_service.get_user_address(
            db,
            user_id=current_user.id,
            address_id=address_id,
        )
    except AddressNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/addresses/{address_id}",
    response_model=AddressResponse,
    summary="Update a saved address for the current authenticated user",
)
def update_current_user_address(
    address_id: int,
    payload: AddressUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    address_service: Annotated[AddressService, Depends(get_address_service)],
) -> AddressResponse:
    try:
        return address_service.update_user_address(
            db,
            current_user=current_user,
            address_id=address_id,
            payload=payload,
        )
    except AddressNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AddressValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except AddressServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the address.",
        ) from exc


@router.delete(
    "/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved address for the current authenticated user",
)
def delete_current_user_address(
    address_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    address_service: Annotated[AddressService, Depends(get_address_service)],
) -> Response:
    try:
        address_service.delete_user_address(
            db,
            current_user=current_user,
            address_id=address_id,
        )
    except AddressNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AddressServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the address.",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/addresses/{address_id}/set-default",
    response_model=AddressResponse,
    summary="Set a saved address as default for the current authenticated user",
)
def set_default_current_user_address(
    address_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    address_service: Annotated[AddressService, Depends(get_address_service)],
) -> AddressResponse:
    try:
        return address_service.set_default_user_address(
            db,
            current_user=current_user,
            address_id=address_id,
        )
    except AddressNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AddressServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to set the default address.",
        ) from exc
