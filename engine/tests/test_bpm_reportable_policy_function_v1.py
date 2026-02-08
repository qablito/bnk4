from __future__ import annotations

from engine.core.config import EngineConfig
from engine.features import bpm_v1


def test_select_reportable_from_raw_prefers_double_time_when_safe():
    cfg = EngineConfig()
    reportable, conf, timefeel, codes = bpm_v1._select_reportable_bpm_from_raw_v1(
        raw_bpm_exact=71.4,
        raw_bpm_rounded=71,
        raw_confidence="high",
        raw_stability=0.80,
        scored=[(71, 1.0), (70, 0.97), (72, 0.97), (142, 0.0)],
        tol_bpm=1,
        config=cfg,
    )

    assert reportable == 143
    assert conf == "medium"
    assert timefeel == "double_time_preferred"
    assert "prefer_double_time_from_raw" in codes
    assert "prefer_emit_within_1" in codes


def test_select_reportable_from_raw_omits_when_runnerup_is_strong_unrelated():
    cfg = EngineConfig()
    reportable, conf, timefeel, codes = bpm_v1._select_reportable_bpm_from_raw_v1(
        raw_bpm_exact=70.0,
        raw_bpm_rounded=70,
        raw_confidence="high",
        raw_stability=0.90,
        scored=[(70, 0.8), (140, 0.75), (105, 0.40)],
        tol_bpm=1,
        config=cfg,
    )

    assert reportable is None
    assert conf == "low"
    assert timefeel == "unknown"
    assert "ambiguous_runner_up" in codes
    assert "omitted_low_confidence" in codes


def test_select_reportable_from_raw_does_not_double_over_raw_max():
    cfg = EngineConfig()
    reportable, conf, timefeel, codes = bpm_v1._select_reportable_bpm_from_raw_v1(
        raw_bpm_exact=97.0,
        raw_bpm_rounded=97,
        raw_confidence="high",
        raw_stability=0.95,
        scored=[(97, 1.0), (98, 0.97), (194, 0.2)],
        tol_bpm=1,
        config=cfg,
    )

    assert reportable == 97
    assert conf == "high"
    assert timefeel == "normal"
    assert ("capped_by_raw_max" in codes) or ("prefer_raw" in codes)
