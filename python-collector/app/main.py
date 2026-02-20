"""
Data Collector Service — application entry point.

Network isolation
-----------------
This service is designed to run **exclusively** on Docker's internal
bridge network.  It MUST NOT be reachable from public internet traffic.

* No port is published to the host in docker-compose.yml.
* No CORS middleware is registered — cross-origin browser requests are
  not a valid use-case for an internal service-to-service API.
* The sole authorised caller is the Node.js API Gateway, which runs on
  the same Docker network and communicates via the service DNS name.
* A reverse proxy / firewall layer MUST block any path under
  ``/internal/*`` from external ingress if this service is ever moved
  closer to a public network boundary.

JSON contract
-------------
``default_response_class=JSONResponse`` ensures every response
(including FastAPI-generated 422 validation errors) is sent as
``application/json``.  Custom exception handlers below enforce the same
:class:`~app.models.responses.ErrorResponse` envelope for 404, 422,
and any unhandled 500-class exception.
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import health_router, internal_router
from app.config import get_settings
from app.models.responses import ErrorResponse
from app.services.cache_service import CacheService
from app.services.collector_service import CollectorService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Runs startup logic before yielding, then shutdown logic after the
    ``yield`` when the application receives a shutdown signal.
    """
    settings = get_settings()
    app.state.settings = settings

    # ── Startup ──────────────────────────────────────────────────────── #
    logger.info(
        "Starting %s v%s [%s]",
        settings.service_name,
        settings.service_version,
        settings.environment,
    )

    cache = CacheService(settings)
    await cache.connect()
    app.state.cache = cache

    collector = CollectorService(settings=settings, cache=cache)
    await collector.startup()
    app.state.collector = collector

    logger.info("Application startup complete.")
    yield

    # ── Shutdown ─────────────────────────────────────────────────────── #
    logger.info("Shutting down application...")
    await collector.shutdown()
    await cache.disconnect()
    logger.info("Application shutdown complete.")


# --------------------------------------------------------------------------- #
# Application factory
# --------------------------------------------------------------------------- #

_settings = get_settings()

app = FastAPI(
    title="Data Collector Service",
    description=(
        "**INTERNAL USE ONLY.** "
        "This microservice aggregates product prices from multiple simulated "
        "sources and is reachable exclusively from the Node.js API Gateway "
        "over Docker's internal bridge network. "
        "It must never be exposed to public internet traffic."
    ),
    version=_settings.service_version,
    # Enforce JSON for every response, including FastAPI-generated errors.
    default_response_class=JSONResponse,
    # Docs are disabled in production; no sensitive routes are ever listed
    # publicly even in development builds.
    docs_url="/docs" if _settings.environment != "production" else None,
    redoc_url="/redoc" if _settings.environment != "production" else None,
    lifespan=lifespan,
)

# --------------------------------------------------------------------------- #
# NO CORS
# --------------------------------------------------------------------------- #
# Cross-Origin Resource Sharing is intentionally absent.
# This service speaks only to the Node.js Gateway (same Docker network).
# Browser clients never contact this service directly; adding CORS headers
# here would only widen the attack surface without any legitimate use-case.

# --------------------------------------------------------------------------- #
# Exception handlers  — uniform ErrorResponse JSON envelope
# --------------------------------------------------------------------------- #

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Translate FastAPI/Starlette ``HTTPException`` into the standard
    :class:`~app.models.responses.ErrorResponse` JSON envelope.
    """
    body = ErrorResponse(
        detail=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        status_code=exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(body),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Translate Pydantic v2 validation failures into the standard envelope.

    The first validation error message is surfaced as ``detail`` so the
    Gateway can relay a meaningful message without exposing internal
    stack traces.
    """
    errors = exc.errors()
    first_msg = errors[0]["msg"] if errors else "Invalid request payload"
    body = ErrorResponse(
        detail=first_msg,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(body),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Catch-all for any unhandled exception.

    Returns a generic 500 JSON response so the caller always receives
    ``application/json`` regardless of error type.
    """
    logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
    body = ErrorResponse(
        detail="An unexpected internal error occurred.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(body),
    )

app.include_router(health_router)
app.include_router(internal_router)


# --------------------------------------------------------------------------- #
# Root
# --------------------------------------------------------------------------- #

@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    """Minimal root response — not part of the public API."""
    return JSONResponse(
        content={
            "service": _settings.service_name,
            "version": _settings.service_version,
            "status": "running",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
