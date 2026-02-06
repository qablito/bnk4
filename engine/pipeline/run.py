from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
from uuid import uuid4

from engine.core.config import EngineConfig
from engine.core.output import TrackInfo

from engine.preprocess.preprocess_v1 import preprocess_v1
from engine.features.types import FeatureContext
from engine.features.bpm_v1 import extract_bpm_v1
from engine.features.key_mode_v1 import extract_key_mode_v1

from pathlib import Path
from engine.ingest.decode_wav_v1 import decode_wav_v1

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
    _test_overrides: Optional[Dict[str, Any]] = None,
    input_path: Optional[str] = None,
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
    if audio is None and track is None and audio_or_track is not None and input_path is None:
        # If caller passed a path-like, treat it as input_path (not audio).
        if isinstance(audio_or_track, (str, Path)):
            input_path = str(audio_or_track)
        else:
            audio = audio_or_track

    # --- Validate exactly one input source (track, audio, input_path) ---
    provided = [track is not None, audio is not None, input_path is not None]
    if sum(provided) != 1:
        raise TypeError("run_analysis_v1 requires exactly one of: track=..., audio=..., input_path=...")
    
    # --- Normalize input_path -> audio (v1: WAV only via stdlib ingest) ---
    if input_path is not None:
        p = Path(input_path)
        if p.suffix.lower() != ".wav":
            raise ValueError("v1 input_path only supports .wav")
        audio = decode_wav_v1(p)
        input_path = None

    cfg = config or EngineConfig()
    aid = analysis_id or str(uuid4())

    if input_path is not None:
        audio = decode_wav_v1(Path(input_path))

    # If caller provided only audio, derive TrackInfo best-effort
    if track is None:
        fmt = getattr(audio, "format", "unknown")
        track = TrackInfo(
            duration_seconds=float(getattr(audio, "duration_seconds")),
            format=str(fmt) if fmt else "unknown",
            sample_rate_hz=int(getattr(audio, "sample_rate_hz")),
            channels=int(getattr(audio, "channels")),
        )

    # Preprocess only if we have audio (track-only path has no audio payload)
    pre = None
    if audio is not None:
        pre = preprocess_v1(audio, config=cfg)

    out: Dict[str, Any] = {
        "engine": {"name": "bnk-analysis-engine", "version": "v1"},
        "analysis_id": aid,
        "created_at": _now_rfc3339(),
        "role": role,
        "track": asdict(track),
        "metrics": {},
        "warnings": [],
    }
    metrics: Dict[str, Any] = out["metrics"]

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

    # Feature extraction only if we actually have preprocessed audio
    if pre is not None:
        ctx = FeatureContext(
            audio=pre,
            has_rhythm_evidence=True,
            has_tonal_evidence=True,
            bpm_hint_exact=None,
            key_mode_hint=None,
        )

        # --- test overrides (3.5) ---
        if _test_overrides:
            ctx = FeatureContext(
                audio=ctx.audio,
                has_rhythm_evidence=_test_overrides.get("has_rhythm_evidence", ctx.has_rhythm_evidence),
                has_tonal_evidence=_test_overrides.get("has_tonal_evidence", ctx.has_tonal_evidence),
                bpm_hint_exact=_test_overrides.get("bpm_hint_exact", ctx.bpm_hint_exact),
                key_mode_hint=_test_overrides.get("key_mode_hint", ctx.key_mode_hint),
            )

        bpm_block = extract_bpm_v1(ctx, config=cfg)
        key_mode_block = extract_key_mode_v1(ctx, config=cfg)

        # Guest: do not expose value_exact
        if role == "guest" and bpm_block is not None:
            bpm_block = dict(bpm_block)
            bpm_val = dict(bpm_block.get("value", {}))
            bpm_val.pop("value_exact", None)
            bpm_block["value"] = bpm_val

        if bpm_block is not None:
            metrics["bpm"] = bpm_block
        if key_mode_block is not None:
            metrics["key_mode"] = key_mode_block

    return out