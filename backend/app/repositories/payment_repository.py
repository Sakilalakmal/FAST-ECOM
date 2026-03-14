from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order, PaymentStatus
from app.models.payment import Payment
from app.schemas.payment import PaymentListQuery


class PaymentRepository:
    def get_order_by_id_and_user_id(
        self,
        db: Session,
        *,
        order_id: int,
        user_id: int,
    ) -> Order | None:
        stmt = select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id,
            Order.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    def get_order_by_id(self, db: Session, *, order_id: int) -> Order | None:
        stmt = select(Order).where(
            Order.id == order_id,
            Order.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    def create_payment(self, db: Session, *, payment_data: dict[str, object]) -> Payment:
        payment = Payment(**payment_data)
        db.add(payment)
        db.flush()
        return payment

    def get_payment_by_id_and_user_id(
        self,
        db: Session,
        *,
        payment_id: int,
        user_id: int,
    ) -> Payment | None:
        stmt = (
            select(Payment)
            .options(*self._payment_load_options())
            .where(
                Payment.id == payment_id,
                Payment.user_id == user_id,
                Payment.deleted_at.is_(None),
            )
        )
        return db.scalar(stmt)

    def get_payment_by_id(self, db: Session, *, payment_id: int) -> Payment | None:
        stmt = (
            select(Payment)
            .options(*self._payment_load_options())
            .where(
                Payment.id == payment_id,
                Payment.deleted_at.is_(None),
            )
        )
        return db.scalar(stmt)

    def list_payments_by_user(
        self,
        db: Session,
        *,
        user_id: int,
        filters: PaymentListQuery,
    ) -> tuple[list[Payment], int]:
        stmt = (
            select(Payment)
            .options(*self._payment_load_options())
            .where(
                Payment.user_id == user_id,
                Payment.deleted_at.is_(None),
            )
        )
        count_stmt = select(func.count(Payment.id)).where(
            Payment.user_id == user_id,
            Payment.deleted_at.is_(None),
        )

        if filters.order_id is not None:
            stmt = stmt.where(Payment.order_id == filters.order_id)
            count_stmt = count_stmt.where(Payment.order_id == filters.order_id)

        stmt = (
            stmt.order_by(Payment.created_at.desc(), Payment.id.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        total = int(db.scalar(count_stmt) or 0)
        items = list(db.scalars(stmt).all())
        return items, total

    def list_payments(
        self,
        db: Session,
        *,
        filters: PaymentListQuery,
    ) -> tuple[list[Payment], int]:
        stmt = (
            select(Payment)
            .options(*self._payment_load_options())
            .where(Payment.deleted_at.is_(None))
        )
        count_stmt = select(func.count(Payment.id)).where(Payment.deleted_at.is_(None))

        if filters.order_id is not None:
            stmt = stmt.where(Payment.order_id == filters.order_id)
            count_stmt = count_stmt.where(Payment.order_id == filters.order_id)

        stmt = (
            stmt.order_by(Payment.created_at.desc(), Payment.id.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        total = int(db.scalar(count_stmt) or 0)
        items = list(db.scalars(stmt).all())
        return items, total

    def get_active_payment_by_order_id(self, db: Session, *, order_id: int) -> Payment | None:
        stmt = (
            select(Payment)
            .options(*self._payment_load_options())
            .where(
                Payment.order_id == order_id,
                Payment.deleted_at.is_(None),
                Payment.status.in_((PaymentStatus.PENDING, PaymentStatus.REQUIRES_ACTION)),
            )
            .order_by(Payment.attempt_number.desc(), Payment.id.desc())
            .limit(1)
        )
        return db.scalar(stmt)

    def get_latest_payment_by_order_id(self, db: Session, *, order_id: int) -> Payment | None:
        stmt = (
            select(Payment)
            .options(*self._payment_load_options())
            .where(
                Payment.order_id == order_id,
                Payment.deleted_at.is_(None),
            )
            .order_by(Payment.attempt_number.desc(), Payment.id.desc())
            .limit(1)
        )
        return db.scalar(stmt)

    def get_next_attempt_number(self, db: Session, *, order_id: int) -> int:
        stmt = select(func.coalesce(func.max(Payment.attempt_number), 0)).where(
            Payment.order_id == order_id,
            Payment.deleted_at.is_(None),
        )
        return int(db.scalar(stmt) or 0) + 1

    def update_payment(
        self,
        db: Session,
        *,
        payment: Payment,
        update_data: dict[str, object],
    ) -> Payment:
        for field_name, value in update_data.items():
            setattr(payment, field_name, value)

        db.add(payment)
        db.flush()
        return payment

    def update_order_payment_status(
        self,
        db: Session,
        *,
        order: Order,
        payment_status: PaymentStatus,
    ) -> Order:
        order.payment_status = payment_status
        db.add(order)
        db.flush()
        return order

    def _payment_load_options(self):
        return (selectinload(Payment.order),)
