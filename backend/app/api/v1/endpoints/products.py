from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.db import get_db_session
from app.schemas.product import ProductListResponse, ProductResponse, PublicProductListQuery
from app.services.product_service import ProductNotFoundError, ProductService

router = APIRouter(tags=["products"])


def get_product_service() -> ProductService:
    return ProductService()


@router.get(
    "/products",
    response_model=ProductListResponse,
    summary="List active products",
)
def list_public_products(
    filters: Annotated[PublicProductListQuery, Depends()],
    db: Annotated[Session, Depends(get_db_session)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductListResponse:
    return product_service.list_public_products(db, filters=filters)


@router.get(
    "/products/{slug}",
    response_model=ProductResponse,
    summary="Get an active product by slug",
)
def get_public_product(
    slug: str,
    db: Annotated[Session, Depends(get_db_session)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    try:
        return product_service.get_public_product(db, slug=slug)
    except ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
