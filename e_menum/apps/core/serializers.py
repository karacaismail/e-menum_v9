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
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
        ]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """
    Full user serializer for profile and user management.

    Includes all user fields except sensitive data (password, deleted_at).
    """

    full_name = serializers.CharField(read_only=True)
    organization_name = serializers.CharField(
        source="organization.name", read_only=True, allow_null=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
            "phone",
            "status",
            "is_staff",
            "is_superuser",
            "email_verified_at",
            "last_login_at",
            "organization",
            "organization_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "is_staff",
            "is_superuser",
            "email_verified_at",
            "last_login_at",
            "created_at",
            "updated_at",
        ]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information.

    Only allows updating safe fields (name, avatar, phone).
    """

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "avatar",
            "phone",
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
            "id",
            "name",
            "slug",
            "logo",
        ]
        read_only_fields = fields


class OrganizationListSerializer(serializers.ModelSerializer):
    """
    Organization serializer for list views.

    Includes summary information about the organization.
    """

    user_count = serializers.SerializerMethodField()
    is_on_trial = serializers.BooleanField(read_only=True)

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "email",
            "phone",
            "logo",
            "status",
            "is_on_trial",
            "trial_ends_at",
            "user_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_user_count(self, obj):
        """Get the count of active users in the organization."""
        return obj.users.filter(deleted_at__isnull=True).count()


class OrganizationDetailSerializer(serializers.ModelSerializer):
    """
    Full organization serializer for detail views.

    Includes all organization fields and computed properties.
    """

    user_count = serializers.SerializerMethodField()
    branch_count = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    is_on_trial = serializers.BooleanField(read_only=True)

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "email",
            "phone",
            "logo",
            "settings",
            "status",
            "is_active",
            "is_on_trial",
            "trial_ends_at",
            "user_count",
            "branch_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "is_active",
            "is_on_trial",
            "user_count",
            "branch_count",
            "created_at",
            "updated_at",
        ]

    def get_user_count(self, obj):
        """Get the count of active users in the organization."""
        return obj.users.filter(deleted_at__isnull=True).count()

    def get_branch_count(self, obj):
        """Get the count of active branches in the organization."""
        return obj.branches.filter(deleted_at__isnull=True).count()


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new organization.

    Generates slug automatically from name if not provided.
    """

    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
            "email",
            "phone",
            "logo",
            "settings",
        ]
        extra_kwargs = {
            "slug": {"required": False},
        }

    def validate_slug(self, value):
        """Ensure slug is unique."""
        if value and Organization.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                _("An organization with this slug already exists.")
            )
        return value

    def create(self, validated_data):
        """Create organization with auto-generated slug if not provided."""
        from django.utils.text import slugify

        if "slug" not in validated_data or not validated_data["slug"]:
            base_slug = slugify(validated_data["name"])
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            validated_data["slug"] = slug

        return super().create(validated_data)


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating organization information.

    Restricts which fields can be updated.
    """

    class Meta:
        model = Organization
        fields = [
            "name",
            "email",
            "phone",
            "logo",
            "settings",
        ]


# =============================================================================
# USER MANAGEMENT SERIALIZERS
# =============================================================================


class UserListSerializer(serializers.ModelSerializer):
    """
    User serializer for list views.

    Optimized for listing users with minimal data.
    """

    full_name = serializers.CharField(read_only=True)
    is_active_user = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
            "phone",
            "status",
            "is_active_user",
            "is_staff",
            "email_verified_at",
            "last_login_at",
            "created_at",
        ]
        read_only_fields = fields


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Full user serializer for detail views.

    Includes all user fields and related organization info.
    """

    full_name = serializers.CharField(read_only=True)
    is_active_user = serializers.BooleanField(read_only=True)
    is_email_verified = serializers.BooleanField(read_only=True)
    organization_name = serializers.CharField(
        source="organization.name", read_only=True, allow_null=True
    )
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
            "phone",
            "status",
            "is_active_user",
            "is_staff",
            "is_superuser",
            "is_email_verified",
            "email_verified_at",
            "last_login_at",
            "organization",
            "organization_name",
            "roles",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "is_active_user",
            "is_email_verified",
            "is_staff",
            "is_superuser",
            "email_verified_at",
            "last_login_at",
            "created_at",
            "updated_at",
        ]

    def get_roles(self, obj):
        """Get the user's roles within their organization."""
        from apps.core.models import UserRole

        user_roles = UserRole.objects.filter(
            user=obj, organization=obj.organization
        ).select_related("role")
        return [
            {
                "id": str(ur.role.id),
                "name": ur.role.name,
                "display_name": ur.role.display_name,
            }
            for ur in user_roles
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new user within an organization.

    Requires password and handles initial user setup.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=12,
        style={"input_type": "password"},
        help_text=_("Password (minimum 12 characters)"),
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text=_("Confirm password"),
    )
    role = serializers.UUIDField(
        required=False, write_only=True, help_text=_("Role ID to assign to the user")
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone",
            "password",
            "confirm_password",
            "role",
        ]

    def validate_email(self, value):
        """Ensure email is unique."""
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
        return email

    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError(
                {"confirm_password": _("Passwords do not match.")}
            )
        return attrs

    def create(self, validated_data):
        """Create user with password and optional role assignment."""
        from apps.core.models import Role, UserRole

        validated_data.pop("confirm_password", None)
        role_id = validated_data.pop("role", None)
        password = validated_data.pop("password")
        organization = validated_data.get("organization")

        user = User.objects.create_user(password=password, **validated_data)

        # Assign role if provided
        if role_id and organization:
            try:
                role = Role.objects.get(id=role_id)
                UserRole.objects.create(
                    user=user,
                    role=role,
                    organization=organization,
                    granted_by=self.context["request"].user,
                )
            except Role.DoesNotExist:
                pass  # Silently ignore invalid role

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user information.

    Restricts which fields can be updated by organization managers.
    """

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone",
            "avatar",
            "status",
        ]

    def validate_status(self, value):
        """Prevent self-suspension."""
        request = self.context.get("request")
        if request and self.instance:
            if self.instance.id == request.user.id and value == UserStatus.SUSPENDED:
                raise serializers.ValidationError(
                    _("You cannot suspend your own account.")
                )
        return value


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

    email = serializers.EmailField(required=True, help_text=_("User email address"))
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text=_("User password"),
    )

    def validate(self, attrs):
        """
        Validate credentials and return user with tokens.

        Raises:
            ValidationError: If credentials are invalid or user is inactive
        """
        email = attrs.get("email", "").lower().strip()
        password = attrs.get("password", "")

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": _("No account found with this email address.")},
                code=ErrorCodes.AUTH_INVALID_CREDENTIALS,
            )

        # Check if user is soft-deleted
        if user.is_deleted:
            raise serializers.ValidationError(
                {"email": _("This account has been deleted.")},
                code=ErrorCodes.AUTH_USER_DELETED,
            )

        # Check user status
        if user.status == UserStatus.SUSPENDED:
            raise serializers.ValidationError(
                {
                    "email": _(
                        "This account has been suspended. Please contact support."
                    )
                },
                code=ErrorCodes.AUTH_USER_SUSPENDED,
            )

        if user.status == UserStatus.INVITED:
            raise serializers.ValidationError(
                {"email": _("Please complete your registration first.")},
                code=ErrorCodes.AUTH_USER_INACTIVE,
            )

        # Authenticate with password
        authenticated_user = authenticate(
            request=self.context.get("request"), email=email, password=password
        )

        if not authenticated_user:
            raise serializers.ValidationError(
                {"password": _("Invalid password.")},
                code=ErrorCodes.AUTH_INVALID_CREDENTIALS,
            )

        # Check organization status if user belongs to one
        if authenticated_user.organization:
            org = authenticated_user.organization
            if org.status == OrganizationStatus.SUSPENDED:
                raise serializers.ValidationError(
                    {
                        "email": _(
                            "Your organization has been suspended. Please contact support."
                        )
                    },
                    code=ErrorCodes.ORGANIZATION_SUSPENDED,
                )
            if org.status == OrganizationStatus.DELETED or org.is_deleted:
                raise serializers.ValidationError(
                    {"email": _("Your organization has been deleted.")},
                    code=ErrorCodes.ORGANIZATION_DELETED,
                )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(authenticated_user)

        # Add custom claims
        refresh["email"] = authenticated_user.email
        refresh["first_name"] = authenticated_user.first_name
        refresh["last_name"] = authenticated_user.last_name
        if authenticated_user.organization:
            refresh["organization_id"] = str(authenticated_user.organization.id)
            refresh["organization_slug"] = authenticated_user.organization.slug

        attrs["user"] = authenticated_user
        attrs["tokens"] = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

        return attrs


class LoginResponseSerializer(serializers.Serializer):
    """
    Serializer for login response structure (for documentation).
    """

    access = serializers.CharField(help_text=_("JWT access token"))
    refresh = serializers.CharField(help_text=_("JWT refresh token"))
    user = UserSerializer(help_text=_("Authenticated user details"))
    organization = OrganizationMinimalSerializer(
        help_text=_("User organization (if any)"), allow_null=True
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
        token["email"] = user.email
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["is_staff"] = user.is_staff
        token["is_superuser"] = user.is_superuser

        if user.organization:
            token["organization_id"] = str(user.organization.id)
            token["organization_slug"] = user.organization.slug

        return token

    def validate(self, attrs):
        """Validate and add user info to response."""
        data = super().validate(attrs)

        # Add user info to response
        data["user"] = UserSerializer(self.user).data

        if self.user.organization:
            data["organization"] = OrganizationMinimalSerializer(
                self.user.organization
            ).data
        else:
            data["organization"] = None

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
        required=True, help_text=_("JWT refresh token to invalidate")
    )

    def validate_refresh(self, value):
        """Validate the refresh token format."""
        if not value:
            raise serializers.ValidationError(_("Refresh token is required."))
        return value

    def save(self, **kwargs):
        """Blacklist the refresh token."""
        try:
            token = RefreshToken(self.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            raise serializers.ValidationError(
                {"refresh": _("Invalid or expired refresh token.")},
                code=ErrorCodes.AUTH_REFRESH_TOKEN_INVALID,
            )


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user password.

    Requires current password for verification before setting new password.
    """

    current_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text=_("Current password"),
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=12,
        style={"input_type": "password"},
        help_text=_("New password (minimum 12 characters)"),
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text=_("Confirm new password"),
    )

    def validate_current_password(self, value):
        """Verify current password is correct."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Current password is incorrect."))
        return value

    def validate(self, attrs):
        """Validate password confirmation matches."""
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": _("Passwords do not match.")}
            )

        # Check new password is different from current
        if attrs["new_password"] == attrs["current_password"]:
            raise serializers.ValidationError(
                {
                    "new_password": _(
                        "New password must be different from current password."
                    )
                }
            )

        return attrs

    def save(self, **kwargs):
        """Update user password."""
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])

        # Revoke all existing sessions for security
        Session.objects.filter(user=user, status=SessionStatus.ACTIVE).update(
            status=SessionStatus.REVOKED,
            revoked_at=timezone.now(),
            revoke_reason="Password changed",
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
            "id",
            "user_agent",
            "ip_address",
            "status",
            "created_at",
            "expires_at",
            "is_current",
        ]
        read_only_fields = fields

    def get_is_current(self, obj):
        """Check if this session is the current one."""
        request = self.context.get("request")
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
    # User serializers (minimal/profile)
    "UserMinimalSerializer",
    "UserSerializer",
    "UserProfileUpdateSerializer",
    # User management serializers
    "UserListSerializer",
    "UserDetailSerializer",
    "UserCreateSerializer",
    "UserUpdateSerializer",
    # Organization serializers
    "OrganizationMinimalSerializer",
    "OrganizationListSerializer",
    "OrganizationDetailSerializer",
    "OrganizationCreateSerializer",
    "OrganizationUpdateSerializer",
    # Auth serializers
    "LoginSerializer",
    "LoginResponseSerializer",
    "CustomTokenObtainPairSerializer",
    "CustomTokenRefreshSerializer",
    "LogoutSerializer",
    "PasswordChangeSerializer",
    "SessionSerializer",
    # Response wrappers
    "SuccessResponseSerializer",
    "ErrorResponseSerializer",
]
