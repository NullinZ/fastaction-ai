"""Request correlation and safe server-error responses."""

import json
import logging
import re
import time
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("safe_errors")

REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SAFE_SERVER_ERRORS = {
    500: ("INTERNAL_SERVER_ERROR", "服务暂时不可用，请稍后重试"),
    502: ("UPSTREAM_SERVICE_ERROR", "上游服务暂时不可用，请稍后重试"),
    503: ("SERVICE_UNAVAILABLE", "服务暂时不可用，请稍后重试"),
    504: ("UPSTREAM_TIMEOUT", "上游服务响应超时，请稍后重试"),
}


def safe_server_error_response(status_code: int, request_id: str) -> JSONResponse:
    error_code, message = SAFE_SERVER_ERRORS.get(
        status_code,
        ("SERVER_ERROR", "服务暂时不可用，请稍后重试"),
    )
    response = JSONResponse(
        status_code=status_code,
        content={
            "code": status_code,
            "error_code": error_code,
            "message": message,
            "detail": message,
            "data": None,
            "request_id": request_id,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


def _should_sanitize_server_error(body: bytes) -> bool:
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        return True
    if not isinstance(payload, dict):
        return True
    if payload.get("error_code") and payload.get("request_id"):
        return False
    return isinstance(payload.get("detail"), str) or isinstance(
        payload.get("error"), str
    )


class SafeErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        started_at = time.perf_counter()
        incoming_request_id = (request.headers.get("X-Request-ID") or "").strip()
        request_id = (
            incoming_request_id
            if REQUEST_ID_RE.fullmatch(incoming_request_id)
            else uuid4().hex
        )
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception as exc:
            process_time_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.error(
                "request_failed request_id=%s error_code=%s exception_type=%s "
                "method=%s path=%s process_time_ms=%s",
                request_id,
                "INTERNAL_SERVER_ERROR",
                type(exc).__name__,
                request.method,
                request.url.path,
                process_time_ms,
            )
            response = safe_server_error_response(500, request_id)
            response.headers["X-Process-Time"] = str(process_time_ms)
            return response

        process_time_ms = round((time.perf_counter() - started_at) * 1000, 2)
        if response.status_code >= 500:
            logger.error(
                "request_failed request_id=%s error_code=%s method=%s path=%s "
                "status_code=%s process_time_ms=%s",
                request_id,
                SAFE_SERVER_ERRORS.get(
                    response.status_code, ("SERVER_ERROR", "")
                )[0],
                request.method,
                request.url.path,
                response.status_code,
                process_time_ms,
            )
            original_headers = dict(response.headers)
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            if _should_sanitize_server_error(body):
                response = safe_server_error_response(response.status_code, request_id)
                for name, value in original_headers.items():
                    if name.lower() not in {
                        "content-length",
                        "content-type",
                        "x-request-id",
                    }:
                        response.headers[name] = value
            else:
                response = Response(
                    content=body,
                    status_code=response.status_code,
                    headers=original_headers,
                )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time_ms)
        return response
