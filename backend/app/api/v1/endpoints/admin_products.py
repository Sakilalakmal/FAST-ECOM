from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.products import get_product_service
from app.dependencies.auth import get_current_admin_user
from app.dependencies.db import get_db_session
from app.models.user import User
from app.schemas.product import (
    AdminProductListQuery,
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
)
from app.services.product_service import (
    ProductAlreadyExistsError,
    ProductNotFoundError,
    ProductService,
    ProductServiceError,
    ProductValidationError,
)

router = APIRouter(prefix="/admin/products", tags=["admin-products"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
)
def create_product(
    payload: ProductCreateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    try:
        return product_service.create_product(db, payload=payload)
    except ProductValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProductAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ProductServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the product.",
        ) from exc


@router.get(
    "",
    response_model=ProductListResponse,
    summary="List products for admin management",
)
def list_products(
    filters: Annotated[AdminProductListQuery, Depends()],
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductListResponse:
    return product_service.list_admin_products(db, filters=filters)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get a product for admin management",
)
def get_product(
    product_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    try:
        return product_service.get_admin_product(db, product_id=product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update a product",
)
def update_product(
    product_id: int,
    payload: ProductUpdateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    try:
        return product_service.update_product(db, product_id=product_id, payload=payload)
    except ProductValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProductAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProductServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the product.",
        ) from exc


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
)
def delete_product(
    product_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> Response:
    try:
        product_service.delete_product(db, product_id=product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProductServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the product.",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
