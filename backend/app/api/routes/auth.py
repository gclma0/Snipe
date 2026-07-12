from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import AuthenticatedUser, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
CurrentUser = Depends(get_current_user)


class CurrentUserResponse(BaseModel):
    id: str
    email: str | None = None
    role: str | None = None


@router.get("/me", response_model=CurrentUserResponse)
def read_current_user(user: AuthenticatedUser = CurrentUser) -> CurrentUserResponse:
    return CurrentUserResponse(id=user.id, email=user.email, role=user.role)
