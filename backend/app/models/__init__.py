"""Shared ORM models and mixins.

Import concrete model modules here when they are introduced so Alembic
autogeneration can discover them through a single import location.
"""

from app.models.associations import UserRole
from app.models.address import Address, AddressType
from app.models.base import ORMModel
from app.models.brand import Brand
from app.models.category import Category
from app.models.inventory import Inventory
from app.models.mixins import ActiveMixin, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_specification import ProductSpecification
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.models.variant_option import VariantOption
from app.models.variant_option_value import VariantOptionValue
from app.models.variant_selection import VariantSelection

__all__ = [
    "ActiveMixin",
    "Address",
    "AddressType",
    "Brand",
    "Category",
    "Inventory",
    "ORMModel",
    "PrimaryKeyMixin",
    "Product",
    "ProductImage",
    "ProductSpecification",
    "ProductVariant",
    "RefreshToken",
    "Role",
    "SoftDeleteMixin",
    "TimestampMixin",
    "User",
    "UserRole",
    "VariantOption",
    "VariantOptionValue",
    "VariantSelection",
]
