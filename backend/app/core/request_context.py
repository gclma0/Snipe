import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
PROCESS_TIME_HEADER = "X-Process-Time-ms"


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = _clean_request_id(request.headers.get(REQUEST_ID_HEADER)) or uuid.uuid4().hex
        start_time = time.perf_counter()
        request.state.request_id = request_id
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[PROCESS_TIME_HEADER] = f"{elapsed_ms:.2f}"
        return response


def _clean_request_id(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 128:
        return None
    return cleaned
