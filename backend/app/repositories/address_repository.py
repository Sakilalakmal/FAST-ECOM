from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.address import Address


class AddressRepository:
    def list_addresses_by_user_id(self, db: Session, *, user_id: int) -> list[Address]:
        stmt = (
            select(Address)
            .where(Address.user_id == user_id, Address.deleted_at.is_(None))
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def count_addresses_by_user_id(self, db: Session, *, user_id: int) -> int:
        stmt = select(func.count(Address.id)).where(
            Address.user_id == user_id,
            Address.deleted_at.is_(None),
        )
        return int(db.scalar(stmt) or 0)

    def get_address_by_id_and_user_id(
        self,
        db: Session,
        *,
        address_id: int,
        user_id: int,
    ) -> Address | None:
        stmt = select(Address).where(
            Address.id == address_id,
            Address.user_id == user_id,
            Address.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    def create_address(
        self,
        db: Session,
        *,
        user_id: int,
        address_data: dict[str, object],
    ) -> Address:
        address = Address(user_id=user_id, **address_data)
        db.add(address)
        db.flush()
        return address

    def update_address(
        self,
        db: Session,
        *,
        address: Address,
        update_data: dict[str, object],
    ) -> Address:
        for field_name, value in update_data.items():
            setattr(address, field_name, value)

        db.add(address)
        db.flush()
        return address

    def soft_delete_address(self, db: Session, *, address: Address) -> Address:
        address.deleted_at = datetime.now(UTC)
        address.is_default = False
        db.add(address)
        db.flush()
        return address

    def unset_default_addresses(
        self,
        db: Session,
        *,
        user_id: int,
        exclude_address_id: int | None = None,
    ) -> None:
        stmt = select(Address).where(
            Address.user_id == user_id,
            Address.deleted_at.is_(None),
            Address.is_default.is_(True),
        )
        if exclude_address_id is not None:
            stmt = stmt.where(Address.id != exclude_address_id)

        for address in db.scalars(stmt):
            address.is_default = False
            db.add(address)

        db.flush()

    def set_address_as_default(self, db: Session, *, address: Address) -> Address:
        address.is_default = True
        db.add(address)
        db.flush()
        return address

    def get_default_candidate_for_user(
        self,
        db: Session,
        *,
        user_id: int,
        exclude_address_id: int | None = None,
    ) -> Address | None:
        stmt = (
            select(Address)
            .where(Address.user_id == user_id, Address.deleted_at.is_(None))
            .order_by(Address.created_at.asc())
        )
        if exclude_address_id is not None:
            stmt = stmt.where(Address.id != exclude_address_id)

        return db.scalar(stmt)
