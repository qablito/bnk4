from __future__ import annotations

from typing import Any

from engine.core.config import EngineConfig
from engine.features.types import FeatureContext
from engine.observability import hooks


def extract_key_mode_v1(ctx: FeatureContext, *, config: EngineConfig) -> dict[str, Any] | None:
    """
    Returns the unlocked key_mode metric block (Precision Contract shape) or None (omit).
    v1 stubs:
      - If ctx.has_tonal_evidence is False -> omit
      - confidence simulated:
          - if key_mode_hint provided -> 0.8
          - else -> 0.3 (omit by threshold default 0.45)
    """
    if not ctx.has_tonal_evidence:
        return None

    if ctx.key_mode_hint is None:
        confidence = 0.3
        if confidence < config.tunables.key_mode_min_confidence_omit:
            hooks.emit(
                "feature_omitted",
                feature="key_mode",
                reason="confidence_below_threshold",
                stage="feature:key_mode",
            )
            return None
        value = "C major"
    else:
        value = str(ctx.key_mode_hint)
        confidence = 0.8

    if confidence < config.tunables.key_mode_min_confidence_omit:
        hooks.emit(
            "feature_omitted",
            feature="key_mode",
            reason="confidence_below_threshold",
            stage="feature:key_mode",
        )
        return None

    # minimal candidates: top-2
    candidates = [
        {"value": value, "rank": 1},
        {"value": "A minor" if value.endswith("major") else "C major", "rank": 2},
    ]

    return {
        "value": value,
        "confidence": confidence,
        "candidates": candidates,
        "method": "key_mode_estimation_v1",
        "limits": "Stub v1: deterministic; real key detection not implemented yet.",
    }
