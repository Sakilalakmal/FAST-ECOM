from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db_session
from app.models.user import User
from app.schemas.wishlist import AddWishlistItemRequest, WishlistResponse
from app.services.wishlist_service import (
    WishlistItemNotFoundError,
    WishlistProductNotFoundError,
    WishlistService,
    WishlistServiceError,
)

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


def get_wishlist_service() -> WishlistService:
    return WishlistService()


@router.get(
    "",
    response_model=WishlistResponse,
    summary="Get the current authenticated user's wishlist",
)
def get_current_wishlist(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    wishlist_service: Annotated[WishlistService, Depends(get_wishlist_service)],
) -> WishlistResponse:
    try:
        return wishlist_service.get_current_wishlist(db, current_user=current_user)
    except WishlistServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load the wishlist.",
        ) from exc


@router.post(
    "/items",
    response_model=WishlistResponse,
    status_code=status.HTTP_200_OK,
    summary="Add a product to the current authenticated user's wishlist",
)
def add_wishlist_item(
    payload: AddWishlistItemRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    wishlist_service: Annotated[WishlistService, Depends(get_wishlist_service)],
) -> WishlistResponse:
    try:
        return wishlist_service.add_item(db, current_user=current_user, payload=payload)
    except WishlistProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except WishlistServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to add the product to the wishlist.",
        ) from exc


@router.delete(
    "/items/{product_id}",
    response_model=WishlistResponse,
    summary="Remove a product from the current authenticated user's wishlist",
)
def remove_wishlist_item(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    wishlist_service: Annotated[WishlistService, Depends(get_wishlist_service)],
) -> WishlistResponse:
    try:
        return wishlist_service.remove_item(db, current_user=current_user, product_id=product_id)
    except WishlistItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except WishlistServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to remove the product from the wishlist.",
        ) from exc


@router.delete(
    "/items",
    response_model=WishlistResponse,
    summary="Clear the current authenticated user's wishlist",
)
def clear_wishlist(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    wishlist_service: Annotated[WishlistService, Depends(get_wishlist_service)],
) -> WishlistResponse:
    try:
        return wishlist_service.clear_wishlist(db, current_user=current_user)
    except WishlistServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to clear the wishlist.",
        ) from exc
