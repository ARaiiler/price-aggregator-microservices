"""
Internal API routes.

!!! SECURITY — DO NOT EXPOSE PUBLICLY !!!
-----------------------------------------
Every endpoint in this module is designed for **internal service-to-service
communication only** and MUST remain unreachable from public internet traffic.

Enforcement assumptions
~~~~~~~~~~~~~~~~~~~~~~~
* This service runs on Docker's isolated ``internal-network`` bridge
  (subnet 172.28.0.0/16) and publishes **no host ports**.
* The Node.js API Gateway is the **sole authorised caller**.  Requests
  arrive over Docker DNS (e.g. ``http://python-collector:8000``).
* A reverse proxy or firewall layer MUST block any path beginning with
  ``/internal/`` from reaching this service from outside the cluster.
* No CORS headers are set — browser-originated cross-origin requests
  are not a valid use-case for this API.

JSON contract
~~~~~~~~~~~~~
All responses are ``application/json``.  The ``default_response_class``
set in ``main.py`` enforces this globally; individual handlers reinforce
it via typed ``response_model`` declarations.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.models.requests import SearchRequest
from app.models.responses import ComparisonResponse, ErrorResponse, HealthResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# INTERNAL ONLY — see module docstring for the full security contract.
# ---------------------------------------------------------------------------
# Requests reaching this router must originate from within the Docker
# internal-network bridge.  The prefix ``/internal`` is a deliberate
# naming convention; a reverse proxy MUST deny any traffic matching
# ``/internal/*`` before it reaches the public internet.
# ---------------------------------------------------------------------------
internal_router = APIRouter(prefix="/internal", tags=["Internal"])
health_router = APIRouter(tags=["Health"])

# Shared error-response documentation injected into every endpoint's
# OpenAPI ``responses`` object so callers see the error shape in /docs.
_ERROR_RESPONSES: dict = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": "Request rejected (e.g. wrong Content-Type)",
    },
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "model": ErrorResponse,
        "description": "Pydantic validation failure",
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErrorResponse,
        "description": "Unexpected server-side error",
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": "All external data sources failed to return results",
    },
}


# --------------------------------------------------------------------------- #
# Health check
# --------------------------------------------------------------------------- #


@health_router.get(
    "/health",
    response_model=HealthResponse,
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse}},
    summary="Service health check",
    description=(
        "Returns the operational status of this service and its Redis dependency. "
        "Intended for use by Docker health checks and orchestration tooling. "
        "JSON only."
    ),
)
async def health_check(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    cache = request.app.state.cache

    redis_ok = await cache.ping()

    return HealthResponse(
        status="healthy" if redis_ok else "degraded",
        service=settings.service_name,
        version=settings.service_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc),
        redis_connected=redis_ok,
    )


# --------------------------------------------------------------------------- #
# Internal search endpoint
# --------------------------------------------------------------------------- #


@internal_router.post(
    "/search",
    # ------------------------------------------------------------------ #
    # INTERNAL ONLY — must not be reachable from public internet.         #
    # Caller: Node.js API Gateway (Docker internal-network, DNS only).    #
    # No CORS. No authentication here — Gateway owns that responsibility. #
    # Accepts:  application/json                                          #
    # Produces: application/json                                          #
    # ------------------------------------------------------------------ #
    response_model=ComparisonResponse,
    responses=_ERROR_RESPONSES,
    status_code=status.HTTP_200_OK,
    summary="[INTERNAL] Search for product prices",
    description=(
        "**Not for public use.** "
        "Accepts a JSON body with `product_name`, fans-out to all registered "
        "data sources concurrently, normalises prices to USD, and returns a "
        "per-source comparison sorted cheapest-first. "
        "Results are served from the `latest_price` Redis cache (10-min TTL) "
        "when available, otherwise fetched live and written to both "
        "`latest_price` and `price_history` keys. "
        "Responds exclusively with `application/json`."
    ),
)
async def search_products(
    payload: SearchRequest,
    request: Request,
) -> ComparisonResponse:
    """
    POST /internal/search

    Accepts
    -------
    Content-Type: application/json

    .. code-block:: json

        { "product_name": "wireless headphones" }

    Produces
    --------
    Content-Type: application/json — always, including on error.

    Success (200)
    ~~~~~~~~~~~~
    .. code-block:: json

        {
          "product_name": "Wireless Headphones",
          "sources": [
            { "source": "Fnac",  "price": 199.99, "currency": "USD",
              "url": "https://...", "in_stock": true },
            { "source": "Jumia", "price": 205.50, "currency": "USD",
              "url": "https://...", "in_stock": true }
          ],
          "cached": false,
          "timestamp": "2026-02-18T10:00:00+00:00"
        }

    Error (400 / 422 / 500)
    ~~~~~~~~~~~~~~~~~~~~~~~
    .. code-block:: json

        { "detail": "...", "status_code": 422, "timestamp": "..." }
    """
    collector = request.app.state.collector

    # Enforce JSON-only request body.  FastAPI validates Content-Type for
    # declared Pydantic body parameters, but we make the contract explicit
    # here so the error is logged and returned as our ErrorResponse envelope
    # rather than a raw Starlette 422.
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("application/json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"This endpoint accepts application/json only. "
                f"Received Content-Type: '{content_type or 'not set'}'"
            ),
        )

    logger.info("POST /internal/search  product='%s'", payload.product_name)

    try:
        response = await collector.search(payload.product_name)
    except Exception as exc:
        logger.exception(
            "Unhandled error in POST /internal/search  product='%s': %s",
            payload.product_name,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while collecting product data.",
        ) from exc

    if not response.sources:
        logger.warning(
            "All external sources failed  product='%s'", payload.product_name,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="All external sources failed",
        )

    return response
