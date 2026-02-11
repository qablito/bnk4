from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

from engine.core.config import EngineConfig
from engine.pipeline.run import run_analysis_v1

Role = Literal["guest", "free", "pro"]
VALID_ROLES: set[str] = {"guest", "free", "pro"}
LISTABLE_AUDIO_SUFFIXES: set[str] = {".mp3", ".wav", ".m4a"}
DEFAULT_AUDIO_ROOT_REL = "audiosToTest"
REPO_ROOT = Path(__file__).resolve().parents[2]


def get_audio_root() -> Path:
    raw_root = (os.getenv("ANALYZER_AUDIO_ROOT") or DEFAULT_AUDIO_ROOT_REL).strip()
    root = Path(raw_root)
    if not root.is_absolute():
        root = REPO_ROOT / root
    return root.resolve()


def list_samples(audio_root: Path | None = None) -> list[dict[str, Any]]:
    root = (audio_root or get_audio_root()).resolve()
    if not root.exists() or not root.is_dir():
        return []

    entries: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in LISTABLE_AUDIO_SUFFIXES:
            continue
        rel_path = path.relative_to(root).as_posix()
        entries.append(
            {
                "sample_id": rel_path,
                "filename": path.name,
                "rel_path": rel_path,
                "size_bytes": int(path.stat().st_size),
            }
        )

    entries.sort(key=lambda item: item["sample_id"])
    return entries


def parse_sample_id_payload(payload: dict[str, Any]) -> tuple[Role, str]:
    role = payload.get("role")
    if role not in VALID_ROLES:
        raise ValueError("role must be one of: guest, free, pro")

    # v1 accepts only sample_id. Keep nested and back-compat flat shapes.
    nested_input = payload.get("input")
    if isinstance(nested_input, dict):
        kind = nested_input.get("kind")
        if kind != "sample_id":
            raise ValueError("input.kind must be 'sample_id' in v1")
        sample_id = nested_input.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id.strip():
            raise ValueError("input.sample_id is required")
        return role, sample_id

    sample_id = payload.get("sample_id")
    if not isinstance(sample_id, str) or not sample_id.strip():
        raise ValueError("sample_id is required")
    return role, sample_id


def resolve_sample_path(audio_root: Path, sample_id: str) -> Path:
    normalized = sample_id.replace("\\", "/").strip()
    if not normalized:
        raise ValueError("sample_id is required")

    root = audio_root.resolve()
    candidate = (root / normalized).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("sample_id resolves outside audio root") from exc

    if not candidate.exists() or not candidate.is_file():
        raise ValueError("sample_id not found")

    return candidate


def analyze_sample(*, role: Role, sample_path: Path) -> dict[str, Any]:
    return run_analysis_v1(role=role, input_path=str(sample_path), config=EngineConfig())
