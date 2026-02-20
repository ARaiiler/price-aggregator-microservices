"""
Outbound response models.

All models in this module are serialised to JSON exclusively.  The
service never produces HTML, plain-text, or other content types.
"""
from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field

from .product import ProductListing


# --------------------------------------------------------------------------- #
# Error envelope  (returned on every 4xx / 5xx)
# --------------------------------------------------------------------------- #

class ErrorResponse(BaseModel):
    """
    Uniform JSON error envelope.

    Every non-2xx response from any endpoint in this service uses this
    shape so callers can parse errors without branching on content type.

    Example
    -------
    .. code-block:: json

        {
          "detail": "product_name must not be blank or whitespace-only",
          "status_code": 422,
          "timestamp": "2026-02-18T10:00:00+00:00"
        }
    """

    detail: str = Field(..., description="Human-readable error message")
    status_code: int = Field(..., description="HTTP status code echoed from the response")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the error was generated",
    )


# --------------------------------------------------------------------------- #
# Per-source entry
# --------------------------------------------------------------------------- #

class SourceEntry(BaseModel):
    """
    Best (lowest) normalised price found at a single data source.

    Every source that returns at least one result contributes exactly one
    ``SourceEntry`` to the comparison list.  Prices are always in USD.
    """

    source: str = Field(..., description="Human-readable name of the data source")
    price: float = Field(..., description="Lowest price found at this source (USD)")
    currency: str = Field(default="USD", description="Always USD after normalisation")
    url: str = Field(
        default="",
        description="Direct product URL for the cheapest listing at this source",
    )
    in_stock: bool = Field(
        default=True,
        description="Stock status of the cheapest listing",
    )


# --------------------------------------------------------------------------- #
# Comparison response
# --------------------------------------------------------------------------- #

class ComparisonResponse(BaseModel):
    """
    Structured price-comparison result returned by POST /internal/search.

    Shape
    -----
    .. code-block:: json

        {
          "product_name": "Wireless Headphones",
          "sources": [
            { "source": "Fnac",  "price": 199.99, "currency": "USD", ... },
            { "source": "Jumia", "price": 205.50, "currency": "USD", ... }
          ],
          "cached": false,
          "timestamp": "2026-02-18T10:00:00+00:00"
        }

    Each ``SourceEntry`` reflects the *lowest* normalised price found at
    that source.  Sources are sorted cheapest-first.
    """

    product_name: str = Field(..., description="Normalised search query")
    sources: List[SourceEntry] = Field(
        default_factory=list,
        description="Per-source best price entries, sorted cheapest first",
    )
    cached: bool = Field(
        default=False,
        description="True when the response was served from the Redis cache",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of this response",
    )


# --------------------------------------------------------------------------- #
# Legacy flat response (kept for internal use / backward compat)
# --------------------------------------------------------------------------- #

class SearchResponse(BaseModel):
    """
    Flat listing response — not returned by the public route but retained
    for potential internal tooling and forward compatibility.
    """

    success: bool = Field(..., description="Whether the request succeeded")
    query: str = Field(..., description="Echo of the original search query")
    results: List[ProductListing] = Field(
        default_factory=list,
        description="Normalised listings sorted by price ascending",
    )
    total_results: int = Field(..., description="Number of listings returned")
    sources_queried: int = Field(
        ..., description="Number of sources that were contacted"
    )
    cached: bool = Field(
        default=False,
        description="True when the response was served from the Redis cache",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of this response",
    )


class HealthResponse(BaseModel):
    """
    Response model for GET /health.
    """

    status: str = Field(..., description="One of: healthy, degraded, unhealthy")
    service: str
    version: str
    environment: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    redis_connected: bool = Field(
        ..., description="Whether Redis is reachable at the time of the check"
    )
