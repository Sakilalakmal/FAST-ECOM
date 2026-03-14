from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.payment import Payment, PaymentMethod
from app.models.user import User
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import (
    AdminPaymentStatusUpdateRequest,
    PaymentCreateRequest,
    PaymentListQuery,
    PaymentListResponse,
    PaymentOrderSummary,
    PaymentResponse,
)


class PaymentServiceError(Exception):
    pass


class PaymentNotFoundError(PaymentServiceError):
    pass


class PaymentValidationError(PaymentServiceError):
    pass


class PaymentService:
    SUPPORTED_CREATION_METHODS = {
        PaymentMethod.CASH_ON_DELIVERY,
        PaymentMethod.BANK_TRANSFER,
    }
    PAYABLE_ORDER_STATUSES = {
        OrderStatus.PENDING,
        OrderStatus.CONFIRMED,
        OrderStatus.PROCESSING,
    }

    def __init__(self, repository: PaymentRepository | None = None) -> None:
        self.repository = repository or PaymentRepository()

    def create_payment_for_order(
        self,
        db: Session,
        *,
        current_user: User,
        order_id: int,
        payload: PaymentCreateRequest,
    ) -> PaymentResponse:
        order = self.repository.get_order_by_id_and_user_id(
            db,
            order_id=order_id,
            user_id=current_user.id,
        )
        if order is None:
            raise PaymentNotFoundError("Order not found.")

        self._validate_order_for_payment_creation(db, order=order, payload=payload)

        initiated_at = datetime.now(UTC)
        payment_id: int
        try:
            payment = self.repository.create_payment(
                db,
                payment_data={
                    "order_id": order.id,
                    "user_id": current_user.id,
                    "attempt_number": self.repository.get_next_attempt_number(
                        db,
                        order_id=order.id,
                    ),
                    "payment_method": payload.payment_method,
                    "status": self._get_initial_status(payload.payment_method),
                    "amount": order.total_amount,
                    "currency_code": order.currency_code,
                    "provider_name": payload.provider_name,
                    "provider_reference": payload.provider_reference,
                    "external_reference": payload.external_reference,
                    "initiated_at": initiated_at,
                    "notes": payload.notes,
                },
            )
            self.repository.update_order_payment_status(
                db,
                order=order,
                payment_status=payment.status,
            )
            payment_id = payment.id
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise PaymentServiceError("Unable to create the payment.") from exc

        created_payment = self.repository.get_payment_by_id_and_user_id(
            db,
            payment_id=payment_id,
            user_id=current_user.id,
        )
        if created_payment is None:
            raise PaymentServiceError("Unable to load the created payment.")
        return self.build_payment_response(created_payment)

    def list_user_payments(
        self,
        db: Session,
        *,
        current_user: User,
        filters: PaymentListQuery,
    ) -> PaymentListResponse:
        if filters.order_id is not None:
            order = self.repository.get_order_by_id_and_user_id(
                db,
                order_id=filters.order_id,
                user_id=current_user.id,
            )
            if order is None:
                raise PaymentNotFoundError("Order not found.")

        payments, total = self.repository.list_payments_by_user(
            db,
            user_id=current_user.id,
            filters=filters,
        )
        return PaymentListResponse.create(
            items=[self.build_payment_response(payment) for payment in payments],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    def list_user_order_payments(
        self,
        db: Session,
        *,
        current_user: User,
        order_id: int,
        filters: PaymentListQuery,
    ) -> PaymentListResponse:
        order = self.repository.get_order_by_id_and_user_id(
            db,
            order_id=order_id,
            user_id=current_user.id,
        )
        if order is None:
            raise PaymentNotFoundError("Order not found.")

        scoped_filters = PaymentListQuery(
            page=filters.page,
            page_size=filters.page_size,
            order_id=order_id,
        )
        payments, total = self.repository.list_payments_by_user(
            db,
            user_id=current_user.id,
            filters=scoped_filters,
        )
        return PaymentListResponse.create(
            items=[self.build_payment_response(payment) for payment in payments],
            total=total,
            page=scoped_filters.page,
            page_size=scoped_filters.page_size,
        )

    def get_user_payment(
        self,
        db: Session,
        *,
        current_user: User,
        payment_id: int,
    ) -> PaymentResponse:
        payment = self.repository.get_payment_by_id_and_user_id(
            db,
            payment_id=payment_id,
            user_id=current_user.id,
        )
        if payment is None:
            raise PaymentNotFoundError("Payment not found.")
        return self.build_payment_response(payment)

    def list_admin_payments(
        self,
        db: Session,
        *,
        filters: PaymentListQuery,
    ) -> PaymentListResponse:
        payments, total = self.repository.list_payments(db, filters=filters)
        return PaymentListResponse.create(
            items=[self.build_payment_response(payment) for payment in payments],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    def get_admin_payment(self, db: Session, *, payment_id: int) -> PaymentResponse:
        payment = self.repository.get_payment_by_id(db, payment_id=payment_id)
        if payment is None:
            raise PaymentNotFoundError("Payment not found.")
        return self.build_payment_response(payment)

    def update_admin_payment_status(
        self,
        db: Session,
        *,
        payment_id: int,
        payload: AdminPaymentStatusUpdateRequest,
    ) -> PaymentResponse:
        payment = self.repository.get_payment_by_id(db, payment_id=payment_id)
        if payment is None:
            raise PaymentNotFoundError("Payment not found.")

        latest_payment = self.repository.get_latest_payment_by_order_id(
            db,
            order_id=payment.order_id,
        )
        if latest_payment is None or latest_payment.id != payment.id:
            raise PaymentValidationError("Only the latest payment attempt can be updated.")

        self._validate_status_transition(current_status=payment.status, target_status=payload.status)
        update_data = self._build_status_update_data(payment=payment, payload=payload)

        try:
            self.repository.update_payment(db, payment=payment, update_data=update_data)
            self.repository.update_order_payment_status(
                db,
                order=payment.order,
                payment_status=payload.status,
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise PaymentServiceError("Unable to update the payment status.") from exc

        refreshed_payment = self.repository.get_payment_by_id(db, payment_id=payment_id)
        if refreshed_payment is None:
            raise PaymentServiceError("Unable to load the updated payment.")
        return self.build_payment_response(refreshed_payment)

    def build_payment_response(self, payment: Payment) -> PaymentResponse:
        order = payment.order
        if order is None:
            raise PaymentServiceError("Payment order relationship is not available.")

        return PaymentResponse(
            id=payment.id,
            order_id=payment.order_id,
            user_id=payment.user_id,
            attempt_number=payment.attempt_number,
            payment_method=payment.payment_method,
            status=payment.status,
            amount=payment.amount,
            currency_code=payment.currency_code,
            provider_name=payment.provider_name,
            provider_transaction_id=payment.provider_transaction_id,
            provider_reference=payment.provider_reference,
            external_reference=payment.external_reference,
            notes=payment.notes,
            initiated_at=payment.initiated_at,
            completed_at=payment.completed_at,
            failed_at=payment.failed_at,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            order=self._build_order_summary(order),
        )

    def _build_order_summary(self, order: Order) -> PaymentOrderSummary:
        return PaymentOrderSummary(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            payment_status=order.payment_status,
            total_amount=order.total_amount,
            currency_code=order.currency_code,
            placed_at=order.placed_at,
        )

    def _validate_order_for_payment_creation(
        self,
        db: Session,
        *,
        order: Order,
        payload: PaymentCreateRequest,
    ) -> None:
        if payload.payment_method not in self.SUPPORTED_CREATION_METHODS:
            raise PaymentValidationError(
                "This payment method is not available yet for checkout."
            )
        if order.status not in self.PAYABLE_ORDER_STATUSES:
            raise PaymentValidationError(
                "This order cannot accept a new payment in its current status."
            )
        if order.payment_status in {PaymentStatus.PAID, PaymentStatus.REFUNDED}:
            raise PaymentValidationError("This order already has a finalized payment status.")
        if self.repository.get_active_payment_by_order_id(db, order_id=order.id) is not None:
            raise PaymentValidationError("An active payment attempt already exists for this order.")

    def _get_initial_status(self, payment_method: PaymentMethod) -> PaymentStatus:
        if payment_method == PaymentMethod.BANK_TRANSFER:
            return PaymentStatus.REQUIRES_ACTION
        return PaymentStatus.PENDING

    def _validate_status_transition(
        self,
        *,
        current_status: PaymentStatus,
        target_status: PaymentStatus,
    ) -> None:
        if current_status == target_status:
            return
        if current_status == PaymentStatus.PAID and target_status != PaymentStatus.REFUNDED:
            raise PaymentValidationError("A paid payment can only be marked as refunded.")
        if target_status == PaymentStatus.UNPAID:
            raise PaymentValidationError("unpaid is not a valid payment record status.")
        if current_status in {PaymentStatus.FAILED, PaymentStatus.CANCELLED, PaymentStatus.REFUNDED}:
            raise PaymentValidationError("This payment attempt is already finalized.")
        if target_status == PaymentStatus.REFUNDED and current_status != PaymentStatus.PAID:
            raise PaymentValidationError("Only a paid payment can be marked as refunded.")

    def _build_status_update_data(
        self,
        *,
        payment: Payment,
        payload: AdminPaymentStatusUpdateRequest,
    ) -> dict[str, object]:
        timestamp = datetime.now(UTC)
        update_data = payload.model_dump(exclude_unset=True)
        update_data["status"] = payload.status

        if payment.initiated_at is None:
            update_data["initiated_at"] = timestamp

        if payload.status == PaymentStatus.PAID:
            update_data["completed_at"] = timestamp
            update_data["failed_at"] = None
        elif payload.status in {PaymentStatus.FAILED, PaymentStatus.CANCELLED}:
            update_data["failed_at"] = timestamp

        return update_data
