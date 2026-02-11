from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from api import app
from fastapi.testclient import TestClient
from service import get_audio_root, list_samples


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


def test_analyze_known_sample_contract_shape() -> None:
    audio_root = get_audio_root()
    if not audio_root.exists():
        pytest.skip("audiosToTest/ not present; skipping analyzer-api integration test")

    samples = list_samples(audio_root)
    wav_sample = next((s for s in samples if s["sample_id"].lower().endswith(".wav")), None)
    if wav_sample is None:
        pytest.skip("No .wav sample found in audiosToTest/; skipping integration test")

    client = TestClient(app)
    resp = client.post(
        "/analyze",
        json={
            "role": "pro",
            "input": {"kind": "sample_id", "sample_id": wav_sample["sample_id"]},
        },
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body.get("analysis_id"), str) and body["analysis_id"]
    assert body["role"] == "pro"
    assert isinstance(body.get("track"), dict)
    assert isinstance(body.get("metrics"), dict)
    assert "bpm" in body["metrics"]
    assert "key" in body["metrics"]
