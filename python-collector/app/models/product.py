"""
Core product domain models.
"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SourceResult(BaseModel):
    """
    Raw result returned by a single scraper source before normalisation.

    Each scraper is responsible for populating this model.  Currency
    conversion and price validation happen in the normaliser utility.
    """

    source_name: str = Field(..., description="Human-readable name of the source")
    source_url: str = Field(..., description="URL of the product listing")
    raw_price: float = Field(..., description="Price as extracted from the source")
    raw_currency: str = Field(
        default="USD",
        description="ISO-4217 currency code as reported by the source",
    )
    in_stock: bool = Field(default=True, description="Stock availability")
    product_name: str = Field(..., description="Product name as seen on the source")
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when this result was fetched",
    )

    @field_validator("raw_price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("price must be a non-negative number")
        return round(v, 2)


class ProductListing(BaseModel):
    """
    Normalised product listing that is ultimately returned to the client.

    All prices are expressed in USD; currency conversion is performed by
    the normaliser utility before this model is instantiated.
    """

    source_name: str = Field(..., description="Name of the source")
    source_url: str = Field(..., description="Direct URL to the product listing")
    product_name: str = Field(..., description="Normalised product name")
    price_usd: float = Field(..., description="Normalised price in USD")
    currency: str = Field(default="USD", description="Always USD after normalisation")
    in_stock: bool = Field(..., description="Stock availability")
    fetched_at: datetime = Field(..., description="UTC timestamp of retrieval")

    @field_validator("price_usd")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("normalised price must be a non-negative number")
        return round(v, 2)
