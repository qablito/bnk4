from __future__ import annotations

import math
import wave
from array import array
from collections.abc import Iterable
from pathlib import Path


def _lowpass_alpha_v1(*, sample_rate_hz: float, cutoff_hz: float) -> float:
    """
    First-order (one-pole) low-pass filter alpha for:

        y[n] = y[n-1] + alpha * (x[n] - y[n-1])

    alpha is in (0, 1) for valid parameters.
    """
    sr = float(sample_rate_hz)
    fc = float(cutoff_hz)
    if sr <= 0:
        raise ValueError("sample_rate_hz must be > 0")
    if fc <= 0:
        raise ValueError("cutoff_hz must be > 0")

    w = 2.0 * math.pi * fc
    return w / (w + sr)


def _lowpass_iir_v1(
    x: list[float],
    *,
    sample_rate_hz: float,
    cutoff_hz: float,
    y0: float = 0.0,
) -> list[float]:
    """
    Convenience helper used by tests. Streaming code uses the same recurrence
    without building intermediate arrays.
    """
    a = _lowpass_alpha_v1(sample_rate_hz=sample_rate_hz, cutoff_hz=cutoff_hz)
    y = float(y0)
    out: list[float] = []
    for v in x:
        y += a * (float(v) - y)
        out.append(y)
    return out


def _iter_energy_frames_v1(
    wf: wave.Wave_read,
    *,
    frame_size: int,
    lowpass_cutoff_hz: float,
) -> Iterable[float]:
    """
    Yield simple frame energies from a WAV stream.

    This is intentionally stdlib-only and biased for deterministic tempo hints.
    It is not a full-featured audio decoder.
    """
    channels = int(wf.getnchannels())
    sampwidth = int(wf.getsampwidth())

    if channels not in (1, 2):
        raise ValueError(f"unsupported channels: {channels} (expected 1 or 2)")

    if sampwidth != 2:
        # Keep v1 small. ffmpeg->wav defaults to 16-bit PCM, which covers our eval set.
        raise ValueError(f"unsupported sample width: {sampwidth} bytes (expected 2)")

    # Low-pass state (mono).
    sr = float(wf.getframerate())
    alpha = _lowpass_alpha_v1(sample_rate_hz=sr, cutoff_hz=float(lowpass_cutoff_hz))
    y = 0.0

    while True:
        raw = wf.readframes(frame_size)
        if not raw:
            break

        a = array("h")
        a.frombytes(raw)
        if not a:
            break

        if channels == 1:
            e = 0.0
            for xi in a:
                y += alpha * (float(int(xi)) - y)
                e += abs(y)
            yield e / float(len(a))
            continue

        # Stereo: average to mono, then energy.
        e = 0.0
        n = len(a) // 2
        for i in range(0, n * 2, 2):
            m = (int(a[i]) + int(a[i + 1])) // 2
            y += alpha * (float(m) - y)
            e += abs(y)
        yield e / float(max(n, 1))


def _iter_energy_frames_bands_v1(
    wf: wave.Wave_read,
    *,
    frame_size: int,
    lowpass_cutoff_hz: float,
    highpass_cutoff_hz: float,
) -> Iterable[tuple[float, float]]:
    """
    Yield (low_band_energy, high_band_energy) per frame.

    High band is approximated via a 1st-order high-pass:
      hp(x) = x - lp_hp(x)
    """
    channels = int(wf.getnchannels())
    sampwidth = int(wf.getsampwidth())

    if channels not in (1, 2):
        raise ValueError(f"unsupported channels: {channels} (expected 1 or 2)")

    if sampwidth != 2:
        raise ValueError(f"unsupported sample width: {sampwidth} bytes (expected 2)")

    sr = float(wf.getframerate())
    alpha_low = _lowpass_alpha_v1(sample_rate_hz=sr, cutoff_hz=float(lowpass_cutoff_hz))
    alpha_hp = _lowpass_alpha_v1(sample_rate_hz=sr, cutoff_hz=float(highpass_cutoff_hz))
    y_low = 0.0
    y_hp = 0.0

    while True:
        raw = wf.readframes(frame_size)
        if not raw:
            break

        a = array("h")
        a.frombytes(raw)
        if not a:
            break

        if channels == 1:
            e_low = 0.0
            e_high = 0.0
            for xi in a:
                x = float(int(xi))
                y_low += alpha_low * (x - y_low)
                y_hp += alpha_hp * (x - y_hp)
                e_low += abs(y_low)
                e_high += abs(x - y_hp)
            n = float(len(a))
            yield (e_low / n, e_high / n)
            continue

        e_low = 0.0
        e_high = 0.0
        n = len(a) // 2
        for i in range(0, n * 2, 2):
            m = (int(a[i]) + int(a[i + 1])) // 2
            x = float(m)
            y_low += alpha_low * (x - y_low)
            y_hp += alpha_hp * (x - y_hp)
            e_low += abs(y_low)
            e_high += abs(x - y_hp)
        yield (e_low / float(max(n, 1)), e_high / float(max(n, 1)))


