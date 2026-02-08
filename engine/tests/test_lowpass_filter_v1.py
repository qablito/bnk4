from __future__ import annotations

import math

import pytest

from engine.preprocess import bpm_hint_windows_v1 as bpmh


def test_lowpass_impulse_response_decays_monotonically() -> None:
    sr = 1000.0
    cutoff = 150.0
    x = [1.0] + [0.0] * 64
    y = bpmh._lowpass_iir_v1(x, sample_rate_hz=sr, cutoff_hz=cutoff)

    assert len(y) == len(x)
    assert y[0] > 0.0
    assert y[1] >= 0.0

    # First-order lowpass impulse response is exponential decay (monotonic decreasing).
    eps = 1e-12
    for i in range(0, len(y) - 1):
        assert y[i] + eps >= y[i + 1]


def test_lowpass_dc_passes_and_converges() -> None:
    sr = 1000.0
    cutoff = 150.0
    x = [1.0] * 256
    y = bpmh._lowpass_iir_v1(x, sample_rate_hz=sr, cutoff_hz=cutoff)

    assert len(y) == len(x)
    # Step response should approach the DC input (1.0).
    assert y[-1] > 0.95

    # Monotonic increasing for a unit step with y0=0.
    eps = 1e-12
    for i in range(0, len(y) - 1):
        assert y[i] <= y[i + 1] + eps


def test_lowpass_invalid_parameters_raise() -> None:
    with pytest.raises(ValueError):
        bpmh._lowpass_alpha_v1(sample_rate_hz=0.0, cutoff_hz=150.0)
    with pytest.raises(ValueError):
        bpmh._lowpass_alpha_v1(sample_rate_hz=1000.0, cutoff_hz=0.0)


def test_lowpass_alpha_reasonable_range() -> None:
    a = bpmh._lowpass_alpha_v1(sample_rate_hz=44100.0, cutoff_hz=150.0)
    assert 0.0 < a < 1.0
    # Rough sanity: alpha increases with higher cutoff.
    b = bpmh._lowpass_alpha_v1(sample_rate_hz=44100.0, cutoff_hz=300.0)
    assert b > a
    assert math.isfinite(a) and math.isfinite(b)
