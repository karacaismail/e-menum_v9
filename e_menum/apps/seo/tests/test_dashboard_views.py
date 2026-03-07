"""
Tests for SEO Dashboard and Shield Dashboard admin views.

Covers:
- SEO dashboard returns 200 for staff user
- SEO dashboard returns redirect for anonymous user
- Shield dashboard returns 200 for staff user
- Shield dashboard returns redirect for anonymous user
- SEO dashboard context contains expected keys
"""

from django.test import TestCase

from apps.core.models import User


class TestSEODashboardView(TestCase):
    """Test the admin SEO dashboard view at /admin/seo-dashboard/."""

    def setUp(self):
        self.url = "/admin/seo-dashboard/"
        self.user = User.objects.create_user(
            email="staff@test.com",
            password="testpass123",
            first_name="Staff",
            last_name="User",
        )
        self.user.is_staff = True
        self.user.save()

    def test_seo_dashboard_returns_200_for_staff(self):
        """Staff users should get a 200 response on the SEO dashboard."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_seo_dashboard_redirects_anonymous_user(self):
        """Anonymous users should be redirected (302) when accessing the SEO dashboard."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_seo_dashboard_redirect_targets_admin_login(self):
        """Anonymous users should be redirected to the admin login page."""
        response = self.client.get(self.url)
        self.assertIn("/admin/login/", response.url)

    def test_seo_dashboard_context_contains_expected_keys(self):
        """The SEO dashboard context should contain all expected data keys."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        expected_keys = [
            "title",
            "total_redirects",
            "total_broken_links",
            "today_404s",
            "avg_seo_score",
            "top_404s",
            "recent_broken_links",
            "last_crawl",
        ]
        for key in expected_keys:
            self.assertIn(key, response.context, f"Missing context key: {key}")

    def test_seo_dashboard_title_is_correct(self):
        """The context title should be 'SEO Dashboard'."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context["title"], "SEO Dashboard")

    def test_seo_dashboard_stats_are_zero_when_empty(self):
        """When no SEO data exists, stat values should be zero or None."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.context["total_redirects"], 0)
        self.assertEqual(response.context["total_broken_links"], 0)
        self.assertEqual(response.context["today_404s"], 0)
        self.assertIsNone(response.context["last_crawl"])

    def test_seo_dashboard_non_staff_user_redirected(self):
        """Non-staff users should be redirected, not granted access."""
        non_staff = User.objects.create_user(
            email="regular@test.com",
            password="testpass123",
            first_name="Regular",
            last_name="User",
        )
        self.client.force_login(non_staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


class TestShieldDashboardView(TestCase):
    """Test the admin Shield dashboard view at /admin/shield-dashboard/."""

    def setUp(self):
        self.url = "/admin/shield-dashboard/"
        self.user = User.objects.create_user(
            email="shieldstaff@test.com",
            password="testpass123",
            first_name="Shield",
            last_name="Staff",
        )
        self.user.is_staff = True
        self.user.save()

    def test_shield_dashboard_returns_200_for_staff(self):
        """Staff users should get a 200 response on the Shield dashboard."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_shield_dashboard_redirects_anonymous_user(self):
        """Anonymous users should be redirected (302) when accessing the Shield dashboard."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_shield_dashboard_redirect_targets_admin_login(self):
        """Anonymous users should be redirected to the admin login page."""
        response = self.client.get(self.url)
        self.assertIn("/admin/login/", response.url)

    def test_shield_dashboard_context_contains_expected_keys(self):
        """The Shield dashboard context should contain all expected data keys."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        expected_keys = [
            "title",
            "blocked_today",
            "blocked_7d",
            "blocked_30d",
            "high_risk_ips",
            "top_reasons",
            "top_blocked_ips",
            "recent_logs",
        ]
        for key in expected_keys:
            self.assertIn(key, response.context, f"Missing context key: {key}")

    def test_shield_dashboard_title_is_correct(self):
        """The context title should be 'Shield Dashboard'."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context["title"], "Shield Dashboard")

    def test_shield_dashboard_stats_are_zero_when_empty(self):
        """When no shield data exists, stat values should be zero."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.context["blocked_today"], 0)
        self.assertEqual(response.context["blocked_7d"], 0)
        self.assertEqual(response.context["blocked_30d"], 0)
        self.assertEqual(response.context["high_risk_ips"], 0)

    def test_shield_dashboard_non_staff_user_redirected(self):
        """Non-staff users should be redirected, not granted access."""
        non_staff = User.objects.create_user(
            email="shieldregular@test.com",
            password="testpass123",
            first_name="Regular",
            last_name="User",
        )
        self.client.force_login(non_staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
