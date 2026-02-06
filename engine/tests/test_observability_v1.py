from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest

from engine.core.config import EngineConfig
from engine.core.errors import EngineError
from engine.core.output import TrackInfo
from engine.ingest.types import DecodedAudio
from engine.observability import hooks
from engine.pipeline.run import run_analysis_v1


def test_emits_started_and_completed_on_success(monkeypatch):
    events: List[Tuple[str, Dict[str, Any]]] = []

    def capture(event: str, **payload: Any) -> None:
        events.append((event, payload))

    monkeypatch.setattr(hooks, "emit", capture)

    out = run_analysis_v1(
        role="guest",
        track=TrackInfo(duration_seconds=1.0, format="wav", sample_rate_hz=44100, channels=2),
        config=EngineConfig(),
    )
    assert out["role"] == "guest"

    names = [e for e, _ in events]
    assert "analysis_started" in names
    assert "analysis_completed" in names
    assert names.index("analysis_started") < names.index("analysis_completed")


def test_emits_failed_with_error_code_on_engine_error(monkeypatch):
    events: List[Tuple[str, Dict[str, Any]]] = []

    def capture(event: str, **payload: Any) -> None:
        events.append((event, payload))

    monkeypatch.setattr(hooks, "emit", capture)

    track = TrackInfo(duration_seconds=1.0, format="wav", sample_rate_hz=44100, channels=2)
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=1.0)

    with pytest.raises(EngineError) as excinfo:
        run_analysis_v1(role="guest", track=track, audio=audio, config=EngineConfig())

    assert excinfo.value.code == "INVALID_INPUT"
    assert any(e == "analysis_failed" and p.get("error_code") == "INVALID_INPUT" for e, p in events)


def test_emits_feature_omitted_when_below_threshold(monkeypatch):
    events: List[Tuple[str, Dict[str, Any]]] = []

    def capture(event: str, **payload: Any) -> None:
        events.append((event, payload))

    monkeypatch.setattr(hooks, "emit", capture)

    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=10.0)
    out = run_analysis_v1(audio, "free", config=EngineConfig())
    assert out["role"] == "free"

    omitted = [p for e, p in events if e == "feature_omitted"]
    omitted_features = {p.get("feature") for p in omitted}
    assert "bpm" in omitted_features
    assert "key_mode" in omitted_features
    assert all(p.get("reason") == "confidence_below_threshold" for p in omitted)

