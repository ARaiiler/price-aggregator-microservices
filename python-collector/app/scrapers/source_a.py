"""
Fnac scraper (simulated).

Models the French electronics & media retailer `Fnac <https://www.fnac.com>`_.
All data is generated deterministically from the product name so the
service remains fully runnable and CI-friendly without real HTTP traffic.

When real scraping is implemented, replace the body of ``fetch`` while
keeping the same return type (``List[SourceResult]``).
"""
import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import List

import httpx

from app.models.product import SourceResult
from .base import BaseScraper

logger = logging.getLogger(__name__)


class FnacScraper(BaseScraper):
    """
    Simulated Fnac scraper.

    * **Currency:** EUR
    * **Price range:** 50 – 1 500 €
    * **Listings per query:** 1 – 2
    * **In-stock probability:** ~85 %
    * **Simulated latency:** 60 – 220 ms

    Determinism is achieved by seeding a ``random.Random`` instance with
    the *product_name*, so the same query always yields the same results
    regardless of when or where the test suite runs.
    """

    source_name = "Fnac"
    base_url = "https://www.fnac.com"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def fetch(self, product_name: str) -> List[SourceResult]:
        """
        Simulate fetching product listings from Fnac.

        The search URL follows Fnac's real pattern::

            https://www.fnac.com/SearchResult/ResultList.aspx?Search={slug}
        """
        rng = random.Random(product_name)

        # Simulate network latency (60 – 220 ms)
        await asyncio.sleep(rng.uniform(0.06, 0.22))

        slug = product_name.lower().replace(" ", "+")
        results: List[SourceResult] = []

        listing_count = rng.randint(1, 2)
        for i in range(listing_count):
            variant = f" (Édition {chr(65 + i)})" if i > 0 else ""
            results.append(
                SourceResult(
                    source_name=self.source_name,
                    source_url=(
                        f"{self.base_url}/SearchResult/ResultList.aspx"
                        f"?Search={slug}&item={i}"
                    ),
                    raw_price=round(rng.uniform(50.0, 1500.0), 2),
                    raw_currency="EUR",
                    in_stock=rng.choices([True, False], weights=[85, 15])[0],
                    product_name=f"{product_name}{variant}",
                    fetched_at=datetime.now(timezone.utc),
                )
            )

        logger.info(
            "Fnac returned %d result(s) for '%s'", len(results), product_name
        )
        return results
