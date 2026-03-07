"""
Custom authentication backend supporting login with email or username.

When the user types their identifier in the login form, this backend:
1. Checks if the value looks like an email (contains @)
2. If yes, looks up by email (case-insensitive)
3. If no, looks up by username (case-insensitive)
4. Verifies the password and user status

Used by both the restaurant portal (session auth) and optionally the
REST API (JWT auth). Replaces Django's default ModelBackend as the
primary auth backend.
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

logger = logging.getLogger(__name__)

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Authenticate with email or username.

    Accepts the ``username`` kwarg (Django's default parameter name from
    AuthenticationForm / authenticate()) and decides whether the value is
    an email address or a username based on the presence of ``@``.

    Usage:
        from django.contrib.auth import authenticate

        # Login with email
        user = authenticate(request, username='owner@cafe.com', password='secret')

        # Login with username
        user = authenticate(request, username='cafe_owner', password='secret')
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user by email or username.

        Args:
            request: The current HttpRequest.
            username: Email address or username string.
            password: Plain-text password.

        Returns:
            User instance if authentication succeeds, None otherwise.
        """
        if username is None or password is None:
            return None

        identifier = username.strip()
        if not identifier:
            return None

        # Determine lookup strategy
        try:
            if "@" in identifier:
                user = User.objects.get(email__iexact=identifier)
            else:
                user = User.objects.get(username__iexact=identifier)
        except User.DoesNotExist:
            # Run the default password hasher once to mitigate timing attacks
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # Shouldn't happen due to unique constraints, but be safe
            logger.warning("Multiple users found for identifier: %s", identifier)
            return None

        # Verify password and check user can authenticate
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
