"""
Tests for the scraper layer
============================
Covers:
  - ``BaseScraper.safe_fetch()`` swallows exceptions and returns ``[]``
  - ``safe_fetch()`` returns the list produced by ``fetch()`` on success
  - ``safe_fetch()`` returns ``[]`` on ``httpx.TimeoutException``
  - ``FnacScraper`` and ``JumiaScraper`` return well-formed
    ``SourceResult`` objects (currency, source_name checks)
  - ``CollectorService._build_scrapers()`` returns one scraper per source
  - ``CollectorService.search()`` gathers results from all scrapers,
    normalises them, and returns a ``ComparisonResponse``
  - ``CollectorService.search()`` returns ``ComparisonResponse(sources=[])``
    when every scraper fails
  - Cache is updated (``set_latest`` called) on a successful MISS
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.models.product import SourceResult
from app.scrapers.source_a import FnacScraper
from app.scrapers.source_b import JumiaScraper


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _fake_httpx_client() -> AsyncMock:
    client = AsyncMock(spec=httpx.AsyncClient)
    client.aclose = AsyncMock()
    return client


def _make_raw(source_name: str, currency: str, price: float) -> SourceResult:
    return SourceResult(
        source_name=source_name,
        source_url=f"https://example.com/p/0",
        raw_price=price,
        raw_currency=currency,
        in_stock=True,
        product_name="laptop",
        fetched_at=datetime(2026, 2, 18, 10, 0, 0, tzinfo=timezone.utc),
    )


# --------------------------------------------------------------------------- #
# safe_fetch — exception swallowing
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_safe_fetch_returns_empty_list_when_fetch_raises() -> None:
    scraper = FnacScraper(client=_fake_httpx_client())

    with patch.object(scraper, "fetch", side_effect=RuntimeError("boom")):
        result = await scraper.safe_fetch("laptop")

    assert result == []


@pytest.mark.asyncio
async def test_safe_fetch_returns_results_when_fetch_succeeds() -> None:
    fake_result = [_make_raw("Fnac", "EUR", 100.0)]
    scraper = FnacScraper(client=_fake_httpx_client())

    with patch.object(scraper, "fetch", return_value=fake_result):
        result = await scraper.safe_fetch("laptop")

    assert result == fake_result


@pytest.mark.asyncio
async def test_safe_fetch_returns_empty_list_on_httpx_timeout() -> None:
    scraper = FnacScraper(client=_fake_httpx_client())

    with patch.object(
        scraper,
        "fetch",
        side_effect=httpx.TimeoutException("timed out"),
    ):
        result = await scraper.safe_fetch("laptop")

    assert result == []


@pytest.mark.asyncio
async def test_safe_fetch_returns_empty_list_on_network_error() -> None:
    scraper = JumiaScraper(client=_fake_httpx_client())

    with patch.object(scraper, "fetch", side_effect=httpx.ConnectError("refused")):
        result = await scraper.safe_fetch("laptop")

    assert result == []


# --------------------------------------------------------------------------- #
# FnacScraper — structural checks
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_fnac_scraper_fetch_returns_list() -> None:
    scraper = FnacScraper(client=_fake_httpx_client())
    results = await scraper.fetch("laptop")
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_fnac_scraper_source_name() -> None:
    scraper = FnacScraper(client=_fake_httpx_client())
    results = await scraper.fetch("laptop")
    assert len(results) >= 1
    for r in results:
        assert r.source_name == "Fnac"


@pytest.mark.asyncio
async def test_fnac_scraper_currency_is_eur() -> None:
    scraper = FnacScraper(client=_fake_httpx_client())
    results = await scraper.fetch("laptop")
    for r in results:
        assert r.raw_currency == "EUR"


@pytest.mark.asyncio
async def test_fnac_scraper_prices_are_positive() -> None:
    scraper = FnacScraper(client=_fake_httpx_client())
    results = await scraper.fetch("laptop")
    for r in results:
        assert r.raw_price >= 0


@pytest.mark.asyncio
async def test_fnac_scraper_deterministic() -> None:
    """Same product_name must always produce identical results."""
    scraper = FnacScraper(client=_fake_httpx_client())
    run_a = await scraper.fetch("laptop")
    run_b = await scraper.fetch("laptop")
    assert len(run_a) == len(run_b)
    for a, b in zip(run_a, run_b):
        assert a.raw_price == b.raw_price
        assert a.source_url == b.source_url


# --------------------------------------------------------------------------- #
# JumiaScraper — structural checks
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_jumia_scraper_fetch_returns_list() -> None:
    scraper = JumiaScraper(client=_fake_httpx_client())
    results = await scraper.fetch("laptop")
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_jumia_scraper_source_name() -> None:
    scraper = JumiaScraper(client=_fake_httpx_client())
    results = await scraper.fetch("laptop")
    assert len(results) >= 1
    for r in results:
        assert r.source_name == "Jumia"


@pytest.mark.asyncio
async def test_jumia_scraper_currency_is_mad() -> None:
    scraper = JumiaScraper(client=_fake_httpx_client())
    results = await scraper.fetch("laptop")
    for r in results:
        assert r.raw_currency == "MAD"


@pytest.mark.asyncio
async def test_jumia_scraper_deterministic() -> None:
    """Same product_name must always produce identical results."""
    scraper = JumiaScraper(client=_fake_httpx_client())
    run_a = await scraper.fetch("laptop")
    run_b = await scraper.fetch("laptop")
    assert len(run_a) == len(run_b)
    for a, b in zip(run_a, run_b):
        assert a.raw_price == b.raw_price
        assert a.source_url == b.source_url


# --------------------------------------------------------------------------- #
# CollectorService integration (mocked scrapers)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_collector_search_cache_miss_calls_scrapers(
    mock_cache: AsyncMock,
) -> None:
    """search() with a cache miss should run both scrapers concurrently."""
    from app.services.collector_service import CollectorService

    mock_cache.get_latest.return_value = None

    scraper_a = AsyncMock()
    scraper_a.safe_fetch = AsyncMock(
        return_value=[_make_raw("Fnac", "EUR", 100.0)]
    )
    scraper_b = AsyncMock()
    scraper_b.safe_fetch = AsyncMock(
        return_value=[_make_raw("Jumia", "MAD", 1000.0)]
    )

    svc = CollectorService.__new__(CollectorService)
    svc._cache = mock_cache
    svc._http_client = None

    with patch.object(svc, "_build_scrapers", return_value=[scraper_a, scraper_b]):
        response = await svc.search("laptop")

    scraper_a.safe_fetch.assert_called_once_with("laptop")
    scraper_b.safe_fetch.assert_called_once_with("laptop")
    assert len(response.sources) == 2


@pytest.mark.asyncio
async def test_collector_search_cache_miss_stores_result(
    mock_cache: AsyncMock,
) -> None:
    """After a successful gather the service should call set_latest."""
    from app.services.collector_service import CollectorService

    mock_cache.get_latest.return_value = None

    scraper_a = AsyncMock()
    scraper_a.safe_fetch = AsyncMock(
        return_value=[_make_raw("Fnac", "EUR", 100.0)]
    )

    svc = CollectorService.__new__(CollectorService)
    svc._cache = mock_cache
    svc._http_client = None

    with patch.object(svc, "_build_scrapers", return_value=[scraper_a]):
        await svc.search("laptop")

    mock_cache.set_latest.assert_called_once()
    mock_cache.append_history.assert_called_once()


@pytest.mark.asyncio
async def test_collector_search_cache_hit_returns_cached(
    mock_cache: AsyncMock,
    sample_comparison_response: ComparisonResponse,
) -> None:
    from app.models.responses import ComparisonResponse
    from app.services.collector_service import CollectorService

    cached = sample_comparison_response
    cached.cached = True
    mock_cache.get_latest.return_value = cached

    svc = CollectorService.__new__(CollectorService)
    svc._cache = mock_cache
    svc._http_client = None

    with patch.object(svc, "_build_scrapers", return_value=[]):
        response = await svc.search("laptop")

    assert response.cached is True
    mock_cache.set_latest.assert_not_called()


@pytest.mark.asyncio
async def test_collector_search_all_fail_returns_empty_sources(
    mock_cache: AsyncMock,
) -> None:
    from app.services.collector_service import CollectorService

    mock_cache.get_latest.return_value = None

    scraper_a = AsyncMock()
    scraper_a.safe_fetch = AsyncMock(return_value=[])
    scraper_b = AsyncMock()
    scraper_b.safe_fetch = AsyncMock(return_value=[])

    svc = CollectorService.__new__(CollectorService)
    svc._cache = mock_cache
    svc._http_client = None

    with patch.object(svc, "_build_scrapers", return_value=[scraper_a, scraper_b]):
        response = await svc.search("laptop")

    assert response.sources == []
    # No data → cache must NOT be updated
    mock_cache.set_latest.assert_not_called()


@pytest.mark.asyncio
async def test_collector_search_sources_sorted_by_price(
    mock_cache: AsyncMock,
) -> None:
    """Sources in the response must be sorted ascending by price (USD)."""
    from app.services.collector_service import CollectorService

    mock_cache.get_latest.return_value = None

    # MAD 1000 → $100, EUR 100 → $109  (Jumia is cheaper)
    scraper_a = AsyncMock()
    scraper_a.safe_fetch = AsyncMock(
        return_value=[_make_raw("Fnac", "EUR", 100.0)]
    )
    scraper_b = AsyncMock()
    scraper_b.safe_fetch = AsyncMock(
        return_value=[_make_raw("Jumia", "MAD", 1000.0)]
    )

    svc = CollectorService.__new__(CollectorService)
    svc._cache = mock_cache
    svc._http_client = None

    with patch.object(svc, "_build_scrapers", return_value=[scraper_a, scraper_b]):
        response = await svc.search("laptop")

    prices = [s.price for s in response.sources]
    assert prices == sorted(prices)


# --------------------------------------------------------------------------- #
# _build_scrapers
# --------------------------------------------------------------------------- #


def test_build_scrapers_returns_two_scrapers() -> None:
    from app.services.collector_service import CollectorService

    svc = CollectorService.__new__(CollectorService)
    svc._http_client = _fake_httpx_client()

    scrapers = svc._build_scrapers()
    assert len(scrapers) == 2


def test_build_scrapers_contains_source_a_and_b() -> None:
    from app.services.collector_service import CollectorService

    svc = CollectorService.__new__(CollectorService)
    svc._http_client = _fake_httpx_client()

    scrapers = svc._build_scrapers()
    types = {type(s) for s in scrapers}
    assert FnacScraper in types
    assert JumiaScraper in types
