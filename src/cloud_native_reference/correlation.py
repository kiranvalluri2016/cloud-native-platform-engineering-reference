from __future__ import annotations

import re
from uuid import uuid4


_SAFE_CORRELATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def correlation_id(value: str | None) -> str:
    """Return a bounded safe caller ID or generate a server-owned UUID."""
    if value and _SAFE_CORRELATION_ID.fullmatch(value):
        return value
    return str(uuid4())
