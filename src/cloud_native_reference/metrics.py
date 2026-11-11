from __future__ import annotations

from collections import Counter
from threading import Lock


class Metrics:
    def __init__(self) -> None:
        self._requests: Counter[tuple[str, int]] = Counter()
        self._lock = Lock()

    def record(self, route: str, status: int) -> None:
        with self._lock:
            self._requests[(route, status)] += 1

    def render(self) -> str:
        with self._lock:
            lines = [
                "# HELP platform_api_http_requests_total Completed HTTP requests.",
                "# TYPE platform_api_http_requests_total counter",
            ]
            for (route, status), count in sorted(self._requests.items()):
                lines.append(
                    f'platform_api_http_requests_total{{route="{route}",status="{status}"}} {count}'
                )
        return "\n".join(lines) + "\n"
