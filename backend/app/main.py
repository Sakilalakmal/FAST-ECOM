from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings


def create_application() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
        version="0.1.0",
    )
    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app


app = create_application()
