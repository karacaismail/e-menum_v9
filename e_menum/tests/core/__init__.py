"""
Unit tests for the core application.

This package contains tests for core models including:
- Organization (tenant model)
- User (custom user model)
- Branch (multi-location support)
- Role, Permission (RBAC)
- Session (JWT refresh token management)
- AuditLog (system-wide audit logging)

Run these tests with:
    pytest tests/core/ -v

Test markers:
    @pytest.mark.model - Model-specific tests
    @pytest.mark.unit - Isolated unit tests
"""
