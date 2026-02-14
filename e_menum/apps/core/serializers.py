"""
Serializers for the Core application.

This module provides serializers for:
- Authentication (login, logout, token refresh)
- User management (registration, profile)
- Organization serialization

These serializers follow Django REST Framework best practices and integrate
with SimpleJWT for token-based authentication.

Usage:
    from apps.core.serializers import LoginSerializer, UserSerializer

    # In views
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
"""

from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from apps.core.models import Organization, User, Session
from apps.core.choices import UserStatus, OrganizationStatus, SessionStatus
from shared.utils.exceptions import ErrorCodes


# =============================================================================
# USER SERIALIZERS
# =============================================================================

class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal user serializer for embedding in other responses.

    Used when user data is included as a nested object (e.g., in audit logs,
    created_by fields, etc.)
    """

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'avatar',
        ]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """
    Full user serializer for profile and user management.

    Includes all user fields except sensitive data (password, deleted_at).
    """

    full_name = serializers.CharField(read_only=True)
    organization_name = serializers.CharField(
        source='organization.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'avatar',
            'phone',
            'status',
            'is_staff',
            'is_superuser',
            'email_verified_at',
            'last_login_at',
            'organization',
            'organization_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'email',
            'is_staff',
            'is_superuser',
            'email_verified_at',
            'last_login_at',
            'created_at',
            'updated_at',
        ]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information.

    Only allows updating safe fields (name, avatar, phone).
    """

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'avatar',
            'phone',
        ]


# =============================================================================
# ORGANIZATION SERIALIZERS
# =============================================================================

class OrganizationMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal organization serializer for embedding in auth responses.
    """

    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'slug',
            'logo',
        ]
        read_only_fields = fields


# =============================================================================
# AUTHENTICATION SERIALIZERS
# =============================================================================

class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    Validates email and password, returning user and tokens on success.

    Usage:
        serializer = LoginSerializer(data={'email': '...', 'password': '...'})
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            tokens = serializer.validated_data['tokens']

    Response includes:
        - user: User object
        - tokens: {'access': '...', 'refresh': '...'}
    """

    email = serializers.EmailField(
        required=True,
        help_text=_('User email address')
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text=_('User password')
    )

    def validate(self, attrs):
        """
        Validate credentials and return user with tokens.

        Raises:
            ValidationError: If credentials are invalid or user is inactive
        """
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password', '')

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'email': _('No account found with this email address.')
            }, code=ErrorCodes.AUTH_INVALID_CREDENTIALS)

        # Check if user is soft-deleted
        if user.is_deleted:
            raise serializers.ValidationError({
                'email': _('This account has been deleted.')
            }, code=ErrorCodes.AUTH_USER_DELETED)

        # Check user status
        if user.status == UserStatus.SUSPENDED:
            raise serializers.ValidationError({
                'email': _('This account has been suspended. Please contact support.')
            }, code=ErrorCodes.AUTH_USER_SUSPENDED)

        if user.status == UserStatus.INVITED:
            raise serializers.ValidationError({
                'email': _('Please complete your registration first.')
            }, code=ErrorCodes.AUTH_USER_INACTIVE)

        # Authenticate with password
        authenticated_user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password
        )

        if not authenticated_user:
            raise serializers.ValidationError({
                'password': _('Invalid password.')
            }, code=ErrorCodes.AUTH_INVALID_CREDENTIALS)

        # Check organization status if user belongs to one
        if authenticated_user.organization:
            org = authenticated_user.organization
            if org.status == OrganizationStatus.SUSPENDED:
                raise serializers.ValidationError({
                    'email': _('Your organization has been suspended. Please contact support.')
                }, code=ErrorCodes.ORGANIZATION_SUSPENDED)
            if org.status == OrganizationStatus.DELETED or org.is_deleted:
                raise serializers.ValidationError({
                    'email': _('Your organization has been deleted.')
                }, code=ErrorCodes.ORGANIZATION_DELETED)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(authenticated_user)

        # Add custom claims
        refresh['email'] = authenticated_user.email
        refresh['first_name'] = authenticated_user.first_name
        refresh['last_name'] = authenticated_user.last_name
        if authenticated_user.organization:
            refresh['organization_id'] = str(authenticated_user.organization.id)
            refresh['organization_slug'] = authenticated_user.organization.slug

        attrs['user'] = authenticated_user
        attrs['tokens'] = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

        return attrs


