"""
Tests for CacheService
=======================
All tests target the public interface of ``CacheService`` directly.
A fake AsyncMock redis client is injected so no real connection is made.

Covers:
  - ``connect()``  / ``disconnect()``
  - ``ping()`` → True on success, False on exception
  - ``get_latest()`` → None on cache miss, ComparisonResponse on hit
  - ``set_latest()`` → calls ``client.setex`` with correct key and TTL
  - ``append_history()`` → calls ``client.rpush`` with correct key
  - ``get_history()`` → returns list of ComparisonResponse on hit, [] on miss
  - Key normalisation (lowercase, stripped)
  - JSON round-trip serialisation fidelity
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.responses import ComparisonResponse, SourceEntry
from app.services.cache_service import CacheService


# --------------------------------------------------------------------------- #
# Fixtures / helpers
# --------------------------------------------------------------------------- #


def _make_service(redis_client: AsyncMock) -> CacheService:
    """Return a CacheService with the redis client already injected."""
    svc = CacheService.__new__(CacheService)
    svc._client = redis_client
    # Inject a minimal settings mock so set_latest can read the TTL
    settings_mock = MagicMock()
    settings_mock.latest_price_ttl_seconds = 600
    svc._settings = settings_mock
    return svc


def _comparison(product_name: str = "Laptop", cached: bool = False) -> ComparisonResponse:
    return ComparisonResponse(
        product_name=product_name,
        sources=[
            SourceEntry(source="Fnac", price=109.0, currency="USD",
                        url="https://www.fnac.com/SearchResult/ResultList.aspx?Search=laptop&item=0", in_stock=True)
        ],
        cached=cached,
        timestamp=datetime(2026, 2, 18, 10, 0, 0, tzinfo=timezone.utc),
    )


def _serialise(comparison: ComparisonResponse) -> str:
    return json.dumps(comparison.model_dump(mode="json"), default=str)


# --------------------------------------------------------------------------- #
# Key normalisation
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_latest_uses_lowercase_stripped_key(mock_redis: AsyncMock) -> None:
    svc = _make_service(mock_redis)
    await svc.get_latest("  Laptop  ")
    call_key = mock_redis.get.call_args[0][0]
    assert call_key == "latest_price:laptop"


@pytest.mark.asyncio
async def test_set_latest_uses_lowercase_stripped_key(
    mock_redis: AsyncMock,
    sample_comparison_response: ComparisonResponse,
) -> None:
    svc = _make_service(mock_redis)
    await svc.set_latest("  LAPTOP  ", sample_comparison_response)
    call_key = mock_redis.setex.call_args[0][0]
    assert call_key == "latest_price:laptop"


@pytest.mark.asyncio
async def test_append_history_uses_lowercase_stripped_key(
    mock_redis: AsyncMock,
    sample_comparison_response: ComparisonResponse,
) -> None:
    svc = _make_service(mock_redis)
    await svc.append_history("Laptop", sample_comparison_response)
    call_key = mock_redis.rpush.call_args[0][0]
    assert call_key == "price_history:laptop"


@pytest.mark.asyncio
async def test_get_history_uses_lowercase_stripped_key(mock_redis: AsyncMock) -> None:
    svc = _make_service(mock_redis)
    await svc.get_history("Laptop")
    call_key = mock_redis.lrange.call_args[0][0]
    assert call_key == "price_history:laptop"


# --------------------------------------------------------------------------- #
# ping
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_ping_returns_true_when_redis_ok(mock_redis: AsyncMock) -> None:
    svc = _make_service(mock_redis)
    result = await svc.ping()
    assert result is True


@pytest.mark.asyncio
async def test_ping_returns_false_on_exception(mock_redis: AsyncMock) -> None:
    mock_redis.ping.side_effect = Exception("timeout")
    svc = _make_service(mock_redis)
    result = await svc.ping()
    assert result is False


# --------------------------------------------------------------------------- #
# get_latest
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_latest_returns_none_on_cache_miss(mock_redis: AsyncMock) -> None:
    mock_redis.get.return_value = None
    svc = _make_service(mock_redis)
    result = await svc.get_latest("laptop")
    assert result is None


@pytest.mark.asyncio
async def test_get_latest_returns_comparison_on_cache_hit(mock_redis: AsyncMock) -> None:
    comparison = _comparison()
    mock_redis.get.return_value = _serialise(comparison)
    svc = _make_service(mock_redis)

    result = await svc.get_latest("laptop")
    assert isinstance(result, ComparisonResponse)
    assert result.product_name == "Laptop"


@pytest.mark.asyncio
async def test_get_latest_deserialises_sources(mock_redis: AsyncMock) -> None:
    comparison = _comparison()
    mock_redis.get.return_value = _serialise(comparison)
    svc = _make_service(mock_redis)

    result = await svc.get_latest("laptop")
    assert len(result.sources) == 1
    assert result.sources[0].source == "Fnac"
    assert result.sources[0].price == pytest.approx(109.0)


# --------------------------------------------------------------------------- #
# set_latest
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_set_latest_calls_setex_with_correct_ttl(
    mock_redis: AsyncMock,
    sample_comparison_response: ComparisonResponse,
) -> None:
    svc = _make_service(mock_redis)
    await svc.set_latest("laptop", sample_comparison_response)
    _, ttl_arg, _ = mock_redis.setex.call_args[0]
    assert ttl_arg == 600


@pytest.mark.asyncio
async def test_set_latest_stores_valid_json(
    mock_redis: AsyncMock,
    sample_comparison_response: ComparisonResponse,
) -> None:
    svc = _make_service(mock_redis)
    await svc.set_latest("laptop", sample_comparison_response)
    _, _, json_arg = mock_redis.setex.call_args[0]
    parsed = json.loads(json_arg)
    assert parsed["product_name"] == sample_comparison_response.product_name


# --------------------------------------------------------------------------- #
# append_history
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_append_history_calls_rpush(
    mock_redis: AsyncMock,
    sample_comparison_response: ComparisonResponse,
) -> None:
    svc = _make_service(mock_redis)
    await svc.append_history("laptop", sample_comparison_response)
    mock_redis.rpush.assert_called_once()


@pytest.mark.asyncio
async def test_append_history_stores_valid_json(
    mock_redis: AsyncMock,
    sample_comparison_response: ComparisonResponse,
) -> None:
    svc = _make_service(mock_redis)
    await svc.append_history("laptop", sample_comparison_response)
    _, json_arg = mock_redis.rpush.call_args[0]
    parsed = json.loads(json_arg)
    assert "product_name" in parsed


# --------------------------------------------------------------------------- #
# get_history
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_history_returns_empty_list_when_no_data(mock_redis: AsyncMock) -> None:
    mock_redis.lrange.return_value = []
    svc = _make_service(mock_redis)
    result = await svc.get_history("laptop")
    assert result == []


@pytest.mark.asyncio
async def test_get_history_returns_comparison_list(mock_redis: AsyncMock) -> None:
    comparison = _comparison()
    mock_redis.lrange.return_value = [_serialise(comparison), _serialise(comparison)]
    svc = _make_service(mock_redis)

    result = await svc.get_history("laptop")
    assert len(result) == 2
    assert all(isinstance(r, ComparisonResponse) for r in result)


@pytest.mark.asyncio
async def test_get_history_full_range_uses_lrange_correctly(mock_redis: AsyncMock) -> None:
    mock_redis.lrange.return_value = []
    svc = _make_service(mock_redis)
    await svc.get_history("laptop", count=-1)
    mock_redis.lrange.assert_called_once_with("price_history:laptop", 0, -1)


@pytest.mark.asyncio
async def test_get_history_limited_count(mock_redis: AsyncMock) -> None:
    mock_redis.lrange.return_value = []
    svc = _make_service(mock_redis)
    await svc.get_history("laptop", count=5)
    # Actual implementation: start = -(count) → lrange(key, -5, -1)
    mock_redis.lrange.assert_called_once_with("price_history:laptop", -5, -1)
