from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db_session
from app.models.user import User
from app.schemas.order import OrderListQuery, OrderListResponse, OrderResponse, PlaceOrderRequest
from app.services.order_service import (
    OrderAddressNotFoundError,
    OrderCartEmptyError,
    OrderInventoryError,
    OrderNotFoundError,
    OrderService,
    OrderServiceError,
    OrderValidationError,
)

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_service() -> OrderService:
    return OrderService()


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place an order from the current authenticated user's cart",
)
def place_order(
    payload: PlaceOrderRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    try:
        return order_service.place_order(db, current_user=current_user, payload=payload)
    except OrderAddressNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (OrderCartEmptyError, OrderValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OrderInventoryError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except OrderServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to place the order.",
        ) from exc


@router.get(
    "",
    response_model=OrderListResponse,
    summary="List orders for the current authenticated user",
)
def list_orders(
    filters: Annotated[OrderListQuery, Depends()],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderListResponse:
    return order_service.list_user_orders(db, current_user=current_user, filters=filters)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get an order for the current authenticated user",
)
def get_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    try:
        return order_service.get_user_order(db, current_user=current_user, order_id=order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
