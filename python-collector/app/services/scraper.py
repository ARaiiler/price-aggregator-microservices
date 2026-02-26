"""
Product scraper service.
Fetches product pricing data from multiple simulated (or real) sources
and normalises prices via CurrencyNormalizer before returning results.

Each source returns prices in its own currency to demonstrate the
data‑transformation requirement.
"""

import asyncio
import hashlib
import logging
import random
from datetime import datetime
from typing import Dict, List

import httpx

from ..config import get_settings
from ..models import Product
from .normalizer import CurrencyNormalizer

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Simulated catalogue per source ─────────────────────────
# In production these would be HTTP calls / BeautifulSoup scrapes.

_CATALOGUE: Dict[str, list] = {
    "Amazon": [
        {"kw": ["laptop", "pc", "computer"], "name": "Laptop Pro 15\"", "base_usd": 799.99, "cur": "USD", "img": "https://via.placeholder.com/150?text=Laptop"},
        {"kw": ["phone", "smartphone", "iphone", "mobile"], "name": "SmartPhone X 128GB", "base_usd": 699.00, "cur": "USD", "img": "https://via.placeholder.com/150?text=Phone"},
        {"kw": ["headphones", "earbuds", "audio", "casque"], "name": "Wireless Headphones ANC", "base_usd": 149.99, "cur": "USD", "img": "https://via.placeholder.com/150?text=Headphones"},
        {"kw": ["keyboard", "clavier"], "name": "Mechanical Keyboard RGB", "base_usd": 89.95, "cur": "USD", "img": "https://via.placeholder.com/150?text=Keyboard"},
        {"kw": ["monitor", "ecran", "screen"], "name": "4K Monitor 27\"", "base_usd": 349.00, "cur": "USD", "img": "https://via.placeholder.com/150?text=Monitor"},
        {"kw": ["mouse", "souris"], "name": "Gaming Mouse 16K DPI", "base_usd": 59.99, "cur": "USD", "img": "https://via.placeholder.com/150?text=Mouse"},
        {"kw": ["tablet", "ipad", "tablette"], "name": "Tablet Pro 11\"", "base_usd": 499.00, "cur": "USD", "img": "https://via.placeholder.com/150?text=Tablet"},
        {"kw": ["watch", "montre", "smartwatch"], "name": "SmartWatch Series 9", "base_usd": 399.00, "cur": "USD", "img": "https://via.placeholder.com/150?text=Watch"},
    ],
    "Jumia": [
        {"kw": ["laptop", "pc", "computer"], "name": "Laptop Budget 14\"", "base_usd": 420.00, "cur": "MAD", "img": "https://via.placeholder.com/150?text=Laptop"},
        {"kw": ["phone", "smartphone", "iphone", "mobile"], "name": "Téléphone Y 64GB", "base_usd": 250.00, "cur": "MAD", "img": "https://via.placeholder.com/150?text=Phone"},
        {"kw": ["headphones", "earbuds", "audio", "casque"], "name": "Casque Bluetooth Sport", "base_usd": 35.00, "cur": "MAD", "img": "https://via.placeholder.com/150?text=Headphones"},
        {"kw": ["keyboard", "clavier"], "name": "Clavier Mécanique K60", "base_usd": 55.00, "cur": "MAD", "img": "https://via.placeholder.com/150?text=Keyboard"},
        {"kw": ["monitor", "ecran", "screen"], "name": "Écran Full-HD 24\"", "base_usd": 180.00, "cur": "MAD", "img": "https://via.placeholder.com/150?text=Monitor"},
        {"kw": ["mouse", "souris"], "name": "Souris Sans Fil 2.4G", "base_usd": 15.00, "cur": "MAD", "img": "https://via.placeholder.com/150?text=Mouse"},
        {"kw": ["tablet", "ipad", "tablette"], "name": "Tablette A8 10.5\"", "base_usd": 220.00, "cur": "MAD", "img": "https://via.placeholder.com/150?text=Tablet"},
        {"kw": ["watch", "montre", "smartwatch"], "name": "Montre Connectée Fit", "base_usd": 75.00, "cur": "MAD", "img": "https://via.placeholder.com/150?text=Watch"},
    ],
    "eBay": [
        {"kw": ["laptop", "pc", "computer"], "name": "Refurb ThinkPad T480", "base_usd": 379.00, "cur": "EUR", "img": "https://via.placeholder.com/150?text=Laptop"},
        {"kw": ["phone", "smartphone", "iphone", "mobile"], "name": "Smartphone Z 256GB", "base_usd": 549.99, "cur": "EUR", "img": "https://via.placeholder.com/150?text=Phone"},
        {"kw": ["headphones", "earbuds", "audio", "casque"], "name": "Over-Ear Studio Headphones", "base_usd": 112.50, "cur": "EUR", "img": "https://via.placeholder.com/150?text=Headphones"},
        {"kw": ["keyboard", "clavier"], "name": "Compact 65% Keyboard", "base_usd": 72.00, "cur": "EUR", "img": "https://via.placeholder.com/150?text=Keyboard"},
        {"kw": ["monitor", "ecran", "screen"], "name": "Curved Monitor 32\" QHD", "base_usd": 299.00, "cur": "EUR", "img": "https://via.placeholder.com/150?text=Monitor"},
        {"kw": ["mouse", "souris"], "name": "Ergonomic Vertical Mouse", "base_usd": 34.50, "cur": "EUR", "img": "https://via.placeholder.com/150?text=Mouse"},
        {"kw": ["tablet", "ipad", "tablette"], "name": "Android Tablet 10\"", "base_usd": 189.00, "cur": "EUR", "img": "https://via.placeholder.com/150?text=Tablet"},
        {"kw": ["watch", "montre", "smartwatch"], "name": "Classic Hybrid Watch", "base_usd": 199.00, "cur": "EUR", "img": "https://via.placeholder.com/150?text=Watch"},
    ],
}


