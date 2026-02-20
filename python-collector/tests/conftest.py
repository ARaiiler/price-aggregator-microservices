"""
Shared pytest fixtures for the Python Data Collector test suite.

Design decisions
----------------
* No real Redis or external HTTP connections are made in any test.
* ``app.state`` is populated with mock objects before each test that
  exercises an HTTP endpoint, using FastAPI's ``app.state`` directly
  via the ASGI lifespan bypass (TestClient with ``raise_server_exceptions``).
* Async tests use ``pytest-asyncio`` in ``auto`` mode (configured in
  ``pytest.ini``).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import AsyncIterator, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.models.product import ProductListing, SourceResult
from app.models.responses import ComparisonResponse, SourceEntry

# --------------------------------------------------------------------------- #
# Settings fixture
# --------------------------------------------------------------------------- #


@pytest.fixture()
def test_settings() -> Settings:
    """Minimal Settings instance that never touches real infrastructure."""
    return Settings(
        SERVICE_NAME="test-collector",
        SERVICE_VERSION="0.0.1",
        ENVIRONMENT="development",
        SERVICE_PORT=8000,
        LOG_LEVEL="debug",
        REDIS_HOST="localhost",
        REDIS_PORT=6379,
        REDIS_PASSWORD="",
        LATEST_PRICE_TTL_SECONDS=600,
        CACHE_TTL_SECONDS=3600,
        SCRAPER_TIMEOUT_SECONDS=5.0,
    )


# --------------------------------------------------------------------------- #
# Domain data fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture()
def raw_result_eur() -> SourceResult:
    """A raw EUR-priced result from the Fnac scraper."""
    return SourceResult(
        source_name="Fnac",
        source_url="https://www.fnac.com/SearchResult/ResultList.aspx?Search=laptop&item=0",
        raw_price=100.00,   # EUR → $109.00 USD
        raw_currency="EUR",
        in_stock=True,
        product_name="laptop",
        fetched_at=datetime(2026, 2, 18, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def raw_result_mad() -> SourceResult:
    """A raw MAD-priced result from the Jumia scraper."""
    return SourceResult(
        source_name="Jumia",
        source_url="https://www.jumia.ma/catalog/?q=laptop&item=0",
        raw_price=1000.00,   # MAD → $100.00 USD
        raw_currency="MAD",
        in_stock=False,
        product_name="laptop — Standard Edition",
        fetched_at=datetime(2026, 2, 18, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def sample_product_listing() -> ProductListing:
    return ProductListing(
        source_name="Fnac",
        source_url="https://www.fnac.com/SearchResult/ResultList.aspx?Search=laptop&item=0",
        product_name="Laptop",
        price_usd=109.00,
        currency="USD",
        in_stock=True,
        fetched_at=datetime(2026, 2, 18, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def sample_comparison_response() -> ComparisonResponse:
    """A fully built ComparisonResponse with two sources."""
    return ComparisonResponse(
        product_name="Laptop",
        sources=[
            SourceEntry(
                source="Jumia",
                price=100.00,
                currency="USD",
                url="https://www.jumia.ma/catalog/?q=laptop&item=0",
                in_stock=False,
            ),
            SourceEntry(
                source="Fnac",
                price=109.00,
                currency="USD",
                url="https://www.fnac.com/SearchResult/ResultList.aspx?Search=laptop&item=0",
                in_stock=True,
            ),
        ],
        cached=False,
        timestamp=datetime(2026, 2, 18, 10, 0, 0, tzinfo=timezone.utc),
    )


# --------------------------------------------------------------------------- #
# Mock Redis client
# --------------------------------------------------------------------------- #


@pytest.fixture()
def mock_redis() -> AsyncMock:
    """
    AsyncMock that mimics the redis.asyncio.Redis interface used by
    CacheService.  Backed by a plain dict for key-value storage so
    tests can assert on stored values without touching real Redis.
    """
    store: dict = {}

    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)

    async def _get(key):
        return store.get(key)

    async def _setex(key, ttl, value):
        store[key] = value

    async def _rpush(key, value):
        if key not in store:
            store[key] = []
        store[key].append(value)
        return len(store[key])

    async def _lrange(key, start, stop):
        items = store.get(key, [])
        if stop == -1:
            return items[start:]
        return items[start: stop + 1]

    async def _delete(key):
        removed = 1 if key in store else 0
        store.pop(key, None)
        return removed

    redis.get = AsyncMock(side_effect=_get)
    redis.setex = AsyncMock(side_effect=_setex)
    redis.rpush = AsyncMock(side_effect=_rpush)
    redis.lrange = AsyncMock(side_effect=_lrange)
    redis.delete = AsyncMock(side_effect=_delete)
    redis.aclose = AsyncMock()

    # Expose the backing store for assertion convenience
    redis._store = store

    return redis


# --------------------------------------------------------------------------- #
# Mock httpx client
# --------------------------------------------------------------------------- #


@pytest.fixture()
def mock_httpx_client() -> AsyncMock:
    """AsyncMock for httpx.AsyncClient; no real HTTP is issued."""
    client = AsyncMock()
    client.aclose = AsyncMock()
    return client


# --------------------------------------------------------------------------- #
# Mock CacheService
# --------------------------------------------------------------------------- #


@pytest.fixture()
def mock_cache() -> AsyncMock:
    """
    AsyncMock that mimics CacheService's public interface.
    Individual tests override return values as needed.
    """
    cache = AsyncMock()
    cache.ping = AsyncMock(return_value=True)
    cache.get_latest = AsyncMock(return_value=None)   # cache miss by default
    cache.set_latest = AsyncMock(return_value=None)
    cache.append_history = AsyncMock(return_value=None)
    cache.get_history = AsyncMock(return_value=[])
    cache.invalidate_latest = AsyncMock(return_value=None)
    cache.invalidate_history = AsyncMock(return_value=None)
    return cache


# --------------------------------------------------------------------------- #
# Mock CollectorService
# --------------------------------------------------------------------------- #


@pytest.fixture()
def mock_collector(sample_comparison_response: ComparisonResponse) -> AsyncMock:
    """
    AsyncMock that mimics CollectorService.  Returns a default
    ComparisonResponse; individual tests override search.return_value.
    """
    collector = AsyncMock()
    collector.search = AsyncMock(return_value=sample_comparison_response)
    return collector


# --------------------------------------------------------------------------- #
# TestClient with injected mocks in app.state
# --------------------------------------------------------------------------- #


@pytest.fixture()
def client(
    test_settings: Settings,
    mock_cache: AsyncMock,
    mock_collector: AsyncMock,
) -> TestClient:
    """
    Synchronous TestClient with app.state pre-populated with mock
    services so the lifespan is never executed during tests.
    """
    app.state.settings = test_settings
    app.state.cache = mock_cache
    app.state.collector = mock_collector

    # ``raise_server_exceptions=True`` (default) surfaces Python errors
    # as real exceptions rather than silently returning 500.
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
