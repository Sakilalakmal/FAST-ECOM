from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_brands,
    admin_categories,
    auth,
    brands,
    categories,
    health,
    sample,
    users,
)

api_router = APIRouter()
api_router.include_router(admin_brands.router)
api_router.include_router(admin_categories.router)
api_router.include_router(auth.router)
api_router.include_router(brands.router)
api_router.include_router(categories.router)
api_router.include_router(health.router)
api_router.include_router(sample.router)
api_router.include_router(users.router)
