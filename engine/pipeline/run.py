from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
from uuid import uuid4

from engine.core.config import EngineConfig
from engine.core.output import TrackInfo

Role = Literal["guest", "free", "pro"]

def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def run_analysis_v1(
    audio_or_track: Optional[Any] = None,
    role: Optional[Role] = None,
    *,
    track: Optional[TrackInfo] = None,
    audio: Optional[Any] = None,
    config: Optional[EngineConfig] = None,
    analysis_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Engine v1 contract-first runner.

    Supported call styles:
      A) Keyword style (preferred):
         run_analysis_v1(role="guest", track=TrackInfo(...))
         run_analysis_v1(role="guest", audio=decoded_audio)

      B) Back-compat positional style (used by tests):
         run_analysis_v1(decoded_audio, "guest", config=...)

    Exactly one of (track, audio) must be provided after normalization.
    """

    # --- Normalize positional style ---
    if audio is None and track is None and audio_or_track is not None:
        # Positional first argument is treated as audio unless caller also gave track/audio explicitly.
        audio = audio_or_track

    if role is None:
        raise TypeError("run_analysis_v1 requires role (e.g. 'guest'|'free'|'pro')")

    # --- Validate exactly one input source ---
    if (track is None and audio is None) or (track is not None and audio is not None):
        raise TypeError("run_analysis_v1 requires exactly one of: track=... or audio=...")

    _ = config or EngineConfig()
    aid = analysis_id or str(uuid4())

    if track is None:
        # Best-effort extraction from decoded audio object
        fmt = getattr(audio, "format", "unknown")
        track = TrackInfo(
            duration_seconds=float(getattr(audio, "duration_seconds")),
            format=str(fmt) if fmt else "unknown",
            sample_rate_hz=int(getattr(audio, "sample_rate_hz")),
            channels=int(getattr(audio, "channels")),
        )

    out: Dict[str, Any] = {
        "engine": {"name": "bnk-analysis-engine", "version": "v1"},
        "analysis_id": aid,
        "created_at": _now_rfc3339(),
        "role": role,
        "track": asdict(track),
        "metrics": {},
        "warnings": [],
    }

    # Events gating per spec: guest gets {} (or omit). We'll keep {} for stability.
    if role == "guest":
        out["events"] = {}
    else:
        out["events"] = {
            "clipping": {"sample_clipping_ranges": [], "true_peak_exceedance_ranges": []},
            "stereo": {"stereo_issue_ranges": []},
            "tonality": {"tonal_drift_ranges": []},
            "noise": {"noise_change_ranges": []},
        }

    return out
