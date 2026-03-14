from fastapi import APIRouter, Depends

from app.models.schemas import OpsMetricsResponse
from app.services.auth_service import AuthenticatedUser, require_authenticated_user
from app.services.run_manager import get_queue_metrics


router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/metrics", response_model=OpsMetricsResponse)
def get_ops_metrics(
    _: AuthenticatedUser = Depends(require_authenticated_user),
) -> OpsMetricsResponse:
    return OpsMetricsResponse(**get_queue_metrics())
