import sys
from types import ModuleType
from unittest.mock import Mock

import pytest
import requests

from frontend.utils.api_client import APIClient


def test_health_check_returns_backend_status_and_uses_20_second_timeout(monkeypatch):
    response = Mock(status_code=200)
    response.json.return_value = {
        "status": "healthy",
        "database": "postgresql_connected",
    }
    get_mock = Mock(return_value=response)
    monkeypatch.setattr("frontend.utils.api_client.requests.get", get_mock)
    client = APIClient("https://backend.example/api/v1")

    result = client.check_health()

    assert get_mock.call_args.args == ("https://backend.example/api/v1/health",)
    assert get_mock.call_args.kwargs["timeout"] == 20
    assert result["status"] == "healthy"
    assert result["database"] == "postgresql_connected"
    assert result["diagnostic"] == "The backend health check succeeded."


@pytest.mark.parametrize(
    ("exception", "expected_status", "diagnostic"),
    [
        (
            requests.exceptions.Timeout,
            "offline",
            "The health check timed out after 20 seconds.",
        ),
        (
            requests.exceptions.ConnectionError,
            "offline",
            "Could not connect to the backend.",
        ),
    ],
)
def test_health_check_reports_connection_failures(
    monkeypatch, exception, expected_status, diagnostic
):
    get_mock = Mock(side_effect=exception("contains no displayed details"))
    monkeypatch.setattr("frontend.utils.api_client.requests.get", get_mock)

    result = APIClient("https://backend.example/api/v1").check_health()

    assert result["status"] == expected_status
    assert diagnostic in result["diagnostic"]


def test_health_check_reports_unsuccessful_http_response(monkeypatch):
    response = Mock(status_code=503)
    get_mock = Mock(return_value=response)
    monkeypatch.setattr("frontend.utils.api_client.requests.get", get_mock)

    result = APIClient("https://backend.example/api/v1").check_health()

    assert result == {
        "status": "unhealthy",
        "diagnostic": "The backend returned HTTP 503 for its health check.",
    }


def test_health_check_reports_invalid_json(monkeypatch):
    response = Mock(status_code=200)
    response.json.side_effect = ValueError("response body is not displayed")
    monkeypatch.setattr(
        "frontend.utils.api_client.requests.get",
        Mock(return_value=response),
    )

    result = APIClient("https://backend.example/api/v1").check_health()

    assert result == {
        "status": "unhealthy",
        "diagnostic": "The backend returned invalid JSON for its health check.",
    }


@pytest.mark.parametrize(
    ("backend_url", "expected_url"),
    [
        ("https://backend.example/api/v1", "https://backend.example/api/v1/health"),
        (
            "https://backend.example/api/v1/health",
            "https://backend.example/api/v1/health",
        ),
        (
            "https://backend.example/api/v1/health/health/",
            "https://backend.example/api/v1/health",
        ),
    ],
)
def test_health_url_appends_health_exactly_once(backend_url, expected_url):
    assert APIClient(backend_url).health_url == expected_url


def test_health_check_rejects_incorrect_backend_url_without_request(monkeypatch):
    get_mock = Mock()
    monkeypatch.setattr("frontend.utils.api_client.requests.get", get_mock)

    result = APIClient("not-a-url").check_health()

    assert result["status"] == "offline"
    assert "Invalid BACKEND_API_URL" in result["diagnostic"]
    assert get_mock.call_count == 0


def test_health_url_does_not_expose_credentials_or_query_values():
    client = APIClient("https://user:password@backend.example/api/v1")

    assert client.health_url == "https://backend.example/api/v1/health"
    assert "password" not in client.health_url


def test_health_url_rejects_query_parameters_without_exposing_values():
    client = APIClient("https://backend.example/api/v1?token=do-not-display")

    assert client.health_url is None
    result = client.check_health()
    assert "do-not-display" not in result["diagnostic"]


def test_backend_url_is_read_from_streamlit_secrets(monkeypatch):
    streamlit_module = ModuleType("streamlit")
    streamlit_module.__path__ = []
    streamlit_module.secrets = {
        "BACKEND_API_URL": "https://secret-configured.example/api/v1"
    }
    errors_module = ModuleType("streamlit.errors")

    class StreamlitSecretNotFoundError(Exception):
        pass

    errors_module.StreamlitSecretNotFoundError = StreamlitSecretNotFoundError
    monkeypatch.setitem(sys.modules, "streamlit", streamlit_module)
    monkeypatch.setitem(sys.modules, "streamlit.errors", errors_module)
    monkeypatch.delenv("BACKEND_API_URL", raising=False)

    client = APIClient()

    assert client.base_url == "https://secret-configured.example/api/v1"
    assert (
        client.health_url
        == "https://secret-configured.example/api/v1/health"
    )
