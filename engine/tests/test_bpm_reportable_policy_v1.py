from __future__ import annotations

from engine.core.config import EngineConfig
from engine.features.bpm_v1 import extract_bpm_v1
from engine.features.types import FeatureContext
from engine.preprocess.preprocess_v1 import PreprocessedAudio


def _ctx(*, duration_seconds: float, windows: list[float]) -> FeatureContext:
    pre = PreprocessedAudio(
        internal_sample_rate_hz=44100,
        channels=2,
        duration_seconds=duration_seconds,
        layout="stereo",
    )
    return FeatureContext(
        audio=pre,
        has_rhythm_evidence=True,
        bpm_hint_windows=windows,
    )


def test_reportable_policy_prefers_double_time_for_stable_raw_under_95():
    """
    Drill-like case: raw is stable (~71) but human-reportable is typically 2x.

    Policy should emit reportable ~= 2x raw with confidence capped to medium when
    there is no direct 2x evidence.
    """
    cfg = EngineConfig()
    out = extract_bpm_v1(_ctx(duration_seconds=60.0, windows=[71.4] * 16), config=cfg)
    assert out is not None

    assert out.get("bpm_raw") == 71.4
    assert out.get("bpm_raw_confidence") == "high"

    assert out.get("bpm_reportable") == 143
    assert out.get("bpm_reportable_confidence") == "medium"
    assert out.get("timefeel") == "double_time_preferred"
    assert "prefer_double_time_from_raw" in (out.get("bpm_reason_codes") or [])

    # Back-compat: bpm.value aligns with reportable.
    assert out.get("value", {}).get("value_rounded") == 143
    assert out.get("confidence") == "medium"


def test_reportable_policy_does_not_force_double_over_raw_max():
    cfg = EngineConfig()
    out = extract_bpm_v1(_ctx(duration_seconds=60.0, windows=[97.0] * 16), config=cfg)
    assert out is not None

    assert out.get("bpm_raw") == 97
    assert out.get("bpm_reportable") == 97
    assert out.get("timefeel") == "normal"
    assert out.get("value", {}).get("value_rounded") == 97

    codes = out.get("bpm_reason_codes") or []
    assert ("capped_by_raw_max" in codes) or ("prefer_raw" in codes)


def test_reportable_policy_prefers_emit_within_1_over_omit():
    """
    When the chosen reportable BPM is within +/-1 of a candidate and the selection
    is otherwise safe, prefer emitting a value rather than omitting.
    """
    cfg = EngineConfig()
    out = extract_bpm_v1(_ctx(duration_seconds=60.0, windows=[71.4] * 16), config=cfg)
    assert out is not None
    assert out.get("bpm_reportable") in (142, 143)
    assert out.get("bpm_reportable_confidence") != "low"

    codes = out.get("bpm_reason_codes") or []
    assert "prefer_emit_within_1" in codes
