from fastapi import APIRouter

router = APIRouter(prefix="/sample", tags=["sample"])


@router.get("/ping", summary="Sample modular endpoint")
def ping() -> dict[str, str]:
    return {"message": "pong"}
