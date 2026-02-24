"""
Tests for apps.seo_shield.risk_engine.RiskEngine.

Covers risk evaluation for normal requests, suspicious paths, header
anomalies, scanner UA patterns, bot impersonation, action thresholds,
and the RiskResult dataclass.
"""

from django.test import TestCase, RequestFactory, override_settings

from apps.seo_shield.risk_engine import RiskEngine, RiskResult


class RiskResultTests(TestCase):
    """Tests for the RiskResult dataclass."""

    def test_default_values(self):
        """RiskResult has sensible defaults."""
        r = RiskResult()
        self.assertEqual(r.score, 0)
        self.assertEqual(r.signals, {})
        self.assertEqual(r.action, 'pass')

    def test_custom_values(self):
        """RiskResult accepts custom values."""
        r = RiskResult(score=75, signals={'rate_limit': 100}, action='block')
        self.assertEqual(r.score, 75)
        self.assertEqual(r.signals, {'rate_limit': 100})
        self.assertEqual(r.action, 'block')

    def test_signals_default_independent(self):
        """Each RiskResult gets its own signals dict (no shared state)."""
        r1 = RiskResult()
        r2 = RiskResult()
        r1.signals['test'] = 50
        self.assertEqual(r2.signals, {})


class RiskEngineDetermineActionTests(TestCase):
    """Tests for RiskEngine._determine_action thresholds."""

    def setUp(self):
        self.engine = RiskEngine()

    def test_pass_below_log_threshold(self):
        """Score below 30 yields 'pass'."""
        self.assertEqual(self.engine._determine_action(0), 'pass')
        self.assertEqual(self.engine._determine_action(10), 'pass')
        self.assertEqual(self.engine._determine_action(29), 'pass')

    def test_log_at_threshold(self):
        """Score at log threshold (30) yields 'log'."""
        self.assertEqual(self.engine._determine_action(30), 'log')

    def test_log_between_thresholds(self):
        """Score between log and challenge thresholds yields 'log'."""
        self.assertEqual(self.engine._determine_action(45), 'log')
        self.assertEqual(self.engine._determine_action(59), 'log')

    def test_challenge_at_threshold(self):
        """Score at challenge threshold (60) yields 'challenge'."""
        self.assertEqual(self.engine._determine_action(60), 'challenge')

    def test_challenge_between_thresholds(self):
        """Score between challenge and block thresholds yields 'challenge'."""
        self.assertEqual(self.engine._determine_action(70), 'challenge')
        self.assertEqual(self.engine._determine_action(79), 'challenge')

    def test_block_at_threshold(self):
        """Score at block threshold (80) yields 'block'."""
        self.assertEqual(self.engine._determine_action(80), 'block')

    def test_block_above_threshold(self):
        """Score above block threshold yields 'block'."""
        self.assertEqual(self.engine._determine_action(95), 'block')
        self.assertEqual(self.engine._determine_action(100), 'block')

    @override_settings(
        SHIELD_THRESHOLD_LOG=20,
        SHIELD_THRESHOLD_CHALLENGE=50,
        SHIELD_THRESHOLD_BLOCK=70,
    )
    def test_custom_thresholds_from_settings(self):
        """Thresholds can be overridden via Django settings."""
        engine = RiskEngine()
        self.assertEqual(engine._determine_action(19), 'pass')
        self.assertEqual(engine._determine_action(20), 'log')
        self.assertEqual(engine._determine_action(50), 'challenge')
        self.assertEqual(engine._determine_action(70), 'block')


