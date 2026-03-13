from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db_session
from app.models.user import User
from app.schemas.cart import AddCartItemRequest, CartResponse, UpdateCartItemRequest
from app.services.cart_service import (
    CartItemNotFoundError,
    CartService,
    CartServiceError,
    CartValidationError,
    CartVariantNotFoundError,
    CartVariantUnavailableError,
)

router = APIRouter(prefix="/cart", tags=["cart"])


def get_cart_service() -> CartService:
    return CartService()


@router.get(
    "",
    response_model=CartResponse,
    summary="Get the current authenticated user's cart",
)
def get_current_cart(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> CartResponse:
    try:
        return cart_service.get_current_cart(db, current_user=current_user)
    except CartServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load the cart.",
        ) from exc


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Add an item to the current authenticated user's cart",
)
def add_cart_item(
    payload: AddCartItemRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> CartResponse:
    try:
        return cart_service.add_item(db, current_user=current_user, payload=payload)
    except CartValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CartVariantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CartVariantUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except CartServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to add the item to the cart.",
        ) from exc


@router.patch(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Update the quantity of a cart item",
)
def update_cart_item_quantity(
    item_id: int,
    payload: UpdateCartItemRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> CartResponse:
    try:
        return cart_service.update_item_quantity(
            db,
            current_user=current_user,
            item_id=item_id,
            payload=payload,
        )
    except CartValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CartItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CartVariantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CartVariantUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except CartServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the cart item.",
        ) from exc


@router.delete(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Remove an item from the current authenticated user's cart",
)
def remove_cart_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> CartResponse:
    try:
        return cart_service.remove_item(db, current_user=current_user, item_id=item_id)
    except CartItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CartServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to remove the cart item.",
        ) from exc


@router.delete(
    "/items",
    response_model=CartResponse,
    summary="Clear all items from the current authenticated user's cart",
)
def clear_cart(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> CartResponse:
    try:
        return cart_service.clear_cart(db, current_user=current_user)
    except CartServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to clear the cart.",
        ) from exc
