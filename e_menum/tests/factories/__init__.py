"""
E-Menum Test Factories Package

This package contains factory_boy factories for creating test data.
Factories follow Django ORM patterns and integrate with pytest-django.

Usage:
    from tests.factories.core import OrganizationFactory, UserFactory

    # Or import all core factories
    from tests.factories import (
        OrganizationFactory,
        UserFactory,
        BranchFactory,
        RoleFactory,
        PermissionFactory,
        SessionFactory,
        UserRoleFactory,
        RolePermissionFactory,
        AuditLogFactory,
    )

Factory Naming Convention:
    - {Model}Factory: Base factory for the model
    - {Variant}{Model}Factory: Specialized variant (e.g., AdminUserFactory)

Common Patterns:
    # Create single instance (saved to DB)
    user = UserFactory()

    # Create with custom attributes
    user = UserFactory(email="custom@example.com", first_name="John")

    # Build without saving (memory only)
    user = UserFactory.build()

    # Create batch of instances
    users = UserFactory.create_batch(5)

    # Create with related objects
    user = UserFactory(organization=OrganizationFactory())

    # Build batch without saving
    users = UserFactory.build_batch(3)
"""

# Core module factories
from tests.factories.core import (
    # Organization factories
    OrganizationFactory,
    OrganizationWithPlanFactory,
    # User factories
    UserFactory,
    AdminUserFactory,
    StaffUserFactory,
    InvitedUserFactory,
    # Branch factories
    BranchFactory,
    MainBranchFactory,
    # Role factories
    RoleFactory,
    PlatformRoleFactory,
    SystemRoleFactory,
    # Permission factories
    PermissionFactory,
    SystemPermissionFactory,
    # Session factories
    SessionFactory,
    ExpiredSessionFactory,
    RevokedSessionFactory,
    # UserRole factories
    UserRoleFactory,
    TemporaryUserRoleFactory,
    # RolePermission factories
    RolePermissionFactory,
    # AuditLog factories
    AuditLogFactory,
    SystemAuditLogFactory,
    LoginAuditLogFactory,
    UpdateAuditLogFactory,
)

__all__ = [
    # Organization
    "OrganizationFactory",
    "OrganizationWithPlanFactory",
    # User
    "UserFactory",
    "AdminUserFactory",
    "StaffUserFactory",
    "InvitedUserFactory",
    # Branch
    "BranchFactory",
    "MainBranchFactory",
    # Role
    "RoleFactory",
    "PlatformRoleFactory",
    "SystemRoleFactory",
    # Permission
    "PermissionFactory",
    "SystemPermissionFactory",
    # Session
    "SessionFactory",
    "ExpiredSessionFactory",
    "RevokedSessionFactory",
    # UserRole
    "UserRoleFactory",
    "TemporaryUserRoleFactory",
    # RolePermission
    "RolePermissionFactory",
    # AuditLog
    "AuditLogFactory",
    "SystemAuditLogFactory",
    "LoginAuditLogFactory",
    "UpdateAuditLogFactory",
]
