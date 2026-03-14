import logging
import os
from dataclasses import dataclass
from queue import Full, Queue
from threading import Lock, Thread
from typing import Any

from fastapi import HTTPException

from app.models.schemas import ProcessRequest
from app.services.database import (
    create_run_record,
    delete_job_record,
    get_job_record,
    get_run_record,
    list_jobs_older_than,
    mark_incomplete_runs_failed,
    update_run_record,
)
from app.services.file_manager import cleanup_job_directory, get_original_file, get_retention_cutoff
from app.services.image_pipeline import process_image
from app.services.logger_service import current_timestamp
from app.utils.ids import generate_job_id


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunTask:
    job_id: str
    run_id: str
    owner_id: str
    settings: dict[str, Any]


QUEUE_STOP = object()
QUEUE_CONTROL_LOCK = Lock()
ACTIVE_RUNS_LOCK = Lock()
RUN_QUEUE: Queue[RunTask | object] | None = None
WORKER_THREADS: list[Thread] = []
ACTIVE_RUN_IDS: set[str] = set()


def _get_positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return max(1, value)


def get_worker_count() -> int:
    return _get_positive_int_env("FORENSICLEAR_WORKER_COUNT", 2)


def get_queue_max_size() -> int:
    return _get_positive_int_env("FORENSICLEAR_QUEUE_MAX_SIZE", 12)


def create_run(job_id: str, owner_id: str, settings: ProcessRequest) -> dict[str, Any]:
    if not get_job_record(job_id, owner_id=owner_id):
        raise HTTPException(status_code=404, detail="Job not found.")

    run_id = generate_job_id()
    timestamp = current_timestamp()
    record = {
        "job_id": job_id,
        "run_id": run_id,
        "owner_id": owner_id,
        "status": "queued",
        "created_at": timestamp,
        "started_at": None,
        "completed_at": None,
        "duration_seconds": None,
        "warnings_json": [],
        "error_message": None,
        "settings_json": settings.model_dump(),
        "progress_phase": "queued",
        "audit_log_json": None,
        "output_filename": None,
        "output_sha256": None,
        "last_updated_at": timestamp,
    }
    create_run_record(record)
    return get_run_record(job_id, run_id, owner_id=owner_id) or record


def update_run(job_id: str, run_id: str, **updates: Any) -> dict[str, Any] | None:
    updates["last_updated_at"] = current_timestamp()
    return update_run_record(job_id, run_id, updates)


def submit_run(job_id: str, run_id: str, owner_id: str, settings: dict[str, Any]) -> None:
    if RUN_QUEUE is None:
        update_run(
            job_id,
            run_id,
            status="failed",
            completed_at=current_timestamp(),
            error_message="Processing workers are not available.",
            progress_phase="failed",
        )
        raise HTTPException(status_code=503, detail="Processing workers are not available.")

    task = RunTask(job_id=job_id, run_id=run_id, owner_id=owner_id, settings=settings)

    try:
        RUN_QUEUE.put_nowait(task)
    except Full as exc:
        update_run(
            job_id,
            run_id,
            status="failed",
            completed_at=current_timestamp(),
            error_message="Processing queue is at capacity. Retry shortly.",
            progress_phase="queue_rejected",
        )
        raise HTTPException(status_code=503, detail="Processing queue is at capacity. Retry shortly.") from exc


def _execute_run(job_id: str, run_id: str, owner_id: str, settings: dict[str, Any]) -> None:
    update_run(
        job_id,
        run_id,
        status="processing",
        started_at=current_timestamp(),
        progress_phase="loading_original",
    )

    try:
        original_path = get_original_file(job_id, owner_id=owner_id)
        result = process_image(
            job_id,
            run_id,
            original_path,
            ProcessRequest(**settings),
            progress_callback=lambda phase: update_run(job_id, run_id, progress_phase=phase),
        )
        update_run(
            job_id,
            run_id,
            status="completed",
            completed_at=current_timestamp(),
            duration_seconds=result["duration_seconds"],
            warnings_json=result["warnings"],
            progress_phase="completed",
            audit_log_json=result["audit_log"],
            output_filename=result["output_path"].name,
            output_sha256=result["output_sha256"],
        )
    except HTTPException as exc:
        update_run(
            job_id,
            run_id,
            status="failed",
            completed_at=current_timestamp(),
            error_message=str(exc.detail),
            progress_phase="failed",
        )
    except Exception:
        logger.exception("Run %s for job %s failed unexpectedly.", run_id, job_id)
        update_run(
            job_id,
            run_id,
            status="failed",
            completed_at=current_timestamp(),
            error_message="Processing failed due to an unexpected server error.",
            progress_phase="failed",
        )


def _worker_loop(work_queue: Queue[RunTask | object]) -> None:
    while True:
        task = work_queue.get()

        try:
            if task is QUEUE_STOP:
                return

            if not isinstance(task, RunTask):
                logger.warning("Discarded unexpected item from processing queue.")
                continue
            with ACTIVE_RUNS_LOCK:
                ACTIVE_RUN_IDS.add(task.run_id)

            _execute_run(task.job_id, task.run_id, task.owner_id, task.settings)
        finally:
            if isinstance(task, RunTask):
                with ACTIVE_RUNS_LOCK:
                    ACTIVE_RUN_IDS.discard(task.run_id)
            work_queue.task_done()


def start_worker_pool() -> None:
    global RUN_QUEUE, WORKER_THREADS

    with QUEUE_CONTROL_LOCK:
        if WORKER_THREADS and all(thread.is_alive() for thread in WORKER_THREADS):
            return

        RUN_QUEUE = Queue(maxsize=get_queue_max_size())
        WORKER_THREADS = []

        for index in range(get_worker_count()):
            worker = Thread(
                target=_worker_loop,
                args=(RUN_QUEUE,),
                name=f"forensiclear-runner-{index + 1}",
                daemon=True,
            )
            worker.start()
            WORKER_THREADS.append(worker)

        logger.info(
            "Started processing worker pool with %s workers and queue size %s.",
            len(WORKER_THREADS),
            RUN_QUEUE.maxsize,
        )


def get_queue_metrics() -> dict[str, int]:
    queued_runs = RUN_QUEUE.qsize() if RUN_QUEUE is not None else 0
    with ACTIVE_RUNS_LOCK:
        active_runs = len(ACTIVE_RUN_IDS)

    worker_count = len([thread for thread in WORKER_THREADS if thread.is_alive()])
    queue_max_size = RUN_QUEUE.maxsize if RUN_QUEUE is not None else get_queue_max_size()

    return {
        "queued_runs": queued_runs,
        "active_runs": active_runs,
        "worker_count": worker_count,
        "queue_max_size": queue_max_size,
    }


def reconcile_incomplete_runs() -> None:
    mark_incomplete_runs_failed(
        completed_at=current_timestamp(),
        error_message="Run interrupted before completion.",
    )


def cleanup_expired_jobs() -> None:
    cutoff = get_retention_cutoff()
    for job in list_jobs_older_than(cutoff):
        cleanup_job_directory(job["job_id"])
        delete_job_record(job["job_id"])


def shutdown_worker_pool() -> None:
    global RUN_QUEUE, WORKER_THREADS

    with QUEUE_CONTROL_LOCK:
        work_queue = RUN_QUEUE
        workers = WORKER_THREADS
        RUN_QUEUE = None
        WORKER_THREADS = []

    if work_queue is None:
        return

    for _ in workers:
        work_queue.put(QUEUE_STOP)

    for worker in workers:
        worker.join(timeout=2)

    with ACTIVE_RUNS_LOCK:
        ACTIVE_RUN_IDS.clear()
