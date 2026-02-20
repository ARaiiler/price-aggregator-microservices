"""
Tests for POST /internal/search
================================
Covers:
  - Valid JSON body → 200 + ComparisonResponse shape
  - Wrong Content-Type → 400 + ErrorResponse shape
  - Blank / missing ``product_name`` → 422 + ErrorResponse shape
  - Cache HIT path: ``collector.search`` is NOT called; ``cached=true``
  - Cache MISS path: ``collector.search`` IS called; result returned
  - One scraper fails → partial results from the surviving source
  - All scrapers fail → 503 with ``detail: "All external sources failed"``
  - Unexpected internal error → 500 + ErrorResponse shape
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.models.responses import ComparisonResponse, SourceEntry


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


VALID_PAYLOAD = {"product_name": "laptop"}

HEADERS_JSON = {"Content-Type": "application/json"}
HEADERS_FORM = {"Content-Type": "application/x-www-form-urlencoded"}


def _cached_response(product_name: str = "Laptop") -> ComparisonResponse:
    return ComparisonResponse(
        product_name=product_name,
        sources=[
            SourceEntry(source="Fnac", price=109.00, currency="USD",
                        url="https://www.fnac.com/SearchResult/ResultList.aspx?Search=laptop&item=0",
                        in_stock=True)
        ],
        cached=True,
        timestamp=datetime(2026, 2, 18, 10, 0, 0, tzinfo=timezone.utc),
    )


def _empty_response() -> ComparisonResponse:
    return ComparisonResponse(
        product_name="Laptop",
        sources=[],
        cached=False,
        timestamp=datetime(2026, 2, 18, 10, 0, 0, tzinfo=timezone.utc),
    )


# --------------------------------------------------------------------------- #
# Content-Type enforcement
# --------------------------------------------------------------------------- #


def test_search_rejects_non_json_content_type(client: TestClient) -> None:
    response = client.post(
        "/internal/search",
        content="product_name=laptop",
        headers=HEADERS_FORM,
    )
    assert response.status_code == 400
    body = response.json()
    # Must conform to ErrorResponse envelope
    assert "detail" in body
    assert "status_code" in body
    assert body["status_code"] == 400


def test_search_accepts_explicit_json_content_type(
    client: TestClient,
    mock_collector: AsyncMock,
    sample_comparison_response: ComparisonResponse,
) -> None:
    mock_collector.search.return_value = sample_comparison_response
    response = client.post("/internal/search", json=VALID_PAYLOAD)
    assert response.status_code == 200


# --------------------------------------------------------------------------- #
# Validation errors
# --------------------------------------------------------------------------- #


def test_search_rejects_blank_product_name(client: TestClient) -> None:
    response = client.post("/internal/search", json={"product_name": "   "})
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body


def test_search_rejects_missing_product_name(client: TestClient) -> None:
    response = client.post("/internal/search", json={})
    assert response.status_code == 422


def test_search_rejects_empty_string_product_name(client: TestClient) -> None:
    response = client.post("/internal/search", json={"product_name": ""})
    assert response.status_code == 422


# --------------------------------------------------------------------------- #
# Response shape
# --------------------------------------------------------------------------- #


def test_search_response_shape(
    client: TestClient,
    mock_collector: AsyncMock,
    sample_comparison_response: ComparisonResponse,
) -> None:
    mock_collector.search.return_value = sample_comparison_response
    data = client.post("/internal/search", json=VALID_PAYLOAD).json()

    required_keys = {"product_name", "sources", "cached", "timestamp"}
    assert required_keys.issubset(data.keys())


def test_search_sources_shape(
    client: TestClient,
    mock_collector: AsyncMock,
    sample_comparison_response: ComparisonResponse,
) -> None:
    mock_collector.search.return_value = sample_comparison_response
    data = client.post("/internal/search", json=VALID_PAYLOAD).json()

    assert isinstance(data["sources"], list)
    assert len(data["sources"]) > 0

    entry_keys = {"source", "price", "currency", "url", "in_stock"}
    for entry in data["sources"]:
        assert entry_keys.issubset(entry.keys())


# --------------------------------------------------------------------------- #
# Cache HIT path
# --------------------------------------------------------------------------- #


def test_search_cache_hit_returns_cached_flag(
    client: TestClient,
    mock_cache: AsyncMock,
    mock_collector: AsyncMock,
) -> None:
    """When cache has a stored result, ``cached`` must be True and the
    collector service's search method must NOT be called."""
    cached = _cached_response()
    mock_cache.get_latest.return_value = cached
    # Override collector on app.state to detect spurious calls
    mock_collector.search.return_value = None

    response = client.post("/internal/search", json=VALID_PAYLOAD)
    assert response.status_code == 200

    data = response.json()
    assert data["cached"] is True
    mock_collector.search.assert_not_called()


