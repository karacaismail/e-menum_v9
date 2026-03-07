"""
Tests for apps.seo_shield.middleware.SEOShieldMiddleware.

Covers the full Shield pipeline: enabled/disabled toggle, IP whitelisting,
rate limiting, risk-based blocking, challenge action, log action, and
BlockLog audit trail creation.
"""

from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, RequestFactory, override_settings

from apps.seo_shield.middleware import SEOShieldMiddleware
from apps.seo_shield.models import BlockLog, IPRiskScore


def _dummy_view(request):
    """Simple view that returns 200."""
    from django.http import HttpResponse

    return HttpResponse("OK", status=200)


class SEOShieldMiddlewareTests(TestCase):
    """Tests for SEOShieldMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        cache.clear()
        self.middleware = SEOShieldMiddleware(_dummy_view)

    def tearDown(self):
        cache.clear()

    def _make_normal_request(self, path="/", ip="192.168.1.1"):
        """Create a request that looks like a normal browser."""
        request = self.factory.get(
            path,
            HTTP_USER_AGENT=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            ),
            HTTP_ACCEPT="text/html,application/xhtml+xml",
            HTTP_ACCEPT_ENCODING="gzip, deflate, br",
            HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9",
        )
        request.META["REMOTE_ADDR"] = ip
        return request

    @override_settings(SHIELD_ENABLED=True)
    def test_normal_request_passes_through(self):
        """Normal browser request passes through middleware."""
        request = self._make_normal_request()
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(SHIELD_ENABLED=False)
    def test_disabled_shield_passes_all(self):
        """When SHIELD_ENABLED=False, all requests pass through."""
        request = self.factory.get(
            "/.env",
            HTTP_USER_AGENT="sqlmap/1.6",
        )
        request.META["REMOTE_ADDR"] = "1.2.3.4"

        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(SHIELD_ENABLED=True, SHIELD_WHITELIST_IPS=["10.0.0.1"])
    def test_whitelisted_ip_passes(self):
        """Whitelisted IPs (from settings) bypass all Shield checks."""
        request = self.factory.get(
            "/.env",
            HTTP_USER_AGENT="sqlmap/1.6",
        )
        request.META["REMOTE_ADDR"] = "10.0.0.1"

        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(SHIELD_ENABLED=True)
    def test_db_whitelisted_ip_passes(self):
        """IPs whitelisted in the database bypass all Shield checks."""
        IPRiskScore.objects.create(
            ip_address="10.0.0.2",
            is_whitelisted=True,
        )
        request = self.factory.get(
            "/.env",
            HTTP_USER_AGENT="sqlmap/1.6",
        )
        request.META["REMOTE_ADDR"] = "10.0.0.2"

        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(
        SHIELD_ENABLED=True,
        SHIELD_RATE_LIMIT_WINDOW=60,
        SHIELD_RATE_LIMIT_MAX=3,
    )
    def test_rate_limited_ip_gets_429(self):
        """IP exceeding rate limit receives 429 response."""
        for i in range(4):
            request = self._make_normal_request(ip="192.168.1.50")
            response = self.middleware(request)

        # The 4th request (over limit of 3) should be blocked
        # Need to send one more since the counter includes the current request
        request = self._make_normal_request(ip="192.168.1.50")
        response = self.middleware(request)
        # After exceeding the limit, subsequent requests get 429
        self.assertEqual(response.status_code, 429)
        self.assertIn("TOO_MANY_REQUESTS", response.content.decode())

    @override_settings(
        SHIELD_ENABLED=True,
        SHIELD_RATE_LIMIT_WINDOW=60,
        SHIELD_RATE_LIMIT_MAX=3,
    )
    def test_rate_limit_creates_block_log(self):
        """Rate limited request creates a BlockLog entry."""
        for i in range(5):
            request = self._make_normal_request(ip="192.168.1.60")
            self.middleware(request)

        logs = BlockLog.objects.filter(
            ip_address="192.168.1.60",
            reason="rate_limit",
        )
        self.assertTrue(logs.exists())
        log = logs.first()
        self.assertEqual(log.action_taken, "blocked")
        self.assertEqual(log.response_code, 429)

    @override_settings(SHIELD_ENABLED=True)
    @patch("apps.seo_shield.middleware.RiskEngine.evaluate")
    def test_high_risk_blocked(self, mock_evaluate):
        """Request with high risk score (>=80) is blocked with 429."""
        from apps.seo_shield.risk_engine import RiskResult

        mock_evaluate.return_value = RiskResult(
            score=90,
            signals={
                "rate_limit": 0,
                "header_anomaly": 100,
                "path_pattern": 100,
                "ua_anomaly": 80,
                "robots_violation": 0,
            },
            action="block",
        )

        request = self._make_normal_request(ip="192.168.1.70")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 429)

    @override_settings(SHIELD_ENABLED=True)
    @patch("apps.seo_shield.middleware.RiskEngine.evaluate")
    def test_block_creates_block_log(self, mock_evaluate):
        """Blocked request creates a BlockLog entry with reason 'risk_threshold'."""
        from apps.seo_shield.risk_engine import RiskResult

        mock_evaluate.return_value = RiskResult(
            score=85,
            signals={
                "rate_limit": 0,
                "header_anomaly": 100,
                "path_pattern": 100,
                "ua_anomaly": 80,
                "robots_violation": 0,
            },
            action="block",
        )

        request = self._make_normal_request(ip="192.168.1.71")
        self.middleware(request)

        log = BlockLog.objects.filter(
            ip_address="192.168.1.71",
            reason="risk_threshold",
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.action_taken, "blocked")
        self.assertEqual(log.risk_score, 85)

    @override_settings(SHIELD_ENABLED=True)
    @patch("apps.seo_shield.middleware.RiskEngine.evaluate")
    def test_challenge_action_returns_429(self, mock_evaluate):
        """Challenge action currently returns 429 (same as block)."""
        from apps.seo_shield.risk_engine import RiskResult

        mock_evaluate.return_value = RiskResult(
            score=65,
            signals={
                "rate_limit": 0,
                "header_anomaly": 50,
                "path_pattern": 100,
                "ua_anomaly": 0,
                "robots_violation": 0,
            },
            action="challenge",
        )

        request = self._make_normal_request(ip="192.168.1.72")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 429)

    @override_settings(SHIELD_ENABLED=True)
    @patch("apps.seo_shield.middleware.RiskEngine.evaluate")
    def test_challenge_creates_block_log(self, mock_evaluate):
        """Challenge action creates BlockLog with action_taken='challenged'."""
        from apps.seo_shield.risk_engine import RiskResult

        mock_evaluate.return_value = RiskResult(
            score=65,
            signals={
                "rate_limit": 0,
                "header_anomaly": 50,
                "path_pattern": 100,
                "ua_anomaly": 0,
                "robots_violation": 0,
            },
            action="challenge",
        )

        request = self._make_normal_request(ip="192.168.1.73")
        self.middleware(request)

        log = BlockLog.objects.filter(
            ip_address="192.168.1.73",
            reason="risk_challenge",
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.action_taken, "challenged")

    @override_settings(SHIELD_ENABLED=True)
    @patch("apps.seo_shield.middleware.RiskEngine.evaluate")
    def test_log_action_passes_request(self, mock_evaluate):
        """Log action allows the request through with 200."""
        from apps.seo_shield.risk_engine import RiskResult

        mock_evaluate.return_value = RiskResult(
            score=35,
            signals={
                "rate_limit": 0,
                "header_anomaly": 30,
                "path_pattern": 0,
                "ua_anomaly": 0,
                "robots_violation": 0,
            },
            action="log",
        )

        request = self._make_normal_request(ip="192.168.1.74")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(SHIELD_ENABLED=True)
    @patch("apps.seo_shield.middleware.RiskEngine.evaluate")
    def test_log_action_creates_block_log(self, mock_evaluate):
        """Log action creates BlockLog with action_taken='logged' and 200 code."""
        from apps.seo_shield.risk_engine import RiskResult

        mock_evaluate.return_value = RiskResult(
            score=40,
            signals={
                "rate_limit": 0,
                "header_anomaly": 40,
                "path_pattern": 0,
                "ua_anomaly": 0,
                "robots_violation": 0,
            },
            action="log",
        )

        request = self._make_normal_request(ip="192.168.1.75")
        self.middleware(request)

        log = BlockLog.objects.filter(
            ip_address="192.168.1.75",
            reason="risk_elevated",
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.action_taken, "logged")
        self.assertEqual(log.response_code, 200)

    @override_settings(SHIELD_ENABLED=True)
    @patch("apps.seo_shield.middleware.RiskEngine.evaluate")
    def test_pass_action_no_block_log(self, mock_evaluate):
        """Pass action does not create any BlockLog entry."""
        from apps.seo_shield.risk_engine import RiskResult

        mock_evaluate.return_value = RiskResult(
            score=5,
            signals={
                "rate_limit": 0,
                "header_anomaly": 0,
                "path_pattern": 0,
                "ua_anomaly": 0,
                "robots_violation": 0,
            },
            action="pass",
        )

        request = self._make_normal_request(ip="192.168.1.76")
        self.middleware(request)

        logs = BlockLog.objects.filter(ip_address="192.168.1.76")
        self.assertFalse(logs.exists())

    @override_settings(SHIELD_ENABLED=True)
    @patch("apps.seo_shield.middleware.RiskEngine.evaluate")
    @patch("apps.core.events.shield_threat_detected.send")
    def test_block_sends_threat_event(self, mock_signal, mock_evaluate):
        """Block action sends shield_threat_detected signal."""
        from apps.seo_shield.risk_engine import RiskResult

        mock_evaluate.return_value = RiskResult(
            score=90,
            signals={
                "rate_limit": 100,
                "header_anomaly": 0,
                "path_pattern": 0,
                "ua_anomaly": 0,
                "robots_violation": 0,
            },
            action="block",
        )

        request = self._make_normal_request(ip="192.168.1.77")
        self.middleware(request)

        mock_signal.assert_called_once()
        call_kwargs = mock_signal.call_args[1]
        self.assertEqual(call_kwargs["ip_address"], "192.168.1.77")
        self.assertEqual(call_kwargs["action"], "block")

    @override_settings(SHIELD_ENABLED=True)
    def test_429_response_json_format(self):
        """429 response body is valid JSON with expected structure."""
        import json

        response = self.middleware._get_response_429()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Content-Type"], "application/json")

        body = json.loads(response.content)
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], "TOO_MANY_REQUESTS")
