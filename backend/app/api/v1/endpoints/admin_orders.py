from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.orders import get_order_service
from app.dependencies.auth import get_current_admin_user
from app.dependencies.db import get_db_session
from app.models.user import User
from app.schemas.order import (
    AdminOrderStatusUpdateRequest,
    OrderListQuery,
    OrderListResponse,
    OrderResponse,
)
from app.services.order_service import OrderNotFoundError, OrderService, OrderServiceError

router = APIRouter(prefix="/admin/orders", tags=["admin-orders"])


@router.get(
    "",
    response_model=OrderListResponse,
    summary="List orders for admin management",
)
def list_orders(
    filters: Annotated[OrderListQuery, Depends()],
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderListResponse:
    return order_service.list_admin_orders(db, filters=filters)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get an order for admin management",
)
def get_order(
    order_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    try:
        return order_service.get_admin_order(db, order_id=order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update an order status",
)
def update_order_status(
    order_id: int,
    payload: AdminOrderStatusUpdateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    try:
        return order_service.update_order_status(db, order_id=order_id, payload=payload)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OrderServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the order status.",
        ) from exc


