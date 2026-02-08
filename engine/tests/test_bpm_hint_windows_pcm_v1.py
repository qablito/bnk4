from __future__ import annotations

import wave
from array import array
from pathlib import Path

from engine.core.config import EngineConfig
from engine.ingest.ingest_v1 import decode_input_path_v1
from engine.pipeline.run import run_analysis_v1


def _write_click_track_wav(
    path: Path,
    *,
    bpm: float,
    duration_s: float,
    sample_rate_hz: int = 44100,
    channels: int = 1,
    subdivide: bool = False,
    subdivide_ratio: float = 0.55,
) -> None:
    assert channels in (1, 2)
    n = int(round(duration_s * sample_rate_hz))
    data = array("h", [0]) * (n * channels)

    period_s = 60.0 / float(bpm)
    click_len = int(0.005 * sample_rate_hz)  # 5ms click
    amp = 20000

    def write_click(at_s: float, *, amp_i: int) -> None:
        i0 = int(round(at_s * sample_rate_hz))
        for j in range(click_len):
            idx = i0 + j
            if idx >= n:
                break
            if channels == 1:
                data[idx] = amp_i
            else:
                base = idx * 2
                data[base] = amp_i
                data[base + 1] = amp_i

    t = 0.0
    while t < duration_s:
        write_click(t, amp_i=amp)
        if subdivide:
            # Add a weaker subdivision click halfway through the beat.
            write_click(t + (period_s * 0.5), amp_i=int(amp * float(subdivide_ratio)))
        t += period_s

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate_hz)
        wf.writeframes(data.tobytes())


def _write_two_tempo_click_track_wav(
    path: Path,
    *,
    bpm_a: float,
    bpm_b: float,
    duration_s: float,
    sample_rate_hz: int = 44100,
    channels: int = 1,
) -> None:
    half = duration_s / 2.0
    assert half > 0

    n = int(round(duration_s * sample_rate_hz))
    data = array("h", [0]) * (n * channels)

    def write_clicks(start_s: float, end_s: float, bpm: float) -> None:
        period_s = 60.0 / float(bpm)
        click_len = int(0.005 * sample_rate_hz)
        amp = 20000
        t = start_s
        while t < end_s:
            i0 = int(round(t * sample_rate_hz))
            for j in range(click_len):
                idx = i0 + j
                if idx >= n:
                    break
                if channels == 1:
                    data[idx] = amp
                else:
                    base = idx * 2
                    data[base] = amp
                    data[base + 1] = amp
            t += period_s

    write_clicks(0.0, half, bpm_a)
    write_clicks(half, duration_s, bpm_b)

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate_hz)
        wf.writeframes(data.tobytes())


def test_decode_input_path_v1_populates_bpm_hint_windows_for_wav(tmp_path: Path) -> None:
    p = tmp_path / "click_120.wav"
    _write_click_track_wav(p, bpm=120.0, duration_s=30.0)

    audio = decode_input_path_v1(p)
    windows = getattr(audio, "bpm_hint_windows", None)
    assert isinstance(windows, list)
    assert len(windows) >= 3

    rounded = [int(round(x)) for x in windows]
    assert set(rounded) <= {119, 120, 121}


def test_half_time_with_subdivision_is_ambiguous_and_omits_value(tmp_path: Path) -> None:
    # Half/double ambiguity: a strong pulse exists at 85 BPM, but subdivisions
    # can support a 170 BPM interpretation. v1 should not "force" a value here.
    p = tmp_path / "half_time_85_with_subdivision.wav"
    _write_click_track_wav(p, bpm=85.0, duration_s=40.0, subdivide=True, subdivide_ratio=0.19)

    out = run_analysis_v1(role="free", input_path=p, config=EngineConfig())
    bpm = out["metrics"]["bpm"]

    assert bpm.get("confidence") == "low"
    assert "value" not in bpm
    cand = bpm.get("candidates", [])
    assert isinstance(cand, list)
    bpms = {c["value"]["value_rounded"] for c in cand}
    assert 85 in bpms
    assert 170 in bpms


def test_run_analysis_v1_produces_bpm_from_pcm_windows(tmp_path: Path) -> None:
    p = tmp_path / "click_140.wav"
    _write_click_track_wav(p, bpm=140.0, duration_s=40.0)

    out = run_analysis_v1(role="free", input_path=p, config=EngineConfig())
    bpm = out["metrics"]["bpm"]
    assert bpm["value"]["value_rounded"] in {139, 140, 141}


def test_two_tempo_track_is_ambiguous_and_omits_value_but_keeps_candidates(tmp_path: Path) -> None:
    p = tmp_path / "two_tempo.wav"
    _write_two_tempo_click_track_wav(p, bpm_a=70.0, bpm_b=140.0, duration_s=60.0)

    out = run_analysis_v1(role="free", input_path=p, config=EngineConfig())
    bpm = out["metrics"]["bpm"]

    # Ambiguous: keep candidates, omit final value.
    assert bpm.get("confidence") == "low"
    assert "value" not in bpm

    cand = bpm.get("candidates", [])
    assert isinstance(cand, list)
    bpms = {c["value"]["value_rounded"] for c in cand}
    assert 70 in bpms
    assert 140 in bpms
