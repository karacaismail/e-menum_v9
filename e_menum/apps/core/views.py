"""
Views for the Core application.

This module provides views for:
- Authentication (login, logout, token refresh)
- User profile management
- Session management

All views follow Django REST Framework best practices and integrate
with SimpleJWT for token-based authentication.

API Endpoints:
    POST /api/v1/auth/login/     - User login, returns JWT tokens
    POST /api/v1/auth/logout/    - Logout, blacklists refresh token
    POST /api/v1/auth/refresh/   - Refresh access token
    GET  /api/v1/auth/me/        - Get current user profile
    PUT  /api/v1/auth/me/        - Update current user profile
    POST /api/v1/auth/password/  - Change password

Usage:
    from apps.core.views import LoginView, LogoutView

    urlpatterns = [
        path('login/', LoginView.as_view(), name='login'),
        path('logout/', LogoutView.as_view(), name='logout'),
    ]
"""

import hashlib
from datetime import timedelta

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from django.db import models

from apps.core.models import User, Session, AuditLog, Organization
from apps.core.choices import AuditAction, SessionStatus
from apps.core.serializers import (
    LoginSerializer,
    LoginResponseSerializer,
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
    LogoutSerializer,
    UserSerializer,
    UserProfileUpdateSerializer,
    PasswordChangeSerializer,
    SessionSerializer,
    OrganizationMinimalSerializer,
    # Organization management serializers
    OrganizationListSerializer,
    OrganizationDetailSerializer,
    OrganizationCreateSerializer,
    OrganizationUpdateSerializer,
    # User management serializers
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)
from shared.utils.exceptions import (
    ErrorCodes,
    AuthenticationException,
)
from shared.views import BaseTenantViewSet, BaseModelViewSet


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_client_ip(request):
    """
    Extract client IP address from request.

    Handles proxy headers (X-Forwarded-For) for accurate IP detection.

    Args:
        request: Django request object

    Returns:
        str: Client IP address or None
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain (client IP)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def hash_token(token):
    """
    Hash a token for secure storage.

    Args:
        token: Token string to hash

    Returns:
        str: SHA256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def build_success_response(data, status_code=status.HTTP_200_OK):
    """
    Build a standardized success response.

    Args:
        data: Response data
        status_code: HTTP status code

    Returns:
        Response: Formatted success response
    """
    return Response({
        'success': True,
        'data': data
    }, status=status_code)


