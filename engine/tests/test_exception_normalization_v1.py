from __future__ import annotations

from typing import Any

import pytest

from engine.core.config import EngineConfig
from engine.core.errors import EngineError
from engine.core.output import TrackInfo
from engine.observability import hooks
from engine.pipeline import run as run_mod
from engine.pipeline.run import run_analysis_v1


def _capture_emit(monkeypatch) -> list[tuple[str, dict[str, Any]]]:
    events: list[tuple[str, dict[str, Any]]] = []

    def capture(event: str, **payload: Any) -> None:
        events.append((event, payload))

    monkeypatch.setattr(hooks, "emit", capture)
    return events


def test_invalid_input_emits_failed_with_invalid_input(monkeypatch):
    events = _capture_emit(monkeypatch)

    with pytest.raises(EngineError) as excinfo:
        run_analysis_v1(role="guest", config=EngineConfig())

    assert excinfo.value.code == "INVALID_INPUT"
    failed = [p for e, p in events if e == "analysis_failed"]
    assert any(p.get("error_code") == "INVALID_INPUT" for p in failed)
    assert any(p.get("stage") == "validate" for p in failed)


def test_ingest_unsupported_extension_emits_failed_with_unsupported_input(tmp_path, monkeypatch):
    events = _capture_emit(monkeypatch)
    p = tmp_path / "x.mp3"
    p.write_bytes(b"nope")

    with pytest.raises(EngineError) as excinfo:
        run_analysis_v1(role="guest", input_path=str(p), config=EngineConfig())

    assert excinfo.value.code == "UNSUPPORTED_INPUT"
    failed = [p for e, p in events if e == "analysis_failed"]
    assert any(p.get("error_code") == "UNSUPPORTED_INPUT" for p in failed)
    assert any(p.get("stage") == "ingest" for p in failed)
    assert any(p.get("analysis_id") for p in failed)


def test_packaging_failure_wrapped_as_internal_error(monkeypatch):
    events = _capture_emit(monkeypatch)

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("packaging exploded")

    monkeypatch.setattr(run_mod, "package_output_v1", boom)

    with pytest.raises(EngineError) as excinfo:
        run_analysis_v1(
            role="free",
            track=TrackInfo(duration_seconds=1.0, format="wav", sample_rate_hz=44100, channels=2),
            config=EngineConfig(),
        )

    assert excinfo.value.code == "INTERNAL_ERROR"
    failed = [p for e, p in events if e == "analysis_failed"]
    assert any(p.get("error_code") == "INTERNAL_ERROR" for p in failed)
    assert any(p.get("stage") == "packaging" for p in failed)
