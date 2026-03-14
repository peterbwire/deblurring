from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.services.file_manager import get_media_type, get_run_log_path, get_run_output_file
from app.utils.signing import verify_signature


router = APIRouter(tags=["download"])


@router.get("/download/image/{job_id}/{run_id}")
def download_image(job_id: str, run_id: str, expires: int, signature: str) -> FileResponse:
    verify_signature("download_image", job_id, run_id, expires, signature)
    image_path = get_run_output_file(job_id, run_id)
    return FileResponse(
        path=image_path,
        media_type=get_media_type(image_path),
        filename=f"{job_id}-{run_id}-restored{image_path.suffix}",
    )


@router.get("/download/log/{job_id}/{run_id}")
def download_log(job_id: str, run_id: str, expires: int, signature: str) -> FileResponse:
    verify_signature("download_log", job_id, run_id, expires, signature)
    log_path = get_run_log_path(job_id, run_id)
    if not log_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found.")
    return FileResponse(
        path=log_path,
        media_type="application/json",
        filename=f"{job_id}-{run_id}-audit-log.json",
    )
