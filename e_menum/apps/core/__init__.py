"""
E-Menum Core Application.

This app contains the foundational models for the E-Menum platform:
- Organization: Multi-tenant root entity
- User: Custom user model with organization membership
- Role: RBAC role definitions (platform and organization scoped)
- Permission: Granular resource.action permissions
- Session: JWT refresh token management
- Branch: Multi-location support
- AuditLog: System-wide audit logging

Critical Rules:
- Every query MUST include organizationId for tenant isolation
- All entities use soft delete (deleted_at timestamp)
- No physical deletions allowed
"""

default_app_config = 'apps.core.apps.CoreConfig'
