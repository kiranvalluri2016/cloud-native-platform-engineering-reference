from __future__ import annotations

import io
import json
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from cloud_native_reference.app import create_server
from cloud_native_reference.logging_config import configure_logging


@pytest.fixture
def api_server() -> tuple[str, io.StringIO, object]:
    log_stream = io.StringIO()
    server = create_server("127.0.0.1", 0, configure_logging(log_stream))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    yield base_url, log_stream, server
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def get_json(url: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], dict[str, str]]:
    with urlopen(Request(url, headers=headers or {}), timeout=2) as response:
        normalized_headers = {name.lower(): value for name, value in response.headers.items()}
        return response.status, normalized_headers, json.loads(response.read())


def test_health_and_metadata_endpoints_return_safe_payloads(api_server: tuple[str, io.StringIO, object]) -> None:
    base_url, _, _ = api_server
    for path, expected_status in (("/live", "live"), ("/ready", "ready")):
        status, headers, body = get_json(f"{base_url}{path}")
        assert status == 200
        assert body["status"] == expected_status
        assert body["correlation_id"] == headers["x-correlation-id"]

    status, _, body = get_json(f"{base_url}/api/v1/info")
    assert status == 200
    assert body == {
        "service": "cloud-native-reference-api",
        "version": "0.1.0",
        "correlation_id": body["correlation_id"],
    }


def test_correlation_id_is_propagated_only_when_safe(api_server: tuple[str, io.StringIO, object]) -> None:
    base_url, _, _ = api_server
    _, headers, body = get_json(f"{base_url}/live", {"X-Correlation-ID": "review-123"})
    assert headers["x-correlation-id"] == "review-123"
    assert body["correlation_id"] == "review-123"

    _, headers, body = get_json(f"{base_url}/live", {"X-Correlation-ID": "unsafe value"})
    assert headers["x-correlation-id"] != "unsafe value"
    assert body["correlation_id"] == headers["x-correlation-id"]


def test_metrics_and_logs_contain_operational_data_not_request_secrets(
    api_server: tuple[str, io.StringIO, object],
) -> None:
    base_url, log_stream, _ = api_server
    get_json(
        f"{base_url}/live",
        {"X-Correlation-ID": "review-456", "Authorization": "Bearer never-log-this"},
    )
    with urlopen(f"{base_url}/metrics", timeout=2) as response:
        metrics = response.read().decode()

    assert 'platform_api_http_requests_total{route="/live",status="200"} 1' in metrics
    log_line = json.loads(log_stream.getvalue().splitlines()[0])
    assert log_line["correlation_id"] == "review-456"
    assert "Authorization" not in log_stream.getvalue()
    assert "never-log-this" not in log_stream.getvalue()


def test_unknown_route_is_safe_and_correlated(api_server: tuple[str, io.StringIO, object]) -> None:
    base_url, _, _ = api_server
    with pytest.raises(HTTPError) as error:
        urlopen(f"{base_url}/missing", timeout=2)
    assert error.value.code == 404
    body = json.loads(error.value.read())
    assert body["error"] == "not_found"
    assert body["correlation_id"]


def test_unknown_paths_use_a_fixed_operational_label(api_server: tuple[str, io.StringIO, object]) -> None:
    base_url, log_stream, _ = api_server
    untrusted_path = "/customers/private-record?token=do-not-log"
    with pytest.raises(HTTPError) as error:
        urlopen(f"{base_url}{untrusted_path}", timeout=2)
    assert error.value.code == 404
    error.value.read()

    with urlopen(f"{base_url}/metrics", timeout=2) as response:
        metrics = response.read().decode()

    assert 'platform_api_http_requests_total{route="unknown",status="404"} 1' in metrics
    assert untrusted_path not in metrics
    assert "private-record" not in log_stream.getvalue()
    assert "do-not-log" not in log_stream.getvalue()
    unknown_log = json.loads(log_stream.getvalue().splitlines()[0])
    assert unknown_log["route"] == "unknown"
