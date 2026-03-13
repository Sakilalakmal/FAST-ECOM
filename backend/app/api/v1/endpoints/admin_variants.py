from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin_user
from app.dependencies.db import get_db_session
from app.models.user import User
from app.schemas.inventory import InventoryResponse, InventoryUpdateRequest
from app.schemas.variant import (
    ProductVariantCreateRequest,
    ProductVariantResponse,
    ProductVariantUpdateRequest,
    VariantOptionCreateRequest,
    VariantOptionResponse,
    VariantOptionUpdateRequest,
    VariantOptionValueCreateRequest,
    VariantOptionValueResponse,
    VariantOptionValueUpdateRequest,
)
from app.services.inventory_service import (
    InventoryService,
    InventoryServiceError,
    InventoryValidationError,
    InventoryVariantNotFoundError,
)
from app.services.variant_service import (
    ProductVariantNotFoundError,
    VariantConflictError,
    VariantOptionNotFoundError,
    VariantOptionValueNotFoundError,
    VariantProductNotFoundError,
    VariantService,
    VariantServiceError,
    VariantValidationError,
)

router = APIRouter(prefix="/admin", tags=["admin-variants"])


def get_variant_service() -> VariantService:
    return VariantService()


def get_inventory_service() -> InventoryService:
    return InventoryService()


@router.post(
    "/products/{product_id}/variant-options",
    response_model=VariantOptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a variant option for a product",
)
def create_variant_option(
    product_id: int,
    payload: VariantOptionCreateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    variant_service: Annotated[VariantService, Depends(get_variant_service)],
) -> VariantOptionResponse:
    try:
        return variant_service.create_variant_option(db, product_id=product_id, payload=payload)
    except VariantValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except VariantProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VariantConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except VariantServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the variant option.",
        ) from exc


@router.get(
    "/products/{product_id}/variant-options",
    response_model=list[VariantOptionResponse],
    summary="List variant options for a product",
)
def list_variant_options(
    product_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    variant_service: Annotated[VariantService, Depends(get_variant_service)],
) -> list[VariantOptionResponse]:
    try:
        return variant_service.list_variant_options(db, product_id=product_id)
    except VariantProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/variant-options/{option_id}",
    response_model=VariantOptionResponse,
    summary="Update a variant option",
)
def update_variant_option(
    option_id: int,
    payload: VariantOptionUpdateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    variant_service: Annotated[VariantService, Depends(get_variant_service)],
) -> VariantOptionResponse:
    try:
        return variant_service.update_variant_option(db, option_id=option_id, payload=payload)
    except VariantValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except VariantOptionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VariantConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except VariantServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the variant option.",
        ) from exc


@router.delete(
    "/variant-options/{option_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a variant option",
)
def delete_variant_option(
    option_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    variant_service: Annotated[VariantService, Depends(get_variant_service)],
) -> Response:
    try:
        variant_service.delete_variant_option(db, option_id=option_id)
    except VariantOptionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VariantConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except VariantServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the variant option.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/variant-options/{option_id}/values",
    response_model=VariantOptionValueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a variant option value",
)
def create_variant_option_value(
    option_id: int,
    payload: VariantOptionValueCreateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    variant_service: Annotated[VariantService, Depends(get_variant_service)],
) -> VariantOptionValueResponse:
    try:
        return variant_service.create_variant_option_value(db, option_id=option_id, payload=payload)
    except VariantOptionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VariantConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except VariantServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the variant option value.",
        ) from exc


@router.patch(
    "/variant-option-values/{value_id}",
    response_model=VariantOptionValueResponse,
    summary="Update a variant option value",
)
def update_variant_option_value(
    value_id: int,
    payload: VariantOptionValueUpdateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    variant_service: Annotated[VariantService, Depends(get_variant_service)],
) -> VariantOptionValueResponse:
    try:
        return variant_service.update_variant_option_value(db, value_id=value_id, payload=payload)
    except VariantValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except VariantOptionValueNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VariantConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except VariantServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the variant option value.",
        ) from exc


@router.delete(
    "/variant-option-values/{value_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a variant option value",
)
def delete_variant_option_value(
    value_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    variant_service: Annotated[VariantService, Depends(get_variant_service)],
) -> Response:
    try:
        variant_service.delete_variant_option_value(db, value_id=value_id)
    except VariantOptionValueNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VariantConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except VariantServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the variant option value.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/products/{product_id}/variants",
    response_model=ProductVariantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product variant",
)
def create_variant(
    product_id: int,
    payload: ProductVariantCreateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    variant_service: Annotated[VariantService, Depends(get_variant_service)],
) -> ProductVariantResponse:
    try:
        return variant_service.create_variant(db, product_id=product_id, payload=payload)
    except VariantValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except VariantProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VariantConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except VariantServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the variant.",
        ) from exc


@router.get(
    "/products/{product_id}/variants",
    response_model=list[ProductVariantResponse],
    summary="List variants for a product",
)
def list_variants(
    product_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    variant_service: Annotated[VariantService, Depends(get_variant_service)],
) -> list[ProductVariantResponse]:
    try:
        return variant_service.list_variants_by_product(db, product_id=product_id)
    except VariantProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/variants/{variant_id}",
    response_model=ProductVariantResponse,
    summary="Get a product variant",
)
def get_variant(
    variant_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    variant_service: Annotated[VariantService, Depends(get_variant_service)],
) -> ProductVariantResponse:
    try:
        return variant_service.get_variant(db, variant_id=variant_id)
    except ProductVariantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/variants/{variant_id}",
    response_model=ProductVariantResponse,
    summary="Update a product variant",
)
def update_variant(
    variant_id: int,
    payload: ProductVariantUpdateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    variant_service: Annotated[VariantService, Depends(get_variant_service)],
) -> ProductVariantResponse:
    try:
        return variant_service.update_variant(db, variant_id=variant_id, payload=payload)
    except VariantValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProductVariantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VariantConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except VariantServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the variant.",
        ) from exc


@router.delete(
    "/variants/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product variant",
)
def delete_variant(
    variant_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    variant_service: Annotated[VariantService, Depends(get_variant_service)],
) -> Response:
    try:
        variant_service.delete_variant(db, variant_id=variant_id)
    except ProductVariantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VariantServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the variant.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/variants/{variant_id}/inventory",
    response_model=InventoryResponse,
    summary="Get inventory for a product variant",
)
def get_variant_inventory(
    variant_id: int,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> InventoryResponse:
    try:
        return inventory_service.get_variant_inventory(db, variant_id=variant_id)
    except InventoryVariantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InventoryServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load variant inventory.",
        ) from exc


@router.patch(
    "/variants/{variant_id}/inventory",
    response_model=InventoryResponse,
    summary="Update inventory for a product variant",
)
def update_variant_inventory(
    variant_id: int,
    payload: InventoryUpdateRequest,
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    inventory_service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> InventoryResponse:
    try:
        return inventory_service.update_variant_inventory(db, variant_id=variant_id, payload=payload)
    except InventoryValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except InventoryVariantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InventoryServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update variant inventory.",
        ) from exc
