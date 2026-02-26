"""
Currency normalisation service.
Converts prices from any source currency into the configured default
currency (e.g. MAD) before sending data to the Node.js gateway.

Uses static fallback rates so the service works offline; rates can be
refreshed from a live API when RAPIDAPI_KEY is set.
"""

import logging
from datetime import datetime
from typing import Dict

import httpx

from ..config import get_settings
from ..models import CurrencyRates

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Static fallback rates (base = USD) ─────────────────────

_FALLBACK_RATES: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "MAD": 10.05,
    "CAD": 1.36,
    "JPY": 149.50,
    "CNY": 7.24,
    "TRY": 30.25,
    "INR": 83.12,
    "AED": 3.67,
}


class CurrencyNormalizer:
    """Convert arbitrary price+currency → target currency."""

    def __init__(self) -> None:
        self.rates = CurrencyRates(
            base="USD",
            rates=_FALLBACK_RATES.copy(),
            updated_at=datetime.utcnow(),
        )
        self.target = settings.DEFAULT_CURRENCY

    # ── live refresh (optional) ────────────────────────────

    async def refresh_rates(self) -> None:
        """Try to fetch live rates; fall back to static on failure."""
        if not settings.RAPIDAPI_KEY:
            logger.info("No RAPIDAPI_KEY set – using static exchange rates")
            return

        url = "https://open.er-api.com/v6/latest/USD"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                if data.get("result") == "success":
                    self.rates.rates = data["rates"]
                    self.rates.updated_at = datetime.utcnow()
                    logger.info("Exchange rates refreshed from API")
        except Exception as exc:
            logger.warning("Could not refresh rates (%s) – using fallback", exc)

    # ── conversion ─────────────────────────────────────────

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str | None = None,
    ) -> float:
        """
        Convert *amount* from *from_currency* to *to_currency*
        (defaults to self.target which comes from settings).

        Conversion: amount → USD → target
        """
        to_currency = (to_currency or self.target).upper()
        from_currency = from_currency.upper()

        if from_currency == to_currency:
            return round(amount, 2)

        # from → USD
        from_rate = self.rates.rates.get(from_currency, 1.0)
        amount_usd = amount / from_rate

        # USD → target
        to_rate = self.rates.rates.get(to_currency, 1.0)
        return round(amount_usd * to_rate, 2)

    def get_rates(self) -> CurrencyRates:
        return self.rates
