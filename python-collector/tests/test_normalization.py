"""
Tests for app.utils.normalizer
================================
Covers:
  - ``_to_usd()`` for each supported currency (USD, EUR, GBP, JPY, CAD, AUD, MAD)
  - Unknown currency falls back to USD rate (price unchanged), logs warning
  - ``normalize_result()`` produces a correctly populated ``ProductListing``
  - Product name is title-cased and stripped
  - Price is rounded to 2 decimal places
  - ``price_usd`` is non-negative (boundary: 0.00)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import pytest

from app.models.product import SourceResult
from app.utils.normalizer import _to_usd, normalize_result

# FX rates used by the normalizer (kept local to avoid coupling)
_EXPECTED_RATES = {
    "USD": 1.0,
    "EUR": 1.09,
    "GBP": 1.27,
    "JPY": 0.0067,
    "CAD": 0.74,
    "AUD": 0.65,
    "MAD": 0.10,
}


def _make_raw(
    raw_price: float,
    raw_currency: str = "USD",
    product_name: str = "Test Product",
) -> SourceResult:
    return SourceResult(
        source_name="TestSource",
        source_url="https://test.example.com/product/0",
        raw_price=raw_price,
        raw_currency=raw_currency,
        in_stock=True,
        product_name=product_name,
        fetched_at=datetime(2026, 2, 18, 10, 0, 0, tzinfo=timezone.utc),
    )


# --------------------------------------------------------------------------- #
# _to_usd — individual currency conversions
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("currency,rate", _EXPECTED_RATES.items())
def test_to_usd_correct_conversion(currency: str, rate: float) -> None:
    result = _to_usd(100.0, currency)
    assert result == pytest.approx(100.0 * rate, rel=1e-6)


def test_to_usd_usd_unchanged() -> None:
    assert _to_usd(50.00, "USD") == pytest.approx(50.00)


def test_to_usd_eur_to_usd() -> None:
    assert _to_usd(100.0, "EUR") == pytest.approx(109.00)


def test_to_usd_gbp_to_usd() -> None:
    assert _to_usd(100.0, "GBP") == pytest.approx(127.00)


def test_to_usd_jpy_to_usd() -> None:
    assert _to_usd(1000.0, "JPY") == pytest.approx(6.70, rel=1e-4)


def test_to_usd_cad_to_usd() -> None:
    assert _to_usd(100.0, "CAD") == pytest.approx(74.00)


def test_to_usd_aud_to_usd() -> None:
    assert _to_usd(100.0, "AUD") == pytest.approx(65.00)


def test_to_usd_mad_to_usd() -> None:
    assert _to_usd(1000.0, "MAD") == pytest.approx(100.00)


def test_to_usd_zero_price() -> None:
    assert _to_usd(0.0, "USD") == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# Unknown currency fallback
# --------------------------------------------------------------------------- #


def test_to_usd_unknown_currency_falls_back_to_usd(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        result = _to_usd(100.0, "XYZ")
    assert result == pytest.approx(100.0)     # rate = 1.0 (USD fallback)
    assert "XYZ" in caplog.text or "unknown" in caplog.text.lower()


# --------------------------------------------------------------------------- #
# normalize_result — full integration
# --------------------------------------------------------------------------- #


def test_normalize_result_returns_product_listing(raw_result_eur: SourceResult) -> None:
    from app.models.product import ProductListing
    listing = normalize_result(raw_result_eur)
    assert isinstance(listing, ProductListing)


def test_normalize_result_eur_price_converted(raw_result_eur: SourceResult) -> None:
    listing = normalize_result(raw_result_eur)
    assert listing.price_usd == pytest.approx(109.00)


def test_normalize_result_gbp_price_converted(raw_result_mad: SourceResult) -> None:
    listing = normalize_result(raw_result_mad)
    # 1000 MAD * 0.10 = $100.00 USD
    assert listing.price_usd == pytest.approx(100.00)


def test_normalize_result_currency_always_usd() -> None:
    raw = _make_raw(50.0, "EUR")
    listing = normalize_result(raw)
    assert listing.currency == "USD"


def test_normalize_result_product_name_title_cased() -> None:
    raw = _make_raw(10.0, "USD", product_name="wireless headphones")
    listing = normalize_result(raw)
    assert listing.product_name == "Wireless Headphones"


def test_normalize_result_product_name_stripped() -> None:
    raw = _make_raw(10.0, "USD", product_name="  laptop  ")
    listing = normalize_result(raw)
    assert listing.product_name == "Laptop"


def test_normalize_result_price_rounded_to_two_decimals() -> None:
    raw = _make_raw(99.999, "USD")
    listing = normalize_result(raw)
    # ProductListing validator rounds to 2 dp → 100.00
    assert listing.price_usd == pytest.approx(100.00, abs=0.005)


def test_normalize_result_preserves_source_name(raw_result_eur: SourceResult) -> None:
    listing = normalize_result(raw_result_eur)
    assert listing.source_name == raw_result_eur.source_name


def test_normalize_result_preserves_source_url(raw_result_eur: SourceResult) -> None:
    listing = normalize_result(raw_result_eur)
    assert listing.source_url == raw_result_eur.source_url


def test_normalize_result_preserves_in_stock_true(raw_result_eur: SourceResult) -> None:
    listing = normalize_result(raw_result_eur)
    assert listing.in_stock is True


def test_normalize_result_preserves_in_stock_false(raw_result_mad: SourceResult) -> None:
    listing = normalize_result(raw_result_mad)
    assert listing.in_stock is False


def test_normalize_result_preserves_fetched_at(raw_result_eur: SourceResult) -> None:
    listing = normalize_result(raw_result_eur)
    assert listing.fetched_at == raw_result_eur.fetched_at


# --------------------------------------------------------------------------- #
# Boundary / edge cases
# --------------------------------------------------------------------------- #


def test_source_result_rejects_negative_price() -> None:
    with pytest.raises(Exception):
        _make_raw(-1.0, "USD")


def test_product_listing_price_non_negative() -> None:
    raw = _make_raw(0.0, "USD")
    listing = normalize_result(raw)
    assert listing.price_usd >= 0.0
