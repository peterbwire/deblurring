import os
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status


RATE_LIMIT_WINDOW_SECONDS = 60
UPLOAD_LIMIT = int(os.getenv("FORENSICLEAR_UPLOADS_PER_MINUTE", "12"))
PROCESS_LIMIT = int(os.getenv("FORENSICLEAR_RUNS_PER_MINUTE", "18"))

_buckets: dict[str, dict[str, deque[float]]] = {
    "upload": defaultdict(deque),
    "process": defaultdict(deque),
}


def enforce_rate_limit(action: str, owner_id: str) -> None:
    now = time.time()
    bucket = _buckets[action][owner_id]

    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
        bucket.popleft()

    limit = UPLOAD_LIMIT if action == "upload" else PROCESS_LIMIT
    if len(bucket) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {action}. Please wait and try again.",
        )

    bucket.append(now)
