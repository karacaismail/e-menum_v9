"""
URL configuration for the Core application.

This module defines URL patterns for:
- Authentication endpoints (login, logout, token refresh)
- User profile management
- Session management
- Organization management (admin)
- User management (within organization)

URL Structure:
    /api/v1/auth/
        POST login/              - User login, returns JWT tokens
        POST logout/             - Logout, blacklists refresh token
        POST refresh/            - Refresh access token
        POST verify/             - Verify access token validity
        GET/PUT/PATCH me/        - Current user profile
        POST password/           - Change password
        GET sessions/            - List active sessions
        DELETE sessions/<id>/    - Revoke specific session
        POST sessions/revoke-all/ - Revoke all sessions

    /api/v1/organizations/
        GET /                    - List organizations (admin)
        POST /                   - Create organization
        GET /<id>/               - Get organization details
        PUT/PATCH /<id>/         - Update organization
        DELETE /<id>/            - Soft delete organization

    /api/v1/users/
        GET /                    - List users in organization
        POST /                   - Create new user
        GET /<id>/               - Get user details
        PUT/PATCH /<id>/         - Update user
        DELETE /<id>/            - Soft delete user

Usage:
    In config/urls.py:
        path('api/v1/auth/', include('apps.core.urls')),

    Or for specific endpoints:
        path('api/v1/auth/', include(('apps.core.urls', 'core'), namespace='auth')),
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.core.views import (
    # Authentication views
    LoginView,
    LogoutView,
    TokenRefreshView,
    TokenVerifyView,
    UserMeView,
    PasswordChangeView,
    SessionListView,
    SessionRevokeView,
    SessionRevokeAllView,
    # ViewSets
    OrganizationViewSet,
    UserViewSet,
)


app_name = 'core'


# =============================================================================
# ROUTER CONFIGURATION
# =============================================================================

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'users', UserViewSet, basename='user')


# =============================================================================
# AUTHENTICATION URL PATTERNS
# =============================================================================

auth_urlpatterns = [
    # Login/Logout
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Token management
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('verify/', TokenVerifyView.as_view(), name='token-verify'),

    # User profile
    path('me/', UserMeView.as_view(), name='user-me'),
    path('password/', PasswordChangeView.as_view(), name='password-change'),

    # Session management
    path('sessions/', SessionListView.as_view(), name='session-list'),
    path('sessions/<uuid:session_id>/', SessionRevokeView.as_view(), name='session-revoke'),
    path('sessions/revoke-all/', SessionRevokeAllView.as_view(), name='session-revoke-all'),
]


# =============================================================================
# MAIN URL PATTERNS
# =============================================================================

# The main urlpatterns export - includes both auth and resource management
urlpatterns = auth_urlpatterns + router.urls
