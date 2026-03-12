from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.repositories.brand_repository import BrandRepository
from app.schemas.brand import BrandCreateRequest, BrandResponse, BrandUpdateRequest
from app.utils.slug import SlugError, generate_unique_slug, slugify


class BrandServiceError(Exception):
    pass


class BrandNotFoundError(BrandServiceError):
    pass


class BrandAlreadyExistsError(BrandServiceError):
    pass


class BrandValidationError(BrandServiceError):
    pass


class BrandService:
    def __init__(self, repository: BrandRepository | None = None) -> None:
        self.repository = repository or BrandRepository()

    def create_brand(self, db: Session, *, payload: BrandCreateRequest) -> BrandResponse:
        normalized_name = payload.name.strip()
        if self.repository.get_brand_by_name(db, name=normalized_name) is not None:
            raise BrandAlreadyExistsError("A brand with this name already exists.")

        brand_data = payload.model_dump()
        brand_data["name"] = normalized_name
        brand_data["slug"] = self._resolve_create_slug(db, payload=payload)

        try:
            brand = self.repository.create_brand(db, brand_data=brand_data)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise BrandServiceError("Unable to create the brand.") from exc

        return self.build_brand_response(brand)

    def list_admin_brands(self, db: Session) -> list[BrandResponse]:
        brands = self.repository.list_brands(db, active_only=False)
        return [self.build_brand_response(brand) for brand in brands]

    def get_admin_brand(self, db: Session, *, brand_id: int) -> BrandResponse:
        brand = self.repository.get_brand_by_id(db, brand_id=brand_id)
        if brand is None:
            raise BrandNotFoundError("Brand not found.")
        return self.build_brand_response(brand)

    def update_brand(
        self,
        db: Session,
        *,
        brand_id: int,
        payload: BrandUpdateRequest,
    ) -> BrandResponse:
        if not payload.model_fields_set:
            raise BrandValidationError("At least one brand field must be provided.")

        brand = self.repository.get_brand_by_id(db, brand_id=brand_id)
        if brand is None:
            raise BrandNotFoundError("Brand not found.")

        update_data = payload.model_dump(exclude_unset=True)
        if "name" in update_data:
            normalized_name = str(update_data["name"]).strip()
            existing_brand = self.repository.get_brand_by_name(db, name=normalized_name)
            if existing_brand is not None and existing_brand.id != brand.id:
                raise BrandAlreadyExistsError("A brand with this name already exists.")
            update_data["name"] = normalized_name

        if "slug" in update_data:
            explicit_slug = update_data["slug"]
            if explicit_slug is None:
                raise BrandValidationError("slug cannot be null.")
            try:
                normalized_slug = slugify(explicit_slug)
            except SlugError as exc:
                raise BrandValidationError(str(exc)) from exc
            if self.repository.slug_exists(
                db,
                slug=normalized_slug,
                exclude_brand_id=brand.id,
            ):
                raise BrandAlreadyExistsError("A brand with this slug already exists.")
            update_data["slug"] = normalized_slug

        try:
            self.repository.update_brand(db, brand=brand, update_data=update_data)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise BrandServiceError("Unable to update the brand.") from exc

        return self.build_brand_response(brand)

    def delete_brand(self, db: Session, *, brand_id: int) -> None:
        brand = self.repository.get_brand_by_id(db, brand_id=brand_id)
        if brand is None:
            raise BrandNotFoundError("Brand not found.")

        try:
            self.repository.soft_delete_brand(db, brand=brand)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise BrandServiceError("Unable to delete the brand.") from exc

    def list_public_brands(self, db: Session) -> list[BrandResponse]:
        brands = self.repository.list_brands(db, active_only=True)
        return [self.build_brand_response(brand) for brand in brands]

    def get_public_brand(self, db: Session, *, slug: str) -> BrandResponse:
        brand = self.repository.get_brand_by_slug(db, slug=slug, active_only=True)
        if brand is None:
            raise BrandNotFoundError("Brand not found.")
        return self.build_brand_response(brand)

    def build_brand_response(self, brand: Brand) -> BrandResponse:
        return BrandResponse.model_validate(brand)

    def _resolve_create_slug(self, db: Session, *, payload: BrandCreateRequest) -> str:
        if payload.slug is not None:
            try:
                normalized_slug = slugify(payload.slug)
            except SlugError as exc:
                raise BrandValidationError(str(exc)) from exc
            if self.repository.slug_exists(db, slug=normalized_slug):
                raise BrandAlreadyExistsError("A brand with this slug already exists.")
            return normalized_slug

        try:
            return generate_unique_slug(
                source_value=payload.name,
                slug_value=None,
                exists=lambda slug: self.repository.slug_exists(db, slug=slug),
            )
        except SlugError as exc:
            raise BrandValidationError(str(exc)) from exc
