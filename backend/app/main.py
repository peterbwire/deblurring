from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, download, health, ops, preview, process, upload
from app.services.database import init_db
from app.services.file_manager import ensure_storage_dirs
from app.services.observability import configure_logging, request_logging_middleware
from app.services.run_manager import (
    cleanup_expired_jobs,
    reconcile_incomplete_runs,
    shutdown_worker_pool,
    start_worker_pool,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    ensure_storage_dirs()
    init_db()
    reconcile_incomplete_runs()
    cleanup_expired_jobs()
    start_worker_pool()
    yield
    shutdown_worker_pool()


app = FastAPI(
    title="ForensiClear",
    version="0.2.0",
    summary="Lawful forensic-style image restoration workspace",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(request_logging_middleware)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(ops.router)
app.include_router(upload.router)
app.include_router(process.router)
app.include_router(preview.router)
app.include_router(download.router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "app": "ForensiClear",
        "tagline": "Restore clarity. Preserve integrity.",
        "docs": "/docs",
    }
