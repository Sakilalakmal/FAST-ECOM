from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryRepository:
    def create_category(self, db: Session, *, category_data: dict[str, object]) -> Category:
        category = Category(**category_data)
        db.add(category)
        db.flush()
        return category

    def get_category_by_id(self, db: Session, *, category_id: int) -> Category | None:
        stmt = select(Category).where(
            Category.id == category_id,
            Category.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    def get_category_by_slug(
        self,
        db: Session,
        *,
        slug: str,
        active_only: bool = False,
    ) -> Category | None:
        stmt = select(Category).where(
            func.lower(Category.slug) == slug.lower(),
            Category.deleted_at.is_(None),
        )
        if active_only:
            stmt = stmt.where(Category.is_active.is_(True))
        return db.scalar(stmt)

    def get_category_by_name(self, db: Session, *, name: str) -> Category | None:
        stmt = select(Category).where(
            func.lower(Category.name) == name.lower(),
            Category.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    def list_categories(
        self,
        db: Session,
        *,
        active_only: bool = False,
    ) -> list[Category]:
        stmt = select(Category).where(Category.deleted_at.is_(None))
        if active_only:
            stmt = stmt.where(Category.is_active.is_(True))
        stmt = stmt.order_by(Category.sort_order.asc(), Category.name.asc())
        return list(db.scalars(stmt).all())

    def slug_exists(
        self,
        db: Session,
        *,
        slug: str,
        exclude_category_id: int | None = None,
    ) -> bool:
        stmt = select(Category.id).where(
            func.lower(Category.slug) == slug.lower(),
            Category.deleted_at.is_(None),
        )
        if exclude_category_id is not None:
            stmt = stmt.where(Category.id != exclude_category_id)
        return db.scalar(stmt) is not None

    def update_category(
        self,
        db: Session,
        *,
        category: Category,
        update_data: dict[str, object],
    ) -> Category:
        for field_name, value in update_data.items():
            setattr(category, field_name, value)

        db.add(category)
        db.flush()
        return category

    def soft_delete_category(self, db: Session, *, category: Category) -> Category:
        category.deleted_at = datetime.now(UTC)
        db.add(category)
        db.flush()
        return category

    def detach_children(self, db: Session, *, parent_id: int) -> None:
        stmt = select(Category).where(
            Category.parent_id == parent_id,
            Category.deleted_at.is_(None),
        )
        for child in db.scalars(stmt):
            child.parent_id = None
            db.add(child)

        db.flush()
