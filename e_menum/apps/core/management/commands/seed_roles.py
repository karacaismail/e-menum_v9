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

    help = "Seed initial roles and permissions for E-Menum"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update existing records",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without making changes",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        force = options["force"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))

        try:
            with transaction.atomic():
                # Create permissions first
                permissions = self._create_permissions(force, dry_run)
                self.stdout.write(f"Created/updated {len(permissions)} permissions")

                # Create roles
                roles = self._create_roles(force, dry_run)
                self.stdout.write(f"Created/updated {len(roles)} roles")

                # Create role-permission relationships
                role_permissions = self._create_role_permissions(
                    roles, permissions, force, dry_run
                )
                self.stdout.write(
                    f"Created/updated {len(role_permissions)} role-permission relationships"
                )

                if dry_run:
                    # Rollback in dry run
                    raise DryRunException()

        except DryRunException:
            self.stdout.write(
                self.style.WARNING("Dry run completed - no changes were made")
            )
        except Exception as e:
            raise CommandError(f"Failed to seed roles: {str(e)}")

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS("Successfully seeded roles and permissions!")
            )

    def _create_permissions(self, force: bool, dry_run: bool) -> dict:
        """Create or update permission definitions."""
        # Define all resources and their applicable actions
        resources = {
            # Core resources
            "organization": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            "user": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            "branch": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            "role": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Menu resources
            "menu": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
                PermissionAction.PUBLISH,
            ],
            "category": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            "product": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            "theme": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Order resources
            "order": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
                PermissionAction.EXPORT,
            ],
            "table": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            "zone": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            "qr_code": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            "service_request": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.MANAGE,
            ],
            # Customer resources
            "customer": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
                PermissionAction.EXPORT,
            ],
            "feedback": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.MANAGE,
            ],
            # Subscription resources
            "subscription": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.MANAGE,
            ],
            "invoice": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.EXPORT,
            ],
            "plan": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Inventory resources
            "inventory": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Campaign resources
            "campaign": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Dashboard resources
            "dashboard": [
                PermissionAction.VIEW,
                PermissionAction.MANAGE,
            ],
            # Analytics resources
            "analytics": [
                PermissionAction.VIEW,
                PermissionAction.EXPORT,
            ],
            "report": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.EXPORT,
            ],
            # Media resources
            "media": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Notification resources
            "notification": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.MANAGE,
            ],
            # Audit resources
            "audit_log": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.EXPORT,
            ],
            # AI resources
            "ai_generation": [
                PermissionAction.VIEW,
                PermissionAction.CREATE,
                PermissionAction.MANAGE,
            ],
            # Support resources (platform-level)
            "ticket": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.MANAGE,
            ],
            # CRM resources (platform-level)
            "lead": [
                PermissionAction.VIEW,
                PermissionAction.LIST,
                PermissionAction.CREATE,
                PermissionAction.UPDATE,
                PermissionAction.DELETE,
                PermissionAction.MANAGE,
            ],
            # Settings
            "settings": [
                PermissionAction.VIEW,
                PermissionAction.UPDATE,
                PermissionAction.MANAGE,
            ],
        }

        # Generate permission descriptions
        action_descriptions = {
            PermissionAction.VIEW: "View single",
            PermissionAction.LIST: "List all",
            PermissionAction.CREATE: "Create new",
            PermissionAction.UPDATE: "Update existing",
            PermissionAction.DELETE: "Delete",
            PermissionAction.MANAGE: "Full management access to",
            PermissionAction.PUBLISH: "Publish",
            PermissionAction.EXPORT: "Export",
            PermissionAction.IMPORT: "Import",
        }

        permissions = {}
        for resource, actions in resources.items():
            for action in actions:
                code = f"{resource}.{action}"
                resource_name = resource.replace("_", " ").title()
                description = (
                    f"{action_descriptions.get(action, action.label)} {resource_name}"
                )

                permission_data = {
                    "resource": resource,
                    "action": action,
                    "description": description,
                    "is_system": True,
                }

                permission, created = Permission.objects.update_or_create(
                    resource=resource,
                    action=action,
                    defaults=permission_data if force else {"is_system": True},
                )

                if created:
                    for key, value in permission_data.items():
                        setattr(permission, key, value)
                    permission.save()
                    self.stdout.write(f"  + Created permission: {code}")
                else:
                    if force:
                        self.stdout.write(f"  ~ Updated permission: {code}")
                    else:
                        self.stdout.write(
                            f"  - Skipped permission: {code} (already exists)"
                        )

                permissions[code] = permission

        return permissions

    def _create_roles(self, force: bool, dry_run: bool) -> dict:
        """Create or update system roles."""
        roles_data = [
            # Platform roles
            {
                "name": "super_admin",
                "display_name_tr": "Süper Yönetici",
                "display_name_en": "Super Administrator",
                "description_tr": "Tüm izinlere sahip tam sistem erişimi. Platform ayarlarını, tüm organizasyonları ve sistem yapılandırmasını yönetebilir.",
                "description_en": "Full system access with all permissions. Can manage platform settings, all organizations, and system configuration.",
                "display_name_ar": "المدير الأعلى",
                "display_name_fa": "مدیر ارشد",
                "display_name_uk": "Суперадміністратор",
                "description_ar": "وصول كامل للنظام مع جميع الصلاحيات. يمكنه إدارة إعدادات المنصة وجميع المؤسسات وتكوين النظام.",
                "description_fa": "دسترسی کامل به سیستم با تمام مجوزها. می‌تواند تنظیمات پلتفرم، تمام سازمان‌ها و پیکربندی سیستم را مدیریت کند.",
                "description_uk": "Повний доступ до системи з усіма дозволами. Може керувати налаштуваннями платформи, усіма організаціями та конфігурацією системи.",
                "scope": RoleScope.PLATFORM,
                "is_system": True,
                "organization": None,
            },
            {
                "name": "admin",
                "display_name_tr": "Platform Yöneticisi",
                "display_name_en": "Platform Administrator",
                "description_tr": "Müşteri, fatura ve destek yönetimi. Organizasyonları yönetebilir ve fatura işlemlerini gerçekleştirebilir.",
                "description_en": "Customer, billing, and support management. Can manage organizations and handle billing operations.",
                "display_name_ar": "مدير المنصة",
                "display_name_fa": "مدیر پلتفرم",
                "display_name_uk": "Адміністратор платформи",
                "description_ar": "إدارة العملاء والفوترة والدعم. يمكنه إدارة المؤسسات والتعامل مع عمليات الفوترة.",
                "description_fa": "مدیریت مشتریان، صورتحساب و پشتیبانی. می‌تواند سازمان‌ها را مدیریت کرده و عملیات صورتحساب را انجام دهد.",
                "description_uk": "Управління клієнтами, рахунками та підтримкою. Може керувати організаціями та обробляти платіжні операції.",
                "scope": RoleScope.PLATFORM,
                "is_system": True,
                "organization": None,
            },
            {
                "name": "sales",
                "display_name_tr": "Satış Temsilcisi",
                "display_name_en": "Sales Representative",
                "description_tr": "CRM ve potansiyel müşteri yönetimi. Potansiyel müşterileri ve satış süreçlerini yönetebilir.",
                "description_en": "CRM and lead management. Can manage leads, potential customers, and sales pipelines.",
                "display_name_ar": "مندوب المبيعات",
                "display_name_fa": "نماینده فروش",
                "display_name_uk": "Торговий представник",
                "description_ar": "إدارة علاقات العملاء والعملاء المحتملين. يمكنه إدارة العملاء المحتملين وعمليات المبيعات.",
                "description_fa": "مدیریت ارتباط با مشتری و سرنخ‌ها. می‌تواند سرنخ‌ها، مشتریان بالقوه و فرآیندهای فروش را مدیریت کند.",
                "description_uk": "CRM та управління потенційними клієнтами. Може керувати лідами, потенційними клієнтами та процесами продажів.",
                "scope": RoleScope.PLATFORM,
                "is_system": True,
                "organization": None,
            },
            {
                "name": "support",
                "display_name_tr": "Destek Uzmanı",
                "display_name_en": "Support Agent",
                "description_tr": "Sadece destek talepleri. Müşteri destek taleplerini görüntüleyebilir ve yönetebilir.",
                "description_en": "Support tickets only. Can view and manage customer support tickets.",
                "display_name_ar": "أخصائي الدعم",
                "display_name_fa": "کارشناس پشتیبانی",
                "display_name_uk": "Спеціаліст підтримки",
                "description_ar": "تذاكر الدعم فقط. يمكنه عرض وإدارة تذاكر دعم العملاء.",
                "description_fa": "فقط تیکت‌های پشتیبانی. می‌تواند تیکت‌های پشتیبانی مشتریان را مشاهده و مدیریت کند.",
                "description_uk": "Лише тікети підтримки. Може переглядати та керувати тікетами підтримки клієнтів.",
                "scope": RoleScope.PLATFORM,
                "is_system": True,
                "organization": None,
            },
            # Organization roles
            {
                "name": "owner",
                "display_name_tr": "İşletme Sahibi",
                "display_name_en": "Organization Owner",
                "description_tr": "Faturalandırma dahil tam organizasyon erişimi. Abonelik yönetimi dahil organizasyon üzerinde tam kontrol.",
                "description_en": "Full organization access with billing. Complete control over the organization including subscription management.",
                "display_name_ar": "مالك المنشأة",
                "display_name_fa": "مالک کسب‌وکار",
                "display_name_uk": "Власник бізнесу",
                "description_ar": "وصول كامل للمؤسسة مع الفوترة. تحكم كامل بالمؤسسة بما في ذلك إدارة الاشتراكات.",
                "description_fa": "دسترسی کامل به سازمان شامل صورتحساب. کنترل کامل بر سازمان از جمله مدیریت اشتراک.",
                "description_uk": "Повний доступ до організації включно з білінгом. Повний контроль над організацією, включаючи управління підписками.",
                "scope": RoleScope.ORGANIZATION,
                "is_system": True,
                "organization": None,
            },
            {
                "name": "manager",
                "display_name_tr": "Yönetici",
                "display_name_en": "Manager",
                "description_tr": "Menü, sipariş ve personel yönetimi. Menüleri yönetebilir, siparişleri takip edebilir ve ekip üyelerini yönetebilir.",
                "description_en": "Menu, order, and staff management. Can manage menus, handle orders, and manage team members.",
                "display_name_ar": "مدير",
                "display_name_fa": "مدیر",
                "display_name_uk": "Менеджер",
                "description_ar": "إدارة القوائم والطلبات والموظفين. يمكنه إدارة القوائم ومعالجة الطلبات وإدارة أعضاء الفريق.",
                "description_fa": "مدیریت منو، سفارشات و کارکنان. می‌تواند منوها را مدیریت کرده، سفارشات را پیگیری کرده و اعضای تیم را مدیریت کند.",
                "description_uk": "Управління меню, замовленнями та персоналом. Може керувати меню, обробляти замовлення та керувати членами команди.",
                "scope": RoleScope.ORGANIZATION,
                "is_system": True,
                "organization": None,
            },
            {
                "name": "staff",
                "display_name_tr": "Personel",
                "display_name_en": "Staff",
                "description_tr": "Sipariş alma ve masa yönetimi. Sipariş alabilir, masaları yönetebilir ve servis taleplerini karşılayabilir.",
                "description_en": "Order taking and table management. Can take orders, manage tables, and handle service requests.",
                "display_name_ar": "موظف",
                "display_name_fa": "کارمند",
                "display_name_uk": "Персонал",
                "description_ar": "أخذ الطلبات وإدارة الطاولات. يمكنه أخذ الطلبات وإدارة الطاولات والتعامل مع طلبات الخدمة.",
                "description_fa": "دریافت سفارش و مدیریت میزها. می‌تواند سفارشات را دریافت کرده، میزها را مدیریت کرده و درخواست‌های خدمات را پیگیری کند.",
                "description_uk": "Прийом замовлень та управління столиками. Може приймати замовлення, керувати столиками та обробляти запити на обслуговування.",
                "scope": RoleScope.ORGANIZATION,
                "is_system": True,
                "organization": None,
            },
            {
                "name": "viewer",
                "display_name_tr": "İzleyici",
                "display_name_en": "Viewer",
                "description_tr": "Salt okunur dashboard erişimi. Menüleri, siparişleri ve analizleri görüntüleyebilir ancak değişiklik yapamaz.",
                "description_en": "Read-only dashboard access. Can view menus, orders, and analytics but cannot make changes.",
                "display_name_ar": "مشاهد",
                "display_name_fa": "مشاهده‌کننده",
                "display_name_uk": "Спостерігач",
                "description_ar": "وصول للوحة القيادة للقراءة فقط. يمكنه عرض القوائم والطلبات والتحليلات ولكن لا يمكنه إجراء تغييرات.",
                "description_fa": "دسترسی فقط خواندنی به داشبورد. می‌تواند منوها، سفارشات و تحلیل‌ها را مشاهده کند اما نمی‌تواند تغییراتی اعمال کند.",
                "description_uk": "Доступ лише для читання до панелі керування. Може переглядати меню, замовлення та аналітику, але не може вносити зміни.",
                "scope": RoleScope.ORGANIZATION,
                "is_system": True,
                "organization": None,
            },
        ]

        roles = {}
        for data in roles_data:
            name = data["name"]
            scope = data["scope"]

            role, created = Role.objects.update_or_create(
                name=name,
                scope=scope,
                organization=None,  # System roles have no organization
                defaults=data if force else {"is_system": True},
            )

            if created:
                for key, value in data.items():
                    setattr(role, key, value)
                role.save()
                self.stdout.write(
                    f"  + Created role: {data['display_name_tr']} ({name})"
                )
            else:
                if force:
                    self.stdout.write(
                        f"  ~ Updated role: {data['display_name_tr']} ({name})"
                    )
                else:
                    self.stdout.write(
                        f"  - Skipped role: {data['display_name_tr']} ({name}) (already exists)"
                    )

            roles[name] = role

        return roles

    def _create_role_permissions(
        self, roles: dict, permissions: dict, force: bool, dry_run: bool
    ) -> list:
        """Create or update role-permission relationships."""
        # Define which permissions each role has
        # Permissions are specified as resource.action patterns
        # Use '*' as action to grant all actions for a resource
        # Use 'manage' to grant manage action (full access)

        role_permission_config = {
            # Platform roles
            "super_admin": {
                # Full access to everything
                "organization": ["manage"],
                "user": ["manage"],
                "branch": ["manage"],
                "role": ["manage"],
                "menu": ["manage"],
                "category": ["manage"],
                "product": ["manage"],
                "theme": ["manage"],
                "order": ["manage"],
                "table": ["manage"],
                "zone": ["manage"],
                "qr_code": ["manage"],
                "service_request": ["manage"],
                "customer": ["manage"],
                "feedback": ["manage"],
                "subscription": ["manage"],
                "invoice": ["view", "list", "create", "update", "export"],
                "plan": ["manage"],
                "inventory": ["manage"],
                "campaign": ["manage"],
                "dashboard": ["manage"],
                "analytics": ["view", "export"],
                "report": ["view", "list", "create", "export"],
                "media": ["manage"],
                "notification": ["manage"],
                "audit_log": ["view", "list", "export"],
                "ai_generation": ["manage"],
                "ticket": ["manage"],
                "lead": ["manage"],
                "settings": ["manage"],
            },
            "admin": {
                # Customer, billing, support management
                "organization": ["view", "list", "update"],
                "user": ["view", "list", "create", "update"],
                "subscription": ["manage"],
                "invoice": ["view", "list", "create", "update", "export"],
                "plan": ["view", "list"],
                "inventory": ["view", "list"],
                "campaign": ["view", "list"],
                "dashboard": ["view"],
                "ticket": ["manage"],
                "customer": ["view", "list", "update", "export"],
                "feedback": ["view", "list", "manage"],
                "audit_log": ["view", "list"],
                "analytics": ["view"],
                "report": ["view", "list"],
            },
            "sales": {
                # CRM, lead management
                "lead": ["manage"],
                "organization": ["view", "list"],
                "user": ["view", "list"],
                "subscription": ["view", "list"],
                "plan": ["view", "list"],
                "customer": ["view", "list"],
                "analytics": ["view"],
                "report": ["view", "list"],
            },
            "support": {
                # Support tickets only
                "ticket": ["manage"],
                "organization": ["view"],
                "user": ["view"],
                "subscription": ["view"],
                "customer": ["view", "list"],
                "feedback": ["view", "list"],
            },
            # Organization roles
            "owner": {
                # Full organization access, billing
                "organization": ["view", "update"],
                "user": ["manage"],
                "branch": ["manage"],
                "role": ["view", "list"],  # Can't create platform roles
                "menu": ["manage"],
                "category": ["manage"],
                "product": ["manage"],
                "theme": ["manage"],
                "order": ["manage"],
                "table": ["manage"],
                "zone": ["manage"],
                "qr_code": ["manage"],
                "service_request": ["manage"],
                "customer": ["manage"],
                "feedback": ["manage"],
                "subscription": ["view", "update"],
                "invoice": ["view", "list", "export"],
                "inventory": ["manage"],
                "campaign": ["manage"],
                "dashboard": ["view", "manage"],
                "analytics": ["view", "export"],
                "report": ["view", "list", "create", "export"],
                "media": ["manage"],
                "notification": ["manage"],
                "audit_log": ["view", "list"],
                "ai_generation": ["manage"],
                "settings": ["manage"],
            },
            "manager": {
                # Menu, order, staff management
                "organization": ["view"],
                "user": ["view", "list", "create", "update"],  # Can manage staff
                "branch": ["view", "list"],
                "menu": ["manage"],
                "category": ["manage"],
                "product": ["manage"],
                "theme": ["view", "list", "update"],
                "order": ["manage"],
                "table": ["manage"],
                "zone": ["manage"],
                "qr_code": ["manage"],
                "service_request": ["manage"],
                "customer": ["view", "list", "update"],
                "feedback": ["view", "list", "manage"],
                "inventory": ["view", "list", "create", "update"],
                "campaign": ["view", "list", "create", "update"],
                "dashboard": ["view"],
                "analytics": ["view"],
                "report": ["view", "list", "create"],
                "media": ["manage"],
                "notification": ["view", "list", "create"],
                "ai_generation": ["view", "create"],
                "settings": ["view", "update"],
            },
            "staff": {
                # Order taking, table management
                "organization": ["view"],
                "menu": ["view", "list"],
                "category": ["view", "list"],
                "product": ["view", "list", "update"],  # Can update availability
                "order": ["view", "list", "create", "update"],
                "table": ["view", "list", "update"],
                "zone": ["view", "list"],
                "qr_code": ["view", "list"],
                "service_request": ["view", "list", "create", "update"],
                "customer": ["view", "list", "create"],
                "notification": ["view", "list"],
                "media": ["view", "list", "create"],  # Can view and upload media
            },
            "viewer": {
                # Read-only dashboard
                "organization": ["view"],
                "user": ["view", "list"],
                "branch": ["view", "list"],
                "menu": ["view", "list"],
                "category": ["view", "list"],
                "product": ["view", "list"],
                "theme": ["view", "list"],
                "order": ["view", "list"],
                "table": ["view", "list"],
                "zone": ["view", "list"],
                "qr_code": ["view", "list"],
                "customer": ["view", "list"],
                "feedback": ["view", "list"],
                "analytics": ["view"],
                "report": ["view", "list"],
                "notification": ["view", "list"],
                "media": ["view", "list"],  # Can view media (read-only)
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
                    perm_code = f"{resource}.{action}"
                    permission = permissions.get(perm_code)
                    if not permission:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ! Permission "{perm_code}" not found, skipping'
                            )
                        )
                        continue

                    # Define conditions for organization-scoped roles
                    conditions = {}
                    if role.scope == RoleScope.ORGANIZATION:
                        # Organization roles have tenant-scoped conditions
                        conditions = {"organization_id": "${user.organization_id}"}

                    role_permission, created = RolePermission.objects.update_or_create(
                        role=role,
                        permission=permission,
                        defaults={
                            "conditions": conditions,
                        }
                        if force
                        else {},
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
