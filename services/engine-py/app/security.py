"""Security layer for the Python engine.

Defense in depth, all enforced before business logic runs:
  1. API key authentication (X-API-Key) when ENGINE_API_KEY is configured,
     compared in constant time. /health stays public for liveness checks.
  2. Role based authorization for writes: ingestion requires an operator or
     admin role in the X-Role header when auth is enabled.
  3. Per client rate limiting with a sliding window and Retry-After.
  4. Request body size cap to blunt abuse and accidental giant payloads.
  5. Security response headers on every response.
  6. No secrets in code or logs: keys come from the environment only, and
     their values are never printed or returned.

When ENGINE_API_KEY is unset the service runs in open development mode, and
/health reports auth as disabled so the state is never ambiguous.
"""

import hmac
import os
import time
import uuid
from collections import Counter, defaultdict, deque
from typing import Deque, Dict

METRICS: Counter = Counter()


def metrics_snapshot() -> dict:
    return {"requests": {k: v for k, v in sorted(METRICS.items())}}

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

MAX_BODY_BYTES = int(os.getenv("ENGINE_MAX_BODY_BYTES", "1048576"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("ENGINE_RATE_LIMIT_PER_MINUTE", "120"))
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}
WRITE_ROLES = {"operator", "admin"}


def _api_key() -> str:
    return os.getenv("ENGINE_API_KEY", "")


def auth_enabled() -> bool:
    return bool(_api_key())


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Rate limiting, per client IP, sliding 60 second window.
        now = time.time()
        bucket = self._hits[request.client.host if request.client else "unknown"]
        while bucket and bucket[0] < now - 60:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                {"detail": "Rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": "60"},
            )
        bucket.append(now)

        # Body size cap.
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_BYTES:
            return JSONResponse({"detail": "Request body too large"}, status_code=413)

        # Authentication and write authorization.
        if auth_enabled() and request.url.path not in PUBLIC_PATHS:
            provided = request.headers.get("x-api-key", "")
            if not hmac.compare_digest(provided, _api_key()):
                return JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)
            if request.url.path.startswith("/v1/rag/ingest"):
                role = request.headers.get("x-role", "viewer")
                if role not in WRITE_ROLES:
                    return JSONResponse(
                        {"detail": "Ingestion requires operator or admin role"},
                        status_code=403,
                    )

        response = await call_next(request)
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        response.headers["X-Request-Id"] = request_id
        METRICS[f"{request.method} {request.url.path} -> {response.status_code}"] += 1
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response
