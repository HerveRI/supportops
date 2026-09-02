from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class Healthresponse(BaseModel):
    """Response returned by the application health check."""

    status: str


@router.get("/health", response_model=Healthresponse)
def health_check() -> Healthresponse:
    """Return the current health status of the API."""

    return Healthresponse(status="ok")
