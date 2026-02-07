from __future__ import annotations

from typing import Any, Literal

Role = Literal["guest", "free", "pro"]

GUEST_STRIP_KEYS_DEEP = {
    "confidence",
    "evidence",
    "reason_codes",
    "ambiguity",
    "ambiguity_label",
    "score",
    "scores",
}


def _deep_strip_keys(obj: Any, *, strip_keys: set[str]) -> Any:
    """
    Recursively removes any dict keys that match strip_keys.
    Works on dict/list trees; returns a new object only when needed.
    """
    if isinstance(obj, dict):
        changed = False
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if k in strip_keys:
                changed = True
                continue
            nv = _deep_strip_keys(v, strip_keys=strip_keys)
            if nv is not v:
                changed = True
            out[k] = nv
        return out if changed else obj

    if isinstance(obj, list):
        changed = False
        out_list: list[Any] = []
        for v in obj:
            nv = _deep_strip_keys(v, strip_keys=strip_keys)
            if nv is not v:
                changed = True
            out_list.append(nv)
        return out_list if changed else obj

    return obj


def package_output_v1(out: dict[str, Any], *, role: Role) -> dict[str, Any]:
    """
    Applies Engine v1 packaging rules that depend on caller role.

    This function is intentionally small and dependency-free. It is expected to be
    called as the final pipeline step (after metrics/events are computed).
    """
    packaged: dict[str, Any] = dict(out)

    _package_events(packaged, role=role)
    _package_metrics(packaged, role=role)

    return packaged


def _package_events(out: dict[str, Any], *, role: Role) -> None:
    if role == "guest":
        out["events"] = {}
        return

    # Free/Pro: keep categorized events object. Ensure categories exist, but do not
    # overwrite any populated event arrays.
    events = out.get("events")
    if not isinstance(events, dict):
        events = {}
        out["events"] = events

    def ensure_obj(key: str, default: dict[str, Any]) -> dict[str, Any]:
        cur = events.get(key)
        if isinstance(cur, dict):
            return cur
        events[key] = dict(default)
        return events[key]

    clipping = ensure_obj(
        "clipping",
        {"sample_clipping_ranges": [], "true_peak_exceedance_ranges": []},
    )
    if "sample_clipping_ranges" not in clipping:
        clipping["sample_clipping_ranges"] = []
    if "true_peak_exceedance_ranges" not in clipping:
        clipping["true_peak_exceedance_ranges"] = []

    stereo = ensure_obj("stereo", {"stereo_issue_ranges": []})
    if "stereo_issue_ranges" not in stereo:
        stereo["stereo_issue_ranges"] = []

    tonality = ensure_obj("tonality", {"tonal_drift_ranges": []})
    if "tonal_drift_ranges" not in tonality:
        tonality["tonal_drift_ranges"] = []

    noise = ensure_obj("noise", {"noise_change_ranges": []})
    if "noise_change_ranges" not in noise:
        noise["noise_change_ranges"] = []


def _package_metrics(out: dict[str, Any], *, role: Role) -> None:
    metrics = out.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        return

    # Copy-on-write for metrics dict.
    new_metrics: dict[str, Any] = dict(metrics)
    changed = False

    if role == "guest":
        stripped = _deep_strip_keys(new_metrics, strip_keys=GUEST_STRIP_KEYS_DEEP)
        if stripped is not new_metrics:
            new_metrics = stripped
            changed = True

    # Rule: Guest must not receive bpm.value.value_exact.
    if role == "guest" and "bpm" in new_metrics and isinstance(new_metrics["bpm"], dict):
        bpm = dict(new_metrics["bpm"])
        val = bpm.get("value")
        if isinstance(val, dict) and "value_exact" in val:
            new_val = dict(val)
            new_val.pop("value_exact", None)
            bpm["value"] = new_val
            new_metrics["bpm"] = bpm
            changed = True

    # Rule: Locked blocks must omit preview when preview is {}.
    for name, block in list(new_metrics.items()):
        if not isinstance(block, dict):
            continue
        if block.get("locked") is True and block.get("preview") == {}:
            nb = dict(block)
            nb.pop("preview", None)
            new_metrics[name] = nb
            changed = True

    if changed:
        out["metrics"] = new_metrics
