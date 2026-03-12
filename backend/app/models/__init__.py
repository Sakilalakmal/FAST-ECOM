"""Shared ORM models and mixins.

Import concrete model modules here when they are introduced so Alembic
autogeneration can discover them through a single import location.
"""

from app.models.associations import UserRole
from app.models.address import Address, AddressType
from app.models.base import ORMModel
from app.models.brand import Brand
from app.models.category import Category
from app.models.mixins import ActiveMixin, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_specification import ProductSpecification
from app.models.user import User

__all__ = [
    "ActiveMixin",
    "Address",
    "AddressType",
    "Brand",
    "Category",
    "ORMModel",
    "PrimaryKeyMixin",
    "Product",
    "ProductImage",
    "ProductSpecification",
    "RefreshToken",
    "Role",
    "SoftDeleteMixin",
    "TimestampMixin",
    "User",
    "UserRole",
]
