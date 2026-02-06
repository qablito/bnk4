from pathlib import Path

import pytest

from engine.ingest.ingest import IngestLimits, ingest_v1


def test_ingest_bytes_respects_max_bytes():
    with pytest.raises(ValueError):
        ingest_v1(b"x" * 11, limits=IngestLimits(max_bytes=10))


def test_ingest_path_guesses_format(tmp_path: Path):
    p = tmp_path / "beat.wav"
    p.write_bytes(b"RIFFxxxxWAVE")  # not a real wav, but enough for size+suffix
    audio = ingest_v1(str(p), limits=IngestLimits(max_bytes=10_000))
    assert audio.format == "wav"
