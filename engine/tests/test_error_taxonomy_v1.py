from __future__ import annotations

import pytest

from engine.contracts.analysis_output import validate_analysis_output_v1
from engine.core.config import EngineConfig
from engine.core.errors import EngineError
from engine.core.output import TrackInfo
from engine.ingest.types import DecodedAudio
from engine.pipeline.run import run_analysis_v1


def test_unsupported_extension_on_input_path_raises_engine_error(tmp_path):
    p = tmp_path / "x.mp3"
    p.write_bytes(b"not real mp3")

    with pytest.raises(EngineError) as excinfo:
        run_analysis_v1(role="guest", input_path=str(p), config=EngineConfig())

    assert excinfo.value.code == "UNSUPPORTED_INPUT"


def test_bad_call_signature_raises_invalid_input():
    track = TrackInfo(duration_seconds=1.0, format="wav", sample_rate_hz=44100, channels=2)
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=1.0)

    with pytest.raises(EngineError) as excinfo:
        run_analysis_v1(role="guest", track=track, audio=audio, config=EngineConfig())

    assert excinfo.value.code == "INVALID_INPUT"


def test_contract_violation_raises_contract_violation_code():
    with pytest.raises(EngineError) as excinfo:
        validate_analysis_output_v1({})

    assert excinfo.value.code == "CONTRACT_VIOLATION"
