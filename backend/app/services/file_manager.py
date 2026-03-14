import hashlib
import mimetypes
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status

from app.services.database import create_job_record, get_job_record, get_run_record
from app.utils.ids import generate_job_id
from app.utils.image_ops import validate_image_file


BASE_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
LOGS_DIR = BASE_DIR / "logs"
MAX_UPLOAD_SIZE = 15 * 1024 * 1024
UPLOAD_CHUNK_SIZE = 1024 * 1024
RETENTION_DAYS = int(os.getenv("FORENSICLEAR_RETENTION_DAYS", "14"))
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def ensure_storage_dirs() -> None:
    for directory in (UPLOADS_DIR, OUTPUTS_DIR, LOGS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    return Path(filename).name


def validate_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed formats: {allowed}.",
        )
    return suffix


def get_job_upload_dir(job_id: str) -> Path:
    return UPLOADS_DIR / job_id


def get_job_output_dir(job_id: str) -> Path:
    return OUTPUTS_DIR / job_id


def get_job_logs_dir(job_id: str) -> Path:
    return LOGS_DIR / job_id


def get_original_file(job_id: str, owner_id: str | None = None) -> Path:
    job_record = get_job_record(job_id, owner_id=owner_id)
    if not job_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    original_path = get_job_upload_dir(job_id) / job_record["stored_filename"]
    if not original_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original upload for this job could not be located.",
        )
    return original_path


def get_run_output_dir(job_id: str, run_id: str) -> Path:
    return get_job_output_dir(job_id) / run_id


def get_run_output_path(job_id: str, run_id: str, suffix: str = ".png") -> Path:
    output_dir = get_run_output_dir(job_id, run_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"restored{suffix}"


def get_run_output_file(job_id: str, run_id: str) -> Path:
    run_record = get_run_record(job_id, run_id)
    if not run_record or not run_record.get("output_filename"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processed output not found.")

    output_path = get_run_output_dir(job_id, run_id) / run_record["output_filename"]
    if not output_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processed output not found.")
    return output_path


def get_run_log_path(job_id: str, run_id: str) -> Path:
    logs_dir = get_job_logs_dir(job_id)
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir / f"{run_id}.json"


def read_job_manifest(job_id: str, owner_id: str | None = None) -> dict[str, Any]:
    job_record = get_job_record(job_id, owner_id=owner_id)
    if not job_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job metadata is missing for this upload.",
        )
    return job_record


def calculate_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cleanup_job_directory(job_id: str) -> None:
    for directory in (
        get_job_upload_dir(job_id),
        get_job_output_dir(job_id),
        get_job_logs_dir(job_id),
    ):
        if directory.exists():
            shutil.rmtree(directory, ignore_errors=True)


async def save_upload(file: UploadFile, owner_id: str) -> dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A file name is required.")

    ensure_storage_dirs()
    original_filename = sanitize_filename(file.filename)
    suffix = validate_extension(original_filename)
    job_id = generate_job_id()
    upload_dir = get_job_upload_dir(job_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    original_path = upload_dir / f"original{suffix}"
    size_bytes = 0
    digest = hashlib.sha256()

    try:
        with original_path.open("wb") as output_file:
            while True:
                chunk = await file.read(UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds the {MAX_UPLOAD_SIZE // (1024 * 1024)} MB limit.",
                    )
                digest.update(chunk)
                output_file.write(chunk)
    except Exception:
        cleanup_job_directory(job_id)
        raise
    finally:
        await file.close()

    if size_bytes == 0:
        cleanup_job_directory(job_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file was empty.")

    try:
        image_metadata = validate_image_file(str(original_path))
    except ValueError as exc:
        cleanup_job_directory(job_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    uploaded_at = datetime.now(timezone.utc).isoformat()
    create_job_record(
        {
            "job_id": job_id,
            "owner_id": owner_id,
            "original_filename": original_filename,
            "stored_filename": original_path.name,
            "content_type": file.content_type or mimetypes.guess_type(original_filename)[0] or "application/octet-stream",
            "size_bytes": size_bytes,
            "sha256": digest.hexdigest(),
            "width": image_metadata["width"],
            "height": image_metadata["height"],
            "uploaded_at": uploaded_at,
        }
    )

    return {
        "job_id": job_id,
        "original_filename": original_filename,
        "stored_filename": original_path.name,
        "file_size": size_bytes,
        "sha256": digest.hexdigest(),
        "width": image_metadata["width"],
        "height": image_metadata["height"],
        "uploaded_at": uploaded_at,
    }


def get_media_type(path: Path) -> str:
    media_type, _ = mimetypes.guess_type(path.name)
    return media_type or "application/octet-stream"


def get_retention_cutoff() -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    return cutoff.isoformat()
