import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.file_manager import get_run_log_path


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_audit_log(job_id: str, run_id: str, payload: dict[str, Any]) -> Path:
    log_path = get_run_log_path(job_id, run_id)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return log_path


def read_audit_log(job_id: str, run_id: str) -> dict[str, Any]:
    log_path = get_run_log_path(job_id, run_id)
    return json.loads(log_path.read_text(encoding="utf-8"))
