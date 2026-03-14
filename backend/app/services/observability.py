import logging
import time
from uuid import uuid4

from fastapi import Request


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def request_logging_middleware(request: Request, call_next):
    request_id = uuid4().hex[:12]
    request.state.request_id = request_id
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logging.getLogger("forensiclear.http").exception(
            "request_id=%s method=%s path=%s status=500 duration_ms=%s user_id=%s",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
            getattr(request.state, "user_id", "anonymous"),
        )
        raise

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    logging.getLogger("forensiclear.http").info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%s user_id=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        getattr(request.state, "user_id", "anonymous"),
    )
    response.headers["X-Request-Id"] = request_id
    return response
