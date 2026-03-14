from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.payments import get_payment_service
from app.dependencies.auth import get_current_admin_user
from app.dependencies.db import get_db_session
from app.models.user import User
from app.schemas.payment import (
    AdminPaymentStatusUpdateRequest,
    PaymentListQuery,
    PaymentListResponse,
    PaymentResponse,
)
from app.services.payment_service import (
    PaymentNotFoundError,
    PaymentService,
    PaymentServiceError,
    PaymentValidationError,
)

router = APIRouter(prefix="/admin/payments", tags=["admin-payments"])


@router.get(
    "",
    response_model=PaymentListResponse,
    summary="List payments for admin management",
)
def list_payments(
    filters: Annotated[PaymentListQuery, Depends()],
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> PaymentListResponse:
    return payment_service.list_admin_payments(db, filters=filters)


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Get a payment for admin management",
)
def get_payment(
    payment_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> PaymentResponse:
    try:
        return payment_service.get_admin_payment(db, payment_id=payment_id)
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/{payment_id}/status",
    response_model=PaymentResponse,
    summary="Update a payment status",
)
def update_payment_status(
    payment_id: int,
    payload: AdminPaymentStatusUpdateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> PaymentResponse:
    try:
        return payment_service.update_admin_payment_status(
            db,
            payment_id=payment_id,
            payload=payload,
        )
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PaymentValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PaymentServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the payment status.",
        ) from exc
