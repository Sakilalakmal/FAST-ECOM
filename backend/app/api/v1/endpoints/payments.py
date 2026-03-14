from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db_session
from app.models.user import User
from app.schemas.payment import PaymentCreateRequest, PaymentListQuery, PaymentListResponse, PaymentResponse
from app.services.payment_service import (
    PaymentNotFoundError,
    PaymentService,
    PaymentServiceError,
    PaymentValidationError,
)

router = APIRouter(tags=["payments"])


def get_payment_service() -> PaymentService:
    return PaymentService()


@router.post(
    "/orders/{order_id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a payment attempt for the current authenticated user's order",
)
def create_order_payment(
    order_id: int,
    payload: PaymentCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> PaymentResponse:
    try:
        return payment_service.create_payment_for_order(
            db,
            current_user=current_user,
            order_id=order_id,
            payload=payload,
        )
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PaymentValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PaymentServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the payment.",
        ) from exc


@router.get(
    "/orders/{order_id}/payments",
    response_model=PaymentListResponse,
    summary="List payment attempts for one of the current authenticated user's orders",
)
def list_order_payments(
    order_id: int,
    filters: Annotated[PaymentListQuery, Depends()],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> PaymentListResponse:
    try:
        return payment_service.list_user_order_payments(
            db,
            current_user=current_user,
            order_id=order_id,
            filters=filters,
        )
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/payments",
    response_model=PaymentListResponse,
    summary="List payments for the current authenticated user",
)
def list_payments(
    filters: Annotated[PaymentListQuery, Depends()],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> PaymentListResponse:
    try:
        return payment_service.list_user_payments(db, current_user=current_user, filters=filters)
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentResponse,
    summary="Get a payment for the current authenticated user",
)
def get_payment(
    payment_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db_session)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> PaymentResponse:
    try:
        return payment_service.get_user_payment(db, current_user=current_user, payment_id=payment_id)
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
