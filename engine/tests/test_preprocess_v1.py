import pytest

from engine.core.config import EngineConfig
from engine.ingest.types import DecodedAudio
from engine.preprocess.preprocess_v1 import preprocess_v1


def test_preprocess_v1_sets_layout_and_internal_sr():
    cfg = EngineConfig()
    audio = DecodedAudio(sample_rate_hz=48000, channels=2, duration_seconds=10.0)
    pre = preprocess_v1(audio, config=cfg)

    assert pre.layout == "stereo"
    assert pre.internal_sample_rate_hz == cfg.tunables.INTERNAL_SAMPLE_RATE_HZ
    assert pre.channels == 2
    assert pre.duration_seconds == 10.0


def test_preprocess_v1_rejects_invalid_channels():
    cfg = EngineConfig()
    audio = DecodedAudio(sample_rate_hz=44100, channels=3, duration_seconds=10.0)
    with pytest.raises(ValueError):
        preprocess_v1(audio, config=cfg)
