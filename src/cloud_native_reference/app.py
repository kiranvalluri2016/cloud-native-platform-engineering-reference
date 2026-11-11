from __future__ import annotations

import json
import logging
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TypeAlias

from . import __version__
from .correlation import correlation_id
from .logging_config import configure_logging
from .metrics import Metrics


Logger: TypeAlias = logging.Logger

_ROUTE_LABELS = frozenset({"/live", "/ready", "/api/v1/info", "/metrics"})


def route_label(path: str) -> str:
    """Bound observability labels independently of untrusted request paths."""
    return path if path in _ROUTE_LABELS else "unknown"


def handler_factory(metrics: Metrics, logger: Logger) -> type[BaseHTTPRequestHandler]:
    class ApiHandler(BaseHTTPRequestHandler):
        server_version = "platform-api"
        sys_version = ""

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
            started = time.perf_counter()
            request_id = correlation_id(self.headers.get("X-Correlation-ID"))
            path = self.path.split("?", 1)[0]
            route = route_label(path)
            status = HTTPStatus.NOT_FOUND
            content_type = "application/json"
            body: bytes

            if path == "/live":
                status = HTTPStatus.OK
                body = json.dumps({"status": "live", "correlation_id": request_id}).encode()
            elif path == "/ready":
                status = HTTPStatus.OK
                body = json.dumps({"status": "ready", "correlation_id": request_id}).encode()
            elif path == "/api/v1/info":
                status = HTTPStatus.OK
                body = json.dumps(
                    {
                        "service": "cloud-native-reference-api",
                        "version": __version__,
                        "correlation_id": request_id,
                    }
                ).encode()
            elif path == "/metrics":
                status = HTTPStatus.OK
                content_type = "text/plain; version=0.0.4"
                body = metrics.render().encode()
            else:
                body = json.dumps({"error": "not_found", "correlation_id": request_id}).encode()

            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Correlation-ID", request_id)
            self.end_headers()
            self.wfile.write(body)

            metrics.record(route, int(status))
            logger.info(
                "request_completed",
                extra={
                    "correlation_id": request_id,
                    "method": "GET",
                    "route": route,
                    "status": int(status),
                    "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                },
            )

    return ApiHandler


def create_server(host: str = "0.0.0.0", port: int = 8080, logger: Logger | None = None) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), handler_factory(Metrics(), logger or configure_logging()))


def main() -> None:
    server = create_server()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
