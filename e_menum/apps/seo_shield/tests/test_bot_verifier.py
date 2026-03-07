"""
Tests for apps.seo_shield.bot_verifier.BotVerifier.

Covers User-Agent matching, IP range verification, DNS verification
(mocked), database loading, and fallback to DEFAULT_BOTS.
"""

from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from apps.seo_shield.bot_verifier import BotVerifier, DEFAULT_BOTS
from apps.seo_shield.models import BotWhitelist


class BotVerifierUAMatchTests(TestCase):
    """Tests for BotVerifier._ua_match."""

    def setUp(self):
        self.verifier = BotVerifier()

    def test_match_googlebot(self):
        """Googlebot UA string is matched."""
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        self.assertTrue(self.verifier._ua_match(ua, r"Googlebot"))

    def test_match_bingbot(self):
        """Bingbot UA string is matched."""
        ua = "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
        self.assertTrue(self.verifier._ua_match(ua, r"bingbot"))

    def test_match_case_insensitive(self):
        """Matching is case-insensitive."""
        self.assertTrue(self.verifier._ua_match("GOOGLEBOT/2.1", r"Googlebot"))

    def test_no_match_unknown_ua(self):
        """Unknown UA does not match any bot pattern."""
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        self.assertFalse(self.verifier._ua_match(ua, r"Googlebot"))

    def test_invalid_regex_returns_false(self):
        """Invalid regex pattern returns False instead of raising."""
        self.assertFalse(self.verifier._ua_match("test", r"[invalid"))

    def test_empty_ua_returns_false(self):
        """Empty UA string does not match."""
        self.assertFalse(self.verifier._ua_match("", r"Googlebot"))


class BotVerifierIPRangeTests(TestCase):
    """Tests for BotVerifier._ip_range_verify."""

    def setUp(self):
        self.verifier = BotVerifier()

    def test_ip_in_range(self):
        """IP within CIDR range returns True."""
        self.assertTrue(
            self.verifier._ip_range_verify("192.168.1.50", ["192.168.1.0/24"])
        )

    def test_ip_not_in_range(self):
        """IP outside CIDR range returns False."""
        self.assertFalse(self.verifier._ip_range_verify("10.0.0.1", ["192.168.1.0/24"]))

    def test_ip_in_one_of_multiple_ranges(self):
        """IP matching any range in the list returns True."""
        ranges = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
        self.assertTrue(self.verifier._ip_range_verify("172.20.5.3", ranges))

    def test_invalid_ip_returns_false(self):
        """Invalid IP address returns False."""
        self.assertFalse(self.verifier._ip_range_verify("not-an-ip", ["10.0.0.0/8"]))

    def test_invalid_cidr_skipped(self):
        """Invalid CIDR range is skipped without error."""
        self.assertFalse(self.verifier._ip_range_verify("10.0.0.1", ["invalid-cidr"]))

    def test_empty_ranges(self):
        """Empty range list returns False."""
        self.assertFalse(self.verifier._ip_range_verify("10.0.0.1", []))


class BotVerifierDNSVerifyTests(TestCase):
    """Tests for BotVerifier._dns_verify with mocked socket calls."""

    def setUp(self):
        self.verifier = BotVerifier()
        cache.clear()

    def tearDown(self):
        cache.clear()

    @patch("apps.seo_shield.bot_verifier.socket.gethostbyname_ex")
    @patch("apps.seo_shield.bot_verifier.socket.gethostbyaddr")
    def test_valid_dns_verification(self, mock_reverse, mock_forward):
        """DNS verification succeeds when reverse+forward match."""
        mock_reverse.return_value = (
            "crawl-66-249-66-1.googlebot.com",
            [],
            ["66.249.66.1"],
        )
        mock_forward.return_value = (
            "crawl-66-249-66-1.googlebot.com",
            [],
            ["66.249.66.1"],
        )

        self.assertTrue(self.verifier._dns_verify("66.249.66.1", "googlebot.com"))

    @patch("apps.seo_shield.bot_verifier.socket.gethostbyaddr")
    def test_reverse_dns_wrong_domain(self, mock_reverse):
        """DNS verification fails when reverse DNS returns wrong domain."""
        mock_reverse.return_value = ("evil.example.com", [], ["1.2.3.4"])

        self.assertFalse(self.verifier._dns_verify("1.2.3.4", "googlebot.com"))

    @patch("apps.seo_shield.bot_verifier.socket.gethostbyname_ex")
    @patch("apps.seo_shield.bot_verifier.socket.gethostbyaddr")
    def test_forward_dns_ip_mismatch(self, mock_reverse, mock_forward):
        """DNS verification fails when forward DNS IP does not match."""
        mock_reverse.return_value = ("crawl.googlebot.com", [], ["66.249.66.1"])
        mock_forward.return_value = ("crawl.googlebot.com", [], ["66.249.66.99"])

        self.assertFalse(self.verifier._dns_verify("66.249.66.1", "googlebot.com"))

    @patch("apps.seo_shield.bot_verifier.socket.gethostbyaddr")
    def test_dns_socket_error(self, mock_reverse):
        """DNS verification returns False on socket error."""
        import socket

        mock_reverse.side_effect = socket.herror("Host not found")

        self.assertFalse(self.verifier._dns_verify("1.2.3.4", "googlebot.com"))


