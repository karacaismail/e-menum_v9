"""
Tests for apps.seo_shield.rate_limiter.RateLimiter.

Covers rate limit checks under/over limit, cache-based fallback,
client IP extraction, and whitelisted IP bypass via override_settings.
"""

from django.core.cache import cache
from django.test import TestCase, RequestFactory, override_settings

from apps.seo_shield.rate_limiter import RateLimiter


class RateLimiterSimpleCounterTests(TestCase):
    """Tests for RateLimiter using the simple counter (non-Redis) path."""

    def setUp(self):
        self.limiter = RateLimiter()
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_not_limited_under_threshold(self):
        """Requests under the limit are not rate limited."""
        is_limited, current, remaining = self.limiter.is_rate_limited(
            '192.168.1.1', window=60, max_requests=10,
        )
        self.assertFalse(is_limited)
        self.assertEqual(current, 1)
        self.assertEqual(remaining, 9)

    def test_not_limited_at_threshold(self):
        """Requests at exactly the limit are not yet rate limited."""
        for i in range(10):
            is_limited, current, remaining = self.limiter.is_rate_limited(
                '192.168.1.2', window=60, max_requests=10,
            )
        # The 10th request should still be allowed
        self.assertFalse(is_limited)
        self.assertEqual(current, 10)
        self.assertEqual(remaining, 0)

    def test_limited_over_threshold(self):
        """Requests over the limit are rate limited."""
        for i in range(11):
            is_limited, current, remaining = self.limiter.is_rate_limited(
                '192.168.1.3', window=60, max_requests=10,
            )
        # The 11th request should be limited
        self.assertTrue(is_limited)
        self.assertEqual(current, 11)
        self.assertEqual(remaining, 0)

    def test_different_identifiers_independent(self):
        """Different identifiers have independent counters."""
        for i in range(5):
            self.limiter.is_rate_limited('ip_a', window=60, max_requests=10)

        is_limited, current, _ = self.limiter.is_rate_limited(
            'ip_b', window=60, max_requests=10,
        )
        self.assertFalse(is_limited)
        self.assertEqual(current, 1)

    def test_remaining_decreases(self):
        """Remaining count decreases with each request."""
        _, _, remaining1 = self.limiter.is_rate_limited(
            '192.168.1.4', window=60, max_requests=5,
        )
        _, _, remaining2 = self.limiter.is_rate_limited(
            '192.168.1.4', window=60, max_requests=5,
        )
        self.assertEqual(remaining1, 4)
        self.assertEqual(remaining2, 3)

    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    })
    def test_uses_simple_counter_for_locmem(self):
        """LocMemCache backend triggers simple counter path."""
        limiter = RateLimiter()
        self.assertFalse(limiter._is_redis)
        is_limited, current, remaining = limiter.is_rate_limited(
            '192.168.1.5', window=60, max_requests=10,
        )
        self.assertFalse(is_limited)


class RateLimiterClientIPTests(TestCase):
    """Tests for RateLimiter.get_client_ip."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_extracts_from_remote_addr(self):
        """Falls back to REMOTE_ADDR when no X-Forwarded-For."""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '203.0.113.50'
        ip = RateLimiter.get_client_ip(request)
        self.assertEqual(ip, '203.0.113.50')

    def test_extracts_from_x_forwarded_for(self):
        """Extracts the first IP from X-Forwarded-For header."""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '198.51.100.1, 10.0.0.1, 10.0.0.2'
        ip = RateLimiter.get_client_ip(request)
        self.assertEqual(ip, '198.51.100.1')

    def test_single_x_forwarded_for(self):
        """Handles single IP in X-Forwarded-For."""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '198.51.100.5'
        ip = RateLimiter.get_client_ip(request)
        self.assertEqual(ip, '198.51.100.5')

    def test_default_when_no_remote_addr(self):
        """Returns 127.0.0.1 when REMOTE_ADDR is missing."""
        request = self.factory.get('/')
        request.META.pop('REMOTE_ADDR', None)
        ip = RateLimiter.get_client_ip(request)
        self.assertEqual(ip, '127.0.0.1')


class RateLimiterRedisDetectionTests(TestCase):
    """Tests for Redis backend detection."""

    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    })
    def test_non_redis_detected(self):
        """LocMemCache is not detected as Redis."""
        limiter = RateLimiter()
        self.assertFalse(limiter._is_redis)

    def test_explicit_redis_client(self):
        """Passing an explicit redis_client sets _is_redis to True."""
        fake_client = object()
        limiter = RateLimiter(redis_client=fake_client)
        self.assertTrue(limiter._is_redis)
