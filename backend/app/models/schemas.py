from typing import Any, Literal

from pydantic import BaseModel, Field


DenoiseStrength = Literal["low", "medium", "high"]
DeblurMode = Literal["mild", "standard", "aggressive"]
UpscaleSetting = Literal["none", "2x"]
RunState = Literal["queued", "processing", "completed", "failed"]


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "ForensiClear"


class UploadResponse(BaseModel):
    job_id: str
    original_filename: str
    original_url: str
    file_size: int
    sha256: str
    width: int
    height: int


class ProcessRequest(BaseModel):
    denoise_strength: DenoiseStrength = "medium"
    deblur_mode: DeblurMode = "standard"
    sharpen_edges: bool = True
    upscale: UpscaleSetting = "none"
    evidence_safe: bool = True


class ProcessStartResponse(BaseModel):
    job_id: str
    run_id: str
    status: RunState
    status_url: str
    queued_at: str


class RunStatusResponse(BaseModel):
    job_id: str
    run_id: str
    status: RunState
    status_url: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    original_url: str | None = None
    restored_url: str | None = None
    log_url: str | None = None
    image_download_url: str | None = None
    warnings: list[str] = Field(default_factory=list)
    duration_seconds: float | None = None
    error_message: str | None = None
    progress_phase: str | None = None
    audit_log: dict[str, Any] | None = None


class AuthUserResponse(BaseModel):
    user_id: str
    auth_mode: str


class JobHistoryItem(BaseModel):
    job_id: str
    original_filename: str
    uploaded_at: str
    width: int
    height: int
    latest_run_id: str | None = None
    latest_run_status: RunState | None = None


class JobHistoryResponse(BaseModel):
    items: list[JobHistoryItem] = Field(default_factory=list)


class OpsMetricsResponse(BaseModel):
    queued_runs: int
    active_runs: int
    worker_count: int
    queue_max_size: int
