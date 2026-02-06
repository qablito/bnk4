from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest

from engine.core.config import EngineConfig
from engine.core.errors import EngineError
from engine.core.output import TrackInfo
from engine.contracts.analysis_output import ContractViolation
from engine.observability import hooks
from engine.pipeline import run as run_mod
from engine.pipeline.run import run_analysis_v1


def _capture_emit(monkeypatch) -> List[Tuple[str, Dict[str, Any]]]:
    events: List[Tuple[str, Dict[str, Any]]] = []

    def capture(event: str, **payload: Any) -> None:
        events.append((event, payload))

    monkeypatch.setattr(hooks, "emit", capture)
    return events


def test_assert_contract_false_does_not_call_validator(monkeypatch):
    monkeypatch.delenv("BNK_ENGINE_ASSERT_CONTRACT", raising=False)

    def boom(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("validator should not be called")

    monkeypatch.setattr(run_mod, "validate_analysis_output_v1", boom)

    out = run_analysis_v1(
        role="guest",
        track=TrackInfo(duration_seconds=1.0, format="wav", sample_rate_hz=44100, channels=2),
        config=EngineConfig(),
        assert_contract=False,
    )
    assert out["role"] == "guest"


def test_assert_contract_true_bubbles_contract_violation_and_emits_stage_contract(monkeypatch):
    monkeypatch.delenv("BNK_ENGINE_ASSERT_CONTRACT", raising=False)
    events = _capture_emit(monkeypatch)

    def fail(*args: Any, **kwargs: Any) -> None:
        raise ContractViolation("boom", path="$.metrics")

    monkeypatch.setattr(run_mod, "validate_analysis_output_v1", fail)

    with pytest.raises(EngineError) as excinfo:
        run_analysis_v1(
            role="free",
            track=TrackInfo(duration_seconds=1.0, format="wav", sample_rate_hz=44100, channels=2),
            config=EngineConfig(),
            assert_contract=True,
        )

    assert excinfo.value.code == "CONTRACT_VIOLATION"
    failed = [p for e, p in events if e == "analysis_failed"]
    assert any(p.get("error_code") == "CONTRACT_VIOLATION" for p in failed)
    assert any(p.get("stage") == "contract" for p in failed)


def test_assert_contract_env_var_enables_validation(monkeypatch):
    monkeypatch.setenv("BNK_ENGINE_ASSERT_CONTRACT", "1")

    called = {"n": 0}

    def ok(*args: Any, **kwargs: Any) -> None:
        called["n"] += 1
        return None

    monkeypatch.setattr(run_mod, "validate_analysis_output_v1", ok)

    out = run_analysis_v1(
        role="guest",
        track=TrackInfo(duration_seconds=1.0, format="wav", sample_rate_hz=44100, channels=2),
        config=EngineConfig(),
        assert_contract=False,
    )
    assert out["role"] == "guest"
    assert called["n"] == 1

