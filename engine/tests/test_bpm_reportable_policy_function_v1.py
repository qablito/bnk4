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
        double_window_support=0.0,
    )

    assert reportable == 71
    assert conf == "high"
    assert timefeel == "normal"
    assert codes == [
        "no_direct_double_evidence",
        "prefer_raw",
    ]


def test_select_reportable_from_raw_omits_when_runnerup_is_strong_unrelated():
    cfg = EngineConfig()
    reportable, conf, timefeel, codes = bpm_v1._select_reportable_bpm_from_raw_v1(
        raw_bpm_exact=70.0,
        raw_bpm_rounded=70,
        raw_confidence="high",
        raw_stability=0.90,
        scored=[(70, 0.8), (140, 0.75), (130, 0.40)],
        tol_bpm=1,
        config=cfg,
        double_window_support=0.0,
    )

    assert reportable is None
    assert conf == "low"
    assert timefeel == "unknown"
    assert codes == [
        "omitted_ambiguous_runnerup",
        "omitted_low_confidence",
        "has_direct_double_evidence",
    ]


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
        double_window_support=0.0,
    )

    assert reportable == 97
    assert conf == "high"
    assert timefeel == "normal"
    assert codes == ["prefer_raw", "capped_by_raw_max"]


def test_select_reportable_from_raw_marks_direct_double_evidence_when_supported():
    cfg = EngineConfig()
    reportable, conf, timefeel, codes = bpm_v1._select_reportable_bpm_from_raw_v1(
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
    assert timefeel == "double_time_preferred"
    assert codes == [
        "prefer_double_time_from_raw",
        "has_direct_double_evidence",
        "prefer_emit_within_1",
    ]


def test_select_reportable_from_raw_no_direct_double_evidence_blocks_flip_reggaeton_like():
    cfg = EngineConfig()
    reportable, conf, timefeel, codes = bpm_v1._select_reportable_bpm_from_raw_v1(
        raw_bpm_exact=88.0,
        raw_bpm_rounded=88,
        raw_confidence="high",
        raw_stability=0.95,
        scored=[(88, 0.95), (176, 0.05), (118, 0.03)],
        tol_bpm=1,
        config=cfg,
        double_window_support=0.0,
    )

    assert reportable == 88
    assert conf == "high"
    assert timefeel == "normal"
    assert codes == [
        "no_direct_double_evidence",
        "prefer_raw",
    ]


def test_select_reportable_from_raw_marks_capped_by_reportable_range():
    cfg = EngineConfig()
    reportable, conf, timefeel, codes = bpm_v1._select_reportable_bpm_from_raw_v1(
        raw_bpm_exact=59.0,
        raw_bpm_rounded=59,
        raw_confidence="high",
        raw_stability=0.99,
        scored=[(59, 0.9), (118, 0.2), (88, 0.1)],
        tol_bpm=1,
        config=cfg,
        double_window_support=0.0,
    )

    assert reportable == 59
    assert conf == "high"
    assert timefeel == "normal"
    assert codes == ["prefer_raw", "capped_by_reportable_range"]
