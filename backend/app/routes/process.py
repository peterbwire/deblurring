from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models.schemas import ProcessRequest, ProcessStartResponse, RunStatusResponse
from app.services.auth_service import AuthenticatedUser, require_authenticated_user
from app.services.database import get_run_record
from app.services.file_manager import get_original_file, read_job_manifest
from app.services.logger_service import read_audit_log
from app.services.run_manager import create_run, submit_run
from app.services.rate_limiter import enforce_rate_limit
from app.utils.signing import build_signed_url


router = APIRouter(tags=["process"])


@router.post("/process/{job_id}", response_model=ProcessStartResponse)
def start_process(
    job_id: str,
    payload: ProcessRequest,
    request: Request,
    user: AuthenticatedUser = Depends(require_authenticated_user),
) -> ProcessStartResponse:
    enforce_rate_limit("process", user.user_id)
    get_original_file(job_id, owner_id=user.user_id)
    run_record = create_run(job_id, user.user_id, payload)
    submit_run(job_id, run_record["run_id"], user.user_id, run_record["settings_json"])

    return ProcessStartResponse(
        job_id=job_id,
        run_id=run_record["run_id"],
        status=run_record["status"],
        status_url=f"{str(request.base_url).rstrip('/')}/process/{job_id}/{run_record['run_id']}",
        queued_at=run_record["created_at"],
    )


@router.get("/process/{job_id}/{run_id}", response_model=RunStatusResponse)
def get_process_status(
    job_id: str,
    run_id: str,
    request: Request,
    user: AuthenticatedUser = Depends(require_authenticated_user),
) -> RunStatusResponse:
    read_job_manifest(job_id, owner_id=user.user_id)
    run_record = get_run_record(job_id, run_id, owner_id=user.user_id)
    if not run_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
    original_url = build_signed_url(
        request,
        f"/preview/original/{job_id}",
        "preview_original",
        job_id,
    )

    response = RunStatusResponse(
        job_id=job_id,
        run_id=run_id,
        status=run_record["status"],
        status_url=f"{str(request.base_url).rstrip('/')}/process/{job_id}/{run_id}",
        created_at=run_record["created_at"],
        started_at=run_record.get("started_at"),
        completed_at=run_record.get("completed_at"),
        original_url=original_url,
        warnings=run_record.get("warnings_json", []),
        duration_seconds=run_record.get("duration_seconds"),
        error_message=run_record.get("error_message"),
        progress_phase=run_record.get("progress_phase"),
    )

    if run_record["status"] == "completed":
        audit_log = run_record.get("audit_log_json") or read_audit_log(job_id, run_id)
        response.restored_url = build_signed_url(
            request,
            f"/preview/restored/{job_id}/{run_id}",
            "preview_restored",
            job_id,
            run_id=run_id,
        )
        response.image_download_url = build_signed_url(
            request,
            f"/download/image/{job_id}/{run_id}",
            "download_image",
            job_id,
            run_id=run_id,
        )
        response.log_url = build_signed_url(
            request,
            f"/download/log/{job_id}/{run_id}",
            "download_log",
            job_id,
            run_id=run_id,
        )
        response.audit_log = audit_log

    return response
