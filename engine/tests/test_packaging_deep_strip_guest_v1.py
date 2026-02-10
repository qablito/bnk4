from engine.packaging.package_output_v1 import package_output_v1


def test_guest_metrics_deep_strip_confidence_and_evidence():
    out = {
        "engine": {"name": "bnk-analysis-engine", "version": "v1"},
        "analysis_id": "00000000-0000-0000-0000-000000000000",
        "created_at": "2026-02-07T00:00:00Z",
        "role": "guest",
        "track": {},
        "warnings": [],
        "events": {},
        "metrics": {
            "bpm": {
                "value": {"value_rounded": 70, "value_exact": 69.8, "confidence": 0.12},
                "confidence": 0.99,
                "evidence": {"foo": "bar"},
                "bpm_raw": 69.8,
                "bpm_raw_confidence": "high",
                "bpm_reportable": 140,
                "bpm_reportable_confidence": "medium",
                "timefeel": "double_time_preferred",
                "bpm_reason_codes": ["prefer_double_time_from_raw"],
                "bpm_candidates": [
                    {"candidate_bpm": 70, "candidate_family": "half", "candidate_score": 0.9}
                ],
                "candidates": [{"rank": 1, "value": 70}],
            },
            "key_mode": {
                "value": "F#",
                "mode": "minor",
                "confidence": 0.88,
                "candidates": [{"rank": 1, "value": "F# minor"}],
                "reason_codes": ["emit_confident"],
            },
        },
    }

    packaged = package_output_v1(out, role="guest")
    bpm = packaged["metrics"]["bpm"]
    km = packaged["metrics"]["key_mode"]

    # Deep stripped everywhere
    assert "confidence" not in bpm
    assert "evidence" not in bpm
    assert "bpm_raw" not in bpm
    assert "bpm_raw_confidence" not in bpm
    assert "bpm_reportable" not in bpm
    assert "bpm_reportable_confidence" not in bpm
    assert "timefeel" not in bpm
    assert "bpm_reason_codes" not in bpm
    assert "bpm_candidates" not in bpm
    assert "confidence" not in bpm.get("value", {})
    assert "confidence" not in km
    assert "confidence" not in km.get("value", {})

    # Explicit rule
    assert "value_exact" not in bpm.get("value", {})

    # BPM candidates preserved, key candidates stripped for guest minimal contract.
    assert bpm.get("candidates") == [{"rank": 1, "value": 70}]
    assert "candidates" not in km
    assert "reason_codes" not in km
