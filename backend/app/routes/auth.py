from fastapi import APIRouter, Depends, Query

from app.models.schemas import AuthUserResponse, JobHistoryItem, JobHistoryResponse
from app.services.auth_service import AuthenticatedUser, require_authenticated_user
from app.services.database import list_recent_jobs


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=AuthUserResponse)
def get_current_user(user: AuthenticatedUser = Depends(require_authenticated_user)) -> AuthUserResponse:
    return AuthUserResponse(user_id=user.user_id, auth_mode=user.auth_mode)


@router.get("/jobs", response_model=JobHistoryResponse)
def get_recent_jobs(
    limit: int = Query(default=8, ge=1, le=25),
    user: AuthenticatedUser = Depends(require_authenticated_user),
) -> JobHistoryResponse:
    items = [JobHistoryItem(**item) for item in list_recent_jobs(user.user_id, limit=limit)]
    return JobHistoryResponse(items=items)
