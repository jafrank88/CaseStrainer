"""
Smoke test for /casestrainer/api/analyze endpoint.
Uses Flask test client; does not require a running server or Redis for minimal response.
"""

import pytest


@pytest.fixture
def app_client():
    """Create test client with app configured for testing."""
    from src.app_final_vue import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_analyze_endpoint_accepts_post(app_client):
    """POST /casestrainer/api/analyze with minimal text returns 200 or 202 and expected keys."""
    payload = {"type": "text", "text": "Roe v. Wade, 410 U.S. 113 (1973)."}
    response = app_client.post(
        "/casestrainer/api/analyze",
        json=payload,
        content_type="application/json",
    )
    assert response.status_code in (200, 202), f"Unexpected status {response.status_code}: {response.get_data(as_text=True)[:500]}"
    data = response.get_json()
    assert data is not None, "Response should be JSON"
    # Either immediate result or async processing
    has_result = "result" in data or "citations" in data or "task_id" in data or "request_id" in data
    has_status = "status" in data or "success" in data
    assert has_result or has_status, f"Response should contain result/status keys: {list(data.keys())}"
