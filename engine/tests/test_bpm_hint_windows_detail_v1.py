from __future__ import annotations

import wave
from array import array
from pathlib import Path

from engine.preprocess.bpm_hint_windows_v1 import (
    compute_bpm_hint_window_details_from_wav_v1,
    compute_bpm_hint_windows_from_wav_v1,
)


def _write_click_track_wav(
    path: Path,
    *,
    bpm: float,
    duration_s: float,
    sample_rate_hz: int = 44100,
    subdivide: bool = False,
    subdivide_ratio: float = 0.20,
) -> None:
    n = int(round(duration_s * float(sample_rate_hz)))
    buf = array("h", [0] * n)

    period_s = 60.0 / float(bpm)
    click_len = int(0.005 * sample_rate_hz)  # 5ms click
    amp = 20000

    t = 0.0
    while t < duration_s:
        i0 = int(round(t * sample_rate_hz))
        for j in range(click_len):
            k = i0 + j
            if k >= n:
                break
            buf[k] = amp
        if subdivide:
            i1 = int(round((t + (period_s * 0.5)) * sample_rate_hz))
            for j in range(click_len):
                k = i1 + j
                if k >= n:
                    break
                buf[k] = int(amp * float(subdivide_ratio))
        t += period_s

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate_hz)
        wf.writeframes(buf.tobytes())


def test_bpm_hint_windows_preserve_double_candidate_without_hard_switch(tmp_path: Path) -> None:
    """
    We must not hard-switch to double-time in preprocessing.

    If the double-time candidate is strong, we still include best_bpm (raw) and may
    include double_bpm as an additional hint.
    """
    p = tmp_path / "click_85.wav"
    _write_click_track_wav(p, bpm=85.0, duration_s=40.0, subdivide=True, subdivide_ratio=0.20)

    details = compute_bpm_hint_window_details_from_wav_v1(p)
    assert details, "expected window details for non-trivial audio"
    assert any(d.get("double_bpm") is not None for d in details)

    hints = compute_bpm_hint_windows_from_wav_v1(p, double_tempo_alpha=0.04)
    assert hints, "expected flattened hints"

    # We always include best_bpm; previously code could return only double_bpm.
    assert any(abs(h - 85.0) <= 2.0 for h in hints)
    assert any(abs(h - 170.0) <= 10.0 for h in hints)


def test_bpm_hint_windows_do_not_force_double_when_threshold_high(tmp_path: Path) -> None:
    p = tmp_path / "click_97.wav"
    _write_click_track_wav(p, bpm=97.0, duration_s=40.0)

    hints = compute_bpm_hint_windows_from_wav_v1(p, double_tempo_alpha=0.99)
    assert hints
    assert any(abs(h - 97.0) <= 2.0 for h in hints)
    assert not any(abs(h - 194.0) <= 2.0 for h in hints)
