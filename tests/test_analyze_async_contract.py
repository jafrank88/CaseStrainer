from io import BytesIO
from unittest.mock import MagicMock

import pytest

from src.app_final_vue import create_app
from src.api.services.citation_service import CitationService
from src.unified_input_processor import UnifiedInputProcessor


def _make_fake_queue():
    """Fake RQ Queue so file upload async path does not require Redis."""
    mock_job = MagicMock()
    mock_job.id = "test-job-id"
    mock_queue = MagicMock()
    mock_queue.enqueue.return_value = mock_job
    return mock_queue


@pytest.fixture
def client(monkeypatch):
    """Create a Flask test client with analyze internals stubbed for contract testing."""

    def _fake_extract_text(self, input_data):
        # Avoid live network calls for URL inputs in tests.
        if isinstance(input_data, dict) and input_data.get("type") == "url":
            return "Brown v. Board of Education, 347 U.S. 483 (1954)."
        return "Brown v. Board of Education, 347 U.S. 483 (1954)."

    def _fake_process_any_input(self, input_data, input_type, request_id, **kwargs):
        # Contract expectation: tests request async explicitly.
        assert kwargs.get("force_mode") == "async"
        return {
            "success": True,
            "status": "processing",
            "task_id": request_id,
            "request_id": request_id,
            "citations": [],
            "clusters": [],
            "metadata": {
                "processing_mode": "queued",
                "input_type": input_type,
            },
        }

    def _fake_queue(_name, connection=None):
        return _make_fake_queue()

    def _fake_redis_from_url(_url):
        return MagicMock()

    monkeypatch.setattr(CitationService, "extract_text_from_input", _fake_extract_text, raising=True)
    monkeypatch.setattr(UnifiedInputProcessor, "process_any_input", _fake_process_any_input, raising=True)
    # File upload path does "from rq import Queue" and "from redis import Redis"; avoid real Redis in tests.
    monkeypatch.setattr("rq.Queue", _fake_queue)
    monkeypatch.setattr("redis.Redis.from_url", _fake_redis_from_url)

    app = create_app()
    app.testing = True
    with app.test_client() as test_client:
        yield test_client


def test_analyze_text_returns_async_task_contract(client):
    response = client.post(
        "/casestrainer/api/analyze",
        json={
            "type": "text",
            "text": "Brown v. Board of Education, 347 U.S. 483 (1954).",
            "force_mode": "async",
            "enable_verification": True,
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload.get("status") == "processing"
    assert payload.get("task_id")
    assert (payload.get("metadata") or {}).get("processing_mode") == "queued"


def test_analyze_url_returns_async_task_contract(client):
    response = client.post(
        "/casestrainer/api/analyze",
        json={
            "type": "url",
            "url": "https://example.com/legal-doc",
            "force_mode": "async",
            "enable_verification": True,
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload.get("status") == "processing"
    assert payload.get("task_id")
    assert (payload.get("metadata") or {}).get("processing_mode") == "queued"


def test_analyze_file_returns_async_task_contract(client):
    response = client.post(
        "/casestrainer/api/analyze",
        data={
            "type": "file",
            "force_mode": "async",
            "enable_verification": "true",
            "file": (BytesIO(b"Brown v. Board of Education, 347 U.S. 483 (1954)."), "sample.txt"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload.get("status") == "processing"
    assert payload.get("task_id")
    assert (payload.get("metadata") or {}).get("processing_mode") == "queued"
