"""
Redis cache service.

Two key schemes are maintained for every search query:

``latest_price:{product_name}``
    A plain string key (JSON) holding the most recent
    :class:`ComparisonResponse`.  Expires after
    ``settings.latest_price_ttl_seconds`` (default 10 minutes).  Used
    as the fast-path cache so repeated searches within the TTL window
    return instantly without hitting the scrapers.

``price_history:{product_name}``
    A Redis *list* where every completed search appends one JSON-encoded
    :class:`ComparisonResponse` entry via ``RPUSH``.  The list grows
    indefinitely (no TTL) and represents the full price history for a
    product.  Callers can retrieve it in full or limit to the *n* most
    recent entries.

The rest of the application never touches the Redis client directly —
all interactions go through this module.
"""
import json
import logging
from typing import List, Optional

import redis.asyncio as aioredis

from app.config import Settings
from app.models.responses import ComparisonResponse

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Key helpers
# --------------------------------------------------------------------------- #

_LATEST_PREFIX  = "latest_price:"
_HISTORY_PREFIX = "price_history:"


def _normalise(product_name: str) -> str:
    """Lowercase + strip so 'Laptop' and 'laptop' share the same keys."""
    return product_name.strip().lower()


def _latest_key(product_name: str) -> str:
    """``latest_price:{normalised_name}``"""
    return f"{_LATEST_PREFIX}{_normalise(product_name)}"


def _history_key(product_name: str) -> str:
    """``price_history:{normalised_name}``"""
    return f"{_HISTORY_PREFIX}{_normalise(product_name)}"


class CacheService:
    """
    Async Redis cache service.

    Lifecycle
    ---------
    Instantiate once and pass the shared instance to any service or
    route that needs it.  Call ``connect()`` on startup and
    ``disconnect()`` on shutdown (the FastAPI lifespan hook handles
    this automatically when using ``app.state.cache``).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Optional[aioredis.Redis] = None

    # ------------------------------------------------------------------ #
    # Connection management
    # ------------------------------------------------------------------ #

    async def connect(self) -> None:
        """Open an async connection pool to Redis."""
        self._client = await aioredis.from_url(
            self._settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Redis connection established: %s", self._settings.redis_url)

    async def disconnect(self) -> None:
        """Close the connection pool gracefully."""
        if self._client:
            await self._client.aclose()
            logger.info("Redis connection closed.")

    async def ping(self) -> bool:
        """
        Return ``True`` when Redis is reachable, ``False`` otherwise.

        Used by the health-check endpoint to report cache connectivity.
        """
        if self._client is None:
            return False
        try:
            return await self._client.ping()
        except Exception as exc:
            logger.warning("Redis ping failed: %s", exc)
            return False

    # ------------------------------------------------------------------ #
    # latest_price:{product_name}  —  fast-path cache (TTL 10 min)
    # ------------------------------------------------------------------ #

    async def get_latest(
        self, product_name: str
    ) -> Optional[ComparisonResponse]:
        """
        Return the cached ``latest_price`` entry for *product_name*, or
        ``None`` on a miss / Redis error.

        Key: ``latest_price:{normalised_name}``  (string, with TTL)
        """
        if self._client is None:
            return None

        key = _latest_key(product_name)
        try:
            raw = await self._client.get(key)
            if raw is None:
                logger.debug("latest_price MISS  key='%s'", key)
                return None

            comparison = ComparisonResponse(**json.loads(raw))
            logger.debug(
                "latest_price HIT   key='%s'  sources=%d",
                key,
                len(comparison.sources),
            )
            return comparison
        except Exception as exc:
            logger.warning("get_latest failed  key='%s': %s", key, exc)
            return None

    async def set_latest(
        self,
        product_name: str,
        comparison: ComparisonResponse,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Store *comparison* under ``latest_price:{normalised_name}``.

        Parameters
        ----------
        ttl:
            Seconds until expiry.  Defaults to
            ``settings.latest_price_ttl_seconds`` (600 s / 10 min).
        """
        if self._client is None:
            return

        key = _latest_key(product_name)
        effective_ttl = (
            ttl if ttl is not None else self._settings.latest_price_ttl_seconds
        )
        try:
            payload = json.dumps(comparison.model_dump(mode="json"), default=str)
            await self._client.setex(key, effective_ttl, payload)
            logger.debug(
                "set_latest  key='%s'  TTL=%ds  sources=%d",
                key, effective_ttl, len(comparison.sources),
            )
        except Exception as exc:
            logger.warning("set_latest failed  key='%s': %s", key, exc)

    # ------------------------------------------------------------------ #
    # price_history:{product_name}  —  append-only history list (no TTL)
    # ------------------------------------------------------------------ #

    async def append_history(
        self,
        product_name: str,
        comparison: ComparisonResponse,
    ) -> None:
        """
        Append *comparison* to the right of the
        ``price_history:{normalised_name}`` Redis list.

        Each element is a JSON string so the list can be inspected
        directly with ``LRANGE`` from any Redis client.  The list is
        never trimmed or expired — it represents the full price history.
        """
        if self._client is None:
            return

        key = _history_key(product_name)
        try:
            entry = json.dumps(comparison.model_dump(mode="json"), default=str)
            length = await self._client.rpush(key, entry)
            logger.debug(
                "append_history  key='%s'  list_length=%d", key, length
            )
        except Exception as exc:
            logger.warning("append_history failed  key='%s': %s", key, exc)

    async def get_history(
        self,
        product_name: str,
        count: int = -1,
    ) -> List[ComparisonResponse]:
        """
        Return historical search results for *product_name*.

        Parameters
        ----------
        count:
            Maximum number of entries to return, taken from the *most
            recent* end of the list.  ``-1`` (default) returns the full
            history.

        Returns
        -------
        List[ComparisonResponse]
            Chronological order (oldest first).  Empty list on a miss
            or Redis error.
        """
        if self._client is None:
            return []

        key = _history_key(product_name)
        try:
            # LRANGE start/stop are inclusive, zero-based.
            start = 0 if count == -1 else -(count)
            raw_entries = await self._client.lrange(key, start, -1)
            results = []
            for raw in raw_entries:
                try:
                    results.append(ComparisonResponse(**json.loads(raw)))
                except Exception as parse_exc:
                    logger.warning(
                        "Skipping corrupt history entry  key='%s': %s",
                        key, parse_exc,
                    )
            logger.debug(
                "get_history  key='%s'  returned=%d entries", key, len(results)
            )
            return results
        except Exception as exc:
            logger.warning("get_history failed  key='%s': %s", key, exc)
            return []

    # ------------------------------------------------------------------ #
    # Invalidation helpers
    # ------------------------------------------------------------------ #

    async def invalidate_latest(self, product_name: str) -> None:
        """Delete the ``latest_price`` key for *product_name*."""
        await self._delete_key(_latest_key(product_name))

    async def invalidate_history(self, product_name: str) -> None:
        """Delete the entire ``price_history`` list for *product_name*."""
        await self._delete_key(_history_key(product_name))

    async def _delete_key(self, key: str) -> None:
        if self._client is None:
            return
        try:
            deleted = await self._client.delete(key)
            if deleted:
                logger.info("Deleted Redis key '%s'", key)
        except Exception as exc:
            logger.warning("DELETE failed  key='%s': %s", key, exc)
