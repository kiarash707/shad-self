import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import dashboard


def test_health():
    with TestClient(dashboard.app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_dashboard_requires_token(monkeypatch):
    monkeypatch.setenv("DASHBOARD_TOKEN", "test-token")
    with TestClient(dashboard.app) as client:
        response = client.get("/api/status")
        assert response.status_code == 401
        response = client.get("/api/status", headers={"X-Dashboard-Token": "test-token"})
        assert response.status_code == 200


def test_manifest_contains_integrity_fields(tmp_path, monkeypatch):
    session = tmp_path / "sessions"
    session.mkdir()
    (session / "sample.session").write_bytes(b"session-data")
    monkeypatch.setattr(dashboard, "SESSION_PATH", session)
    manifest = dashboard._manifest()
    assert manifest["format_version"] == 1
    assert manifest["file_count"] == 1
    assert len(manifest["files"][0]["sha256"]) == 64


def test_archive_validation_rejects_traversal(tmp_path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("../escape.txt", "bad")
        z.writestr("manifest.json", json.dumps({"format_version": 1, "files": []}))
    with pytest.raises(ValueError):
        dashboard.validate_archive(archive)
