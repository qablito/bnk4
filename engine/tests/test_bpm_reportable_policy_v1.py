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


def test_reportable_policy_no_direct_double_evidence_keeps_raw_for_stable_under_95():
    """
    Drill-like case: raw is stable (~71) but human-reportable is typically 2x.

    Policy should NOT emit a doubled reportable when direct 2x evidence is absent.
    """
    cfg = EngineConfig()
    out = extract_bpm_v1(_ctx(duration_seconds=60.0, windows=[71.4] * 16), config=cfg)
    assert out is not None

    assert out.get("bpm_raw") == 71.4
    assert out.get("bpm_raw_confidence") == "high"

    assert out.get("bpm_reportable") == 71
    assert out.get("bpm_reportable_confidence") == "high"
    assert out.get("timefeel") == "normal"
    assert out.get("bpm_reason_codes") == [
        "no_direct_double_evidence",
        "prefer_raw",
    ]

    # Back-compat: bpm.value aligns with reportable.
    assert out.get("value", {}).get("value_rounded") == 71
    assert out.get("confidence") == "high"


def test_reportable_policy_extract_keeps_raw_when_double_evidence_is_not_direct():
    cfg = EngineConfig()
    out = extract_bpm_v1(
        _ctx(duration_seconds=60.0, windows=[69.0] * 16 + [138.0] * 4),
        config=cfg,
    )
    assert out is not None

    assert out.get("bpm_reportable") == out.get("bpm_raw")
    assert out.get("timefeel") == "normal"
    assert out.get("bpm_reason_codes") == ["no_direct_double_evidence", "prefer_raw"]


def test_reportable_policy_does_not_force_double_over_raw_max():
    cfg = EngineConfig()
    out = extract_bpm_v1(_ctx(duration_seconds=60.0, windows=[97.0] * 16), config=cfg)
    assert out is not None

    assert out.get("bpm_raw") == 97
    assert out.get("bpm_reportable") == 97
    assert out.get("timefeel") == "normal"
    assert out.get("value", {}).get("value_rounded") == 97

    assert out.get("bpm_reason_codes") == ["prefer_raw", "capped_by_raw_max"]


def test_reportable_policy_prefers_emit_within_1_over_omit():
    """
    When the chosen reportable BPM is within +/-1 of a candidate and the selection
    is otherwise safe, prefer emitting a value rather than omitting.
    """
    cfg = EngineConfig()
    # Function-level policy check with direct evidence available.
    from engine.features import bpm_v1

    reportable, conf, _timefeel, codes = bpm_v1._select_reportable_bpm_from_raw_v1(
        raw_bpm_exact=71.0,
        raw_bpm_rounded=71,
        raw_confidence="high",
        raw_stability=0.90,
        scored=[(71, 0.9), (142, 0.35), (105, 0.05)],
        tol_bpm=1,
        config=cfg,
        double_window_support=0.25,
    )
    assert reportable == 142
    assert conf == "high"
    assert "prefer_emit_within_1" in codes


def test_reportable_omission_keeps_advanced_reason_codes_and_candidates():
    cfg = EngineConfig()
    out = extract_bpm_v1(
        _ctx(duration_seconds=60.0, windows=[70.0] * 12 + [130.0] * 9 + [140.0] * 3),
        config=cfg,
    )
    assert out is not None
    assert out.get("bpm_reportable") is None
    assert out.get("confidence") == "low"
    assert "value" not in out
    codes = out.get("bpm_reason_codes") or []
    assert isinstance(codes, list)
    assert any(str(code).startswith("omitted_") for code in codes)
    assert isinstance(out.get("bpm_candidates"), list)
    assert len(out["bpm_candidates"]) >= 1