class RiskEngineEvaluateTests(TestCase):
    """Tests for RiskEngine.evaluate with various request scenarios."""

    def setUp(self):
        self.engine = RiskEngine()
        self.factory = RequestFactory()

    def test_normal_request_low_score(self):
        """Normal browser request gets low risk score and 'pass' action."""
        request = self.factory.get('/', HTTP_USER_AGENT=(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ), HTTP_ACCEPT='text/html,application/xhtml+xml',
            HTTP_ACCEPT_ENCODING='gzip, deflate, br',
            HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9',
        )

        result = self.engine.evaluate(request, ip_address='1.2.3.4')
        self.assertEqual(result.action, 'pass')
        self.assertLess(result.score, 30)

    def test_suspicious_path_env(self):
        """Request to /.env triggers high path_pattern signal."""
        request = self.factory.get('/.env', HTTP_USER_AGENT=(
            'Mozilla/5.0 Chrome/120.0.0.0'
        ), HTTP_ACCEPT='text/html',
            HTTP_ACCEPT_ENCODING='gzip',
            HTTP_ACCEPT_LANGUAGE='en-US',
        )

        result = self.engine.evaluate(request, ip_address='1.2.3.4')
        self.assertEqual(result.signals['path_pattern'], 100)
        self.assertGreaterEqual(result.score, 20)

    def test_suspicious_path_wp_admin(self):
        """Request to /wp-admin triggers path_pattern signal."""
        request = self.factory.get('/wp-admin', HTTP_USER_AGENT=(
            'Mozilla/5.0 Chrome/120.0.0.0'
        ), HTTP_ACCEPT='text/html',
            HTTP_ACCEPT_ENCODING='gzip',
            HTTP_ACCEPT_LANGUAGE='en-US',
        )

        result = self.engine.evaluate(request, ip_address='1.2.3.4')
        self.assertEqual(result.signals['path_pattern'], 100)

    def test_missing_accept_header_anomaly(self):
        """Missing Accept header contributes to header_anomaly score."""
        request = self.factory.get('/', HTTP_USER_AGENT='SomeBot/1.0')
        # RequestFactory does not add Accept/Accept-Encoding/Accept-Language
        # by default, so all three header checks will trigger.

        result = self.engine.evaluate(request, ip_address='1.2.3.4')
        self.assertGreater(result.signals['header_anomaly'], 0)

    def test_no_user_agent_header(self):
        """Missing User-Agent triggers both header_anomaly and ua_anomaly."""
        request = self.factory.get('/')
        # Remove User-Agent
        request.META.pop('HTTP_USER_AGENT', None)

        result = self.engine.evaluate(request, ip_address='1.2.3.4')
        self.assertEqual(result.signals['ua_anomaly'], 100)
        self.assertGreaterEqual(result.signals['header_anomaly'], 40)

    def test_scanner_ua_sqlmap(self):
        """sqlmap User-Agent triggers ua_anomaly signal."""
        request = self.factory.get('/', HTTP_USER_AGENT='sqlmap/1.6',
                                   HTTP_ACCEPT='*/*',
                                   HTTP_ACCEPT_ENCODING='gzip',
                                   HTTP_ACCEPT_LANGUAGE='en')

        result = self.engine.evaluate(request, ip_address='1.2.3.4')
        self.assertEqual(result.signals['ua_anomaly'], 80)

    def test_scanner_ua_nikto(self):
        """nikto User-Agent triggers ua_anomaly signal."""
        request = self.factory.get('/', HTTP_USER_AGENT='Mozilla/5.0 nikto',
                                   HTTP_ACCEPT='*/*',
                                   HTTP_ACCEPT_ENCODING='gzip',
                                   HTTP_ACCEPT_LANGUAGE='en')

        result = self.engine.evaluate(request, ip_address='1.2.3.4')
        self.assertEqual(result.signals['ua_anomaly'], 80)

    def test_rate_limited_request(self):
        """Rate limited request gets rate_limit signal of 100."""
        request = self.factory.get('/', HTTP_USER_AGENT=(
            'Mozilla/5.0 Chrome/120.0.0.0'
        ), HTTP_ACCEPT='text/html',
            HTTP_ACCEPT_ENCODING='gzip',
            HTTP_ACCEPT_LANGUAGE='en-US',
        )

        result = self.engine.evaluate(
            request, ip_address='1.2.3.4', rate_limited=True,
        )
        self.assertEqual(result.signals['rate_limit'], 100)
        self.assertGreaterEqual(result.score, 30)

    def test_bot_impersonation(self):
        """Failed bot verification triggers ua_anomaly of 80."""
        request = self.factory.get('/', HTTP_USER_AGENT='Googlebot/2.1',
                                   HTTP_ACCEPT='text/html',
                                   HTTP_ACCEPT_ENCODING='gzip',
                                   HTTP_ACCEPT_LANGUAGE='en-US')

        result = self.engine.evaluate(
            request, ip_address='1.2.3.4', bot_verified=False,
        )
        self.assertEqual(result.signals['ua_anomaly'], 80)

    def test_verified_bot_no_ua_anomaly(self):
        """Verified bot gets no ua_anomaly score."""
        request = self.factory.get('/', HTTP_USER_AGENT='Googlebot/2.1',
                                   HTTP_ACCEPT='text/html',
                                   HTTP_ACCEPT_ENCODING='gzip',
                                   HTTP_ACCEPT_LANGUAGE='en-US')

        result = self.engine.evaluate(
            request, ip_address='66.249.66.1', bot_verified=True,
        )
        self.assertEqual(result.signals['ua_anomaly'], 0)

    def test_robots_violation_always_zero(self):
        """robots_violation signal is always 0 (not yet implemented)."""
        request = self.factory.get('/', HTTP_USER_AGENT='TestBot/1.0',
                                   HTTP_ACCEPT='*/*',
                                   HTTP_ACCEPT_ENCODING='gzip',
                                   HTTP_ACCEPT_LANGUAGE='en')

        result = self.engine.evaluate(request, ip_address='1.2.3.4')
        self.assertEqual(result.signals['robots_violation'], 0)

    def test_sql_injection_in_query_string(self):
        """SQL injection patterns in query string trigger path_pattern."""
        request = self.factory.get(
            '/?id=1 UNION SELECT * FROM users',
            HTTP_USER_AGENT='Chrome/120',
            HTTP_ACCEPT='text/html',
            HTTP_ACCEPT_ENCODING='gzip',
            HTTP_ACCEPT_LANGUAGE='en',
        )

        result = self.engine.evaluate(request, ip_address='1.2.3.4')
        self.assertEqual(result.signals['path_pattern'], 100)

    def test_short_user_agent(self):
        """Very short UA (less than 10 chars) gets high ua_anomaly."""
        request = self.factory.get('/', HTTP_USER_AGENT='Bot',
                                   HTTP_ACCEPT='*/*',
                                   HTTP_ACCEPT_ENCODING='gzip',
                                   HTTP_ACCEPT_LANGUAGE='en')

        result = self.engine.evaluate(request, ip_address='1.2.3.4')
        self.assertEqual(result.signals['ua_anomaly'], 70)
