"""
Tests for apps.seo.middleware module.

Covers:
- RedirectMiddleware: matches Redirect records, returns 301/302, increments hit_count
- CanonicalDomainMiddleware: www-to-non-www, trailing slash normalisation
- SEOHeadersMiddleware: X-Robots-Tag, Link canonical header, Permissions-Policy
"""

from django.http import HttpResponse
from django.test import TestCase, RequestFactory, override_settings

from apps.seo.middleware import (
    CanonicalDomainMiddleware,
    RedirectMiddleware,
    SEOHeadersMiddleware,
)
from apps.seo.models import Redirect, RedirectType


def dummy_response(request):
    """Dummy get_response callable returning a 200 HTML response."""
    response = HttpResponse("OK", content_type="text/html; charset=utf-8")
    return response


def dummy_json_response(request):
    """Dummy get_response callable returning a JSON response."""
    return HttpResponse("{}", content_type="application/json")


class TestRedirectMiddleware(TestCase):
    """Test RedirectMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RedirectMiddleware(dummy_response)

    def test_301_redirect(self):
        Redirect.objects.create(
            source_path="/old-page/",
            target_path="/new-page/",
            redirect_type=RedirectType.PERMANENT,
            is_active=True,
        )
        request = self.factory.get("/old-page/")
        response = self.middleware(request)

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/new-page/")

    def test_302_redirect(self):
        Redirect.objects.create(
            source_path="/temp-page/",
            target_path="/new-temp/",
            redirect_type=RedirectType.TEMPORARY,
            is_active=True,
        )
        request = self.factory.get("/temp-page/")
        response = self.middleware(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/new-temp/")

    def test_308_redirect_uses_permanent_class(self):
        Redirect.objects.create(
            source_path="/strict-perm/",
            target_path="/target/",
            redirect_type=RedirectType.PERMANENT_STRICT,
            is_active=True,
        )
        request = self.factory.get("/strict-perm/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 301)  # HttpResponsePermanentRedirect

    def test_307_redirect_uses_temporary_class(self):
        Redirect.objects.create(
            source_path="/strict-temp/",
            target_path="/target/",
            redirect_type=RedirectType.TEMPORARY_STRICT,
            is_active=True,
        )
        request = self.factory.get("/strict-temp/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 302)  # HttpResponseRedirect

    def test_no_redirect_for_unknown_path(self):
        request = self.factory.get("/unknown/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_inactive_redirect_is_ignored(self):
        Redirect.objects.create(
            source_path="/inactive/",
            target_path="/target/",
            is_active=False,
        )
        request = self.factory.get("/inactive/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_soft_deleted_redirect_is_ignored(self):
        from django.utils import timezone

        Redirect.objects.create(
            source_path="/deleted/",
            target_path="/target/",
            is_active=True,
            deleted_at=timezone.now(),
        )
        request = self.factory.get("/deleted/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_hit_count_incremented(self):
        redirect = Redirect.objects.create(
            source_path="/counted-page/",
            target_path="/target/",
            redirect_type=RedirectType.PERMANENT,
            is_active=True,
            hit_count=0,
        )
        request = self.factory.get("/counted-page/")
        self.middleware(request)

        redirect.refresh_from_db()
        self.assertEqual(redirect.hit_count, 1)
        self.assertIsNotNone(redirect.last_hit)


class TestCanonicalDomainMiddleware(TestCase):
    """Test CanonicalDomainMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(SEO_CANONICAL_DOMAIN="e-menum.net")
    def test_www_redirects_to_non_www(self):
        middleware = CanonicalDomainMiddleware(dummy_response)
        middleware.canonical_domain = "e-menum.net"

        request = self.factory.get("/some-page/")
        request.META["HTTP_HOST"] = "www.e-menum.net"
        request.META["SERVER_NAME"] = "www.e-menum.net"
        response = middleware(request)

        self.assertEqual(response.status_code, 301)
        self.assertIn("e-menum.net", response["Location"])
        self.assertIn("/some-page/", response["Location"])

    @override_settings(SEO_CANONICAL_DOMAIN="e-menum.net")
    def test_canonical_domain_no_redirect(self):
        middleware = CanonicalDomainMiddleware(dummy_response)
        middleware.canonical_domain = "e-menum.net"

        request = self.factory.get("/page/")
        request.META["HTTP_HOST"] = "e-menum.net"
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    @override_settings(APPEND_SLASH=True)
    def test_trailing_slash_appended(self):
        middleware = CanonicalDomainMiddleware(dummy_response)
        middleware.canonical_domain = ""

        request = self.factory.get("/no-trailing-slash")
        response = middleware(request)

        self.assertEqual(response.status_code, 301)
        self.assertTrue(response["Location"].endswith("/no-trailing-slash/"))

    @override_settings(APPEND_SLASH=True)
    def test_trailing_slash_not_added_to_files(self):
        middleware = CanonicalDomainMiddleware(dummy_response)
        middleware.canonical_domain = ""

        request = self.factory.get("/static/style.css")
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    @override_settings(APPEND_SLASH=True)
    def test_trailing_slash_not_added_to_api(self):
        middleware = CanonicalDomainMiddleware(dummy_response)
        middleware.canonical_domain = ""

        request = self.factory.get("/api/v1/menus")
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    @override_settings(APPEND_SLASH=True)
    def test_trailing_slash_not_added_to_admin(self):
        middleware = CanonicalDomainMiddleware(dummy_response)
        middleware.canonical_domain = ""

        request = self.factory.get("/admin/something")
        response = middleware(request)

        self.assertEqual(response.status_code, 200)

    @override_settings(APPEND_SLASH=True)
    def test_trailing_slash_preserves_query_string(self):
        middleware = CanonicalDomainMiddleware(dummy_response)
        middleware.canonical_domain = ""

        request = self.factory.get("/page?foo=bar")
        response = middleware(request)

        self.assertEqual(response.status_code, 301)
        self.assertIn("?foo=bar", response["Location"])


