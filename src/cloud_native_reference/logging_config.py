from __future__ import annotations

import json
import logging
import sys
from typing import TextIO


class JsonFormatter(logging.Formatter):
    """Emit only explicitly supplied operational fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for field in ("correlation_id", "method", "route", "status", "duration_ms"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload, sort_keys=True)


def configure_logging(stream: TextIO | None = None) -> logging.Logger:
    logger = logging.getLogger("cloud_native_reference")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger
