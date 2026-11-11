# Observability contract

Every completed HTTP request produces one JSON log event with UTC timestamp, severity, event name, method, path, status, duration, and correlation ID. The logger intentionally excludes request bodies, authorization headers, cookies, secret references, and environment dumps.

`GET /metrics` exposes an in-process request counter for local demonstration. It is not a replacement for a production metrics backend, scrape configuration, alerting policy, retention design, or service-level objective.

Correlation IDs are accepted only when they match a bounded safe character set; otherwise the API generates a UUID. The correlation ID is returned in `X-Correlation-ID` and the safe JSON response body.