class BotVerifierVerifyBotTests(TestCase):
    """Tests for BotVerifier.verify_bot integration."""

    def setUp(self):
        self.verifier = BotVerifier()
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_empty_ua_returns_false_none(self):
        """Empty UA returns (False, None)."""
        is_verified, name = self.verifier.verify_bot("1.2.3.4", "")
        self.assertFalse(is_verified)
        self.assertIsNone(name)

    def test_unknown_ua_returns_false_none(self):
        """Unknown UA not matching any bot returns (False, None)."""
        is_verified, name = self.verifier.verify_bot(
            "1.2.3.4", "Mozilla/5.0 Chrome/120"
        )
        self.assertFalse(is_verified)
        self.assertIsNone(name)

    def test_user_agent_only_bot_accepted(self):
        """Bots with user_agent method are accepted on UA match alone."""
        # facebookexternalhit uses user_agent method in DEFAULT_BOTS
        is_verified, name = self.verifier.verify_bot(
            "1.2.3.4", "facebookexternalhit/1.1"
        )
        self.assertTrue(is_verified)
        self.assertEqual(name, "facebookexternalhit")

    @patch("apps.seo_shield.bot_verifier.socket.gethostbyname_ex")
    @patch("apps.seo_shield.bot_verifier.socket.gethostbyaddr")
    def test_dns_bot_verified(self, mock_reverse, mock_forward):
        """DNS-verified bot returns (True, bot_name)."""
        mock_reverse.return_value = ("crawl-1.googlebot.com", [], ["66.249.66.1"])
        mock_forward.return_value = ("crawl-1.googlebot.com", [], ["66.249.66.1"])

        is_verified, name = self.verifier.verify_bot("66.249.66.1", "Googlebot/2.1")
        self.assertTrue(is_verified)
        self.assertEqual(name, "Googlebot")

    @patch("apps.seo_shield.bot_verifier.socket.gethostbyaddr")
    def test_dns_bot_impersonation(self, mock_reverse):
        """Bot impersonation returns (False, bot_name)."""
        mock_reverse.return_value = ("evil.example.com", [], ["1.2.3.4"])

        is_verified, name = self.verifier.verify_bot("1.2.3.4", "Googlebot/2.1")
        self.assertFalse(is_verified)
        self.assertEqual(name, "Googlebot")

    def test_loads_from_database(self):
        """Verifier loads bot entries from the database when available."""
        cache.clear()
        BotWhitelist.objects.create(
            name="CustomBot",
            user_agent_pattern=r"CustomBot",
            verification_method=BotWhitelist.VerificationMethod.USER_AGENT,
            is_active=True,
        )
        # Force reload
        verifier = BotVerifier()
        is_verified, name = verifier.verify_bot("1.2.3.4", "CustomBot/1.0")
        self.assertTrue(is_verified)
        self.assertEqual(name, "CustomBot")

    def test_falls_back_to_defaults_when_db_empty(self):
        """Verifier uses DEFAULT_BOTS when no active DB entries exist."""
        cache.clear()
        verifier = BotVerifier()
        bot_list = verifier._get_bot_whitelist()
        self.assertEqual(len(bot_list), len(DEFAULT_BOTS))

    def test_ip_range_bot_verified(self):
        """Bot with ip_range method is verified when IP is in range."""
        cache.clear()
        BotWhitelist.objects.create(
            name="RangeBot",
            user_agent_pattern=r"RangeBot",
            verification_method=BotWhitelist.VerificationMethod.IP_RANGE,
            ip_ranges=["10.0.0.0/8"],
            is_active=True,
        )
        verifier = BotVerifier()
        is_verified, name = verifier.verify_bot("10.5.3.1", "RangeBot/1.0")
        self.assertTrue(is_verified)
        self.assertEqual(name, "RangeBot")

    def test_ip_range_bot_fails_outside_range(self):
        """Bot with ip_range method fails when IP is not in range."""
        cache.clear()
        BotWhitelist.objects.create(
            name="RangeBot2",
            user_agent_pattern=r"RangeBot2",
            verification_method=BotWhitelist.VerificationMethod.IP_RANGE,
            ip_ranges=["10.0.0.0/8"],
            is_active=True,
        )
        verifier = BotVerifier()
        is_verified, name = verifier.verify_bot("192.168.1.1", "RangeBot2/1.0")
        self.assertFalse(is_verified)
        self.assertEqual(name, "RangeBot2")
