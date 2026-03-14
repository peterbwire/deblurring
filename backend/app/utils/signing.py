import hmac
import os
import time
from hashlib import sha256
from urllib.parse import urlencode

from fastapi import HTTPException, Request, status


DEFAULT_SIGNED_URL_TTL_SECONDS = 60 * 60
SIGNING_SECRET = os.getenv("FORENSICLEAR_SIGNING_SECRET", "forensiclear-dev-secret-change-me")


def _signature_payload(resource: str, job_id: str, run_id: str | None, expires: int) -> str:
    return f"{resource}:{job_id}:{run_id or '-'}:{expires}"


def create_signature(resource: str, job_id: str, run_id: str | None, expires: int) -> str:
    payload = _signature_payload(resource, job_id, run_id, expires).encode("utf-8")
    return hmac.new(SIGNING_SECRET.encode("utf-8"), payload, sha256).hexdigest()


def build_signed_url(
    request: Request,
    route_path: str,
    resource: str,
    job_id: str,
    run_id: str | None = None,
    ttl_seconds: int = DEFAULT_SIGNED_URL_TTL_SECONDS,
) -> str:
    expires = int(time.time()) + ttl_seconds
    signature = create_signature(resource, job_id, run_id, expires)
    query = urlencode({"expires": expires, "signature": signature})
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}{route_path}?{query}"


def verify_signature(
    resource: str,
    job_id: str,
    run_id: str | None,
    expires: int,
    signature: str,
) -> None:
    if expires < int(time.time()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Signed link has expired.")

    expected = create_signature(resource, job_id, run_id, expires)
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Signed link is invalid.")
