from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.models.schemas import UploadResponse
from app.services.auth_service import AuthenticatedUser, require_authenticated_user
from app.services.file_manager import save_upload
from app.services.rate_limiter import enforce_rate_limit
from app.utils.signing import build_signed_url


router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(require_authenticated_user),
) -> UploadResponse:
    enforce_rate_limit("upload", user.user_id)
    upload_result = await save_upload(file, owner_id=user.user_id)
    original_url = build_signed_url(
        request,
        f"/preview/original/{upload_result['job_id']}",
        "preview_original",
        upload_result["job_id"],
    )
    return UploadResponse(
        job_id=upload_result["job_id"],
        original_filename=upload_result["original_filename"],
        original_url=original_url,
        file_size=upload_result["file_size"],
        sha256=upload_result["sha256"],
        width=upload_result["width"],
        height=upload_result["height"],
    )