def _product_id(name: str, source: str) -> str:
    """Deterministic short id from name+source."""
    return hashlib.md5(f"{source}:{name}".encode()).hexdigest()[:12]


class ProductScraper:
    """
    Scrapes multiple sources in parallel and normalises currencies.
    """

    def __init__(self, normalizer: CurrencyNormalizer | None = None) -> None:
        self.normalizer = normalizer or CurrencyNormalizer()
        self.sources = list(_CATALOGUE.keys())

    # ── public API ─────────────────────────────────────────

    async def search_products(self, query: str) -> List[Product]:
        """
        Search all sources concurrently, normalise prices, return
        a flat sorted list.
        """
        tasks = [
            self._scrape_source(source, query) for source in self.sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        products: List[Product] = []
        for res in results:
            if isinstance(res, Exception):
                logger.error("Source scrape failed: %s", res)
                continue
            products.extend(res)

        # sort by normalised price
        products.sort(key=lambda p: p.price)
        return products

    # ── per-source scraper ─────────────────────────────────

    async def _scrape_source(self, source: str, query: str) -> List[Product]:
        """Simulate scraping one marketplace."""
        # small delay to mimic network I/O
        await asyncio.sleep(random.uniform(0.05, 0.2))

        query_lower = query.strip().lower()
        catalogue = _CATALOGUE.get(source, [])
        matched: List[Product] = []

        for item in catalogue:
            # keyword match (any keyword substring present in query)
            if not any(kw in query_lower for kw in item["kw"]):
                # also allow query as substring of product name
                if query_lower not in item["name"].lower():
                    continue

            # Simulate price jitter ± 5 %
            raw_price = item["base_usd"] * random.uniform(0.95, 1.05)
            original_currency = item["cur"]

            # Express raw price in the source's native currency
            original_price = self.normalizer.convert(raw_price, "USD", original_currency)

            # Normalise to target currency
            normalised_price = self.normalizer.convert(
                original_price, original_currency
            )

            slug = item["name"].lower().replace(" ", "-").replace("\"", "")
            product = Product(
                id=_product_id(item["name"], source),
                name=item["name"],
                price=normalised_price,
                original_price=original_price,
                source=source,
                url=f"https://{source.lower()}.com/dp/{slug}",
                image_url=item.get("img"),
                currency=self.normalizer.target,
                original_currency=original_currency,
                in_stock=random.random() < 0.85,
                rating=round(random.uniform(3.0, 5.0), 1),
                timestamp=datetime.utcnow(),
            )
            matched.append(product)

        return matched
