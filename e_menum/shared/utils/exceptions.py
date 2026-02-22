"""
Custom exception handling for E-Menum API.

This module provides a custom exception handler for Django REST Framework
that formats all API responses consistently, including error responses.

Response Format:
    Success:
        {
            "success": true,
            "data": {...}
        }

    Error:
        {
            "success": false,
            "error": {
                "code": "ERROR_CODE",
                "message": "Human-readable message",
                "details": {...}  # Optional, for validation errors
            }
        }

Usage:
    In settings.py:
        REST_FRAMEWORK = {
            'EXCEPTION_HANDLER': 'shared.utils.exceptions.custom_exception_handler',
        }

Error Codes:
    Authentication: AUTH_*, e.g., AUTH_INVALID_CREDENTIALS, AUTH_TOKEN_EXPIRED
    Authorization: FORBIDDEN_*, e.g., FORBIDDEN_NO_PERMISSION
    Validation: VALIDATION_ERROR
    Resources: {RESOURCE}_NOT_FOUND, e.g., MENU_NOT_FOUND, USER_NOT_FOUND
    Business Logic: BUSINESS_*, e.g., BUSINESS_PLAN_LIMIT_EXCEEDED
"""

from typing import Any, Optional

from django.http import Http404
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied as DRFPermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler


# =============================================================================
# ERROR CODES
# =============================================================================

class ErrorCodes:
    """
    Centralized error codes for consistent API error responses.

    Naming Convention: {CATEGORY}_{SPECIFIC_ERROR}
    - AUTH_*: Authentication errors
    - FORBIDDEN_*: Authorization errors
    - VALIDATION_*: Input validation errors
    - {RESOURCE}_*: Resource-specific errors (MENU_NOT_FOUND, USER_SUSPENDED)
    - BUSINESS_*: Business logic errors
    - SERVER_*: Internal server errors
    """

    # Authentication errors
    AUTH_INVALID_CREDENTIALS = 'AUTH_INVALID_CREDENTIALS'
    AUTH_TOKEN_EXPIRED = 'AUTH_TOKEN_EXPIRED'
    AUTH_TOKEN_INVALID = 'AUTH_TOKEN_INVALID'
    AUTH_TOKEN_MISSING = 'AUTH_TOKEN_MISSING'
    AUTH_USER_INACTIVE = 'AUTH_USER_INACTIVE'
    AUTH_USER_SUSPENDED = 'AUTH_USER_SUSPENDED'
    AUTH_USER_DELETED = 'AUTH_USER_DELETED'
    AUTH_EMAIL_NOT_VERIFIED = 'AUTH_EMAIL_NOT_VERIFIED'
    AUTH_REFRESH_TOKEN_EXPIRED = 'AUTH_REFRESH_TOKEN_EXPIRED'
    AUTH_REFRESH_TOKEN_INVALID = 'AUTH_REFRESH_TOKEN_INVALID'
    AUTH_SESSION_REVOKED = 'AUTH_SESSION_REVOKED'

    # Authorization errors
    FORBIDDEN_NO_PERMISSION = 'FORBIDDEN_NO_PERMISSION'
    FORBIDDEN_NOT_OWNER = 'FORBIDDEN_NOT_OWNER'
    FORBIDDEN_TENANT_MISMATCH = 'FORBIDDEN_TENANT_MISMATCH'
    FORBIDDEN_ROLE_REQUIRED = 'FORBIDDEN_ROLE_REQUIRED'

    # Validation errors
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    VALIDATION_REQUIRED_FIELD = 'VALIDATION_REQUIRED_FIELD'
    VALIDATION_INVALID_FORMAT = 'VALIDATION_INVALID_FORMAT'
    VALIDATION_UNIQUE_CONSTRAINT = 'VALIDATION_UNIQUE_CONSTRAINT'

    # Resource errors (Generic)
    RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND'

    # User errors
    USER_NOT_FOUND = 'USER_NOT_FOUND'
    USER_EMAIL_EXISTS = 'USER_EMAIL_EXISTS'
    USER_SUSPENDED = 'USER_SUSPENDED'

    # Organization errors
    ORGANIZATION_NOT_FOUND = 'ORGANIZATION_NOT_FOUND'
    ORGANIZATION_SUSPENDED = 'ORGANIZATION_SUSPENDED'
    ORGANIZATION_DELETED = 'ORGANIZATION_DELETED'

    # Menu errors
    MENU_NOT_FOUND = 'MENU_NOT_FOUND'
    MENU_NOT_PUBLISHED = 'MENU_NOT_PUBLISHED'

    # Category errors
    CATEGORY_NOT_FOUND = 'CATEGORY_NOT_FOUND'

    # Product errors
    PRODUCT_NOT_FOUND = 'PRODUCT_NOT_FOUND'
    PRODUCT_NOT_AVAILABLE = 'PRODUCT_NOT_AVAILABLE'

    # Order errors
    ORDER_NOT_FOUND = 'ORDER_NOT_FOUND'
    ORDER_INVALID_STATUS = 'ORDER_INVALID_STATUS'
    ORDER_ALREADY_COMPLETED = 'ORDER_ALREADY_COMPLETED'

    # Business logic errors
    BUSINESS_PLAN_LIMIT_EXCEEDED = 'BUSINESS_PLAN_LIMIT_EXCEEDED'
    BUSINESS_SUBSCRIPTION_REQUIRED = 'BUSINESS_SUBSCRIPTION_REQUIRED'
    BUSINESS_TRIAL_EXPIRED = 'BUSINESS_TRIAL_EXPIRED'
    BUSINESS_FEATURE_NOT_AVAILABLE = 'BUSINESS_FEATURE_NOT_AVAILABLE'

    # Server errors
    SERVER_ERROR = 'SERVER_ERROR'
    SERVER_DATABASE_ERROR = 'SERVER_DATABASE_ERROR'
    SERVER_TIMEOUT = 'SERVER_TIMEOUT'

    # Rate limiting
    RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED'


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class AppException(APIException):
    """
    Base exception class for E-Menum application errors.

    Usage:
        raise AppException(
            code='MENU_NOT_FOUND',
            message='Menu with given ID not found',
            status_code=404
        )

    Args:
        code: Error code from ErrorCodes class
        message: Human-readable error message
        status_code: HTTP status code (default: 400)
        details: Additional error details (optional)
    """

    def __init__(
        self,
        code: str,
        message: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict = None
    ):
        self.code = code
        self.message = message or str(_('An error occurred'))
        self.status_code = status_code
        self.details = details or {}
        super().__init__(detail=self.message)


