from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from engine.core.errors import EngineError

class ContractViolation(EngineError):
    """Raised when an analysis output violates the Engine v1 contract."""

    def __init__(self, message: str, *, path: Optional[str] = None):
        ctx = {"path": path} if path else None
        super().__init__(code="CONTRACT_VIOLATION", message=message, context=ctx)


@dataclass(frozen=True)
class ValidateOptions:
    """
    Minimal contract validation options.

    guest_events_policy:
      - "empty_object": guest must include events={}
      - "omit_ok": guest may omit events or include {}
    """
    guest_events_policy: str = "empty_object"


LOCKED_FORBIDDEN_KEYS = {
    "confidence",
    "candidates",
    "evidence",
    "reason_codes",
    "ambiguity",
    "ambiguity_label",
    "score",
    "scores",
}

# v1 locked blocks are value-less; only unlock_hint and an optional non-empty preview are allowed.
LOCKED_ALLOWED_KEYS = {"locked", "unlock_hint", "preview"}


def _is_uuid_like(v: str) -> bool:
    # Lightweight check; no uuid import to keep it tiny and permissive.
    if not isinstance(v, str):
        return False
    parts = v.split("-")
    if len(parts) != 5:
        return False
    lens = [8, 4, 4, 4, 12]
    return all(len(p) == ln for p, ln in zip(parts, lens))


def _err(path: str, msg: str) -> ContractViolation:
    return ContractViolation(f"{path}: {msg}", path=path)


def validate_analysis_output_v1(obj: Dict[str, Any], *, opts: Optional[ValidateOptions] = None) -> None:
    """
    Validates the canonical analysis output shape + role gating invariants (Engine v1).

    This is NOT full JSONSchema evaluation. It is a strict-enough safety net to prevent
    accidental contract breaks during implementation.
    """
    opts = opts or ValidateOptions()

    if not isinstance(obj, dict):
        raise _err("$", "output must be an object")

    # --- required top-level keys (minimal set) ---
    for k in ("engine", "analysis_id", "created_at", "role", "track", "metrics", "warnings"):
        if k not in obj:
            raise _err("$", f"missing required key '{k}'")

    engine = obj["engine"]
    if not isinstance(engine, dict):
        raise _err("$.engine", "must be an object")
    if engine.get("name") != "bnk-analysis-engine":
        raise _err("$.engine.name", "must be 'bnk-analysis-engine'")
    if engine.get("version") != "v1":
        raise _err("$.engine.version", "must be 'v1'")

    if not _is_uuid_like(obj["analysis_id"]):
        raise _err("$.analysis_id", "must look like a UUID")

    role = obj["role"]
    if role not in ("guest", "free", "pro"):
        raise _err("$.role", "must be one of: guest, free, pro")

    track = obj["track"]
    if not isinstance(track, dict):
        raise _err("$.track", "must be an object")

    metrics = obj["metrics"]
    if not isinstance(metrics, dict):
        raise _err("$.metrics", "must be an object")

    warnings = obj["warnings"]
    if not isinstance(warnings, list):
        raise _err("$.warnings", "must be an array")

    # --- events gating ---
    if role == "guest":
        if "events" in obj:
            if not isinstance(obj["events"], dict):
                raise _err("$.events", "guest events must be an object")
            if opts.guest_events_policy == "empty_object" and obj["events"] != {}:
                raise _err("$.events", "guest events must be {}")
        else:
            if opts.guest_events_policy == "empty_object":
                raise _err("$", "guest must include events: {} per Engine v1 example")
    else:
        # free/pro may omit or include structured events; if present, must be object
        if "events" in obj and not isinstance(obj["events"], dict):
            raise _err("$.events", "must be an object when present")

    # --- per-metric validation (locked vs unlocked invariants) ---
    for mname, mval in metrics.items():
        path = f"$.metrics.{mname}"
        if not isinstance(mval, dict):
            raise _err(path, "metric block must be an object")

        locked = bool(mval.get("locked", False))
        if locked:
            # Locked metric invariants
            if mval.get("locked") is not True:
                raise _err(path + ".locked", "if present, locked must be true")

            if "unlock_hint" not in mval or not isinstance(mval["unlock_hint"], str) or not mval["unlock_hint"].strip():
                raise _err(path + ".unlock_hint", "locked metrics must include non-empty unlock_hint")

            extra_keys = set(mval.keys()) - LOCKED_ALLOWED_KEYS
            if extra_keys:
                raise _err(path, f"locked metric must not include: {', '.join(sorted(extra_keys))}")

            # Forbidden keys in any locked block
            present_forbidden = LOCKED_FORBIDDEN_KEYS.intersection(mval.keys())
            if present_forbidden:
                raise _err(path, f"locked metric must not include: {', '.join(sorted(present_forbidden))}")

            # preview: optional, but must be omitted if empty
            if "preview" in mval:
                if not isinstance(mval["preview"], dict):
                    raise _err(path + ".preview", "preview must be an object")
                if mval["preview"] == {}:
                    raise _err(path + ".preview", "empty preview must be omitted")

            # value must not appear unless explicitly allowed as preview (we keep it strict)
            if "value" in mval:
                raise _err(path + ".value", "locked metrics must not include value (use preview if allowed)")

            # NOTE: locked metrics MUST NOT expose numeric confidence for any role (handled above)

        else:
            # Unlocked metrics: allow precision-contract style.
            # We do not enforce full contract here, only prevent obvious guest leaks.
            if role == "guest":
                # Guest must not receive evidence anywhere.
                if "evidence" in mval:
                    raise _err(path + ".evidence", "guest must not receive evidence")
                # Guest must not receive numeric confidence except where explicitly allowed (we choose strict: none).
                if "confidence" in mval:
                    raise _err(path + ".confidence", "guest must not receive numeric confidence in v1")
                if mname == "bpm":
                    val = mval.get("value")
                    if isinstance(val, dict) and "value_exact" in val:
                        raise _err(path + ".value.value_exact", "guest bpm must not include value_exact")
                # Guest candidates: only allowed on bpm/key_mode and only rank/value.
                if "candidates" in mval:
                    if mname not in ("bpm", "key_mode"):
                        raise _err(path + ".candidates", "guest candidates only allowed for bpm and key_mode")
                    _validate_guest_candidates(mval["candidates"], path + ".candidates")

            # Engine v1 says bpm/key_mode MUST be omitted when unreliable.
            # This validator can't compute reliability, but it CAN prevent them being returned as locked.
            if mname in ("bpm", "key_mode") and "locked" in mval:
                raise _err(path + ".locked", "bpm/key_mode must never be locked; omit instead")


def _validate_guest_candidates(cands: Any, path: str) -> None:
    if not isinstance(cands, list):
        raise _err(path, "must be an array")
    for i, c in enumerate(cands):
        cpath = f"{path}[{i}]"
        if not isinstance(c, dict):
            raise _err(cpath, "candidate must be an object")
        allowed = {"value", "rank"}
        extra = set(c.keys()) - allowed
        if extra:
            raise _err(cpath, f"guest candidates must not include: {', '.join(sorted(extra))}")
        if "rank" not in c or not isinstance(c["rank"], int):
            raise _err(cpath + ".rank", "rank must be an int")
        if "value" not in c:
            raise _err(cpath + ".value", "value is required")
