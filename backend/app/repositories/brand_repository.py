from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.brand import Brand


class BrandRepository:
    def create_brand(self, db: Session, *, brand_data: dict[str, object]) -> Brand:
        brand = Brand(**brand_data)
        db.add(brand)
        db.flush()
        return brand

    def get_brand_by_id(self, db: Session, *, brand_id: int) -> Brand | None:
        stmt = select(Brand).where(
            Brand.id == brand_id,
            Brand.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    def get_brand_by_slug(
        self,
        db: Session,
        *,
        slug: str,
        active_only: bool = False,
    ) -> Brand | None:
        stmt = select(Brand).where(
            func.lower(Brand.slug) == slug.lower(),
            Brand.deleted_at.is_(None),
        )
        if active_only:
            stmt = stmt.where(Brand.is_active.is_(True))
        return db.scalar(stmt)

    def get_brand_by_name(self, db: Session, *, name: str) -> Brand | None:
        stmt = select(Brand).where(
            func.lower(Brand.name) == name.lower(),
            Brand.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    def list_brands(
        self,
        db: Session,
        *,
        active_only: bool = False,
    ) -> list[Brand]:
        stmt = select(Brand).where(Brand.deleted_at.is_(None))
        if active_only:
            stmt = stmt.where(Brand.is_active.is_(True))
        stmt = stmt.order_by(Brand.name.asc())
        return list(db.scalars(stmt).all())

    def slug_exists(
        self,
        db: Session,
        *,
        slug: str,
        exclude_brand_id: int | None = None,
    ) -> bool:
        stmt = select(Brand.id).where(
            func.lower(Brand.slug) == slug.lower(),
            Brand.deleted_at.is_(None),
        )
        if exclude_brand_id is not None:
            stmt = stmt.where(Brand.id != exclude_brand_id)
        return db.scalar(stmt) is not None

    def update_brand(
        self,
        db: Session,
        *,
        brand: Brand,
        update_data: dict[str, object],
    ) -> Brand:
        for field_name, value in update_data.items():
            setattr(brand, field_name, value)

        db.add(brand)
        db.flush()
        return brand

    def soft_delete_brand(self, db: Session, *, brand: Brand) -> Brand:
        brand.deleted_at = datetime.now(UTC)
        db.add(brand)
        db.flush()
        return brand
