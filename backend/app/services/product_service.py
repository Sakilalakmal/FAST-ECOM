from __future__ import annotations

from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_specification import ProductSpecification
from app.repositories.product_repository import ProductRepository
from app.schemas.product import (
    AdminProductListQuery,
    ProductBrandSummary,
    ProductCreateRequest,
    ProductImageCreateRequest,
    ProductImageResponse,
    ProductListItemResponse,
    ProductListResponse,
    ProductResponse,
    ProductSpecificationCreateRequest,
    ProductSpecificationResponse,
    ProductUpdateRequest,
    ProductCategorySummary,
    PublicProductListQuery,
)
from app.services.variant_service import VariantService
from app.utils.slug import SlugError, generate_unique_slug, slugify


class ProductServiceError(Exception):
    pass


class ProductNotFoundError(ProductServiceError):
    pass


class ProductAlreadyExistsError(ProductServiceError):
    pass


class ProductValidationError(ProductServiceError):
    pass


class ProductService:
    def __init__(
        self,
        repository: ProductRepository | None = None,
        variant_service: VariantService | None = None,
    ) -> None:
        self.repository = repository or ProductRepository()
        self.variant_service = variant_service or VariantService()

    def create_product(self, db: Session, *, payload: ProductCreateRequest) -> ProductResponse:
        self._validate_category_and_brand(
            db,
            category_id=payload.category_id,
            brand_id=payload.brand_id,
        )
        self._validate_price_pair(
            base_price=payload.base_price,
            compare_at_price=payload.compare_at_price,
        )
        images_data = self._normalize_image_payloads(payload.images)
        specifications_data = self._normalize_specification_payloads(payload.specifications)

        product_data = payload.model_dump(exclude={"images", "specifications"})
        product_data["slug"] = self._resolve_create_slug(db, payload=payload)
        product_data["currency_code"] = product_data["currency_code"].upper()

        try:
            product = self.repository.create_product(db, product_data=product_data)
            self.repository.replace_product_images(db, product=product, images_data=images_data)
            self.repository.replace_product_specifications(
                db,
                product=product,
                specifications_data=specifications_data,
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ProductServiceError("Unable to create the product.") from exc

        return self.build_product_response(product, public_view=False)

    def list_admin_products(
        self,
        db: Session,
        *,
        filters: AdminProductListQuery,
    ) -> ProductListResponse:
        products, total = self.repository.list_products(
            db,
            filters=filters,
            active_only=False,
        )
        items = [self.build_product_list_item(product, public_view=False) for product in products]
        return ProductListResponse.create(
            items=items,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    def get_admin_product(self, db: Session, *, product_id: int) -> ProductResponse:
        product = self.repository.get_product_by_id(db, product_id=product_id, active_only=False)
        if product is None:
            raise ProductNotFoundError("Product not found.")
        return self.build_product_response(product, public_view=False)

    def update_product(
        self,
        db: Session,
        *,
        product_id: int,
        payload: ProductUpdateRequest,
    ) -> ProductResponse:
        if not payload.model_fields_set:
            raise ProductValidationError("At least one product field must be provided.")

        product = self.repository.get_product_by_id(db, product_id=product_id, active_only=False)
        if product is None:
            raise ProductNotFoundError("Product not found.")

        update_data = payload.model_dump(exclude_unset=True, exclude={"images", "specifications"})
        self._validate_non_nullable_update_fields(update_data)

        category_id = update_data.get("category_id", product.category_id)
        brand_id = update_data["brand_id"] if "brand_id" in update_data else product.brand_id
        self._validate_category_and_brand(
            db,
            category_id=category_id,
            brand_id=brand_id,
        )

        base_price = update_data.get("base_price", product.base_price)
        compare_at_price = (
            update_data["compare_at_price"]
            if "compare_at_price" in update_data
            else product.compare_at_price
        )
        self._validate_price_pair(
            base_price=base_price,
            compare_at_price=compare_at_price,
        )

        if "name" in update_data:
            update_data["name"] = str(update_data["name"]).strip()

        if "currency_code" in update_data and update_data["currency_code"] is not None:
            update_data["currency_code"] = str(update_data["currency_code"]).upper()

        if "slug" in update_data:
            explicit_slug = update_data["slug"]
            try:
                normalized_slug = slugify(str(explicit_slug))
            except SlugError as exc:
                raise ProductValidationError(str(exc)) from exc
            if self.repository.slug_exists(
                db,
                slug=normalized_slug,
                exclude_product_id=product.id,
            ):
                raise ProductAlreadyExistsError("A product with this slug already exists.")
            update_data["slug"] = normalized_slug

        images_data = None
        if payload.images is not None:
            images_data = self._normalize_image_payloads(payload.images)

        specifications_data = None
        if payload.specifications is not None:
            specifications_data = self._normalize_specification_payloads(payload.specifications)

        try:
            if update_data:
                self.repository.update_product(db, product=product, update_data=update_data)
            if images_data is not None:
                self.repository.replace_product_images(db, product=product, images_data=images_data)
            if specifications_data is not None:
                self.repository.replace_product_specifications(
                    db,
                    product=product,
                    specifications_data=specifications_data,
                )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ProductServiceError("Unable to update the product.") from exc

        return self.build_product_response(product, public_view=False)

    def delete_product(self, db: Session, *, product_id: int) -> None:
        product = self.repository.get_product_by_id(db, product_id=product_id, active_only=False)
        if product is None:
            raise ProductNotFoundError("Product not found.")

        try:
            self.repository.soft_delete_product(db, product=product)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ProductServiceError("Unable to delete the product.") from exc

    def list_public_products(
        self,
        db: Session,
        *,
        filters: PublicProductListQuery,
    ) -> ProductListResponse:
        products, total = self.repository.list_products(
            db,
            filters=filters,
            active_only=True,
        )
        items = [self.build_product_list_item(product, public_view=True) for product in products]
        return ProductListResponse.create(
            items=items,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    def get_public_product(self, db: Session, *, slug: str) -> ProductResponse:
        product = self.repository.get_product_by_slug(db, slug=slug, active_only=True)
        if product is None:
            raise ProductNotFoundError("Product not found.")
        return self.build_product_response(product, public_view=True)

    def build_product_list_item(
        self,
        product: Product,
        *,
        public_view: bool,
    ) -> ProductListItemResponse:
        primary_image = self._select_primary_image(product.images)
        return ProductListItemResponse(
            id=product.id,
            name=product.name,
            slug=product.slug,
            short_description=product.short_description,
            base_price=product.base_price,
            compare_at_price=product.compare_at_price,
            currency_code=product.currency_code,
            is_active=product.is_active,
            is_featured=product.is_featured,
            sort_order=product.sort_order,
            category=self._build_category_summary(product),
            brand=self._build_brand_summary(product, public_view=public_view),
            primary_image=(
                ProductImageResponse.model_validate(primary_image) if primary_image is not None else None
            ),
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    def build_product_response(
        self,
        product: Product,
        *,
        public_view: bool,
    ) -> ProductResponse:
        return ProductResponse(
            id=product.id,
            name=product.name,
            slug=product.slug,
            short_description=product.short_description,
            description=product.description,
            category=self._build_category_summary(product),
            brand=self._build_brand_summary(product, public_view=public_view),
            base_price=product.base_price,
            compare_at_price=product.compare_at_price,
            currency_code=product.currency_code,
            sku=product.sku,
            is_active=product.is_active,
            is_featured=product.is_featured,
            sort_order=product.sort_order,
            images=[ProductImageResponse.model_validate(image) for image in product.images],
            specifications=[
                ProductSpecificationResponse.model_validate(specification)
                for specification in product.specifications
            ],
            variants=self.variant_service.build_public_variant_summaries(
                product,
                public_view=public_view,
            ),
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    def _build_category_summary(self, product: Product) -> ProductCategorySummary:
        return ProductCategorySummary.model_validate(product.category)

    def _build_brand_summary(
        self,
        product: Product,
        *,
        public_view: bool,
    ) -> ProductBrandSummary | None:
        if product.brand is None:
            return None
        if public_view and (product.brand.deleted_at is not None or not product.brand.is_active):
            return None
        return ProductBrandSummary.model_validate(product.brand)

    def _resolve_create_slug(self, db: Session, *, payload: ProductCreateRequest) -> str:
        if payload.slug is not None:
            try:
                normalized_slug = slugify(payload.slug)
            except SlugError as exc:
                raise ProductValidationError(str(exc)) from exc
            if self.repository.slug_exists(db, slug=normalized_slug):
                raise ProductAlreadyExistsError("A product with this slug already exists.")
            return normalized_slug

        try:
            return generate_unique_slug(
                source_value=payload.name,
                slug_value=None,
                exists=lambda slug: self.repository.slug_exists(db, slug=slug),
            )
        except SlugError as exc:
            raise ProductValidationError(str(exc)) from exc

    def _validate_category_and_brand(
        self,
        db: Session,
        *,
        category_id: int | None,
        brand_id: int | None,
    ) -> None:
        if category_id is None:
            raise ProductValidationError("category_id cannot be null.")
        category = self.repository.get_category_by_id(db, category_id=category_id)
        if category is None:
            raise ProductValidationError("Category not found.")

        if brand_id is not None:
            brand = self.repository.get_brand_by_id(db, brand_id=brand_id)
            if brand is None:
                raise ProductValidationError("Brand not found.")

    def _validate_price_pair(
        self,
        *,
        base_price: Decimal | None,
        compare_at_price: Decimal | None,
    ) -> None:
        if base_price is None:
            raise ProductValidationError("base_price cannot be null.")
        if compare_at_price is not None and compare_at_price < base_price:
            raise ProductValidationError(
                "compare_at_price must be greater than or equal to base_price."
            )

    def _validate_non_nullable_update_fields(self, update_data: dict[str, object]) -> None:
        required_fields = {
            "name",
            "category_id",
            "base_price",
            "currency_code",
            "is_active",
            "is_featured",
            "sort_order",
        }
        for required_field in required_fields:
            if required_field in update_data and update_data[required_field] is None:
                raise ProductValidationError(f"{required_field} cannot be null.")

        if "slug" in update_data and update_data["slug"] is None:
            raise ProductValidationError("slug cannot be null.")

    def _normalize_image_payloads(
        self,
        images: list[ProductImageCreateRequest],
    ) -> list[dict[str, object]]:
        normalized_images = [image.model_dump() for image in images]
        if not normalized_images:
            return normalized_images

        primary_count = sum(1 for image in normalized_images if image["is_primary"])
        if primary_count > 1:
            raise ProductValidationError("Only one product image can be marked as primary.")
        if primary_count == 0:
            normalized_images[0]["is_primary"] = True

        return normalized_images

    def _normalize_specification_payloads(
        self,
        specifications: list[ProductSpecificationCreateRequest],
    ) -> list[dict[str, object]]:
        normalized_specifications = [specification.model_dump() for specification in specifications]
        seen_keys: set[str] = set()
        for specification in normalized_specifications:
            normalized_key = str(specification["spec_key"]).strip().lower()
            if normalized_key in seen_keys:
                raise ProductValidationError("Specification keys must be unique per product.")
            seen_keys.add(normalized_key)
        return normalized_specifications

    def _select_primary_image(
        self,
        images: list[ProductImage],
    ) -> ProductImage | None:
        if not images:
            return None
        primary_image = next((image for image in images if image.is_primary), None)
        if primary_image is not None:
            return primary_image
        return images[0]
