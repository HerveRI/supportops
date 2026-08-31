from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import require_admin
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get("/me", response_model=UserResponse)
def get_current_admin(current_user: Annotated[User, Depends(require_admin)]) -> User:
    return current_user
