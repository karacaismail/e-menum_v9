"""
URL configuration for the Core application.

This module defines URL patterns for:
- Authentication endpoints (login, logout, token refresh)
- User profile management
- Session management

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

Usage:
    In config/urls.py:
        path('api/v1/auth/', include('apps.core.urls')),

    Or for specific endpoints:
        path('api/v1/auth/', include(('apps.core.urls', 'core'), namespace='auth')),
"""

from django.urls import path

from apps.core.views import (
    LoginView,
    LogoutView,
    TokenRefreshView,
    TokenVerifyView,
    UserMeView,
    PasswordChangeView,
    SessionListView,
    SessionRevokeView,
    SessionRevokeAllView,
)


app_name = 'core'

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

# The main urlpatterns export - use this when including in config/urls.py
urlpatterns = auth_urlpatterns
