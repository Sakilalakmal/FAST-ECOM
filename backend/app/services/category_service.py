from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreateRequest, CategoryResponse, CategoryUpdateRequest
from app.utils.slug import SlugError, generate_unique_slug, slugify


class CategoryServiceError(Exception):
    pass


class CategoryNotFoundError(CategoryServiceError):
    pass


class CategoryAlreadyExistsError(CategoryServiceError):
    pass


class CategoryValidationError(CategoryServiceError):
    pass


class CategoryService:
    def __init__(self, repository: CategoryRepository | None = None) -> None:
        self.repository = repository or CategoryRepository()

    def create_category(self, db: Session, *, payload: CategoryCreateRequest) -> CategoryResponse:
        normalized_name = payload.name.strip()
        if self.repository.get_category_by_name(db, name=normalized_name) is not None:
            raise CategoryAlreadyExistsError("A category with this name already exists.")

        if payload.parent_id is not None:
            parent = self.repository.get_category_by_id(db, category_id=payload.parent_id)
            if parent is None:
                raise CategoryValidationError("Parent category not found.")

        category_data = payload.model_dump()
        category_data["name"] = normalized_name
        category_data["slug"] = self._resolve_create_slug(db, payload=payload)

        try:
            category = self.repository.create_category(db, category_data=category_data)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise CategoryServiceError("Unable to create the category.") from exc

        return self.build_category_response(category)

    def list_admin_categories(self, db: Session) -> list[CategoryResponse]:
        categories = self.repository.list_categories(db, active_only=False)
        return [self.build_category_response(category) for category in categories]

    def get_admin_category(self, db: Session, *, category_id: int) -> CategoryResponse:
        category = self.repository.get_category_by_id(db, category_id=category_id)
        if category is None:
            raise CategoryNotFoundError("Category not found.")
        return self.build_category_response(category)

    def update_category(
        self,
        db: Session,
        *,
        category_id: int,
        payload: CategoryUpdateRequest,
    ) -> CategoryResponse:
        if not payload.model_fields_set:
            raise CategoryValidationError("At least one category field must be provided.")

        category = self.repository.get_category_by_id(db, category_id=category_id)
        if category is None:
            raise CategoryNotFoundError("Category not found.")

        update_data = payload.model_dump(exclude_unset=True)
        if "name" in update_data:
            normalized_name = str(update_data["name"]).strip()
            existing_category = self.repository.get_category_by_name(db, name=normalized_name)
            if existing_category is not None and existing_category.id != category.id:
                raise CategoryAlreadyExistsError("A category with this name already exists.")
            update_data["name"] = normalized_name

        if "parent_id" in update_data:
            parent_id = update_data["parent_id"]
            if parent_id == category.id:
                raise CategoryValidationError("A category cannot be its own parent.")
            if parent_id is not None:
                parent = self.repository.get_category_by_id(db, category_id=parent_id)
                if parent is None:
                    raise CategoryValidationError("Parent category not found.")

        if "slug" in update_data:
            explicit_slug = update_data["slug"]
            if explicit_slug is None:
                raise CategoryValidationError("slug cannot be null.")
            try:
                normalized_slug = slugify(explicit_slug)
            except SlugError as exc:
                raise CategoryValidationError(str(exc)) from exc
            if self.repository.slug_exists(
                db,
                slug=normalized_slug,
                exclude_category_id=category.id,
            ):
                raise CategoryAlreadyExistsError("A category with this slug already exists.")
            update_data["slug"] = normalized_slug

        try:
            self.repository.update_category(db, category=category, update_data=update_data)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise CategoryServiceError("Unable to update the category.") from exc

        return self.build_category_response(category)

    def delete_category(self, db: Session, *, category_id: int) -> None:
        category = self.repository.get_category_by_id(db, category_id=category_id)
        if category is None:
            raise CategoryNotFoundError("Category not found.")

        try:
            self.repository.detach_children(db, parent_id=category.id)
            self.repository.soft_delete_category(db, category=category)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise CategoryServiceError("Unable to delete the category.") from exc

    def list_public_categories(self, db: Session) -> list[CategoryResponse]:
        categories = self.repository.list_categories(db, active_only=True)
        return [self.build_category_response(category) for category in categories]

    def get_public_category(self, db: Session, *, slug: str) -> CategoryResponse:
        category = self.repository.get_category_by_slug(db, slug=slug, active_only=True)
        if category is None:
            raise CategoryNotFoundError("Category not found.")
        return self.build_category_response(category)

    def build_category_response(self, category: Category) -> CategoryResponse:
        return CategoryResponse.model_validate(category)

    def _resolve_create_slug(self, db: Session, *, payload: CategoryCreateRequest) -> str:
        if payload.slug is not None:
            try:
                normalized_slug = slugify(payload.slug)
            except SlugError as exc:
                raise CategoryValidationError(str(exc)) from exc
            if self.repository.slug_exists(db, slug=normalized_slug):
                raise CategoryAlreadyExistsError("A category with this slug already exists.")
            return normalized_slug

        try:
            return generate_unique_slug(
                source_value=payload.name,
                slug_value=None,
                exists=lambda slug: self.repository.slug_exists(db, slug=slug),
            )
        except SlugError as exc:
            raise CategoryValidationError(str(exc)) from exc
