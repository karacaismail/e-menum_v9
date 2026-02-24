"""
Tests for apps.seo.middleware.Track404Middleware.

Covers:
- 404 responses create a NotFound404Log entry
- Static paths (/static/foo) are skipped
- Admin paths (/admin/foo) are skipped
- API paths (/api/foo) are skipped
- File-extension paths (e.g. /foo/bar.css) are skipped
- Aggregation: same path+day increments hit_count
- Different paths on the same day create separate entries
"""

from datetime import date
from unittest.mock import MagicMock

from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from apps.seo.middleware import Track404Middleware
from apps.seo.models import NotFound404Log


class TestTrack404MiddlewareCreatesEntry(TestCase):
    """Test that a 404 response creates a NotFound404Log entry."""

    def setUp(self):
        self.factory = RequestFactory()

    def _make_middleware(self, status_code=404):
        """Create a Track404Middleware with a mock get_response returning the given status."""
        mock_response = HttpResponse(status=status_code)
        get_response = MagicMock(return_value=mock_response)
        return Track404Middleware(get_response)

    def test_404_creates_log_entry(self):
        """A 404 on a normal path should create a NotFound404Log record."""
        middleware = self._make_middleware(status_code=404)
        request = self.factory.get('/nonexistent-page/')

        middleware(request)

        self.assertEqual(NotFound404Log.objects.count(), 1)
        entry = NotFound404Log.objects.first()
        self.assertEqual(entry.path, '/nonexistent-page/')
        self.assertEqual(entry.hit_count, 1)
        self.assertEqual(entry.date, date.today())

    def test_200_does_not_create_log_entry(self):
        """A 200 response should not create any log entry."""
        middleware = self._make_middleware(status_code=200)
        request = self.factory.get('/existing-page/')

        middleware(request)

        self.assertEqual(NotFound404Log.objects.count(), 0)

    def test_500_does_not_create_log_entry(self):
        """A 500 response should not create any log entry."""
        middleware = self._make_middleware(status_code=500)
        request = self.factory.get('/server-error/')

        middleware(request)

        self.assertEqual(NotFound404Log.objects.count(), 0)


class TestTrack404MiddlewareSkipPaths(TestCase):
    """Test that noise paths are skipped by the middleware."""

    def setUp(self):
        self.factory = RequestFactory()
        mock_response = HttpResponse(status=404)
        get_response = MagicMock(return_value=mock_response)
        self.middleware = Track404Middleware(get_response)

    def test_static_path_is_skipped(self):
        """Paths starting with /static/ should not be logged."""
        request = self.factory.get('/static/foo/bar.js')
        self.middleware(request)
        self.assertEqual(NotFound404Log.objects.count(), 0)

    def test_admin_path_is_skipped(self):
        """Paths starting with /admin/ should not be logged."""
        request = self.factory.get('/admin/some-page/')
        self.middleware(request)
        self.assertEqual(NotFound404Log.objects.count(), 0)

    def test_api_path_is_skipped(self):
        """Paths starting with /api/ should not be logged."""
        request = self.factory.get('/api/v1/some-endpoint/')
        self.middleware(request)
        self.assertEqual(NotFound404Log.objects.count(), 0)

    def test_media_path_is_skipped(self):
        """Paths starting with /media/ should not be logged."""
        request = self.factory.get('/media/uploads/image.png')
        self.middleware(request)
        self.assertEqual(NotFound404Log.objects.count(), 0)

    def test_debug_toolbar_path_is_skipped(self):
        """Paths starting with /__debug__/ should not be logged."""
        request = self.factory.get('/__debug__/render_panel/')
        self.middleware(request)
        self.assertEqual(NotFound404Log.objects.count(), 0)

    def test_file_extension_path_is_skipped(self):
        """Paths ending with a file extension (e.g. .css) should not be logged."""
        request = self.factory.get('/foo/bar.css')
        self.middleware(request)
        self.assertEqual(NotFound404Log.objects.count(), 0)

    def test_js_file_path_is_skipped(self):
        """Paths ending with .js should not be logged."""
        request = self.factory.get('/assets/app.js')
        self.middleware(request)
        self.assertEqual(NotFound404Log.objects.count(), 0)

    def test_map_file_path_is_skipped(self):
        """Paths ending with .map should not be logged."""
        request = self.factory.get('/assets/bundle.js.map')
        self.middleware(request)
        self.assertEqual(NotFound404Log.objects.count(), 0)

    def test_ico_file_path_is_skipped(self):
        """Paths ending with .ico (like favicon) should not be logged."""
        request = self.factory.get('/favicon.ico')
        self.middleware(request)
        self.assertEqual(NotFound404Log.objects.count(), 0)


