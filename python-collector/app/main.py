"""
FastAPI Product Collector Service
Fetches and aggregates product pricing data
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import os

from .models import Product, HealthResponse, ProductSearchResponse
from .services.scraper import ProductScraper

app = FastAPI(
    title="Product Collector API",
    description="Microservice for collecting product pricing data",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scraper service
scraper = ProductScraper()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "Python Collector",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint for container orchestration
    """
    return HealthResponse(
        status="healthy",
        service="python-collector",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.get("/fetch-product", response_model=ProductSearchResponse, tags=["Products"])
async def fetch_product(
    product_name: str = Query(..., min_length=1, description="Product name to search for")
):
    """
    Fetch product pricing data from multiple sources
    
    Args:
        product_name: Name of the product to search
    
    Returns:
        ProductSearchResponse with aggregated results
    """
    try:
        # Scrape products (placeholder implementation)
        products = await scraper.search_products(product_name)
        
        return ProductSearchResponse(
            success=True,
            query=product_name,
            results=products,
            timestamp=datetime.utcnow(),
            total_results=len(products)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch products: {str(e)}"
        )


@app.get("/products/{product_id}", tags=["Products"])
async def get_product_by_id(product_id: str):
    """
    Get specific product details by ID
    """
    # Placeholder implementation
    return {
        "message": "Product detail endpoint - to be implemented",
        "product_id": product_id
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENVIRONMENT") == "development"
    )
