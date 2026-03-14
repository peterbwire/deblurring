import os
from dataclasses import dataclass
from functools import lru_cache

from fastapi import HTTPException, Request, status


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    auth_mode: str = "api_key"


@lru_cache(maxsize=1)
def get_api_key_registry() -> dict[str, str]:
    raw = os.getenv("FORENSICLEAR_API_KEYS", "").strip()
    registry: dict[str, str] = {}

    for pair in [item.strip() for item in raw.split(",") if item.strip()]:
        if ":" not in pair:
            continue
        user_id, api_key = pair.split(":", 1)
        user_id = user_id.strip()
        api_key = api_key.strip()
        if user_id and api_key:
            registry[api_key] = user_id

    return registry


def _extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token.strip()


def require_authenticated_user(request: Request) -> AuthenticatedUser:
    registry = get_api_key_registry()
    if not registry:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured on the server.",
        )

    token = _extract_bearer_token(request)
    user_id = registry.get(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token was not recognized.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.user_id = user_id
    return AuthenticatedUser(user_id=user_id)
