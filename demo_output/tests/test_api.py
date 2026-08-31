"""Tests for portfolio API."""

from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_projects():
    r = client.get("/api/projects")
    assert r.status_code == 200
    projects = r.json()
    assert len(projects) >= 2
    assert projects[0]["title"] == "Chief AI"