class TestTrack404MiddlewareAggregation(TestCase):
    """Test hit_count aggregation for same path+day."""

    def setUp(self):
        self.factory = RequestFactory()
        mock_response = HttpResponse(status=404)
        get_response = MagicMock(return_value=mock_response)
        self.middleware = Track404Middleware(get_response)

    def test_same_path_same_day_increments_hit_count(self):
        """A second 404 on the same path and same day should increment hit_count."""
        request = self.factory.get('/missing-page/')

        self.middleware(request)
        self.assertEqual(NotFound404Log.objects.count(), 1)
        entry = NotFound404Log.objects.first()
        self.assertEqual(entry.hit_count, 1)

        # Second hit on the same path
        self.middleware(request)

        # Still only one entry
        self.assertEqual(NotFound404Log.objects.count(), 1)
        entry.refresh_from_db()
        self.assertEqual(entry.hit_count, 2)

    def test_third_hit_increments_to_three(self):
        """Three 404 hits on the same path+day should result in hit_count=3."""
        request = self.factory.get('/another-missing/')

        self.middleware(request)
        self.middleware(request)
        self.middleware(request)

        self.assertEqual(NotFound404Log.objects.count(), 1)
        entry = NotFound404Log.objects.first()
        entry.refresh_from_db()
        self.assertEqual(entry.hit_count, 3)

    def test_different_paths_same_day_create_separate_entries(self):
        """Different paths on the same day should create separate log entries."""
        request_a = self.factory.get('/path-alpha/')
        request_b = self.factory.get('/path-beta/')

        self.middleware(request_a)
        self.middleware(request_b)

        self.assertEqual(NotFound404Log.objects.count(), 2)
        paths = set(NotFound404Log.objects.values_list('path', flat=True))
        self.assertEqual(paths, {'/path-alpha/', '/path-beta/'})

    def test_user_agent_and_referer_are_captured(self):
        """The middleware should capture user agent and referer from the request."""
        request = self.factory.get(
            '/capture-test/',
            HTTP_USER_AGENT='Mozilla/5.0 TestAgent',
            HTTP_REFERER='https://google.com/search?q=test',
        )

        self.middleware(request)

        entry = NotFound404Log.objects.first()
        self.assertEqual(entry.last_user_agent, 'Mozilla/5.0 TestAgent')
        self.assertEqual(entry.last_referer, 'https://google.com/search?q=test')

    def test_ip_is_captured_from_remote_addr(self):
        """The middleware should capture the client IP from REMOTE_ADDR."""
        request = self.factory.get('/ip-test/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'

        self.middleware(request)

        entry = NotFound404Log.objects.first()
        self.assertEqual(entry.last_ip, '192.168.1.100')

    def test_ip_is_captured_from_x_forwarded_for(self):
        """The middleware should prefer X-Forwarded-For over REMOTE_ADDR."""
        request = self.factory.get(
            '/xff-test/',
            HTTP_X_FORWARDED_FOR='10.0.0.1, 10.0.0.2',
        )

        self.middleware(request)

        entry = NotFound404Log.objects.first()
        self.assertEqual(entry.last_ip, '10.0.0.1')