def _detail_from_segment_v1(
    seg: list[float],
    *,
    env_sr_hz: float,
    bpm_min: float,
    bpm_max: float,
    lag_bias_exponent: float,
) -> dict[str, float | None] | None:
    n = len(seg)
    if n < 8:
        return None

    # Center segment (removes DC).
    mean = sum(seg) / float(n)
    x = [v - mean for v in seg]

    min_lag = int(round(env_sr_hz * 60.0 / float(bpm_max)))
    max_lag = int(round(env_sr_hz * 60.0 / float(bpm_min)))
    min_lag = max(1, min_lag)
    max_lag = min(max_lag, n - 1)
    if max_lag <= min_lag:
        return None

    denom = sum(v * v for v in x) + 1e-12
    lag_bias = max(0.0, float(lag_bias_exponent))

    best_lag: int | None = None
    best_adj: float | None = None
    best_raw: float | None = None

    for lag in range(min_lag, max_lag + 1):
        s = 0.0
        for i in range(lag, n):
            s += x[i] * x[i - lag]

        # Optional bias: penalize longer lags. Default is 0 (no bias) to avoid
        # selecting high-tempo harmonics as "best" on produced audio.
        if lag_bias > 0.0:
            adj = s / (float(lag) ** lag_bias)
        else:
            adj = s

        if best_adj is None or adj > best_adj:
            best_adj = adj
            best_raw = s
            best_lag = lag

    if best_lag is None or best_lag <= 0:
        return None

    bpm_best = 60.0 * float(env_sr_hz) / float(best_lag)
    best_score = abs(float(best_raw or 0.0)) / float(denom)
    out: dict[str, float | None] = {"best_bpm": float(bpm_best), "best_score": float(best_score)}

    # Half/double ambiguity evidence: compare half-lag (double tempo) correlation.
    if best_raw is None or abs(float(best_raw)) <= 1e-12:
        return out

    half_a = int(best_lag // 2)
    half_b = half_a + 1
    half_lags = [lag for lag in (half_a, half_b) if lag >= min_lag]

    best_half_lag: int | None = None
    best_half_raw: float | None = None
    best_half_adj: float | None = None
    for half_lag in half_lags:
        s_half = 0.0
        for i in range(half_lag, n):
            s_half += x[i] * x[i - half_lag]

        if lag_bias > 0.0:
            adj_half = s_half / (float(half_lag) ** lag_bias)
        else:
            adj_half = s_half

        if best_half_adj is None or adj_half > best_half_adj:
            best_half_adj = adj_half
            best_half_raw = s_half
            best_half_lag = half_lag

    if best_half_lag is None or best_half_raw is None:
        return out

    bpm_double = 60.0 * float(env_sr_hz) / float(best_half_lag)
    if bpm_double > float(bpm_max):
        return out

    ratio = abs(float(best_half_raw)) / abs(float(best_raw))
    out["double_bpm"] = float(bpm_double)
    out["double_ratio"] = float(ratio)
    return out


def compute_bpm_hint_window_details_from_wav_v1(
    path: str | Path,
    *,
    window_seconds: float = 8.0,
    hop_seconds: float = 4.0,
    frame_seconds: float = 0.01,
    bpm_min: float = 60.0,
    bpm_max: float = 200.0,
    min_audio_seconds: float = 2.0,
    lowpass_cutoff_hz: float = 200.0,
    highpass_cutoff_hz: float = 900.0,
    lag_bias_exponent: float = 0.0,
) -> list[dict[str, float | None]]:
    """
    Compute per-window tempo hints and ambiguity evidence from WAV PCM (stdlib-only).

    Output:
      - list[dict]: one record per window (not flattened), containing low-band
        keys plus optional high-band keys prefixed with `high_`.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    if window_seconds <= 0 or hop_seconds <= 0 or frame_seconds <= 0:
        raise ValueError("window_seconds/hop_seconds/frame_seconds must be > 0")
    if bpm_min <= 0 or bpm_max <= 0 or bpm_max <= bpm_min:
        raise ValueError("invalid bpm_min/bpm_max")
    if lowpass_cutoff_hz <= 0:
        raise ValueError("lowpass_cutoff_hz must be > 0")
    if highpass_cutoff_hz <= 0:
        raise ValueError("highpass_cutoff_hz must be > 0")
    if lag_bias_exponent < 0:
        raise ValueError("lag_bias_exponent must be >= 0")

    with wave.open(str(p), "rb") as wf:
        sr = float(wf.getframerate())
        frames = int(wf.getnframes())
        duration_s = frames / sr if sr > 0 else 0.0
        if duration_s < float(min_audio_seconds):
            return []

        frame_size = max(1, int(round(sr * float(frame_seconds))))
        env_low: list[float] = []
        env_high: list[float] = []
        for e_low, e_high in _iter_energy_frames_bands_v1(
            wf,
            frame_size=frame_size,
            lowpass_cutoff_hz=float(lowpass_cutoff_hz),
            highpass_cutoff_hz=float(highpass_cutoff_hz),
        ):
            env_low.append(float(e_low))
            env_high.append(float(e_high))

    if len(env_low) < 4:
        return []

    def onset_from_env(env: list[float]) -> list[float]:
        onset: list[float] = [0.0]
        for i in range(1, len(env)):
            d = env[i] - env[i - 1]
            onset.append(d if d > 0 else 0.0)
        return onset

    onset_low = onset_from_env(env_low)
    onset_high = onset_from_env(env_high)

    env_sr_hz = 1.0 / float(frame_seconds)

    win_len = int(round(float(window_seconds) * env_sr_hz))
    hop_len = int(round(float(hop_seconds) * env_sr_hz))
    win_len = max(1, win_len)
    hop_len = max(1, hop_len)

    windows: list[dict[str, float | None]] = []

    def merge_low_high(
        low: dict[str, float | None] | None, high: dict[str, float | None] | None
    ) -> dict[str, float | None] | None:
        if low is None and high is None:
            return None
        out: dict[str, float | None] = {}
        if low is not None:
            out.update(low)
        if high is not None:
            for k, v in high.items():
                out[f"high_{k}"] = v
        return out

    if len(onset_low) < win_len:
        low = _detail_from_segment_v1(
            onset_low,
            env_sr_hz=env_sr_hz,
            bpm_min=bpm_min,
            bpm_max=bpm_max,
            lag_bias_exponent=lag_bias_exponent,
        )
        high = _detail_from_segment_v1(
            onset_high,
            env_sr_hz=env_sr_hz,
            bpm_min=bpm_min,
            bpm_max=bpm_max,
            lag_bias_exponent=lag_bias_exponent,
        )
        merged = merge_low_high(low, high)
        return [merged] if merged is not None else []

    for start in range(0, len(onset_low) - win_len + 1, hop_len):
        seg_low = onset_low[start : start + win_len]
        seg_high = onset_high[start : start + win_len]
        low = _detail_from_segment_v1(
            seg_low,
            env_sr_hz=env_sr_hz,
            bpm_min=bpm_min,
            bpm_max=bpm_max,
            lag_bias_exponent=lag_bias_exponent,
        )
        high = _detail_from_segment_v1(
            seg_high,
            env_sr_hz=env_sr_hz,
            bpm_min=bpm_min,
            bpm_max=bpm_max,
            lag_bias_exponent=lag_bias_exponent,
        )
        merged = merge_low_high(low, high)
        if merged is None:
            continue
        windows.append(merged)

    return windows


def compute_bpm_hint_windows_from_wav_v1(
    path: str | Path,
    *,
    window_seconds: float = 8.0,
    hop_seconds: float = 4.0,
    frame_seconds: float = 0.01,
    bpm_min: float = 60.0,
    bpm_max: float = 200.0,
    min_audio_seconds: float = 2.0,
    double_tempo_alpha: float = 0.80,
    lowpass_cutoff_hz: float = 200.0,
    highpass_cutoff_hz: float = 900.0,
    lag_bias_exponent: float = 0.0,
) -> list[float]:
    """
    Compute window-level tempo hints from WAV PCM using stdlib only.

    Output:
      - list[float]: BPM estimates per overlapping window.
    """
    # NOTE: This function returns a flattened list of BPMs suitable for the
    # current `FeatureContext.bpm_hint_windows` type.
    #
    # We always include `best_bpm` per window. If the double-time candidate exists
    # and its correlation ratio is high enough, we include it as an additional hint
    # (without hard-switching).
    details = compute_bpm_hint_window_details_from_wav_v1(
        path,
        window_seconds=window_seconds,
        hop_seconds=hop_seconds,
        frame_seconds=frame_seconds,
        bpm_min=bpm_min,
        bpm_max=bpm_max,
        min_audio_seconds=min_audio_seconds,
        lowpass_cutoff_hz=lowpass_cutoff_hz,
        highpass_cutoff_hz=highpass_cutoff_hz,
        lag_bias_exponent=lag_bias_exponent,
    )

    hints: list[float] = []
    for d in details:
        low_best = d.get("best_bpm")
        if low_best is not None:
            hints.append(float(low_best))
        high_best = d.get("high_best_bpm")
        if high_best is not None:
            hints.append(float(high_best))

        low_double = d.get("double_bpm")
        low_ratio = d.get("double_ratio")
        if low_double is not None and low_ratio is not None:
            if float(low_ratio) >= float(double_tempo_alpha):
                hints.append(float(low_double))

        high_double = d.get("high_double_bpm")
        high_ratio = d.get("high_double_ratio")
        if high_double is not None and high_ratio is not None:
            if float(high_ratio) >= float(double_tempo_alpha):
                hints.append(float(high_double))

    return hints
