from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_brands,
    admin_categories,
    admin_products,
    admin_variants,
    auth,
    brands,
    cart,
    categories,
    health,
    products,
    sample,
    users,
)

api_router = APIRouter()
api_router.include_router(admin_brands.router)
api_router.include_router(admin_categories.router)
api_router.include_router(admin_products.router)
api_router.include_router(admin_variants.router)
api_router.include_router(auth.router)
api_router.include_router(brands.router)
api_router.include_router(cart.router)
api_router.include_router(categories.router)
api_router.include_router(health.router)
api_router.include_router(products.router)
api_router.include_router(sample.router)
api_router.include_router(users.router)
