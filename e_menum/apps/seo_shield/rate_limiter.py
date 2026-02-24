"""
Redis-based sliding window rate limiter for SEO Shield.

Uses a sorted set (ZADD) sliding window algorithm when Redis is available,
and falls back to a simple in-memory counter for development environments
using Django's LocMemCache.

Key format: shield:rate:{identifier}

Usage:
    limiter = RateLimiter()
    ip = limiter.get_client_ip(request)
    is_limited, current, remaining = limiter.is_rate_limited(ip, window=60, max_requests=60)
"""

import logging
import time
from typing import Optional

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('apps.seo_shield')

# Key prefix for rate limit counters
RATE_LIMIT_KEY_PREFIX = 'shield:rate:'


class RateLimiter:
    """
    Sliding window rate limiter backed by Redis or in-memory cache.

    When Redis is the cache backend, uses sorted sets for accurate
    sliding window counting. Falls back to a simple counter with TTL
    when using LocMemCache (development).
    """

    def __init__(self, redis_client=None):
        """
        Initialize the rate limiter.

        Args:
            redis_client: Optional explicit Redis client. If not provided,
                          uses Django's default cache backend.
        """
        self._redis_client = redis_client
        self._is_redis = self._detect_redis_backend()

    def _detect_redis_backend(self) -> bool:
        """
        Detect whether the cache backend is Redis-based.

        Returns:
            True if the default cache backend uses Redis.
        """
        if self._redis_client is not None:
            return True

        cache_backend = getattr(settings, 'CACHES', {}).get('default', {}).get('BACKEND', '')
        return 'redis' in cache_backend.lower()

    def is_rate_limited(
        self,
        identifier: str,
        window: int = 60,
        max_requests: int = 60,
    ) -> tuple[bool, int, int]:
        """
        Check if the given identifier has exceeded the rate limit.

        Args:
            identifier: Unique key for the client (usually IP address).
            window: Time window in seconds (default: 60).
            max_requests: Maximum allowed requests within the window (default: 60).

        Returns:
            A tuple of (is_limited, current_count, remaining).
            - is_limited: True if the limit has been exceeded.
            - current_count: Number of requests in the current window.
            - remaining: Number of requests remaining before limit.
        """
        key = f"{RATE_LIMIT_KEY_PREFIX}{identifier}"

        if self._is_redis:
            return self._sliding_window_check(key, window, max_requests)
        else:
            return self._simple_counter_check(key, window, max_requests)

    def _sliding_window_check(
        self,
        key: str,
        window: int,
        max_requests: int,
    ) -> tuple[bool, int, int]:
        """
        Sliding window rate limit check using Redis sorted sets.

        Algorithm:
        1. Remove entries older than the current window (ZREMRANGEBYSCORE)
        2. Add current timestamp as both score and member (ZADD)
        3. Count entries in the set (ZCARD)
        4. Set expiry on the key to prevent stale data

        Args:
            key: The Redis key for this rate limit bucket.
            window: Time window in seconds.
            max_requests: Maximum requests allowed in the window.

        Returns:
            Tuple of (is_limited, current_count, remaining).
        """
        try:
            # Try to get the raw Redis client from Django cache
            redis_client = self._redis_client
            if redis_client is None:
                redis_client = self._get_redis_client()

            if redis_client is None:
                # Fallback if we cannot get a Redis client
                return self._simple_counter_check(key, window, max_requests)

            now = time.time()
            window_start = now - window
            # Use a unique member to avoid collisions within the same timestamp
            member = f"{now}:{id(object())}"

            pipe = redis_client.pipeline(transaction=True)
            # Remove entries outside the current window
            pipe.zremrangebyscore(key, 0, window_start)
            # Add the current request
            pipe.zadd(key, {member: now})
            # Count entries in the window
            pipe.zcard(key)
            # Set TTL to auto-expire the key
            pipe.expire(key, window + 1)
            results = pipe.execute()

            current_count = results[2]
            remaining = max(0, max_requests - current_count)
            is_limited = current_count > max_requests

            return is_limited, current_count, remaining

        except Exception as exc:
            logger.warning(
                "Redis sliding window check failed, falling back to "
                "simple counter: %s",
                exc,
            )
            return self._simple_counter_check(key, window, max_requests)

    def _simple_counter_check(
        self,
        key: str,
        window: int,
        max_requests: int,
    ) -> tuple[bool, int, int]:
        """
        Simple counter-based rate limit check using Django cache.

        Uses cache.get/set with TTL. Less accurate than sliding window
        but works with any cache backend (LocMemCache, file, etc.).

        Args:
            key: The cache key for this rate limit bucket.
            window: Time window in seconds.
            max_requests: Maximum requests allowed in the window.

        Returns:
            Tuple of (is_limited, current_count, remaining).
        """
        try:
            current_count = cache.get(key, 0)

            if current_count == 0:
                # First request in this window
                cache.set(key, 1, window)
                return False, 1, max_requests - 1

            new_count = current_count + 1

            # Increment without resetting TTL by using cache.incr if available
            try:
                new_count = cache.incr(key)
            except ValueError:
                # Key expired between get and incr, start fresh
                cache.set(key, 1, window)
                return False, 1, max_requests - 1

            remaining = max(0, max_requests - new_count)
            is_limited = new_count > max_requests

            return is_limited, new_count, remaining

        except Exception as exc:
            logger.warning(
                "Rate limit check failed, allowing request: %s", exc,
            )
            return False, 0, max_requests

    def _get_redis_client(self) -> Optional[object]:
        """
        Attempt to get the raw Redis client from Django's cache backend.

        Returns:
            Redis client object, or None if unavailable.
        """
        try:
            # django-redis exposes get_redis_connection
            from django_redis import get_redis_connection
            return get_redis_connection('default')
        except (ImportError, Exception):
            pass

        try:
            # Django 4.x+ RedisCache exposes _cache
            client = getattr(cache, '_cache', None)
            if client is not None:
                return client.get_client()
        except Exception:
            pass

        return None

    @staticmethod
    def get_client_ip(request) -> str:
        """
        Extract the client IP address from the request.

        Checks X-Forwarded-For header first (takes the first/leftmost IP
        which is the original client), then falls back to REMOTE_ADDR.

        Args:
            request: Django HttpRequest object.

        Returns:
            Client IP address as a string.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # X-Forwarded-For: client, proxy1, proxy2
            # Take the first (leftmost) IP = original client
            ip = x_forwarded_for.split(',')[0].strip()
            return ip

        return request.META.get('REMOTE_ADDR', '127.0.0.1')
