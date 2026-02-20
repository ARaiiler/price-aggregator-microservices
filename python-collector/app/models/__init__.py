"""
Models package.

Re-exports all public Pydantic models so that the rest of the
application can import from ``app.models`` directly:

    from app.models import ProductListing, SearchRequest, SearchResponse
"""
from .product import ProductListing, SourceResult
from .requests import SearchRequest
from .responses import (
    ComparisonResponse,
    ErrorResponse,
    HealthResponse,
    SearchResponse,
    SourceEntry,
)

__all__ = [
    "ProductListing",
    "SourceResult",
    "SourceEntry",
    "ComparisonResponse",
    "ErrorResponse",
    "SearchRequest",
    "HealthResponse",
    "SearchResponse",
]
