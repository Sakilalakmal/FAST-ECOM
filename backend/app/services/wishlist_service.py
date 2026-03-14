from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.user import User
from app.models.wishlist import Wishlist
from app.models.wishlist_item import WishlistItem
from app.repositories.wishlist_repository import WishlistRepository
from app.schemas.product import ProductBrandSummary, ProductCategorySummary
from app.schemas.wishlist import (
    AddWishlistItemRequest,
    WishlistItemResponse,
    WishlistProductImageSummary,
    WishlistProductSummary,
    WishlistResponse,
)


class WishlistServiceError(Exception):
    pass


class WishlistItemNotFoundError(WishlistServiceError):
    pass


class WishlistProductNotFoundError(WishlistServiceError):
    pass


class WishlistService:
    def __init__(self, repository: WishlistRepository | None = None) -> None:
        self.repository = repository or WishlistRepository()

    def get_current_wishlist(
        self,
        db: Session,
        *,
        current_user: User,
    ) -> WishlistResponse:
        try:
            wishlist = self.repository.get_or_create_active_wishlist(db, user_id=current_user.id)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise WishlistServiceError("Unable to load the wishlist.") from exc

        return self.build_wishlist_response(wishlist)

    def add_item(
        self,
        db: Session,
        *,
        current_user: User,
        payload: AddWishlistItemRequest,
    ) -> WishlistResponse:
        product = self.repository.get_public_product_by_id(db, product_id=payload.product_id)
        if product is None:
            raise WishlistProductNotFoundError("Product not found or not available for wishlist.")

        try:
            wishlist = self.repository.get_or_create_active_wishlist(db, user_id=current_user.id)
            existing_item = self.repository.get_wishlist_item_by_product_id(
                db,
                wishlist_id=wishlist.id,
                product_id=payload.product_id,
            )
            if existing_item is None:
                self.repository.create_wishlist_item(
                    db,
                    wishlist_id=wishlist.id,
                    product_id=payload.product_id,
                )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise WishlistServiceError("Unable to add the product to the wishlist.") from exc

        refreshed_wishlist = self.repository.get_active_wishlist_by_user_id(
            db,
            user_id=current_user.id,
        )
        if refreshed_wishlist is None:
            raise WishlistServiceError("Unable to load the wishlist.")
        return self.build_wishlist_response(refreshed_wishlist)

    def remove_item(
        self,
        db: Session,
        *,
        current_user: User,
        product_id: int,
    ) -> WishlistResponse:
        wishlist = self.repository.get_active_wishlist_by_user_id(db, user_id=current_user.id)
        if wishlist is None:
            raise WishlistItemNotFoundError("Product is not in the wishlist.")

        wishlist_item = self.repository.get_wishlist_item_by_product_id(
            db,
            wishlist_id=wishlist.id,
            product_id=product_id,
        )
        if wishlist_item is None:
            raise WishlistItemNotFoundError("Product is not in the wishlist.")

        try:
            self.repository.delete_wishlist_item(db, wishlist_item=wishlist_item)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise WishlistServiceError("Unable to remove the product from the wishlist.") from exc

        refreshed_wishlist = self.repository.get_active_wishlist_by_user_id(
            db,
            user_id=current_user.id,
        )
        if refreshed_wishlist is None:
            wishlist = self.repository.get_or_create_active_wishlist(db, user_id=current_user.id)
            db.commit()
            return self.build_wishlist_response(wishlist)
        return self.build_wishlist_response(refreshed_wishlist)

    def clear_wishlist(
        self,
        db: Session,
        *,
        current_user: User,
    ) -> WishlistResponse:
        wishlist = self.repository.get_or_create_active_wishlist(db, user_id=current_user.id)

        try:
            self.repository.clear_wishlist_items(db, wishlist=wishlist)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise WishlistServiceError("Unable to clear the wishlist.") from exc

        refreshed_wishlist = self.repository.get_active_wishlist_by_user_id(
            db,
            user_id=current_user.id,
        )
        if refreshed_wishlist is None:
            raise WishlistServiceError("Unable to load the wishlist.")
        return self.build_wishlist_response(refreshed_wishlist)

    def build_wishlist_response(self, wishlist: Wishlist) -> WishlistResponse:
        visible_items = [
            item
            for item in wishlist.items
            if item.product is not None and self._is_visible_product(item.product)
        ]
        return WishlistResponse(
            id=wishlist.id,
            user_id=wishlist.user_id,
            item_count=len(visible_items),
            items=[self._build_wishlist_item_response(item) for item in visible_items],
            created_at=wishlist.created_at,
            updated_at=wishlist.updated_at,
        )

    def _build_wishlist_item_response(self, item: WishlistItem) -> WishlistItemResponse:
        product = item.product
        if product is None:
            raise WishlistServiceError("Wishlist item product relationship is not available.")

        return WishlistItemResponse(
            id=item.id,
            product=self._build_product_summary(product),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _build_product_summary(self, product: Product) -> WishlistProductSummary:
        return WishlistProductSummary(
            id=product.id,
            name=product.name,
            slug=product.slug,
            short_description=product.short_description,
            base_price=product.base_price,
            compare_at_price=product.compare_at_price,
            currency_code=product.currency_code,
            is_active=product.is_active,
            category=ProductCategorySummary.model_validate(product.category),
            brand=(
                ProductBrandSummary.model_validate(product.brand)
                if product.brand is not None and product.brand.deleted_at is None and product.brand.is_active
                else None
            ),
            primary_image=self._build_primary_image_summary(product.images),
        )

    def _is_visible_product(self, product: Product) -> bool:
        return bool(
            product.deleted_at is None
            and product.is_active
            and product.category is not None
            and product.category.deleted_at is None
            and product.category.is_active
        )

    def _build_primary_image_summary(
        self,
        images: list[ProductImage],
    ) -> WishlistProductImageSummary | None:
        if not images:
            return None

        primary_image = next((image for image in images if image.is_primary), None) or images[0]
        return WishlistProductImageSummary(
            id=primary_image.id,
            image_url=primary_image.image_url,
            alt_text=primary_image.alt_text,
        )
