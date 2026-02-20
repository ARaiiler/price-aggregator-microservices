"""
Jumia scraper (simulated).

Models the pan-African e-commerce marketplace
`Jumia Morocco <https://www.jumia.ma>`_.  All data is generated
deterministically from the product name so the service remains fully
runnable and CI-friendly without real HTTP traffic.

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


class JumiaScraper(BaseScraper):
    """
    Simulated Jumia Morocco scraper.

    * **Currency:** MAD (Moroccan Dirham)
    * **Price range:** 40 – 1 300 MAD
    * **Listings per query:** 1 – 3
    * **In-stock probability:** ~70 % (higher out-of-stock chance)
    * **Simulated latency:** 100 – 350 ms

    Determinism is achieved by seeding a ``random.Random`` instance with
    the *product_name*, so the same query always yields the same results
    regardless of when or where the test suite runs.
    """

    source_name = "Jumia"
    base_url = "https://www.jumia.ma"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def fetch(self, product_name: str) -> List[SourceResult]:
        """
        Simulate fetching product listings from Jumia Morocco.

        The catalog URL follows Jumia's real pattern::

            https://www.jumia.ma/catalog/?q={slug}
        """
        rng = random.Random(product_name)

        # Simulate network latency (100 – 350 ms)
        await asyncio.sleep(rng.uniform(0.10, 0.35))

        slug = product_name.lower().replace(" ", "+")
        results: List[SourceResult] = []

        listing_count = rng.randint(1, 3)
        for i in range(listing_count):
            grade = rng.choice(["Standard", "Pro", "Lite", "Premium"])
            results.append(
                SourceResult(
                    source_name=self.source_name,
                    source_url=(
                        f"{self.base_url}/catalog/?q={slug}&item={i}"
                    ),
                    raw_price=round(rng.uniform(40.0, 1300.0), 2),
                    raw_currency="MAD",
                    in_stock=rng.choices([True, False], weights=[70, 30])[0],
                    product_name=f"{product_name} — {grade} Edition",
                    fetched_at=datetime.now(timezone.utc),
                )
            )

        logger.info(
            "Jumia returned %d result(s) for '%s'", len(results), product_name
        )
        return results
