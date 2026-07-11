"""Tests for portfolio API."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

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
