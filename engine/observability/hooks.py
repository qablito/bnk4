from __future__ import annotations

from typing import Any


def emit(event: str, **payload: Any) -> None:
    """
    Backend-agnostic observability hook.

    v1 default: no-op. Integrations can monkeypatch or wrap this function.
    """
    return None
