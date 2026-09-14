"""Tests for the task creation API endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)


class TestCreateTask:
    """Tests for POST /api/tasks."""

    def test_creates_task_with_title_and_description(self) -> None:
        """A valid request returns 201 with the created task JSON."""
        response = client.post(
            "/api/tasks",
            json={"title": "Fix bug", "description": "Fix the login bug"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Fix bug"
        assert body["description"] == "Fix the login bug"
        assert body["status"] == "backlog"
        assert body["owner"] is None
        assert body["id"]

    def test_creates_task_with_default_description(self) -> None:
        """A request without a description defaults it to an empty string."""
        response = client.post("/api/tasks", json={"title": "Write docs"})

        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Write docs"
        assert body["description"] == ""

    def test_missing_title_returns_400(self) -> None:
        """A request without a title returns 400."""
        response = client.post("/api/tasks", json={"description": "No title"})

        assert response.status_code == 400

    def test_empty_title_returns_400(self) -> None:
        """A request with an empty title returns 400."""
        response = client.post("/api/tasks", json={"title": ""})

        assert response.status_code == 400