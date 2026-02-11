from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

import api as api_mod
from api import app
from fastapi.testclient import TestClient
from service import get_audio_root, list_samples


def test_health_hides_audio_root_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANALYZER_EXPOSE_PATHS", raising=False)
    monkeypatch.setattr(api_mod, "get_audio_root", lambda: "/tmp/audio-root")
    monkeypatch.setattr(
        api_mod,
        "list_samples",
        lambda _audio_root: [{"sample_id": "a.wav"}, {"sample_id": "b.mp3"}],
    )

    client = TestClient(app)
    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "audio_root": "hidden", "n_samples": 2}


def test_health_exposes_audio_root_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANALYZER_EXPOSE_PATHS", "1")
    monkeypatch.setattr(api_mod, "get_audio_root", lambda: "/tmp/audio-root")
    monkeypatch.setattr(api_mod, "list_samples", lambda _audio_root: [])

    client = TestClient(app)
    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {
        "status": "ok",
        "audio_root": "/tmp/audio-root",
        "n_samples": 0,
    }


def test_jobs_not_supported_route() -> None:
    client = TestClient(app)
    resp = client.get("/jobs/abc")
    assert resp.status_code == 404
    assert resp.json() == {
        "code": "JOBS_NOT_SUPPORTED",
        "message": "Async jobs not enabled in v1",
    }


def test_analyze_rejects_path_traversal_with_fastapi_detail() -> None:
    client = TestClient(app)
    resp = client.post(
        "/analyze",
        json={"role": "pro", "input": {"kind": "sample_id", "sample_id": "../secrets.wav"}},
    )
    assert resp.status_code == 422
    assert resp.json() == {"detail": [{"msg": "sample_id resolves outside audio root"}]}


def test_analyze_returns_404_when_sample_id_missing() -> None:
    client = TestClient(app)
    resp = client.post(
        "/analyze",
        json={"role": "pro", "input": {"kind": "sample_id", "sample_id": "missing/not-found.wav"}},
    )
    assert resp.status_code == 404
    assert resp.json() == {"code": "SAMPLE_NOT_FOUND", "message": "sample_id not found"}


def test_analyze_known_sample_contract_shape() -> None:
    audio_root = get_audio_root()
    if not audio_root.exists():
        pytest.skip("audiosToTest/ not present; skipping analyzer-api integration test")

    samples = list_samples(audio_root)
    target = None
    for suffix in (".wav", ".mp3", ".m4a"):
        target = next((s for s in samples if s["sample_id"].lower().endswith(suffix)), None)
        if target is not None:
            break
    if target is None:
        pytest.skip("No .wav/.mp3/.m4a sample found in audiosToTest/; skipping integration test")

    client = TestClient(app)
    resp = client.post(
        "/analyze",
        json={
            "role": "pro",
            "input": {"kind": "sample_id", "sample_id": target["sample_id"]},
        },
    )

    if target["sample_id"].lower().endswith(".m4a") and resp.status_code == 415:
        assert resp.json() == {
            "code": "UNSUPPORTED_FORMAT",
            "message": "Unsupported input format",
        }
        return

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body.get("analysis_id"), str) and body["analysis_id"]
    assert body["role"] == "pro"
    assert isinstance(body.get("track"), dict)
    assert isinstance(body.get("metrics"), dict)
    assert "bpm" in body["metrics"] or "key" in body["metrics"]
