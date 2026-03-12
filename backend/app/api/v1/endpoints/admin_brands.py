from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.brands import get_brand_service
from app.dependencies.auth import get_current_admin_user
from app.dependencies.db import get_db_session
from app.models.user import User
from app.schemas.brand import BrandCreateRequest, BrandResponse, BrandUpdateRequest
from app.services.brand_service import (
    BrandAlreadyExistsError,
    BrandNotFoundError,
    BrandService,
    BrandServiceError,
    BrandValidationError,
)

router = APIRouter(prefix="/admin/brands", tags=["admin-brands"])


@router.post(
    "",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a catalog brand",
)
def create_brand(
    payload: BrandCreateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    brand_service: Annotated[BrandService, Depends(get_brand_service)],
) -> BrandResponse:
    try:
        return brand_service.create_brand(db, payload=payload)
    except BrandValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except BrandAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except BrandServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the brand.",
        ) from exc


@router.get(
    "",
    response_model=list[BrandResponse],
    summary="List catalog brands for admin management",
)
def list_brands(
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    brand_service: Annotated[BrandService, Depends(get_brand_service)],
) -> list[BrandResponse]:
    return brand_service.list_admin_brands(db)


@router.get(
    "/{brand_id}",
    response_model=BrandResponse,
    summary="Get a catalog brand for admin management",
)
def get_brand(
    brand_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    brand_service: Annotated[BrandService, Depends(get_brand_service)],
) -> BrandResponse:
    try:
        return brand_service.get_admin_brand(db, brand_id=brand_id)
    except BrandNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/{brand_id}",
    response_model=BrandResponse,
    summary="Update a catalog brand",
)
def update_brand(
    brand_id: int,
    payload: BrandUpdateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    brand_service: Annotated[BrandService, Depends(get_brand_service)],
) -> BrandResponse:
    try:
        return brand_service.update_brand(db, brand_id=brand_id, payload=payload)
    except BrandValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except BrandAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except BrandNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BrandServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the brand.",
        ) from exc


@router.delete(
    "/{brand_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a catalog brand",
)
def delete_brand(
    brand_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    brand_service: Annotated[BrandService, Depends(get_brand_service)],
) -> Response:
    try:
        brand_service.delete_brand(db, brand_id=brand_id)
    except BrandNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BrandServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the brand.",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
