from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.associations import UserRole
from app.models.user import User


class UserRepository:
    def get_user_by_id(self, db: Session, *, user_id: int) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.id == user_id, User.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def get_user_by_phone_number(self, db: Session, *, phone_number: str) -> User | None:
        stmt = select(User).where(
            User.phone_number == phone_number,
            User.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    def update_user_profile(
        self,
        db: Session,
        *,
        user: User,
        update_data: dict[str, object],
    ) -> User:
        for field_name, value in update_data.items():
            setattr(user, field_name, value)

        db.add(user)
        db.flush()
        return user
