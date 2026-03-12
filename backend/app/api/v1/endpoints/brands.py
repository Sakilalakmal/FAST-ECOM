from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.db import get_db_session
from app.schemas.brand import BrandResponse
from app.services.brand_service import BrandNotFoundError, BrandService

router = APIRouter(tags=["brands"])


def get_brand_service() -> BrandService:
    return BrandService()


@router.get(
    "/brands",
    response_model=list[BrandResponse],
    summary="List active catalog brands",
)
def list_public_brands(
    db: Annotated[Session, Depends(get_db_session)],
    brand_service: Annotated[BrandService, Depends(get_brand_service)],
) -> list[BrandResponse]:
    return brand_service.list_public_brands(db)


@router.get(
    "/brands/{slug}",
    response_model=BrandResponse,
    summary="Get an active catalog brand by slug",
)
def get_public_brand(
    slug: str,
    db: Annotated[Session, Depends(get_db_session)],
    brand_service: Annotated[BrandService, Depends(get_brand_service)],
) -> BrandResponse:
    try:
        return brand_service.get_public_brand(db, slug=slug)
    except BrandNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