def build_error_response(code, message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Build a standardized error response.

    Args:
        code: Error code
        message: Human-readable message
        details: Additional error details
        status_code: HTTP status code

    Returns:
        Response: Formatted error response
    """
    error_data = {
        'success': False,
        'error': {
            'code': code,
            'message': str(message),
        }
    }
    if details:
        error_data['error']['details'] = details
    return Response(error_data, status=status_code)


# =============================================================================
# AUTHENTICATION VIEWS
# =============================================================================

class LoginView(APIView):
    """
    User login endpoint.

    Authenticates user with email and password, returns JWT tokens.

    POST /api/v1/auth/login/
        Request:
            {
                "email": "user@example.com",
                "password": "securepassword"
            }

        Response (200):
            {
                "success": true,
                "data": {
                    "access": "eyJ...",
                    "refresh": "eyJ...",
                    "user": {...},
                    "organization": {...}
                }
            }

        Error (401):
            {
                "success": false,
                "error": {
                    "code": "AUTH_INVALID_CREDENTIALS",
                    "message": "Invalid credentials"
                }
            }
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        """Handle login request."""
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            # Get first error message
            first_error = None
            for field, errors in serializer.errors.items():
                if errors:
                    first_error = errors[0] if isinstance(errors, list) else errors
                    break

            return build_error_response(
                code=ErrorCodes.AUTH_INVALID_CREDENTIALS,
                message=str(first_error) if first_error else _('Invalid credentials'),
                details=serializer.errors,
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        user = serializer.validated_data['user']
        tokens = serializer.validated_data['tokens']

        # Record login timestamp
        user.record_login()

        # Create session record
        Session.objects.create(
            user=user,
            refresh_token=hash_token(tokens['refresh']),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            ip_address=get_client_ip(request),
            expires_at=timezone.now() + timedelta(days=7),  # Match refresh token lifetime
            status=SessionStatus.ACTIVE
        )

        # Log audit event
        AuditLog.log_action(
            action=AuditAction.LOGIN,
            resource='user',
            resource_id=str(user.id),
            user=user,
            organization=user.organization,
            description=f'User {user.email} logged in',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )

        # Build response
        response_data = {
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': UserSerializer(user).data,
        }

        if user.organization:
            response_data['organization'] = OrganizationMinimalSerializer(
                user.organization
            ).data
        else:
            response_data['organization'] = None

        return build_success_response(response_data)


class LogoutView(APIView):
    """
    User logout endpoint.

    Blacklists the refresh token to prevent further use.

    POST /api/v1/auth/logout/
        Request:
            {
                "refresh": "eyJ..."
            }

        Response (200):
            {
                "success": true,
                "data": {
                    "message": "Successfully logged out"
                }
            }
    """

    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        """Handle logout request."""
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return build_error_response(
                code=ErrorCodes.VALIDATION_ERROR,
                message=_('Invalid request'),
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            serializer.save()
        except Exception as e:
            # Log error but don't fail - user is already authenticated
            pass

        # Revoke session in database
        refresh_token = request.data.get('refresh', '')
        if refresh_token:
            hashed_token = hash_token(refresh_token)
            Session.objects.filter(
                user=request.user,
                refresh_token=hashed_token,
                status=SessionStatus.ACTIVE
            ).update(
                status=SessionStatus.REVOKED,
                revoked_at=timezone.now(),
                revoke_reason='User logged out'
            )

        # Log audit event
        AuditLog.log_action(
            action=AuditAction.LOGOUT,
            resource='user',
            resource_id=str(request.user.id),
            user=request.user,
            organization=request.user.organization,
            description=f'User {request.user.email} logged out',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )

        return build_success_response({
            'message': str(_('Successfully logged out'))
        })


class TokenRefreshView(APIView):
    """
    Token refresh endpoint.

    Exchanges a valid refresh token for a new access token.

    POST /api/v1/auth/refresh/
        Request:
            {
                "refresh": "eyJ..."
            }

        Response (200):
            {
                "success": true,
                "data": {
                    "access": "eyJ...",
                    "refresh": "eyJ..."
                }
            }
    """

    permission_classes = [AllowAny]
    serializer_class = CustomTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        """Handle token refresh request."""
        serializer = self.serializer_class(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except InvalidToken as e:
            return build_error_response(
                code=ErrorCodes.AUTH_REFRESH_TOKEN_INVALID,
                message=str(_('Invalid or expired refresh token')),
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        except TokenError as e:
            return build_error_response(
                code=ErrorCodes.AUTH_REFRESH_TOKEN_EXPIRED,
                message=str(_('Refresh token has expired')),
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        return build_success_response({
            'access': serializer.validated_data['access'],
            'refresh': serializer.validated_data.get('refresh', request.data.get('refresh')),
        })


class TokenVerifyView(APIView):
    """
    Token verification endpoint.

    Verifies if an access token is valid.

    POST /api/v1/auth/verify/
        Request:
            {
                "token": "eyJ..."
            }

        Response (200):
            {
                "success": true,
                "data": {
                    "valid": true
                }
            }
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Handle token verification request."""
        token = request.data.get('token')

        if not token:
            return build_error_response(
                code=ErrorCodes.VALIDATION_ERROR,
                message=str(_('Token is required')),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            from rest_framework_simplejwt.tokens import AccessToken
            AccessToken(token)
            return build_success_response({'valid': True})
        except TokenError:
            return build_success_response({'valid': False})


# =============================================================================
# USER PROFILE VIEWS
# =============================================================================

class UserMeView(APIView):
    """
    Current user profile endpoint.

    GET: Retrieve current user's profile
    PUT/PATCH: Update current user's profile

    GET /api/v1/auth/me/
        Response (200):
            {
                "success": true,
                "data": {
                    "id": "uuid",
                    "email": "user@example.com",
                    ...
                }
            }

    PUT /api/v1/auth/me/
        Request:
            {
                "first_name": "John",
                "last_name": "Doe",
                ...
            }

        Response (200):
            {
                "success": true,
                "data": {...}
            }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Get current user profile."""
        serializer = UserSerializer(request.user)
        return build_success_response(serializer.data)

    def put(self, request, *args, **kwargs):
        """Update current user profile (full update)."""
        return self._update_profile(request, partial=False)

    def patch(self, request, *args, **kwargs):
        """Update current user profile (partial update)."""
        return self._update_profile(request, partial=True)

    def _update_profile(self, request, partial=False):
        """
        Handle profile update logic.

        Args:
            request: Django request object
            partial: Whether this is a partial update

        Returns:
            Response: Updated user data or errors
        """
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=partial
        )

        if not serializer.is_valid():
            return build_error_response(
                code=ErrorCodes.VALIDATION_ERROR,
                message=_('Invalid data'),
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        # Log audit event
        AuditLog.log_action(
            action=AuditAction.UPDATE,
            resource='user',
            resource_id=str(request.user.id),
            user=request.user,
            organization=request.user.organization,
            description=f'User {request.user.email} updated profile',
            new_values=serializer.validated_data,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )

        # Return full user data
        return build_success_response(
            UserSerializer(request.user).data
        )


class PasswordChangeView(APIView):
    """
    Password change endpoint.

    Changes the current user's password after verifying the current password.
    All existing sessions are revoked for security.

    POST /api/v1/auth/password/
        Request:
            {
                "current_password": "oldpass",
                "new_password": "newpass123456",
                "confirm_password": "newpass123456"
            }

        Response (200):
            {
                "success": true,
                "data": {
                    "message": "Password changed successfully"
                }
            }
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request, *args, **kwargs):
        """Handle password change request."""
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return build_error_response(
                code=ErrorCodes.VALIDATION_ERROR,
                message=_('Invalid data'),
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        # Log audit event
        AuditLog.log_action(
            action=AuditAction.PASSWORD_CHANGE,
            resource='user',
            resource_id=str(request.user.id),
            user=request.user,
            organization=request.user.organization,
            description=f'User {request.user.email} changed password',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )

        return build_success_response({
            'message': str(_('Password changed successfully. Please log in again.'))
        })


# =============================================================================
# SESSION MANAGEMENT VIEWS
# =============================================================================

class SessionListView(APIView):
    """
    List active sessions for current user.

    GET /api/v1/auth/sessions/
        Response (200):
            {
                "success": true,
                "data": [
                    {
                        "id": "uuid",
                        "user_agent": "...",
                        "ip_address": "...",
                        "created_at": "...",
                        "is_current": true
                    },
                    ...
                ]
            }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """List all active sessions for current user."""
        sessions = Session.objects.filter(
            user=request.user,
            status=SessionStatus.ACTIVE,
            expires_at__gt=timezone.now()
        ).order_by('-created_at')

        serializer = SessionSerializer(
            sessions,
            many=True,
            context={'request': request}
        )

        return build_success_response(serializer.data)


class SessionRevokeView(APIView):
    """
    Revoke a specific session.

    DELETE /api/v1/auth/sessions/{session_id}/
        Response (200):
            {
                "success": true,
                "data": {
                    "message": "Session revoked successfully"
                }
            }
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, session_id, *args, **kwargs):
        """Revoke a specific session."""
        try:
            session = Session.objects.get(
                id=session_id,
                user=request.user,
                status=SessionStatus.ACTIVE
            )
        except Session.DoesNotExist:
            return build_error_response(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=_('Session not found'),
                status_code=status.HTTP_404_NOT_FOUND
            )

        session.revoke(reason='User revoked session')

        # Log audit event
        AuditLog.log_action(
            action=AuditAction.LOGOUT,
            resource='session',
            resource_id=str(session.id),
            user=request.user,
            organization=request.user.organization,
            description=f'User {request.user.email} revoked session',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )

        return build_success_response({
            'message': str(_('Session revoked successfully'))
        })


class SessionRevokeAllView(APIView):
    """
    Revoke all sessions except current one.

    POST /api/v1/auth/sessions/revoke-all/
        Response (200):
            {
                "success": true,
                "data": {
                    "message": "All other sessions revoked",
                    "count": 5
                }
            }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Revoke all sessions except current."""
        # Get current session's token from the request
        current_token = None
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            # We can't easily identify the "current" session from access token
            # So we'll just revoke all sessions - user will need to re-login
            pass

        # Revoke all active sessions
        count = Session.objects.filter(
            user=request.user,
            status=SessionStatus.ACTIVE
        ).update(
            status=SessionStatus.REVOKED,
            revoked_at=timezone.now(),
            revoke_reason='User revoked all sessions'
        )

        # Log audit event
        AuditLog.log_action(
            action=AuditAction.LOGOUT,
            resource='session',
            resource_id='all',
            user=request.user,
            organization=request.user.organization,
            description=f'User {request.user.email} revoked all sessions ({count})',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            metadata={'revoked_count': count}
        )

        return build_success_response({
            'message': str(_('All sessions revoked')),
            'count': count
        })


# =============================================================================
# ORGANIZATION VIEWSET
# =============================================================================

class OrganizationViewSet(BaseModelViewSet):
    """
    ViewSet for organization management.

    This is a platform-level viewset that allows platform admins to manage
    all organizations. For organization members managing their own org,
    use the /api/v1/auth/me/organization/ endpoints.

    API Endpoints:
        GET    /api/v1/organizations/         - List all organizations
        POST   /api/v1/organizations/         - Create a new organization
        GET    /api/v1/organizations/{id}/    - Get organization details
        PUT    /api/v1/organizations/{id}/    - Update organization
        DELETE /api/v1/organizations/{id}/    - Soft delete organization

    Permissions:
        - Requires authentication
        - Requires platform admin role for full access
        - Organization owners can view their own organization
    """

    queryset = Organization.objects.all()
    permission_resource = 'organization'

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == 'list':
            return OrganizationListSerializer
        elif self.action == 'create':
            return OrganizationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrganizationUpdateSerializer
        return OrganizationDetailSerializer

    def get_queryset(self):
        """
        Filter queryset based on user permissions.

        Platform admins can see all organizations.
        Regular users can only see their own organization.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        # Platform admins (superusers or staff) can see all
        if user.is_superuser or user.is_staff:
            return queryset

        # Regular users can only see their own organization
        if user.organization:
            return queryset.filter(id=user.organization.id)

        return queryset.none()

    def perform_create(self, serializer):
        """Create organization."""
        organization = serializer.save()

        # Log audit event
        AuditLog.log_action(
            action=AuditAction.CREATE,
            resource='organization',
            resource_id=str(organization.id),
            user=self.request.user,
            organization=organization,
            description=f'Created organization: {organization.name}',
            new_values=serializer.validated_data,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500]
        )

    def perform_update(self, serializer):
        """Update organization with audit logging."""
        old_values = {
            'name': serializer.instance.name,
            'email': serializer.instance.email,
            'phone': serializer.instance.phone,
        }

        organization = serializer.save()

        # Log audit event
        AuditLog.log_action(
            action=AuditAction.UPDATE,
            resource='organization',
            resource_id=str(organization.id),
            user=self.request.user,
            organization=organization,
            description=f'Updated organization: {organization.name}',
            old_values=old_values,
            new_values=serializer.validated_data,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500]
        )

    def perform_destroy(self, instance):
        """Soft delete organization with audit logging."""
        # Log audit event before deletion
        AuditLog.log_action(
            action=AuditAction.DELETE,
            resource='organization',
            resource_id=str(instance.id),
            user=self.request.user,
            organization=instance,
            description=f'Deleted organization: {instance.name}',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500]
        )

        # Soft delete (inherited from BaseModelViewSet)
        super().perform_destroy(instance)


# =============================================================================
# USER VIEWSET
# =============================================================================

class UserViewSet(BaseTenantViewSet):
    """
    ViewSet for user management within an organization.

    Allows organization owners/managers to manage users in their organization.

    API Endpoints:
        GET    /api/v1/users/         - List organization users
        POST   /api/v1/users/         - Create a new user
        GET    /api/v1/users/{id}/    - Get user details
        PUT    /api/v1/users/{id}/    - Update user
        DELETE /api/v1/users/{id}/    - Soft delete user

    Permissions:
        - Requires authentication
        - Requires organization membership
        - Requires user.view, user.create, user.update, user.delete permissions

    Multi-Tenancy:
        All queries are automatically filtered by the current organization.
    """

    queryset = User.objects.all()
    permission_resource = 'user'

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserDetailSerializer

    def get_queryset(self):
        """
        Return users filtered by organization.

        Uses TenantFilterMixin for automatic organization filtering.
        """
        queryset = super().get_queryset()

        # Apply status filter if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Apply search filter if provided
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(email__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search)
            )

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        """Create user within organization."""
        organization = self.require_organization()
        user = serializer.save(organization=organization)

        # Log audit event
        AuditLog.log_action(
            action=AuditAction.CREATE,
            resource='user',
            resource_id=str(user.id),
            user=self.request.user,
            organization=organization,
            description=f'Created user: {user.email}',
            new_values={
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500]
        )

    def perform_update(self, serializer):
        """Update user with audit logging."""
        instance = serializer.instance
        old_values = {
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'phone': instance.phone,
            'status': instance.status,
        }

        user = serializer.save()

        # Log audit event
        AuditLog.log_action(
            action=AuditAction.UPDATE,
            resource='user',
            resource_id=str(user.id),
            user=self.request.user,
            organization=user.organization,
            description=f'Updated user: {user.email}',
            old_values=old_values,
            new_values=serializer.validated_data,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500]
        )

    def perform_destroy(self, instance):
        """Soft delete user with audit logging."""
        # Prevent self-deletion
        if instance.id == self.request.user.id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'detail': _('You cannot delete your own account.')
            })

        # Log audit event before deletion
        AuditLog.log_action(
            action=AuditAction.DELETE,
            resource='user',
            resource_id=str(instance.id),
            user=self.request.user,
            organization=instance.organization,
            description=f'Deleted user: {instance.email}',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500]
        )

        # Soft delete (inherited from BaseTenantViewSet)
        super().perform_destroy(instance)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Auth views
    'LoginView',
    'LogoutView',
    'TokenRefreshView',
    'TokenVerifyView',

    # Profile views
    'UserMeView',
    'PasswordChangeView',

    # Session views
    'SessionListView',
    'SessionRevokeView',
    'SessionRevokeAllView',

    # ViewSets
    'OrganizationViewSet',
    'UserViewSet',

    # Utilities
    'get_client_ip',
    'build_success_response',
    'build_error_response',
]