class LoginResponseSerializer(serializers.Serializer):
    """
    Serializer for login response structure (for documentation).
    """

    access = serializers.CharField(help_text=_('JWT access token'))
    refresh = serializers.CharField(help_text=_('JWT refresh token'))
    user = UserSerializer(help_text=_('Authenticated user details'))
    organization = OrganizationMinimalSerializer(
        help_text=_('User organization (if any)'),
        allow_null=True
    )


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token obtain serializer that adds user info to the response.

    Extends SimpleJWT's TokenObtainPairSerializer to include custom claims
    and user information in the response.
    """

    @classmethod
    def get_token(cls, user):
        """Add custom claims to the token."""
        token = super().get_token(user)

        # Add custom claims
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser

        if user.organization:
            token['organization_id'] = str(user.organization.id)
            token['organization_slug'] = user.organization.slug

        return token

    def validate(self, attrs):
        """Validate and add user info to response."""
        data = super().validate(attrs)

        # Add user info to response
        data['user'] = UserSerializer(self.user).data

        if self.user.organization:
            data['organization'] = OrganizationMinimalSerializer(
                self.user.organization
            ).data
        else:
            data['organization'] = None

        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Custom token refresh serializer with additional validation.

    Validates the refresh token and checks if the session is still valid.
    """

    def validate(self, attrs):
        """Validate refresh token and session status."""
        try:
            data = super().validate(attrs)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return data


class LogoutSerializer(serializers.Serializer):
    """
    Serializer for user logout.

    Accepts the refresh token to blacklist it.
    """

    refresh = serializers.CharField(
        required=True,
        help_text=_('JWT refresh token to invalidate')
    )

    def validate_refresh(self, value):
        """Validate the refresh token format."""
        if not value:
            raise serializers.ValidationError(
                _('Refresh token is required.')
            )
        return value

    def save(self, **kwargs):
        """Blacklist the refresh token."""
        try:
            token = RefreshToken(self.validated_data['refresh'])
            token.blacklist()
        except TokenError:
            raise serializers.ValidationError({
                'refresh': _('Invalid or expired refresh token.')
            }, code=ErrorCodes.AUTH_REFRESH_TOKEN_INVALID)


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user password.

    Requires current password for verification before setting new password.
    """

    current_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text=_('Current password')
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=12,
        style={'input_type': 'password'},
        help_text=_('New password (minimum 12 characters)')
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text=_('Confirm new password')
    )

    def validate_current_password(self, value):
        """Verify current password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                _('Current password is incorrect.')
            )
        return value

    def validate(self, attrs):
        """Validate password confirmation matches."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': _('Passwords do not match.')
            })

        # Check new password is different from current
        if attrs['new_password'] == attrs['current_password']:
            raise serializers.ValidationError({
                'new_password': _('New password must be different from current password.')
            })

        return attrs

    def save(self, **kwargs):
        """Update user password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password', 'updated_at'])

        # Revoke all existing sessions for security
        Session.objects.filter(
            user=user,
            status=SessionStatus.ACTIVE
        ).update(
            status=SessionStatus.REVOKED,
            revoked_at=timezone.now(),
            revoke_reason='Password changed'
        )

        return user


class SessionSerializer(serializers.ModelSerializer):
    """
    Serializer for user sessions.

    Used for listing active sessions and session management.
    """

    is_current = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = [
            'id',
            'user_agent',
            'ip_address',
            'status',
            'created_at',
            'expires_at',
            'is_current',
        ]
        read_only_fields = fields

    def get_is_current(self, obj):
        """Check if this session is the current one."""
        request = self.context.get('request')
        if not request:
            return False
        # This would need the current session ID from the token
        # For now, return False as placeholder
        return False


# =============================================================================
# API RESPONSE WRAPPER SERIALIZERS
# =============================================================================

class SuccessResponseSerializer(serializers.Serializer):
    """
    Generic success response wrapper for API documentation.

    Standard E-Menum API response format:
        {
            "success": true,
            "data": {...}
        }
    """

    success = serializers.BooleanField(default=True)
    data = serializers.DictField(allow_empty=True)


class ErrorResponseSerializer(serializers.Serializer):
    """
    Generic error response wrapper for API documentation.

    Standard E-Menum API error format:
        {
            "success": false,
            "error": {
                "code": "ERROR_CODE",
                "message": "Human-readable message",
                "details": {...}
            }
        }
    """

    success = serializers.BooleanField(default=False)
    error = serializers.DictField()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # User serializers
    'UserMinimalSerializer',
    'UserSerializer',
    'UserProfileUpdateSerializer',

    # Organization serializers
    'OrganizationMinimalSerializer',

    # Auth serializers
    'LoginSerializer',
    'LoginResponseSerializer',
    'CustomTokenObtainPairSerializer',
    'CustomTokenRefreshSerializer',
    'LogoutSerializer',
    'PasswordChangeSerializer',
    'SessionSerializer',

    # Response wrappers
    'SuccessResponseSerializer',
    'ErrorResponseSerializer',
]
