"""
Pydantic models for request / response validation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime


# ── Product ────────────────────────────────────────────────


class Product(BaseModel):
    """Single product from one source."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = Field(None, description="Unique product identifier")
    name: str = Field(..., description="Product name")
    price: float = Field(..., ge=0, description="Normalised price")
    original_price: float = Field(..., ge=0, description="Price before normalisation")
    source: str = Field(..., description="Source marketplace")
    url: Optional[str] = Field(None, description="Product URL")
    image_url: Optional[str] = Field(None, description="Product image URL")
    currency: str = Field(default="MAD", description="Currency after normalisation")
    original_currency: str = Field(default="USD", description="Original currency")
    in_stock: bool = Field(default=True, description="Availability status")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Rating 0-5")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Price History ──────────────────────────────────────────


class PricePoint(BaseModel):
    """A single price snapshot (used in price history)."""
    price: float
    currency: str
    source: str
    timestamp: datetime


class PriceHistoryResponse(BaseModel):
    """Price history for a product."""
    success: bool
    product_name: str
    history: List[PricePoint]
    total_points: int


# ── Search ─────────────────────────────────────────────────


class ProductSearchResponse(BaseModel):
    """Response returned by /api/search."""
    success: bool
    query: str
    results: List[Product]
    timestamp: datetime
    total_results: int
    sources: List[str] = Field(default_factory=list)


# ── Health ─────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    timestamp: datetime
    version: str
    redis_connected: bool = False


# ── Currency ───────────────────────────────────────────────


class CurrencyRates(BaseModel):
    """Exchange rates used for normalisation."""
    base: str = "USD"
    rates: Dict[str, float] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
