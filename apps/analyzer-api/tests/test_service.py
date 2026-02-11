from __future__ import annotations

from pathlib import Path

import pytest
from service import list_samples, parse_sample_id_payload, resolve_sample_path


def test_resolve_sample_path_rejects_path_traversal(tmp_path: Path) -> None:
    audio_root = tmp_path / "audiosToTest"
    audio_root.mkdir(parents=True)

    with pytest.raises(ValueError, match="outside audio root"):
        resolve_sample_path(audio_root, "../secrets.wav")


def test_list_samples_returns_stable_rel_path_ids(tmp_path: Path) -> None:
    audio_root = tmp_path / "audiosToTest"
    (audio_root / "trap").mkdir(parents=True)

    first = audio_root / "trap" / "alpha.mp3"
    second = audio_root / "beta.wav"
    ignored = audio_root / "notes.txt"

    first.write_bytes(b"123")
    second.write_bytes(b"4567")
    ignored.write_text("skip me")

    out = list_samples(audio_root)
    assert out == [
        {
            "sample_id": "beta.wav",
            "filename": "beta.wav",
            "rel_path": "beta.wav",
            "size_bytes": 4,
        },
        {
            "sample_id": "trap/alpha.mp3",
            "filename": "alpha.mp3",
            "rel_path": "trap/alpha.mp3",
            "size_bytes": 3,
        },
    ]


def test_parse_sample_id_payload_accepts_nested_and_flat_shapes() -> None:
    nested = parse_sample_id_payload(
        {
            "role": "free",
            "input": {"kind": "sample_id", "sample_id": "trap/alpha.mp3"},
        }
    )
    assert nested == ("free", "trap/alpha.mp3")

    flat = parse_sample_id_payload({"role": "pro", "sample_id": "beta.wav"})
    assert flat == ("pro", "beta.wav")
