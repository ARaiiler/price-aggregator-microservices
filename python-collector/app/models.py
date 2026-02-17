"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class Product(BaseModel):
    """Product model"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")
    source: str = Field(..., description="Source of the product data")
    url: Optional[str] = Field(None, description="Product URL")
    currency: str = Field(default="USD", description="Price currency")
    in_stock: bool = Field(default=True, description="Availability status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    timestamp: datetime
    version: str


class ProductSearchResponse(BaseModel):
    """Product search response"""
    success: bool
    query: str
    results: List[Product]
    timestamp: datetime
    total_results: int