# --------------------------------------------------------------------------- #
# Cache MISS path
# --------------------------------------------------------------------------- #


def test_search_cache_miss_calls_collector(
    client: TestClient,
    mock_cache: AsyncMock,
    mock_collector: AsyncMock,
    sample_comparison_response: ComparisonResponse,
) -> None:
    """On cache miss the collector.search() must be invoked and the
    response must have ``cached=False``."""
    mock_cache.get_latest.return_value = None  # MISS
    mock_collector.search.return_value = sample_comparison_response

    response = client.post("/internal/search", json=VALID_PAYLOAD)
    assert response.status_code == 200

    mock_collector.search.assert_called_once_with("laptop")
    data = response.json()
    assert data["cached"] is False


# --------------------------------------------------------------------------- #
# All scrapers fail → HTTP 503
# --------------------------------------------------------------------------- #


def test_search_all_scrapers_fail_returns_503(
    client: TestClient,
    mock_cache: AsyncMock,
    mock_collector: AsyncMock,
) -> None:
    """When every scraper fails the endpoint must return HTTP 503 with
    a clear error message — NOT 200 with empty sources."""
    mock_cache.get_latest.return_value = None
    mock_collector.search.return_value = _empty_response()

    # HTTPException(503) is raised inside the route, so we need
    # raise_server_exceptions=False to capture the HTTP response.
    from app.main import app as fastapi_app
    fastapi_app.state.cache = mock_cache
    fastapi_app.state.collector = mock_collector
    fastapi_app.state.settings = client.app.state.settings

    with TestClient(fastapi_app, raise_server_exceptions=False) as tc:
        response = tc.post("/internal/search", json=VALID_PAYLOAD)

    assert response.status_code == 503
    body = response.json()
    assert "detail" in body
    assert body["detail"] == "All external sources failed"


def test_search_all_scrapers_fail_does_not_write_cache(
    client: TestClient,
    mock_cache: AsyncMock,
    mock_collector: AsyncMock,
) -> None:
    """When all scrapers fail (503), Redis must NOT be written to —
    neither ``set_latest`` nor ``append_history`` should be called."""
    mock_cache.get_latest.return_value = None
    mock_collector.search.return_value = _empty_response()

    from app.main import app as fastapi_app
    fastapi_app.state.cache = mock_cache
    fastapi_app.state.collector = mock_collector
    fastapi_app.state.settings = client.app.state.settings

    with TestClient(fastapi_app, raise_server_exceptions=False) as tc:
        response = tc.post("/internal/search", json=VALID_PAYLOAD)

    assert response.status_code == 503
    # The CollectorService already skips cache writes when sources is
    # empty, but verify the route never calls them either.
    mock_cache.set_latest.assert_not_called()
    mock_cache.append_history.assert_not_called()


# --------------------------------------------------------------------------- #
# Partial failure (one scraper succeeds)
# --------------------------------------------------------------------------- #


def test_search_partial_failure_returns_available_sources(
    client: TestClient,
    mock_cache: AsyncMock,
    mock_collector: AsyncMock,
) -> None:
    partial = ComparisonResponse(
        product_name="Laptop",
        sources=[
            SourceEntry(source="Fnac", price=109.00, currency="USD",
                        url="https://www.fnac.com/SearchResult/ResultList.aspx?Search=laptop&item=0",
                        in_stock=True)
        ],
        cached=False,
        timestamp=datetime(2026, 2, 18, 10, 0, 0, tzinfo=timezone.utc),
    )
    mock_cache.get_latest.return_value = None
    mock_collector.search.return_value = partial

    response = client.post("/internal/search", json=VALID_PAYLOAD)
    assert response.status_code == 200

    data = response.json()
    assert len(data["sources"]) == 1
    assert data["sources"][0]["source"] == "Fnac"


# --------------------------------------------------------------------------- #
# Internal server error
# --------------------------------------------------------------------------- #


def test_search_returns_500_on_unexpected_error(
    client: TestClient,
    mock_cache: AsyncMock,
    mock_collector: AsyncMock,
) -> None:
    mock_cache.get_latest.return_value = None
    mock_collector.search.side_effect = RuntimeError("unexpected boom")

    # ``raise_server_exceptions=True`` in conftest – disable for this test
    from app.main import app as fastapi_app
    fastapi_app.state.cache = mock_cache
    fastapi_app.state.collector = mock_collector

    with TestClient(fastapi_app, raise_server_exceptions=False) as tc:
        response = tc.post("/internal/search", json=VALID_PAYLOAD)

    assert response.status_code == 500
    body = response.json()
    assert "detail" in body
    assert body["status_code"] == 500
