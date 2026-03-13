from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.brand import Brand
from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant
from app.models.product_specification import ProductSpecification
from app.models.variant_option import VariantOption
from app.models.variant_selection import VariantSelection
from app.schemas.product import AdminProductListQuery, ProductSortOption, PublicProductListQuery


class ProductRepository:
    def create_product(self, db: Session, *, product_data: dict[str, object]) -> Product:
        product = Product(**product_data)
        db.add(product)
        db.flush()
        return product

    def get_product_by_id(
        self,
        db: Session,
        *,
        product_id: int,
        active_only: bool = False,
    ) -> Product | None:
        stmt = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.brand),
                selectinload(Product.images),
                selectinload(Product.specifications),
                selectinload(Product.variant_options).selectinload(VariantOption.values),
                selectinload(Product.variants).selectinload(ProductVariant.inventory),
                selectinload(Product.variants)
                .selectinload(ProductVariant.selections)
                .selectinload(VariantSelection.option),
                selectinload(Product.variants)
                .selectinload(ProductVariant.selections)
                .selectinload(VariantSelection.option_value),
            )
            .where(Product.id == product_id, Product.deleted_at.is_(None))
        )
        if active_only:
            stmt = stmt.join(Category, Product.category_id == Category.id).where(
                Product.is_active.is_(True),
                Category.deleted_at.is_(None),
                Category.is_active.is_(True),
            )
        return db.scalar(stmt)

    def get_product_by_slug(
        self,
        db: Session,
        *,
        slug: str,
        active_only: bool = False,
    ) -> Product | None:
        stmt = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.brand),
                selectinload(Product.images),
                selectinload(Product.specifications),
                selectinload(Product.variant_options).selectinload(VariantOption.values),
                selectinload(Product.variants).selectinload(ProductVariant.inventory),
                selectinload(Product.variants)
                .selectinload(ProductVariant.selections)
                .selectinload(VariantSelection.option),
                selectinload(Product.variants)
                .selectinload(ProductVariant.selections)
                .selectinload(VariantSelection.option_value),
            )
            .where(func.lower(Product.slug) == slug.lower(), Product.deleted_at.is_(None))
        )
        if active_only:
            stmt = stmt.join(Category, Product.category_id == Category.id).where(
                Product.is_active.is_(True),
                Category.deleted_at.is_(None),
                Category.is_active.is_(True),
            )
        return db.scalar(stmt)

    def slug_exists(
        self,
        db: Session,
        *,
        slug: str,
        exclude_product_id: int | None = None,
    ) -> bool:
        stmt = select(Product.id).where(
            func.lower(Product.slug) == slug.lower(),
            Product.deleted_at.is_(None),
        )
        if exclude_product_id is not None:
            stmt = stmt.where(Product.id != exclude_product_id)
        return db.scalar(stmt) is not None

    def get_category_by_id(self, db: Session, *, category_id: int) -> Category | None:
        stmt = select(Category).where(Category.id == category_id, Category.deleted_at.is_(None))
        return db.scalar(stmt)

    def get_brand_by_id(self, db: Session, *, brand_id: int) -> Brand | None:
        stmt = select(Brand).where(Brand.id == brand_id, Brand.deleted_at.is_(None))
        return db.scalar(stmt)

    def list_products(
        self,
        db: Session,
        *,
        filters: PublicProductListQuery | AdminProductListQuery,
        active_only: bool,
    ) -> tuple[list[Product], int]:
        stmt = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.brand),
                selectinload(Product.images),
                selectinload(Product.specifications),
            )
            .where(Product.deleted_at.is_(None))
        )
        count_stmt = select(func.count(Product.id)).where(Product.deleted_at.is_(None))

        if active_only:
            stmt = stmt.join(Category, Product.category_id == Category.id).where(
                Product.is_active.is_(True),
                Category.deleted_at.is_(None),
                Category.is_active.is_(True),
            )
            count_stmt = count_stmt.join(Category, Product.category_id == Category.id).where(
                Product.is_active.is_(True),
                Category.deleted_at.is_(None),
                Category.is_active.is_(True),
            )

        if filters.search:
            search_value = f"%{filters.search}%"
            stmt = stmt.where(Product.name.ilike(search_value))
            count_stmt = count_stmt.where(Product.name.ilike(search_value))

        if filters.category_id is not None:
            stmt = stmt.where(Product.category_id == filters.category_id)
            count_stmt = count_stmt.where(Product.category_id == filters.category_id)

        if filters.brand_id is not None:
            stmt = stmt.where(Product.brand_id == filters.brand_id)
            count_stmt = count_stmt.where(Product.brand_id == filters.brand_id)

        if filters.featured is not None:
            stmt = stmt.where(Product.is_featured.is_(filters.featured))
            count_stmt = count_stmt.where(Product.is_featured.is_(filters.featured))

        admin_is_active = getattr(filters, "is_active", None)
        if admin_is_active is not None and not active_only:
            stmt = stmt.where(Product.is_active.is_(admin_is_active))
            count_stmt = count_stmt.where(Product.is_active.is_(admin_is_active))

        stmt = stmt.order_by(*self._build_order_by(sort=filters.sort))
        stmt = stmt.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)

        total = int(db.scalar(count_stmt) or 0)
        items = list(db.scalars(stmt).all())
        return items, total

    def update_product(
        self,
        db: Session,
        *,
        product: Product,
        update_data: dict[str, object],
    ) -> Product:
        for field_name, value in update_data.items():
            setattr(product, field_name, value)

        db.add(product)
        db.flush()
        return product

    def replace_product_images(
        self,
        db: Session,
        *,
        product: Product,
        images_data: list[dict[str, object]],
    ) -> list[ProductImage]:
        product.images.clear()
        db.flush()

        new_images = [ProductImage(product_id=product.id, **image_data) for image_data in images_data]
        product.images.extend(new_images)
        db.add(product)
        db.flush()
        return new_images

    def replace_product_specifications(
        self,
        db: Session,
        *,
        product: Product,
        specifications_data: list[dict[str, object]],
    ) -> list[ProductSpecification]:
        product.specifications.clear()
        db.flush()

        new_specifications = [
            ProductSpecification(product_id=product.id, **specification_data)
            for specification_data in specifications_data
        ]
        product.specifications.extend(new_specifications)
        db.add(product)
        db.flush()
        return new_specifications

    def soft_delete_product(self, db: Session, *, product: Product) -> Product:
        product.deleted_at = datetime.now(UTC)
        db.add(product)
        db.flush()
        return product

    def _build_order_by(self, *, sort: ProductSortOption):
        if sort == ProductSortOption.NEWEST:
            return (Product.created_at.desc(), Product.id.desc())
        if sort == ProductSortOption.PRICE_ASC:
            return (Product.base_price.asc(), Product.id.desc())
        if sort == ProductSortOption.PRICE_DESC:
            return (Product.base_price.desc(), Product.id.desc())
        return (Product.sort_order.asc(), Product.created_at.desc(), Product.id.desc())