class AuthenticationException(AppException):
    """Exception for authentication-related errors."""

    def __init__(
        self,
        code: str = ErrorCodes.AUTH_INVALID_CREDENTIALS,
        message: str = None,
        details: dict = None
    ):
        super().__init__(
            code=code,
            message=message or str(_('Authentication failed')),
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class PermissionException(AppException):
    """Exception for authorization/permission-related errors."""

    def __init__(
        self,
        code: str = ErrorCodes.FORBIDDEN_NO_PERMISSION,
        message: str = None,
        details: dict = None
    ):
        super().__init__(
            code=code,
            message=message or str(_('Permission denied')),
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ResourceNotFoundException(AppException):
    """Exception for resource not found errors."""

    def __init__(
        self,
        code: str = ErrorCodes.RESOURCE_NOT_FOUND,
        message: str = None,
        resource: str = None,
        details: dict = None
    ):
        if not message and resource:
            message = str(_(f'{resource} not found'))
        super().__init__(
            code=code,
            message=message or str(_('Resource not found')),
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class BusinessLogicException(AppException):
    """Exception for business rule violations."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict = None
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


# =============================================================================
# EXCEPTION HANDLER
# =============================================================================

def custom_exception_handler(exc: Exception, context: dict) -> Optional[Response]:
    """
    Custom exception handler for Django REST Framework.

    Formats all error responses in a consistent structure:
        {
            "success": false,
            "error": {
                "code": "ERROR_CODE",
                "message": "Human-readable message",
                "details": {...}
            }
        }

    Args:
        exc: The exception instance
        context: Additional context (view, request, args, kwargs)

    Returns:
        Response: Formatted error response or None for unhandled exceptions
    """

    # Get the standard DRF response first
    response = exception_handler(exc, context)

    # If DRF didn't handle it, we might need to handle it ourselves
    if response is None:
        # Handle Django's Http404
        if isinstance(exc, Http404):
            return _build_error_response(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=str(exc) or str(_('Not found')),
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Handle Django's PermissionDenied
        if isinstance(exc, PermissionDenied):
            return _build_error_response(
                code=ErrorCodes.FORBIDDEN_NO_PERMISSION,
                message=str(exc) or str(_('Permission denied')),
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Handle Django's ValidationError
        if isinstance(exc, DjangoValidationError):
            return _build_error_response(
                code=ErrorCodes.VALIDATION_ERROR,
                message=str(_('Validation error')),
                details={'errors': exc.messages if hasattr(exc, 'messages') else [str(exc)]},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # For unhandled exceptions, return None to let Django handle it
        return None

    # Handle our custom AppException
    if isinstance(exc, AppException):
        return _build_error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            status_code=exc.status_code
        )

    # Handle DRF's ValidationError
    if isinstance(exc, ValidationError):
        return _build_error_response(
            code=ErrorCodes.VALIDATION_ERROR,
            message=str(_('Validation error')),
            details={'fields': response.data},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Handle DRF's AuthenticationFailed
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        code = ErrorCodes.AUTH_TOKEN_INVALID
        if isinstance(exc, NotAuthenticated):
            code = ErrorCodes.AUTH_TOKEN_MISSING
        return _build_error_response(
            code=code,
            message=str(exc.detail) if hasattr(exc, 'detail') else str(_('Authentication failed')),
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Handle DRF's PermissionDenied
    if isinstance(exc, DRFPermissionDenied):
        return _build_error_response(
            code=ErrorCodes.FORBIDDEN_NO_PERMISSION,
            message=str(exc.detail) if hasattr(exc, 'detail') else str(_('Permission denied')),
            status_code=status.HTTP_403_FORBIDDEN
        )

    # Handle DRF's NotFound
    if isinstance(exc, NotFound):
        return _build_error_response(
            code=ErrorCodes.RESOURCE_NOT_FOUND,
            message=str(exc.detail) if hasattr(exc, 'detail') else str(_('Not found')),
            status_code=status.HTTP_404_NOT_FOUND
        )

    # Handle DRF's Throttled
    if isinstance(exc, Throttled):
        return _build_error_response(
            code=ErrorCodes.RATE_LIMIT_EXCEEDED,
            message=str(_('Rate limit exceeded. Try again in {} seconds.')).format(exc.wait),
            details={'retry_after': exc.wait},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    # Handle DRF's ParseError
    if isinstance(exc, ParseError):
        return _build_error_response(
            code=ErrorCodes.VALIDATION_INVALID_FORMAT,
            message=str(exc.detail) if hasattr(exc, 'detail') else str(_('Invalid request format')),
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Default: Format the existing DRF response
    error_data = {
        'success': False,
        'error': {
            'code': ErrorCodes.SERVER_ERROR,
            'message': _get_error_message(response.data),
            'details': response.data if isinstance(response.data, dict) else {}
        }
    }
    response.data = error_data
    return response


def _build_error_response(
    code: str,
    message: str,
    status_code: int,
    details: dict = None
) -> Response:
    """
    Build a standardized error response.

    Args:
        code: Error code
        message: Human-readable message
        status_code: HTTP status code
        details: Additional error details

    Returns:
        Response: Formatted error response
    """
    data = {
        'success': False,
        'error': {
            'code': code,
            'message': str(message),
        }
    }
    if details:
        data['error']['details'] = details

    return Response(data, status=status_code)


def _get_error_message(data: Any) -> str:
    """
    Extract a human-readable message from response data.

    Args:
        data: Response data (dict, list, or string)

    Returns:
        str: Human-readable error message
    """
    if isinstance(data, str):
        return data
    if isinstance(data, list) and len(data) > 0:
        return str(data[0])
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        if 'message' in data:
            return str(data['message'])
        # Get first error from validation errors
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                return f"{key}: {value[0]}"
            return f"{key}: {value}"
    return str(_('An error occurred'))


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ErrorCodes',
    'AppException',
    'AuthenticationException',
    'PermissionException',
    'ResourceNotFoundException',
    'BusinessLogicException',
    'custom_exception_handler',
]
