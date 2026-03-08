"""
Tests for Admin UX Enhancements.

Validates enterprise-grade admin UX features:
- Command palette search API
- Toast notification JS/CSS inclusion
- Keyboard shortcuts modal presence
- Form guard integration
- Floating save bar
- Page load and template rendering
- Admin view access control
"""

import pytest


@pytest.mark.django_db
class TestAdminUXAssets:
    """Test that UX enhancement assets are included in admin pages."""

    def test_admin_ux_css_included(self, admin_user, client):
        """admin-ux.css should be included in admin base template."""
        client.force_login(admin_user)
        response = client.get("/admin/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "admin-ux.css" in content

    def test_admin_ux_js_included(self, admin_user, client):
        """admin-ux.js should be included in admin base template."""
        client.force_login(admin_user)
        response = client.get("/admin/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "admin-ux.js" in content

    def test_command_palette_trigger_present(self, admin_user, client):
        """Command palette trigger button should be in the topbar."""
        client.force_login(admin_user)
        response = client.get("/admin/")
        content = response.content.decode()
        assert "ux-cmd-trigger" in content

    def test_command_palette_modal_present(self, admin_user, client):
        """Command palette modal HTML should be present in admin pages."""
        client.force_login(admin_user)
        response = client.get("/admin/")
        content = response.content.decode()
        assert "ux-cmd-overlay" in content
        assert "ux-cmd-dialog" in content

    def test_toast_stack_present(self, admin_user, client):
        """Toast notification stack should be present in admin pages."""
        client.force_login(admin_user)
        response = client.get("/admin/")
        content = response.content.decode()
        assert "ux-toast-stack" in content

    def test_confirm_dialog_present(self, admin_user, client):
        """Confirm dialog should be present in admin pages."""
        client.force_login(admin_user)
        response = client.get("/admin/")
        content = response.content.decode()
        assert "ux-confirm-overlay" in content

    def test_keyboard_shortcuts_modal_present(self, admin_user, client):
        """Keyboard shortcuts help modal should be present."""
        client.force_login(admin_user)
        response = client.get("/admin/")
        content = response.content.decode()
        assert "keyboard-shortcuts-modal" in content

    def test_alpine_js_included(self, admin_user, client):
        """Alpine.js should be loaded for UX interactivity."""
        client.force_login(admin_user)
        response = client.get("/admin/")
        content = response.content.decode()
        assert "alpinejs" in content


@pytest.mark.django_db
class TestAdminDashboard:
    """Test admin dashboard loads correctly."""

    def test_dashboard_loads(self, admin_user, client):
        """Admin dashboard should return 200."""
        client.force_login(admin_user)
        response = client.get("/admin/")
        assert response.status_code == 200

    def test_dashboard_has_enterprise_css(self, admin_user, client):
        """Enterprise dashboard CSS should be included."""
        client.force_login(admin_user)
        response = client.get("/admin/")
        content = response.content.decode()
        assert "enterprise-dashboard.css" in content

    def test_dashboard_unauthenticated_redirects(self, client):
        """Unauthenticated users should be redirected to login."""
        response = client.get("/admin/")
        assert response.status_code in (301, 302)


@pytest.mark.django_db
class TestAdminChangeList:
    """Test admin change list page enhancements."""

    def test_organization_list_loads(self, admin_user, client):
        """Organization changelist should load with UX enhancements."""
        client.force_login(admin_user)
        response = client.get("/admin/core/organization/")
        assert response.status_code == 200
        content = response.content.decode()
        # Result count badge should be in the title area
        assert "ux-result-count" in content

    def test_user_list_loads(self, admin_user, client):
        """User changelist should load successfully."""
        client.force_login(admin_user)
        response = client.get("/admin/core/user/")
        assert response.status_code == 200

    def test_changelist_has_breadcrumbs(self, admin_user, client):
        """Changelist pages should have breadcrumb navigation."""
        client.force_login(admin_user)
        response = client.get("/admin/core/organization/")
        content = response.content.decode()
        assert "breadcrumbs" in content


@pytest.mark.django_db
class TestAdminChangeForm:
    """Test admin change form page enhancements."""

    def test_add_form_has_form_guard(self, admin_user, client):
        """Add form should include formGuard x-data for unsaved change detection."""
        client.force_login(admin_user)
        response = client.get("/admin/core/organization/add/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "formGuard" in content

    def test_add_form_has_unsaved_indicator(self, admin_user, client):
        """Add form should include the unsaved changes indicator."""
        client.force_login(admin_user)
        response = client.get("/admin/core/organization/add/")
        content = response.content.decode()
        assert "ux-unsaved-indicator" in content


@pytest.mark.django_db
class TestAdminCustomViews:
    """Test custom admin views load correctly."""

    def test_settings_page_loads(self, admin_user, client):
        """Admin settings hub should load."""
        client.force_login(admin_user)
        response = client.get("/admin/settings/")
        assert response.status_code == 200

    def test_reports_page_loads(self, admin_user, client):
        """Admin reports page should load."""
        client.force_login(admin_user)
        response = client.get("/admin/reports/")
        assert response.status_code == 200

    def test_permission_matrix_loads(self, admin_user, client):
        """Permission matrix page should load."""
        client.force_login(admin_user)
        response = client.get("/admin/permission-matrix/")
        assert response.status_code == 200

    def test_seo_dashboard_loads(self, admin_user, client):
        """SEO dashboard should load."""
        client.force_login(admin_user)
        response = client.get("/admin/seo-dashboard/")
        assert response.status_code == 200

    def test_shield_dashboard_loads(self, admin_user, client):
        """Shield dashboard should load."""
        client.force_login(admin_user)
        response = client.get("/admin/shield-dashboard/")
        assert response.status_code == 200

    def test_media_library_loads(self, admin_user, client):
        """Media library page should load."""
        client.force_login(admin_user)
        response = client.get("/admin/media-library/")
        assert response.status_code == 200

    def test_custom_views_require_auth(self, client):
        """All custom admin views should require authentication."""
        protected_urls = [
            "/admin/settings/",
            "/admin/reports/",
            "/admin/permission-matrix/",
            "/admin/seo-dashboard/",
            "/admin/shield-dashboard/",
            "/admin/media-library/",
        ]
        for url in protected_urls:
            response = client.get(url)
            assert response.status_code in (
                301,
                302,
            ), f"{url} should redirect unauthenticated users"


@pytest.mark.django_db
class TestAdminSearchAPI:
    """Test admin search/command palette API."""

    def test_search_api_returns_json(self, admin_user, client):
        """Search API should return JSON results."""
        client.force_login(admin_user)
        response = client.get("/admin/api/search/?q=test")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    def test_search_api_requires_auth(self, client):
        """Search API should require authentication."""
        response = client.get("/admin/api/search/?q=test")
        assert response.status_code in (301, 302, 403)

    def test_search_api_min_query_length(self, admin_user, client):
        """Search API should require minimum query length."""
        client.force_login(admin_user)
        response = client.get("/admin/api/search/?q=a")
        assert response.status_code == 200
        data = response.json()
        # Should return empty or limited results for single char
        assert "results" in data


@pytest.mark.django_db
class TestAdminNavigation:
    """Test admin navigation components."""

    def test_sidebar_groups_present(self, admin_user, client):
        """Admin sidebar should have navigation groups."""
        client.force_login(admin_user)
        response = client.get("/admin/")
        content = response.content.decode()
        assert "rail-sidebar" in content
        assert "accordion-sidebar" in content

    def test_mobile_nav_present(self, admin_user, client):
        """Mobile navigation should be present."""
        client.force_login(admin_user)
        response = client.get("/admin/")
        content = response.content.decode()
        assert "mobile-nav" in content

    def test_notification_widget_present(self, admin_user, client):
        """Notification bell widget should be in the topbar."""
        client.force_login(admin_user)
        response = client.get("/admin/")
        content = response.content.decode()
        assert "notification" in content.lower()
