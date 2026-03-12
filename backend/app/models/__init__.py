"""Shared ORM models and mixins.

Import concrete model modules here when they are introduced so Alembic
autogeneration can discover them through a single import location.
"""

from app.models.associations import UserRole
from app.models.base import ORMModel
from app.models.mixins import ActiveMixin, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User

__all__ = [
    "ActiveMixin",
    "ORMModel",
    "PrimaryKeyMixin",
    "RefreshToken",
    "Role",
    "SoftDeleteMixin",
    "TimestampMixin",
    "User",
    "UserRole",
]
