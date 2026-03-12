from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.db import get_db_session
from app.schemas.category import CategoryResponse
from app.services.category_service import CategoryNotFoundError, CategoryService

router = APIRouter(tags=["categories"])


def get_category_service() -> CategoryService:
    return CategoryService()


@router.get(
    "/categories",
    response_model=list[CategoryResponse],
    summary="List active catalog categories",
)
def list_public_categories(
    db: Annotated[Session, Depends(get_db_session)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
) -> list[CategoryResponse]:
    return category_service.list_public_categories(db)


@router.get(
    "/categories/{slug}",
    response_model=CategoryResponse,
    summary="Get an active catalog category by slug",
)
def get_public_category(
    slug: str,
    db: Annotated[Session, Depends(get_db_session)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    try:
        return category_service.get_public_category(db, slug=slug)
    except CategoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
