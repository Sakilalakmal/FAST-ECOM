from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.categories import get_category_service
from app.dependencies.auth import get_current_admin_user
from app.dependencies.db import get_db_session
from app.models.user import User
from app.schemas.category import CategoryCreateRequest, CategoryResponse, CategoryUpdateRequest
from app.services.category_service import (
    CategoryAlreadyExistsError,
    CategoryNotFoundError,
    CategoryService,
    CategoryServiceError,
    CategoryValidationError,
)

router = APIRouter(prefix="/admin/categories", tags=["admin-categories"])


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a catalog category",
)
def create_category(
    payload: CategoryCreateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    try:
        return category_service.create_category(db, payload=payload)
    except CategoryValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CategoryAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except CategoryServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the category.",
        ) from exc


@router.get(
    "",
    response_model=list[CategoryResponse],
    summary="List catalog categories for admin management",
)
def list_categories(
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
) -> list[CategoryResponse]:
    return category_service.list_admin_categories(db)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get a catalog category for admin management",
)
def get_category(
    category_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    try:
        return category_service.get_admin_category(db, category_id=category_id)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update a catalog category",
)
def update_category(
    category_id: int,
    payload: CategoryUpdateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    try:
        return category_service.update_category(db, category_id=category_id, payload=payload)
    except CategoryValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CategoryAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CategoryServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the category.",
        ) from exc


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a catalog category",
)
def delete_category(
    category_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
) -> Response:
    try:
        category_service.delete_category(db, category_id=category_id)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CategoryServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the category.",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
