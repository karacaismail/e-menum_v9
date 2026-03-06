"""
Django management command for seeding initial Roles and Permissions.

This command creates the default system roles and permissions for E-Menum.
It's idempotent - running it multiple times will update existing records
rather than creating duplicates.

Role Definitions (from spec Appendix A):
| Role | Scope | Permissions |
|------|-------|-------------|
| super_admin | PLATFORM | Full system access |
| admin | PLATFORM | Customer, billing, support management |
| sales | PLATFORM | CRM, lead management |
| support | PLATFORM | Support tickets only |
| owner | ORGANIZATION | Full organization access, billing |
| manager | ORGANIZATION | Menu, order, staff management |
| staff | ORGANIZATION | Order taking, table management |
| viewer | ORGANIZATION | Read-only dashboard |

Usage:
    python manage.py seed_roles
    python manage.py seed_roles --force  # Force update existing records
    python manage.py seed_roles --dry-run  # Show what would be created
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.choices import PermissionAction, RoleScope
from apps.core.models import Permission, Role, RolePermission


class Command(BaseCommand):
    """Management command to seed initial Roles and Permissions."""

    help = 'Seed initial roles and permissions for E-Menum'

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing records',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        force = options['force']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))

        try:
            with transaction.atomic():
                # Create permissions first
                permissions = self._create_permissions(force, dry_run)
                self.stdout.write(f'Created/updated {len(permissions)} permissions')

                # Create roles
                roles = self._create_roles(force, dry_run)
                self.stdout.write(f'Created/updated {len(roles)} roles')

                # Create role-permission relationships
                role_permissions = self._create_role_permissions(roles, permissions, force, dry_run)
                self.stdout.write(f'Created/updated {len(role_permissions)} role-permission relationships')

                if dry_run:
                    # Rollback in dry run
                    raise DryRunException()

        except DryRunException:
            self.stdout.write(self.style.WARNING('Dry run completed - no changes were made'))
        except Exception as e:
            raise CommandError(f'Failed to seed roles: {str(e)}')

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('Successfully seeded roles and permissions!'))

    def _create_permissions(self, force: bool, dry_run: bool) -> dict:
        """Create or update permission definitions."""
        # Define all resources and their applicable actions
        resources = {
            # Core resources
            'organization': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            'user': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            'branch': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            'role': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Menu resources
            'menu': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
                PermissionAction.PUBLISH,
            ],
            'category': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            'product': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            'theme': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Order resources
            'order': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
                PermissionAction.EXPORT,
            ],
            'table': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            'zone': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            'qr_code': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            'service_request': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.MANAGE,
            ],
            # Customer resources
            'customer': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
                PermissionAction.EXPORT,
            ],
            'feedback': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.MANAGE,
            ],
            # Subscription resources
            'subscription': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.MANAGE,
            ],
            'invoice': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.EXPORT,
            ],
            'plan': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Inventory resources
            'inventory': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Campaign resources
            'campaign': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Dashboard resources
            'dashboard': [
                PermissionAction.VIEW,
                PermissionAction.MANAGE,
            ],
            # Analytics resources
            'analytics': [
                PermissionAction.VIEW,
                PermissionAction.EXPORT,
            ],
            'report': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.EXPORT,
            ],
            # Media resources
            'media': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Notification resources
            'notification': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.MANAGE,
            ],
            # Audit resources
            'audit_log': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.EXPORT,
            ],
            # AI resources
            'ai_generation': [
                PermissionAction.VIEW,
                PermissionAction.CREATE,
                PermissionAction.MANAGE,
            ],
            # Support resources (platform-level)
            'ticket': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.MANAGE,
            ],
            # CRM resources (platform-level)
            'lead': [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Settings
            'settings': [
                PermissionAction.VIEW,
                PermissionAction.UPDATE,
                PermissionAction.MANAGE,
            ],
        }

        # Generate permission descriptions
        action_descriptions = {
            PermissionAction.VIEW: 'View single',
            PermissionAction.LIST: 'List all',
            PermissionAction.CREATE: 'Create new',
            PermissionAction.UPDATE: 'Update existing',
            PermissionAction.DELETE: 'Delete',
            PermissionAction.MANAGE: 'Full management access to',
            PermissionAction.PUBLISH: 'Publish',
            PermissionAction.EXPORT: 'Export',
            PermissionAction.IMPORT: 'Import',
        }

        permissions = {}
        for resource, actions in resources.items():
            for action in actions:
                code = f'{resource}.{action}'
                resource_name = resource.replace('_', ' ').title()
                description = f'{action_descriptions.get(action, action.label)} {resource_name}'

                permission_data = {
                    'resource': resource,
                    'action': action,
                    'description': description,
                    'is_system': True,
                }

                permission, created = Permission.objects.update_or_create(
                    resource=resource,
                    action=action,
                    defaults=permission_data if force else {'is_system': True},
                )

                if created:
                    for key, value in permission_data.items():
                        setattr(permission, key, value)
                    permission.save()
                    self.stdout.write(f'  + Created permission: {code}')
                else:
                    if force:
                        self.stdout.write(f'  ~ Updated permission: {code}')
                    else:
                        self.stdout.write(f'  - Skipped permission: {code} (already exists)')

                permissions[code] = permission

        return permissions

    def _create_roles(self, force: bool, dry_run: bool) -> dict:
        """Create or update system roles."""
        roles_data = [
            # Platform roles
            {
                'name': 'super_admin',
                'display_name': 'Super Administrator',
                'description': 'Full system access with all permissions. Can manage platform settings, all organizations, and system configuration.',
                'scope': RoleScope.PLATFORM,
                'is_system': True,
                'organization': None,
            },
            {
                'name': 'admin',
                'display_name': 'Platform Administrator',
                'description': 'Customer, billing, and support management. Can manage organizations and handle billing operations.',
                'scope': RoleScope.PLATFORM,
                'is_system': True,
                'organization': None,
            },
            {
                'name': 'sales',
                'display_name': 'Sales Representative',
                'description': 'CRM and lead management. Can manage leads, potential customers, and sales pipelines.',
                'scope': RoleScope.PLATFORM,
                'is_system': True,
                'organization': None,
            },
            {
                'name': 'support',
                'display_name': 'Support Agent',
                'description': 'Support tickets only. Can view and manage customer support tickets.',
                'scope': RoleScope.PLATFORM,
                'is_system': True,
                'organization': None,
            },
            # Organization roles
            {
                'name': 'owner',
                'display_name': 'Organization Owner',
                'description': 'Full organization access with billing. Complete control over the organization including subscription management.',
                'scope': RoleScope.ORGANIZATION,
                'is_system': True,
                'organization': None,
            },
            {
                'name': 'manager',
                'display_name': 'Manager',
                'description': 'Menu, order, and staff management. Can manage menus, handle orders, and manage team members.',
                'scope': RoleScope.ORGANIZATION,
                'is_system': True,
                'organization': None,
            },
            {
                'name': 'staff',
                'display_name': 'Staff',
                'description': 'Order taking and table management. Can take orders, manage tables, and handle service requests.',
                'scope': RoleScope.ORGANIZATION,
                'is_system': True,
                'organization': None,
            },
            {
                'name': 'viewer',
                'display_name': 'Viewer',
                'description': 'Read-only dashboard access. Can view menus, orders, and analytics but cannot make changes.',
                'scope': RoleScope.ORGANIZATION,
                'is_system': True,
                'organization': None,
            },
        ]

        roles = {}
        for data in roles_data:
            name = data['name']
            scope = data['scope']

            role, created = Role.objects.update_or_create(
                name=name,
                scope=scope,
                organization=None,  # System roles have no organization
                defaults=data if force else {'is_system': True},
            )

            if created:
                for key, value in data.items():
                    setattr(role, key, value)
                role.save()
                self.stdout.write(f'  + Created role: {data["display_name"]} ({name})')
            else:
                if force:
                    self.stdout.write(f'  ~ Updated role: {data["display_name"]} ({name})')
                else:
                    self.stdout.write(f'  - Skipped role: {data["display_name"]} ({name}) (already exists)')

            roles[name] = role

        return roles

    def _create_role_permissions(
        self,
        roles: dict,
        permissions: dict,
        force: bool,
        dry_run: bool
    ) -> list:
        """Create or update role-permission relationships."""
        # Define which permissions each role has
        # Permissions are specified as resource.action patterns
        # Use '*' as action to grant all actions for a resource
        # Use 'manage' to grant manage action (full access)

        role_permission_config = {
            # Platform roles
            'super_admin': {
                # Full access to everything
                'organization': ['manage'],
                'user': ['manage'],
                'branch': ['manage'],
                'role': ['manage'],
                'menu': ['manage'],
                'category': ['manage'],
                'product': ['manage'],
                'theme': ['manage'],
                'order': ['manage'],
                'table': ['manage'],
                'zone': ['manage'],
                'qr_code': ['manage'],
                'service_request': ['manage'],
                'customer': ['manage'],
                'feedback': ['manage'],
                'subscription': ['manage'],
                'invoice': ['view', 'list', 'create', 'update', 'export'],
                'plan': ['manage'],
                'inventory': ['manage'],
                'campaign': ['manage'],
                'dashboard': ['manage'],
                'analytics': ['view', 'export'],
                'report': ['view', 'list', 'create', 'export'],
                'media': ['manage'],
                'notification': ['manage'],
                'audit_log': ['view', 'list', 'export'],
                'ai_generation': ['manage'],
                'ticket': ['manage'],
                'lead': ['manage'],
                'settings': ['manage'],
            },
            'admin': {
                # Customer, billing, support management
                'organization': ['view', 'list', 'update'],
                'user': ['view', 'list', 'create', 'update'],
                'subscription': ['manage'],
                'invoice': ['view', 'list', 'create', 'update', 'export'],
                'plan': ['view', 'list'],
                'inventory': ['view', 'list'],
                'campaign': ['view', 'list'],
                'dashboard': ['view'],
                'ticket': ['manage'],
                'customer': ['view', 'list', 'update', 'export'],
                'feedback': ['view', 'list', 'manage'],
                'audit_log': ['view', 'list'],
                'analytics': ['view'],
                'report': ['view', 'list'],
            },
            'sales': {
                # CRM, lead management
                'lead': ['manage'],
                'organization': ['view', 'list'],
                'user': ['view', 'list'],
                'subscription': ['view', 'list'],
                'plan': ['view', 'list'],
                'customer': ['view', 'list'],
                'analytics': ['view'],
                'report': ['view', 'list'],
            },
            'support': {
                # Support tickets only
                'ticket': ['manage'],
                'organization': ['view'],
                'user': ['view'],
                'subscription': ['view'],
                'customer': ['view', 'list'],
                'feedback': ['view', 'list'],
            },
            # Organization roles
            'owner': {
                # Full organization access, billing
                'organization': ['view', 'update'],
                'user': ['manage'],
                'branch': ['manage'],
                'role': ['view', 'list'],  # Can't create platform roles
                'menu': ['manage'],
                'category': ['manage'],
                'product': ['manage'],
                'theme': ['manage'],
                'order': ['manage'],
                'table': ['manage'],
                'zone': ['manage'],
                'qr_code': ['manage'],
                'service_request': ['manage'],
                'customer': ['manage'],
                'feedback': ['manage'],
                'subscription': ['view', 'update'],
                'invoice': ['view', 'list', 'export'],
                'inventory': ['manage'],
                'campaign': ['manage'],
                'dashboard': ['view', 'manage'],
                'analytics': ['view', 'export'],
                'report': ['view', 'list', 'create', 'export'],
                'media': ['manage'],
                'notification': ['manage'],
                'audit_log': ['view', 'list'],
                'ai_generation': ['manage'],
                'settings': ['manage'],
            },
            'manager': {
                # Menu, order, staff management
                'organization': ['view'],
                'user': ['view', 'list', 'create', 'update'],  # Can manage staff
                'branch': ['view', 'list'],
                'menu': ['manage'],
                'category': ['manage'],
                'product': ['manage'],
                'theme': ['view', 'list', 'update'],
                'order': ['manage'],
                'table': ['manage'],
                'zone': ['manage'],
                'qr_code': ['manage'],
                'service_request': ['manage'],
                'customer': ['view', 'list', 'update'],
                'feedback': ['view', 'list', 'manage'],
                'inventory': ['view', 'list', 'create', 'update'],
                'campaign': ['view', 'list', 'create', 'update'],
                'dashboard': ['view'],
                'analytics': ['view'],
                'report': ['view', 'list', 'create'],
                'media': ['manage'],
                'notification': ['view', 'list', 'create'],
                'ai_generation': ['view', 'create'],
                'settings': ['view', 'update'],
            },
            'staff': {
                # Order taking, table management
                'organization': ['view'],
                'menu': ['view', 'list'],
                'category': ['view', 'list'],
                'product': ['view', 'list', 'update'],  # Can update availability
                'order': ['view', 'list', 'create', 'update'],
                'table': ['view', 'list', 'update'],
                'zone': ['view', 'list'],
                'qr_code': ['view', 'list'],
                'service_request': ['view', 'list', 'create', 'update'],
                'customer': ['view', 'list', 'create'],
                'notification': ['view', 'list'],
            },
            'viewer': {
                # Read-only dashboard
                'organization': ['view'],
                'user': ['view', 'list'],
                'branch': ['view', 'list'],
                'menu': ['view', 'list'],
                'category': ['view', 'list'],
                'product': ['view', 'list'],
                'theme': ['view', 'list'],
                'order': ['view', 'list'],
                'table': ['view', 'list'],
                'zone': ['view', 'list'],
                'qr_code': ['view', 'list'],
                'customer': ['view', 'list'],
                'feedback': ['view', 'list'],
                'analytics': ['view'],
                'report': ['view', 'list'],
                'notification': ['view', 'list'],
            },
        }

        created_role_permissions = []

        for role_name, resource_actions in role_permission_config.items():
            role = roles.get(role_name)
            if not role:
                self.stdout.write(
                    self.style.WARNING(f'  ! Role "{role_name}" not found, skipping')
                )
                continue

            for resource, actions in resource_actions.items():
                for action in actions:
                    perm_code = f'{resource}.{action}'
                    permission = permissions.get(perm_code)
                    if not permission:
                        self.stdout.write(
                            self.style.WARNING(f'  ! Permission "{perm_code}" not found, skipping')
                        )
                        continue

                    # Define conditions for organization-scoped roles
                    conditions = {}
                    if role.scope == RoleScope.ORGANIZATION:
                        # Organization roles have tenant-scoped conditions
                        conditions = {
                            'organization_id': '${user.organization_id}'
                        }

                    role_permission, created = RolePermission.objects.update_or_create(
                        role=role,
                        permission=permission,
                        defaults={
                            'conditions': conditions,
                        } if force else {},
                    )

                    if created:
                        if conditions:
                            role_permission.conditions = conditions
                            role_permission.save()
                        created_role_permissions.append(role_permission)

        return created_role_permissions


class DryRunException(Exception):
    """Exception raised to rollback dry run transactions."""
    pass