class TestSEOHeadersMiddleware(TestCase):
    """Test SEOHeadersMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SEOHeadersMiddleware(dummy_response)

    def test_permissions_policy_header_set(self):
        request = self.factory.get("/")
        response = self.middleware(request)
        self.assertEqual(response["Permissions-Policy"], "interest-cohort=()")

    def test_x_robots_tag_for_admin_paths(self):
        request = self.factory.get("/admin/dashboard/")
        response = self.middleware(request)
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_x_robots_tag_for_api_paths(self):
        # API paths return JSON, middleware skips non-HTML
        middleware = SEOHeadersMiddleware(dummy_json_response)
        request = self.factory.get("/api/v1/menus/")
        response = middleware(request)
        self.assertNotIn("X-Robots-Tag", response)

    def test_x_robots_tag_from_request_attribute(self):
        request = self.factory.get("/custom/")
        request.seo_robots = "noindex, follow"
        response = self.middleware(request)
        self.assertEqual(response["X-Robots-Tag"], "noindex, follow")

    def test_link_canonical_header(self):
        request = self.factory.get("/page/")
        request.seo_canonical = "https://e-menum.net/page/"
        response = self.middleware(request)
        self.assertEqual(
            response["Link"], '<https://e-menum.net/page/>; rel="canonical"'
        )

    def test_no_link_header_without_canonical(self):
        request = self.factory.get("/page/")
        response = self.middleware(request)
        self.assertNotIn("Link", response)

    def test_skips_non_html_responses(self):
        middleware = SEOHeadersMiddleware(dummy_json_response)
        request = self.factory.get("/api/")
        response = middleware(request)
        # Permissions-Policy should not be set for non-HTML
        self.assertNotIn("X-Robots-Tag", response)

    def test_public_page_no_default_robots_header(self):
        request = self.factory.get("/features/")
        response = self.middleware(request)
        # Public pages without seo_robots attribute should not get X-Robots-Tag
        self.assertNotIn("X-Robots-Tag", response)
