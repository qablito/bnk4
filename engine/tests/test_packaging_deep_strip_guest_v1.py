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
                "candidates": [{"rank": 1, "value": 70}],
            },
            "key_mode": {
                "value": {"tonic": "F#", "mode": "minor", "confidence": 0.3},
                "confidence": 0.88,
                "candidates": [{"rank": 1, "value": "F# minor"}],
            },
        },
    }

    packaged = package_output_v1(out, role="guest")
    bpm = packaged["metrics"]["bpm"]
    km = packaged["metrics"]["key_mode"]

    # Deep stripped everywhere
    assert "confidence" not in bpm
    assert "evidence" not in bpm
    assert "confidence" not in bpm.get("value", {})
    assert "confidence" not in km
    assert "confidence" not in km.get("value", {})

    # Explicit rule
    assert "value_exact" not in bpm.get("value", {})

    # Candidates preserved
    assert bpm.get("candidates") == [{"rank": 1, "value": 70}]
    assert km.get("candidates") == [{"rank": 1, "value": "F# minor"}]
