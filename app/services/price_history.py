"""
Redis-backed price history service.
Stores every price snapshot so the Node.js gateway can build history charts.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

import redis.asyncio as aioredis

from ..config import get_settings
from ..models import PricePoint

logger = logging.getLogger(__name__)

settings = get_settings()


def _redis_url() -> str:
    """Build the Redis connection URL from settings."""
    password_part = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
    return f"redis://{password_part}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


class PriceHistoryService:
    """Read / write price snapshots in Redis."""

    def __init__(self) -> None:
        self._redis: Optional[aioredis.Redis] = None

    # ── connection helpers ─────────────────────────────────

    async def connect(self) -> None:
        """Open (or reuse) a Redis connection."""
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(
                    _redis_url(),
                    decode_responses=True,
                    socket_connect_timeout=5,
                )
                await self._redis.ping()
                logger.info("Connected to Redis at %s:%s", settings.REDIS_HOST, settings.REDIS_PORT)
            except Exception as exc:
                logger.warning("Redis unavailable (%s) – price history disabled", exc)
                self._redis = None

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def is_connected(self) -> bool:
        if self._redis is None:
            return False
        try:
            await self._redis.ping()
            return True
        except Exception:
            return False

    # ── key helpers ────────────────────────────────────────

    @staticmethod
    def _key(product_name: str, source: str) -> str:
        """Redis key for a product+source time-series."""
        slug = product_name.strip().lower().replace(" ", "_")
        return f"price_history:{slug}:{source.lower()}"

    # ── write ──────────────────────────────────────────────

    async def record_price(
        self,
        product_name: str,
        price: float,
        currency: str,
        source: str,
    ) -> None:
        """Append a price point to the sorted set (score = timestamp)."""
        if self._redis is None:
            return
        key = self._key(product_name, source)
        point = json.dumps({
            "price": price,
            "currency": currency,
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
        })
        score = datetime.utcnow().timestamp()
        try:
            await self._redis.zadd(key, {point: score})
            await self._redis.expire(key, settings.PRICE_HISTORY_TTL)
        except Exception as exc:
            logger.error("Failed to record price: %s", exc)

    # ── read ───────────────────────────────────────────────

    async def get_history(
        self,
        product_name: str,
        limit: int = 50,
    ) -> List[PricePoint]:
        """Return the most recent price points across all sources."""
        if self._redis is None:
            return []

        pattern = self._key(product_name, "*")
        points: List[PricePoint] = []

        try:
            keys: list = []
            async for k in self._redis.scan_iter(match=pattern, count=100):
                keys.append(k)

            for key in keys:
                raw_items = await self._redis.zrevrange(key, 0, limit - 1)
                for raw in raw_items:
                    data = json.loads(raw)
                    points.append(PricePoint(
                        price=data["price"],
                        currency=data["currency"],
                        source=data["source"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                    ))

            # sort newest first, trim
            points.sort(key=lambda p: p.timestamp, reverse=True)
            return points[:limit]
        except Exception as exc:
            logger.error("Failed to read price history: %s", exc)
            return []
