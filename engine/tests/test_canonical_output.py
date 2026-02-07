from engine.core.output import TrackInfo
from engine.pipeline.run import run_analysis_v1


def test_guest_has_empty_events_object():
    out = run_analysis_v1(
        role="guest",
        track=TrackInfo(duration_seconds=1.0, format="wav", sample_rate_hz=44100, channels=2),
    )
    assert out["role"] == "guest"
    assert "events" in out
    assert out["events"] == {}


def test_free_allows_events_key_present():
    out = run_analysis_v1(
        role="free",
        track=TrackInfo(duration_seconds=1.0, format="wav", sample_rate_hz=44100, channels=2),
    )
    assert out["role"] == "free"
    assert "events" in out
    assert isinstance(out["events"], dict)


def test_required_top_level_keys_exist():
    out = run_analysis_v1(
        role="guest",
        track=TrackInfo(duration_seconds=1.0, format="wav", sample_rate_hz=44100, channels=1),
    )
    for k in (
        "engine",
        "analysis_id",
        "created_at",
        "role",
        "track",
        "metrics",
        "events",
        "warnings",
    ):
        assert k in out
