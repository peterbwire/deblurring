import json
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any


DB_LOCK = Lock()
BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_PATH = BASE_DIR / "forensiclear.db"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with DB_LOCK:
        with _connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    stored_filename TEXT NOT NULL,
                    content_type TEXT,
                    size_bytes INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    uploaded_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    duration_seconds REAL,
                    warnings_json TEXT NOT NULL DEFAULT '[]',
                    error_message TEXT,
                    settings_json TEXT NOT NULL,
                    progress_phase TEXT,
                    audit_log_json TEXT,
                    output_filename TEXT,
                    output_sha256 TEXT,
                    last_updated_at TEXT NOT NULL,
                    FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_jobs_owner_uploaded ON jobs(owner_id, uploaded_at DESC)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_runs_job_created ON runs(job_id, created_at DESC)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status)")


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    payload = dict(row)
    for key in ("warnings_json", "settings_json", "audit_log_json"):
        if key in payload and payload[key]:
            payload[key] = json.loads(payload[key])
    if "warnings_json" in payload and not payload["warnings_json"]:
        payload["warnings_json"] = []
    return payload


def create_job_record(payload: dict[str, Any]) -> None:
    with DB_LOCK:
        with _connect() as connection:
            connection.execute(
                """
                INSERT INTO jobs (
                    job_id, owner_id, original_filename, stored_filename, content_type,
                    size_bytes, sha256, width, height, uploaded_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["job_id"],
                    payload["owner_id"],
                    payload["original_filename"],
                    payload["stored_filename"],
                    payload["content_type"],
                    payload["size_bytes"],
                    payload["sha256"],
                    payload["width"],
                    payload["height"],
                    payload["uploaded_at"],
                ),
            )


def get_job_record(job_id: str, owner_id: str | None = None) -> dict[str, Any] | None:
    query = "SELECT * FROM jobs WHERE job_id = ?"
    parameters: list[Any] = [job_id]
    if owner_id is not None:
        query += " AND owner_id = ?"
        parameters.append(owner_id)

    with DB_LOCK:
        with _connect() as connection:
            row = connection.execute(query, parameters).fetchone()
    return _row_to_dict(row)


def create_run_record(payload: dict[str, Any]) -> None:
    with DB_LOCK:
        with _connect() as connection:
            connection.execute(
                """
                INSERT INTO runs (
                    run_id, job_id, owner_id, status, created_at, started_at, completed_at,
                    duration_seconds, warnings_json, error_message, settings_json, progress_phase,
                    audit_log_json, output_filename, output_sha256, last_updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["run_id"],
                    payload["job_id"],
                    payload["owner_id"],
                    payload["status"],
                    payload["created_at"],
                    payload.get("started_at"),
                    payload.get("completed_at"),
                    payload.get("duration_seconds"),
                    json.dumps(payload.get("warnings_json", [])),
                    payload.get("error_message"),
                    json.dumps(payload["settings_json"]),
                    payload.get("progress_phase"),
                    json.dumps(payload["audit_log_json"]) if payload.get("audit_log_json") is not None else None,
                    payload.get("output_filename"),
                    payload.get("output_sha256"),
                    payload["last_updated_at"],
                ),
            )


def get_run_record(job_id: str, run_id: str, owner_id: str | None = None) -> dict[str, Any] | None:
    query = "SELECT * FROM runs WHERE job_id = ? AND run_id = ?"
    parameters: list[Any] = [job_id, run_id]
    if owner_id is not None:
        query += " AND owner_id = ?"
        parameters.append(owner_id)

    with DB_LOCK:
        with _connect() as connection:
            row = connection.execute(query, parameters).fetchone()
    return _row_to_dict(row)


def update_run_record(job_id: str, run_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    if not updates:
        return get_run_record(job_id, run_id)

    normalized = dict(updates)
    if "warnings_json" in normalized:
        normalized["warnings_json"] = json.dumps(normalized["warnings_json"])
    if "settings_json" in normalized:
        normalized["settings_json"] = json.dumps(normalized["settings_json"])
    if "audit_log_json" in normalized and normalized["audit_log_json"] is not None:
        normalized["audit_log_json"] = json.dumps(normalized["audit_log_json"])

    assignments = ", ".join(f"{column} = ?" for column in normalized.keys())
    parameters = list(normalized.values()) + [job_id, run_id]

    with DB_LOCK:
        with _connect() as connection:
            connection.execute(f"UPDATE runs SET {assignments} WHERE job_id = ? AND run_id = ?", parameters)
    return get_run_record(job_id, run_id)


def mark_incomplete_runs_failed(completed_at: str, error_message: str) -> None:
    with DB_LOCK:
        with _connect() as connection:
            connection.execute(
                """
                UPDATE runs
                SET status = 'failed',
                    completed_at = ?,
                    last_updated_at = ?,
                    error_message = ?,
                    progress_phase = 'failed'
                WHERE status IN ('queued', 'processing')
                """,
                (completed_at, completed_at, error_message),
            )


def list_recent_jobs(owner_id: str, limit: int = 8) -> list[dict[str, Any]]:
    with DB_LOCK:
        with _connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    jobs.job_id,
                    jobs.original_filename,
                    jobs.uploaded_at,
                    jobs.width,
                    jobs.height,
                    runs.run_id AS latest_run_id,
                    runs.status AS latest_run_status
                FROM jobs
                LEFT JOIN runs
                    ON runs.job_id = jobs.job_id
                   AND runs.created_at = (
                        SELECT MAX(created_at)
                        FROM runs r2
                        WHERE r2.job_id = jobs.job_id
                   )
                WHERE jobs.owner_id = ?
                ORDER BY jobs.uploaded_at DESC
                LIMIT ?
                """,
                (owner_id, limit),
            ).fetchall()
    return [dict(row) for row in rows]


def list_jobs_older_than(cutoff_timestamp: str) -> list[dict[str, Any]]:
    with DB_LOCK:
        with _connect() as connection:
            rows = connection.execute(
                """
                SELECT job_id, owner_id
                FROM jobs
                WHERE uploaded_at < ?
                """,
                (cutoff_timestamp,),
            ).fetchall()
    return [dict(row) for row in rows]


def delete_job_record(job_id: str) -> None:
    with DB_LOCK:
        with _connect() as connection:
            connection.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
