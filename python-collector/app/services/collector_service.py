"""
Collector service — the core orchestration layer.

Responsibilities
----------------
1. Dispatch async fetch tasks to every registered scraper in parallel
   using ``asyncio.gather`` (adapter pattern: all scrapers share the
   same ``BaseScraper`` interface, so adding a source requires zero
   changes outside ``_build_scrapers``).
2. Normalise all raw results via the normaliser utility (EUR/GBP → USD).
3. Group normalised listings by source; pick the lowest price per source.
4. Read from / write to the cache service.
5. Return a ``ComparisonResponse`` to the route handler.

Adding a new data source
------------------------
1. Create a scraper module in ``app/scrapers/`` that subclasses
   ``BaseScraper`` and implements ``fetch()``.
2. Import the class here and add an instance to ``_build_scrapers()``.
No other code changes are required.
"""
import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List

import httpx

from app.config import Settings
from app.models.product import ProductListing
from app.models.responses import ComparisonResponse, SourceEntry
from app.scrapers.source_a import FnacScraper
from app.scrapers.source_b import JumiaScraper
from app.services.cache_service import CacheService
from app.utils.normalizer import normalize_result

logger = logging.getLogger(__name__)


class CollectorService:
    """
    Orchestrates the full price-collection pipeline for a given query.

    Parameters
    ----------
    settings:
        Application configuration (injected at startup).
    cache:
        Shared :class:`CacheService` instance (injected at startup).
    """

    def __init__(self, settings: Settings, cache: CacheService) -> None:
        self._settings = settings
        self._cache = cache
        # A single shared httpx client is reused across all scrapers and
        # requests for efficient connection pooling.
        self._http_client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    async def startup(self) -> None:
        """Initialise shared resources (called from the FastAPI lifespan)."""
        self._http_client = httpx.AsyncClient(
            timeout=self._settings.scraper_timeout_seconds
        )
        logger.info("CollectorService started — httpx client initialised.")

    async def shutdown(self) -> None:
        """Release shared resources (called from the FastAPI lifespan)."""
        if self._http_client:
            await self._http_client.aclose()
            logger.info("CollectorService stopped — httpx client closed.")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def search(self, product_name: str) -> ComparisonResponse:
        """
        Return a per-source price comparison for *product_name*.

        Cache strategy
        --------------
        * **HIT**  — ``latest_price:{product_name}`` exists → return immediately
          (``cached=True``).  Scrapers are not contacted.
        * **MISS** — Fan-out to all scrapers concurrently via
          ``asyncio.gather``, normalise results, then:

          1. ``RPUSH`` the new result onto ``price_history:{product_name}``
             (append-only, no expiry — full price history).
          2. ``SETEX`` the result under ``latest_price:{product_name}``
             with a 10-minute TTL (fast-path for repeated queries).

        A failing scraper never raises — ``safe_fetch()`` absorbs
        exceptions and returns ``[]`` so other sources still contribute.
        """
        # ── 1. Check latest_price cache  (key: latest_price:{name}) ───── #
        cached = await self._cache.get_latest(product_name)
        if cached is not None:
            cached.cached = True
            logger.info(
                "Cache HIT  latest_price for '%s'  sources=%d",
                product_name, len(cached.sources),
            )
            return cached

        # ── 2. Parallel scrape (asyncio.gather) ───────────────────────── #
        scrapers = self._build_scrapers()
        tasks = [s.safe_fetch(product_name) for s in scrapers]
        source_outputs = await asyncio.gather(*tasks)

        logger.info(
            "Parallel scrape complete for '%s': %d/%d source(s) returned data",
            product_name,
            sum(1 for out in source_outputs if out),
            len(scrapers),
        )

        # ── 3. Normalise raw prices → USD and group by source ─────────── #
        grouped: Dict[str, List[ProductListing]] = defaultdict(list)
        for output in source_outputs:
            for raw in output:
                listing = normalize_result(raw)     # EUR / GBP → USD
                grouped[listing.source_name].append(listing)

        # ── 4. Pick best (lowest) price per source ────────────────────── #
        source_entries: List[SourceEntry] = []
        for source_name, listings in grouped.items():
            if not listings:
                continue
            best = min(listings, key=lambda lst: lst.price_usd)
            source_entries.append(
                SourceEntry(
                    source=source_name,
                    price=best.price_usd,
                    currency="USD",
                    url=best.source_url,
                    in_stock=best.in_stock,
                )
            )

        # ── 5. Sort cheapest-first ────────────────────────────────────── #
        source_entries.sort(key=lambda e: e.price)

        response = ComparisonResponse(
            product_name=product_name.strip().title(),
            sources=source_entries,
            cached=False,
            timestamp=datetime.now(timezone.utc),
        )

        # ── 6. Persist to Redis ───────────────────────────────────────── #
        if source_entries:
            # a) Append to history list  (key: price_history:{name}, no TTL)
            await self._cache.append_history(product_name, response)

            # b) Cache latest result     (key: latest_price:{name}, TTL 10 min)
            await self._cache.set_latest(product_name, response)

        logger.info(
            "Comparison built for '%s': %d source(s) — written to history + latest",
            product_name, len(source_entries),
        )
        return response

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _build_scrapers(self) -> list:
        """
        Instantiate and return all registered scrapers.

        Pass the shared HTTP client so scrapers can reuse connections.
        To add a source: import its class and append an instance here.
        """
        return [
            FnacScraper(client=self._http_client),
            JumiaScraper(client=self._http_client),
        ]
