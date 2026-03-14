from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.services.file_manager import get_media_type, get_original_file, get_run_output_file
from app.utils.signing import verify_signature


router = APIRouter(tags=["preview"])


@router.get("/preview/original/{job_id}")
def preview_original(job_id: str, expires: int, signature: str) -> FileResponse:
    verify_signature("preview_original", job_id, None, expires, signature)
    original_path = get_original_file(job_id)
    return FileResponse(
        path=original_path,
        media_type=get_media_type(original_path),
        headers={"Content-Disposition": f'inline; filename="{original_path.name}"'},
    )


@router.get("/preview/restored/{job_id}/{run_id}")
def preview_restored(job_id: str, run_id: str, expires: int, signature: str) -> FileResponse:
    verify_signature("preview_restored", job_id, run_id, expires, signature)
    restored_path = get_run_output_file(job_id, run_id)
    return FileResponse(
        path=restored_path,
        media_type=get_media_type(restored_path),
        headers={"Content-Disposition": f'inline; filename="{restored_path.name}"'},
    )
