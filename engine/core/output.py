from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
from uuid import uuid4

Role = Literal["guest", "free", "pro"]

@dataclass(frozen=True)
class TrackInfo:
    duration_seconds: float
    format: str
    sample_rate_hz: int
    channels: int

def now_rfc3339() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def canonical_output(
    *,
    role: Role,
    track: TrackInfo,
    analysis_id: Optional[str] = None,
    created_at: Optional[str] = None,
    metrics: Optional[Dict[str, Any]] = None,
    events: Optional[Dict[str, Any]] = None,
    warnings: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Canonical analysis output object per ANALYSIS_ENGINE_V1.md / CONTRACTS/analysis_output.md.

    Rules enforced here (minimal):
    - Guest MUST receive events: {} (or omit; we choose {} for stability).
    - Non-guest may include categorized events object (caller responsibility for shape).
    """
    out: Dict[str, Any] = {
        "engine": {"name": "bnk-analysis-engine", "version": "v1"},
        "analysis_id": analysis_id or str(uuid4()),
        "created_at": created_at or now_rfc3339(),
        "role": role,
        "track": {
            "duration_seconds": float(track.duration_seconds),
            "format": str(track.format),
            "sample_rate_hz": int(track.sample_rate_hz),
            "channels": int(track.channels),
        },
        "metrics": metrics or {},
        "warnings": warnings or [],
    }

    if role == "guest":
        out["events"] = {}
    else:
        # If not provided, prefer empty categorized shape later; for now just default empty dict.
        out["events"] = events or {}

    return out