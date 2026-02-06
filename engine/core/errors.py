from __future__ import annotations

from typing import Any, Dict, Literal, Optional

ErrorCode = Literal[
    "INVALID_INPUT",
    "UNSUPPORTED_INPUT",
    "CONTRACT_VIOLATION",
    "INTERNAL_ERROR",
]


class EngineError(Exception):
    """
    Stable, code-addressable error for Engine v1.

    - code: stable string for programmatic handling
    - message: concise, non-sensitive summary
    - context: optional structured metadata (must be safe to log)
    """

    def __init__(self, *, code: ErrorCode, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code: str = str(code)
        self.message: str = str(message)
        self.context: Optional[Dict[str, Any]] = context or None


def raise_engine_error(code: ErrorCode, message: str, **context: Any) -> None:
    raise EngineError(code=code, message=message, context=context or None)

