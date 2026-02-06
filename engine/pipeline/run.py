from __future__ import annotations

from typing import Any, Dict, Literal

from engine.core.config import EngineConfig
from engine.core.output import TrackInfo, canonical_output

Role = Literal["guest", "free", "pro"]

def run_analysis_v1(
    *,
    role: Role,
    track: TrackInfo,
    config: EngineConfig | None = None,
) -> Dict[str, Any]:
    """
    v1 pipeline entrypoint.
    This is intentionally a no-op scaffold: returns canonical JSON with empty metrics/events.
    """
    _cfg = config or EngineConfig()
    # NOTE: _cfg currently unused by design; will be used as we implement blocks.
    return canonical_output(role=role, track=track, metrics={}, events={})