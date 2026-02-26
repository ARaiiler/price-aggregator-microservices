"""
FastAPI Product Collector Service  (Backend A)
───────────────────────────────────────────────
• Fetches prices from multiple sources (Amazon, Jumia, eBay)
• Normalises currencies → MAD (configurable)
• Caches price history in Redis
• Exposes a *private* REST API secured by an internal API key
  so only the Node.js gateway can call it
"""

from contextlib import asynccontextmanager
from datetime import datetime
import logging

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from .config import get_settings
from .models import (
    CurrencyRates,
    HealthResponse,
    PriceHistoryResponse,
    Product,
    ProductSearchResponse,
)
from .services.auth import verify_internal_key
from .services.normalizer import CurrencyNormalizer
from .services.price_history import PriceHistoryService
from .services.scraper import ProductScraper

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Shared service instances ───────────────────────────────
normalizer = CurrencyNormalizer()
price_history = PriceHistoryService()
scraper = ProductScraper(normalizer=normalizer)


# ── Lifespan (startup / shutdown) ──────────────────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Connect to Redis on startup, disconnect on shutdown."""
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )
    await normalizer.refresh_rates()
    await price_history.connect()
    logger.info(
        "%s v%s started — target currency: %s",
        settings.SERVICE_NAME,
        settings.SERVICE_VERSION,
        normalizer.target,
    )
    yield
    await price_history.disconnect()
    logger.info("Shutdown complete")


# ── App ────────────────────────────────────────────────────
app = FastAPI(
    title="Product Collector API",
    description=(
        "Internal microservice that scrapes product prices, "
        "normalises currencies, and persists price history in Redis."
    ),
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================== PUBLIC ENDPOINTS =====================


@app.get("/", tags=["Root"])
async def root():
    """Root – basic service info (no auth needed)."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check for Docker / orchestration."""
    return HealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        timestamp=datetime.utcnow(),
        version=settings.SERVICE_VERSION,
        redis_connected=await price_history.is_connected(),
    )


# ================== PRIVATE / INTERNAL API ==================
# Every route below requires the X-Internal-Api-Key header.


@app.get(
    "/api/search",
    response_model=ProductSearchResponse,
    tags=["Products"],
    dependencies=[Depends(verify_internal_key)],
)
async def search_products(
    q: str = Query(..., min_length=1, description="Product name to search"),
):
    """
    Search for products across all sources.
    Prices are normalised to the configured target currency.
    Each result is also stored in Redis price history.
    """
    try:
        products: List[Product] = await scraper.search_products(q)

        # persist every price point
        for p in products:
            await price_history.record_price(
                product_name=p.name,
                price=p.price,
                currency=p.currency,
                source=p.source,
            )

        return ProductSearchResponse(
            success=True,
            query=q,
            results=products,
            timestamp=datetime.utcnow(),
            total_results=len(products),
            sources=scraper.sources,
        )
    except Exception as exc:
        logger.exception("search_products failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get(
    "/api/product/{product_name}/history",
    response_model=PriceHistoryResponse,
    tags=["Products"],
    dependencies=[Depends(verify_internal_key)],
)
async def product_price_history(
    product_name: str,
    limit: int = Query(50, ge=1, le=200),
):
    """Return cached price history for a product across all sources."""
    history = await price_history.get_history(product_name, limit=limit)
    return PriceHistoryResponse(
        success=True,
        product_name=product_name,
        history=history,
        total_points=len(history),
    )


@app.get(
    "/api/currencies",
    response_model=CurrencyRates,
    tags=["Currency"],
    dependencies=[Depends(verify_internal_key)],
)
async def get_currency_rates():
    """Return the exchange rates currently used for normalisation."""
    return normalizer.get_rates()


@app.post(
    "/api/currencies/refresh",
    response_model=CurrencyRates,
    tags=["Currency"],
    dependencies=[Depends(verify_internal_key)],
)
async def refresh_currency_rates():
    """Force-refresh exchange rates from the external provider."""
    await normalizer.refresh_rates()
    return normalizer.get_rates()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENVIRONMENT") == "development"
    )
