from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_enforces_non_root_runtime_and_safe_workdir() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM python:3.12-alpine" in dockerfile
    assert "WORKDIR /app" in dockerfile
    assert "USER 10001:10001" in dockerfile
    assert "PYTHONPATH=/app/src" in dockerfile
    assert "latest" not in dockerfile


def test_dockerignore_excludes_local_and_test_artifacts() -> None:
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    for excluded in (".git/", ".venv/", ".pytest_cache/", "tests/", "docs/"):
        assert excluded in dockerignore
