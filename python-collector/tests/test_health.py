"""
Tests for GET /health
======================
Covers:
  - HTTP 200 response when Redis is reachable
  - All required fields present in the response body
  - ``redis_connected: true``  when ping succeeds
  - ``redis_connected: false`` when ping raises an exception
  - ``status`` is ``"healthy"`` / ``"degraded"`` respectively
"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


# --------------------------------------------------------------------------- #
# Happy path
# --------------------------------------------------------------------------- #


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_shape(client: TestClient) -> None:
    """All documented fields must be present in the response."""
    data = client.get("/health").json()
    required_keys = {"status", "service", "version", "environment", "timestamp", "redis_connected"}
    assert required_keys.issubset(data.keys()), (
        f"Missing keys: {required_keys - set(data.keys())}"
    )


def test_health_status_healthy_when_redis_ok(client: TestClient) -> None:
    # mock_cache.ping is AsyncMock(return_value=True) by default from conftest
    data = client.get("/health").json()
    assert data["status"] == "healthy"
    assert data["redis_connected"] is True


def test_health_service_name_matches_settings(client: TestClient) -> None:
    data = client.get("/health").json()
    assert data["service"] == "test-collector"


def test_health_version_matches_settings(client: TestClient) -> None:
    data = client.get("/health").json()
    assert data["version"] == "0.0.1"


def test_health_environment_matches_settings(client: TestClient) -> None:
    data = client.get("/health").json()
    assert data["environment"] == "development"


def test_health_timestamp_is_present(client: TestClient) -> None:
    data = client.get("/health").json()
    assert data["timestamp"], "timestamp field must be non-empty"


# --------------------------------------------------------------------------- #
# Degraded path (Redis unreachable)
# --------------------------------------------------------------------------- #


def test_health_degraded_when_redis_ping_fails(
    client: TestClient,
    mock_cache: AsyncMock,
) -> None:
    """When CacheService.ping() raises, the endpoint should return
    status='degraded' and redis_connected=False — still HTTP 200."""
    mock_cache.ping.side_effect = Exception("connection refused")

    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "degraded"
    assert data["redis_connected"] is False


def test_health_degraded_when_redis_ping_returns_false(
    client: TestClient,
    mock_cache: AsyncMock,
) -> None:
    mock_cache.ping.return_value = False

    data = client.get("/health").json()
    assert data["status"] == "degraded"
    assert data["redis_connected"] is False
