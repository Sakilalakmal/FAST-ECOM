from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.associations import UserRole
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User


class AuthRepository:
    def get_user_by_email(self, db: Session, *, email: str) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.email == email, User.deleted_at.is_(None))
        )
        return db.scalar(stmt)

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

    def create_user(
        self,
        db: Session,
        *,
        email: str,
        hashed_password: str,
        first_name: str,
        last_name: str,
        phone_number: str | None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
        )
        db.add(user)
        db.flush()
        return user

    def get_role_by_name(self, db: Session, *, name: str) -> Role | None:
        stmt = select(Role).where(Role.name == name, Role.deleted_at.is_(None))
        return db.scalar(stmt)

    def attach_role_to_user(self, db: Session, *, user: User, role: Role) -> UserRole:
        existing_link = db.scalar(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
            )
        )
        if existing_link:
            return existing_link

        link = UserRole(user_id=user.id, role_id=role.id)
        db.add(link)
        db.flush()
        return link

    def update_last_login(
        self,
        db: Session,
        *,
        user: User,
        last_login_at: datetime,
    ) -> User:
        user.last_login_at = last_login_at
        db.add(user)
        db.flush()
        return user

    def store_refresh_token(
        self,
        db: Session,
        *,
        user_id: int,
        jti: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            jti=jti,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        db.add(refresh_token)
        db.flush()
        return refresh_token

    def find_refresh_token_by_jti(self, db: Session, *, jti: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        return db.scalar(stmt)

    def revoke_refresh_token(
        self,
        db: Session,
        *,
        refresh_token: RefreshToken,
        revoked_at: datetime | None = None,
    ) -> RefreshToken:
        refresh_token.revoked_at = revoked_at or datetime.now(UTC)
        db.add(refresh_token)
        db.flush()
        return refresh_token
