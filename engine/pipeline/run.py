from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
from uuid import uuid4

from engine.core.config import EngineConfig
from engine.core.errors import EngineError
from engine.core.output import TrackInfo

from engine.preprocess.preprocess_v1 import preprocess_v1
from engine.features.types import FeatureContext
from engine.features.bpm_v1 import extract_bpm_v1
from engine.features.key_mode_v1 import extract_key_mode_v1

from engine.packaging.package_output_v1 import package_output_v1

from engine.observability import hooks

from pathlib import Path
from engine.ingest.ingest_v1 import decode_input_path_v1

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
    current_stage = "validate"
    aid: Optional[str] = None
    try:
        if role is None:
            raise EngineError(code="INVALID_INPUT", message="role is required")

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
            raise EngineError(
                code="INVALID_INPUT",
                message="Exactly one input source is required",
                context={"provided_track": track is not None, "provided_audio": audio is not None, "provided_input_path": input_path is not None},
            )

        cfg = config or EngineConfig()
        aid = analysis_id or str(uuid4())

        current_stage = "ingest"
        hooks.emit(
            "analysis_started",
            analysis_id=aid,
            role=role,
            engine_version="v1",
            stage=current_stage,
        )

        # --- Normalize input_path -> audio (v1: WAV only via stdlib ingest) ---
        if input_path is not None:
            audio = decode_input_path_v1(Path(input_path))
            input_path = None

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
            try:
                current_stage = "preprocess"
                pre = preprocess_v1(audio, config=cfg)
            except ValueError as exc:
                raise EngineError(code="INVALID_INPUT", message="Invalid input", context={"stage": "preprocess_v1"}) from exc

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

            current_stage = "feature:bpm"
            bpm_block = extract_bpm_v1(ctx, config=cfg)
            current_stage = "feature:key_mode"
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

        # Final v1 packaging step (role gating).
        current_stage = "packaging"
        packaged = package_output_v1(out, role=role)
        hooks.emit(
            "analysis_completed",
            analysis_id=aid,
            role=role,
            engine_version="v1",
            stage=current_stage,
        )
        return packaged
    except EngineError as exc:
        hooks.emit(
            "analysis_failed",
            analysis_id=aid,
            role=role,
            engine_version="v1",
            stage=current_stage,
            error_code=exc.code,
        )
        raise
    except Exception as exc:
        err = EngineError(code="INTERNAL_ERROR", message="Internal error", context={"stage": "run_analysis_v1"})
        hooks.emit(
            "analysis_failed",
            analysis_id=aid,
            role=role,
            engine_version="v1",
            stage=current_stage,
            error_code=err.code,
        )
        raise err from exc
