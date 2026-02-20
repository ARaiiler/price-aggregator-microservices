"""
Price and currency normalisation utilities.

All prices are converted to USD before being returned to the caller.
The exchange-rate table below is intentionally minimal for the
prototype.  In production, replace the static table with a call to a
live FX rates API (e.g. Open Exchange Rates, Frankfurter).
"""
import logging
from typing import Dict

from app.models.product import ProductListing, SourceResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static FX conversion table: <currency ISO code> → <rate vs. USD>
# Example: 1 EUR = 1.09 USD, so EUR rate is 1.09.
# ---------------------------------------------------------------------------
_FX_RATES: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.09,
    "GBP": 1.27,
    "JPY": 0.0067,
    "CAD": 0.74,
    "AUD": 0.65,
    "MAD": 0.10,     # 1 MAD ≈ 0.10 USD
}


def _to_usd(amount: float, currency: str) -> float:
    """
    Convert *amount* in *currency* to USD.

    Falls back to treating the amount as USD if the currency code is not
    found in the conversion table (logs a warning in that case).
    """
    code = currency.strip().upper()
    rate = _FX_RATES.get(code)
    if rate is None:
        logger.warning(
            "Unknown currency '%s'; treating as USD (no conversion applied).",
            currency,
        )
        rate = 1.0
    return round(amount * rate, 2)


def normalize_result(raw: SourceResult) -> ProductListing:
    """
    Convert a raw :class:`SourceResult` into a normalised
    :class:`ProductListing`.

    Normalisation steps
    -------------------
    1. Convert ``raw_price`` from ``raw_currency`` to USD.
    2. Trim and title-case ``product_name``.
    3. Pass all other fields through unchanged.

    Parameters
    ----------
    raw:
        A single un-normalised result from a scraper.

    Returns
    -------
    ProductListing
        A fully normalised listing ready to be returned to the client.
    """
    price_usd = _to_usd(raw.raw_price, raw.raw_currency)

    return ProductListing(
        source_name=raw.source_name,
        source_url=raw.source_url,
        product_name=raw.product_name.strip().title(),
        price_usd=price_usd,
        currency="USD",
        in_stock=raw.in_stock,
        fetched_at=raw.fetched_at,
    )
