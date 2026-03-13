from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.variant_option import VariantOption
from app.models.variant_option_value import VariantOptionValue
from app.models.variant_selection import VariantSelection


class VariantRepository:
    def get_product_by_id(self, db: Session, *, product_id: int) -> Product | None:
        stmt = (
            select(Product)
            .options(
                selectinload(Product.variant_options).selectinload(VariantOption.values),
            )
            .where(Product.id == product_id, Product.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def count_variants_by_product(self, db: Session, *, product_id: int) -> int:
        stmt = select(func.count(ProductVariant.id)).where(
            ProductVariant.product_id == product_id,
            ProductVariant.deleted_at.is_(None),
        )
        return int(db.scalar(stmt) or 0)

    def list_variant_options_by_product(
        self,
        db: Session,
        *,
        product_id: int,
    ) -> list[VariantOption]:
        stmt = (
            select(VariantOption)
            .options(selectinload(VariantOption.values))
            .where(VariantOption.product_id == product_id, VariantOption.deleted_at.is_(None))
            .order_by(VariantOption.sort_order.asc(), VariantOption.id.asc())
        )
        return list(db.scalars(stmt).all())

    def get_variant_option_by_id(self, db: Session, *, option_id: int) -> VariantOption | None:
        stmt = (
            select(VariantOption)
            .options(selectinload(VariantOption.values))
            .where(VariantOption.id == option_id, VariantOption.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def option_name_exists(
        self,
        db: Session,
        *,
        product_id: int,
        normalized_name: str,
        exclude_option_id: int | None = None,
    ) -> bool:
        stmt = select(VariantOption.id).where(
            VariantOption.product_id == product_id,
            VariantOption.normalized_name == normalized_name,
            VariantOption.deleted_at.is_(None),
        )
        if exclude_option_id is not None:
            stmt = stmt.where(VariantOption.id != exclude_option_id)
        return db.scalar(stmt) is not None

    def create_variant_option(
        self,
        db: Session,
        *,
        product_id: int,
        option_data: dict[str, object],
    ) -> VariantOption:
        option = VariantOption(product_id=product_id, **option_data)
        db.add(option)
        db.flush()
        return option

    def update_variant_option(
        self,
        db: Session,
        *,
        option: VariantOption,
        update_data: dict[str, object],
    ) -> VariantOption:
        for field_name, value in update_data.items():
            setattr(option, field_name, value)

        db.add(option)
        db.flush()
        return option

    def soft_delete_variant_option(self, db: Session, *, option: VariantOption) -> VariantOption:
        deleted_at = datetime.now(UTC)
        option.deleted_at = deleted_at
        for value in option.values:
            value.deleted_at = deleted_at
            db.add(value)

        db.add(option)
        db.flush()
        return option

    def get_option_value_by_id(
        self,
        db: Session,
        *,
        value_id: int,
    ) -> VariantOptionValue | None:
        stmt = (
            select(VariantOptionValue)
            .options(selectinload(VariantOptionValue.option))
            .join(VariantOption, VariantOption.id == VariantOptionValue.option_id)
            .where(
                VariantOptionValue.id == value_id,
                VariantOptionValue.deleted_at.is_(None),
                VariantOption.deleted_at.is_(None),
            )
        )
        return db.scalar(stmt)

    def get_option_values_by_ids(
        self,
        db: Session,
        *,
        value_ids: list[int],
    ) -> list[VariantOptionValue]:
        if not value_ids:
            return []

        stmt = (
            select(VariantOptionValue)
            .options(selectinload(VariantOptionValue.option))
            .join(VariantOption, VariantOption.id == VariantOptionValue.option_id)
            .where(
                VariantOptionValue.id.in_(value_ids),
                VariantOptionValue.deleted_at.is_(None),
                VariantOption.deleted_at.is_(None),
            )
        )
        return list(db.scalars(stmt).all())

    def option_value_exists(
        self,
        db: Session,
        *,
        option_id: int,
        normalized_value: str,
        exclude_value_id: int | None = None,
    ) -> bool:
        stmt = select(VariantOptionValue.id).where(
            VariantOptionValue.option_id == option_id,
            VariantOptionValue.normalized_value == normalized_value,
            VariantOptionValue.deleted_at.is_(None),
        )
        if exclude_value_id is not None:
            stmt = stmt.where(VariantOptionValue.id != exclude_value_id)
        return db.scalar(stmt) is not None

    def create_option_value(
        self,
        db: Session,
        *,
        option_id: int,
        value_data: dict[str, object],
    ) -> VariantOptionValue:
        option_value = VariantOptionValue(option_id=option_id, **value_data)
        db.add(option_value)
        db.flush()
        return option_value

    def update_option_value(
        self,
        db: Session,
        *,
        option_value: VariantOptionValue,
        update_data: dict[str, object],
    ) -> VariantOptionValue:
        for field_name, value in update_data.items():
            setattr(option_value, field_name, value)

        db.add(option_value)
        db.flush()
        return option_value

    def soft_delete_option_value(
        self,
        db: Session,
        *,
        option_value: VariantOptionValue,
    ) -> VariantOptionValue:
        option_value.deleted_at = datetime.now(UTC)
        db.add(option_value)
        db.flush()
        return option_value

    def count_variant_assignments_by_option(self, db: Session, *, option_id: int) -> int:
        stmt = (
            select(func.count(VariantSelection.id))
            .join(ProductVariant, ProductVariant.id == VariantSelection.variant_id)
            .where(
                VariantSelection.option_id == option_id,
                ProductVariant.deleted_at.is_(None),
            )
        )
        return int(db.scalar(stmt) or 0)

    def count_variant_assignments_by_option_value(self, db: Session, *, option_value_id: int) -> int:
        stmt = (
            select(func.count(VariantSelection.id))
            .join(ProductVariant, ProductVariant.id == VariantSelection.variant_id)
            .where(
                VariantSelection.option_value_id == option_value_id,
                ProductVariant.deleted_at.is_(None),
            )
        )
        return int(db.scalar(stmt) or 0)

    def list_variants_by_product(
        self,
        db: Session,
        *,
        product_id: int,
    ) -> list[ProductVariant]:
        stmt = (
            select(ProductVariant)
            .options(*self._variant_load_options())
            .where(ProductVariant.product_id == product_id, ProductVariant.deleted_at.is_(None))
            .order_by(ProductVariant.sort_order.asc(), ProductVariant.id.asc())
        )
        return list(db.scalars(stmt).all())

    def get_variant_by_id(self, db: Session, *, variant_id: int) -> ProductVariant | None:
        stmt = (
            select(ProductVariant)
            .options(*self._variant_load_options())
            .where(ProductVariant.id == variant_id, ProductVariant.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def get_variant_by_sku(
        self,
        db: Session,
        *,
        sku: str,
        exclude_variant_id: int | None = None,
    ) -> ProductVariant | None:
        stmt = select(ProductVariant).where(
            func.lower(ProductVariant.sku) == sku.lower(),
            ProductVariant.deleted_at.is_(None),
        )
        if exclude_variant_id is not None:
            stmt = stmt.where(ProductVariant.id != exclude_variant_id)
        return db.scalar(stmt)

    def variant_combination_exists(
        self,
        db: Session,
        *,
        product_id: int,
        combination_signature: str,
        exclude_variant_id: int | None = None,
    ) -> bool:
        stmt = select(ProductVariant.id).where(
            ProductVariant.product_id == product_id,
            ProductVariant.combination_signature == combination_signature,
            ProductVariant.deleted_at.is_(None),
        )
        if exclude_variant_id is not None:
            stmt = stmt.where(ProductVariant.id != exclude_variant_id)
        return db.scalar(stmt) is not None

    def create_variant(
        self,
        db: Session,
        *,
        product_id: int,
        variant_data: dict[str, object],
    ) -> ProductVariant:
        variant = ProductVariant(product_id=product_id, **variant_data)
        db.add(variant)
        db.flush()
        return variant

    def update_variant(
        self,
        db: Session,
        *,
        variant: ProductVariant,
        update_data: dict[str, object],
    ) -> ProductVariant:
        for field_name, value in update_data.items():
            setattr(variant, field_name, value)

        db.add(variant)
        db.flush()
        return variant

    def replace_variant_selections(
        self,
        db: Session,
        *,
        variant: ProductVariant,
        selections_data: list[dict[str, object]],
    ) -> list[VariantSelection]:
        variant.selections.clear()
        db.flush()

        new_selections = [VariantSelection(variant_id=variant.id, **selection) for selection in selections_data]
        variant.selections.extend(new_selections)
        db.add(variant)
        db.flush()
        return new_selections

    def soft_delete_variant(self, db: Session, *, variant: ProductVariant) -> ProductVariant:
        variant.deleted_at = datetime.now(UTC)
        variant.is_active = False
        db.add(variant)
        db.flush()
        return variant

    def _variant_load_options(self):
        return (
            selectinload(ProductVariant.product),
            selectinload(ProductVariant.inventory),
            selectinload(ProductVariant.selections).selectinload(VariantSelection.option),
            selectinload(ProductVariant.selections).selectinload(VariantSelection.option_value),
        )
