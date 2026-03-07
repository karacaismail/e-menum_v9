"""
Management command to seed realistic mock data for ALL admin models.

Creates 3-12 records per model with realistic, relational Turkish restaurant data.
Depends on seed_menu_data having been run first (for Organization, Menu, Products).

Models seeded:
  Core: Branch, UserRole, Session, AuditLog, extra Users
  Orders: Zone, Table, QRCode, QRScan, Order, OrderItem, ServiceRequest
  Customers: Customer, CustomerVisit, Feedback, LoyaltyPoint
  Subscriptions: Subscription, Invoice (+ activates admin for Plan/Feature)
  Media: MediaFolder, Media
  Notifications: Notification

Usage:
    python manage.py seed_all_data
    python manage.py seed_all_data --clear
"""

import logging
import random
import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
now = timezone.now


def rand_past(days_back=90):
    """Return a random datetime within the last N days."""
    return now() - timedelta(
        days=random.randint(1, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )


def rand_recent(hours_back=48):
    """Return a random datetime within the last N hours."""
    return now() - timedelta(
        hours=random.randint(0, hours_back),
        minutes=random.randint(0, 59),
    )


class Command(BaseCommand):
    help = 'Seed realistic mock data for all admin models (3-12 per model)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear seeded data before re-creating',
        )

    def handle(self, *args, **options):
        from apps.core.models import Organization

        # Get existing org from seed_menu_data
        try:
            org = Organization.objects.get(slug='lezzet-sarayi')
        except Organization.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Organization "lezzet-sarayi" not found. '
                'Run "python manage.py seed_menu_data" first.'
            ))
            return

        owner = User.objects.filter(
            email='admin@lezzetsarayi.com'
        ).first()
        if not owner:
            self.stderr.write(self.style.ERROR(
                'Owner user not found. Run seed_menu_data first.'
            ))
            return

        if options['clear']:
            self._clear(org)

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\nSeeding mock data for all models...\n'
        ))

        # ── Platform Users ───────────────────────────────────────
        self._seed_platform_users()

        # ── Core ──────────────────────────────────────────────────
        branches = self._seed_branches(org, owner)
        staff_users = self._seed_users(org, owner)
        self._seed_user_roles(org, owner, staff_users)
        self._seed_extra_org_roles()
        self._seed_sessions(staff_users)
        self._seed_audit_logs(org, owner, staff_users)

        # ── Orders ────────────────────────────────────────────────
        zones = self._seed_zones(org, branches)
        tables = self._seed_tables(org, zones)
        qr_codes = self._seed_qr_codes(org, tables)
        customers = self._seed_customers(org)
        orders = self._seed_orders(org, tables, customers, staff_users)
        self._seed_order_items(orders)
        self._seed_qr_scans(org, qr_codes, customers)
        self._seed_service_requests(org, tables, customers, staff_users)

        # ── Customers ─────────────────────────────────────────────
        self._seed_customer_visits(org, customers, branches, tables)
        self._seed_feedback(org, customers, orders)
        self._seed_loyalty_points(org, customers, orders)

        # ── Subscriptions ─────────────────────────────────────────
        self._seed_subscriptions(org)

        # ── Media ─────────────────────────────────────────────────
        self._seed_media(org, owner)

        # ── Notifications ─────────────────────────────────────────
        self._seed_notifications(org, owner, staff_users)

        self.stdout.write(self.style.SUCCESS(
            '\n✅ All mock data seeded successfully!\n'
        ))

    # ===================================================================
    # CLEAR
    # ===================================================================
    def _clear(self, org):
        self.stdout.write(self.style.WARNING('Clearing seeded data...'))
        from apps.customers.models import (
            Customer, CustomerVisit, Feedback, LoyaltyPoint,
        )
        from apps.media.models import Media, MediaFolder
        from apps.notifications.models import Notification
        from apps.orders.models import (
            Order, OrderItem, QRCode, QRScan, ServiceRequest, Table, Zone,
        )

        # Order matters for FK constraints
        OrderItem.all_objects.filter(order__organization=org).delete()
        ServiceRequest.all_objects.filter(organization=org).delete()
        QRScan.objects.filter(organization=org).delete()
        Order.all_objects.filter(organization=org).delete()
        QRCode.all_objects.filter(organization=org).delete()
        Table.all_objects.filter(organization=org).delete()
        Zone.all_objects.filter(organization=org).delete()

        LoyaltyPoint.objects.filter(organization=org).delete()
        Feedback.all_objects.filter(organization=org).delete()
        CustomerVisit.objects.filter(organization=org).delete()
        Customer.all_objects.filter(organization=org).delete()

        Media.all_objects.filter(organization=org).delete()
        MediaFolder.all_objects.filter(organization=org).delete()

        Notification.all_objects.filter(organization=org).delete()

        from apps.core.models import AuditLog, Branch, Session, UserRole
        AuditLog.objects.filter(organization=org).delete()
        Session.objects.filter(
            user__organization=org
        ).exclude(user__email='admin@lezzetsarayi.com').delete()
        UserRole.objects.filter(organization=org).delete()

        # Delete extra staff users but keep owner and global admin
        User.objects.filter(
            organization=org
        ).exclude(
            email__in=['admin@lezzetsarayi.com', 'admin@e-menum.net']
        ).delete()

        Branch.all_objects.filter(organization=org).delete()

        # Subscriptions
        try:
            from apps.subscriptions.models import Invoice, Subscription
            Invoice.all_objects.filter(
                subscription__organization=org
            ).delete()
            Subscription.all_objects.filter(organization=org).delete()
        except Exception:
            pass

        self.stdout.write(self.style.WARNING('  Cleared!'))

    # ===================================================================
    # PLATFORM: Platform-level users with roles
    # ===================================================================
    def _seed_platform_users(self):
        from apps.core.models import Role, UserRole

        platform_users = [
            {
                'email': 'admin@e-menum.net',
                'role': 'super_admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'password': 'Admin1234!emenum',
                'is_superuser': True,
            },
            {
                'email': 'platform-admin@e-menum.net',
                'role': 'admin',
                'first_name': 'Platform',
                'last_name': 'Admin',
                'password': 'PlatAdmin1234!',
            },
            {
                'email': 'sales@e-menum.net',
                'role': 'sales',
                'first_name': 'Pinar',
                'last_name': 'Yilmaz',
                'password': 'Sales1234!emenum',
            },
            {
                'email': 'support@e-menum.net',
                'role': 'support',
                'first_name': 'Destek',
                'last_name': 'Ekibi',
                'password': 'Support1234!emenum',
            },
        ]

        count = 0
        for pd in platform_users:
            role_name = pd.pop('role')
            password = pd.pop('password')
            is_su = pd.pop('is_superuser', False)

            user, created = User.objects.get_or_create(
                email=pd['email'],
                defaults={
                    **pd,
                    'is_staff': True,
                    'is_superuser': is_su,
                    'status': 'ACTIVE',
                    'organization': None,
                },
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'  Platform user: {user.email}')
            else:
                # Ensure superuser flag is correct
                if is_su and not user.is_superuser:
                    user.is_superuser = True
                    user.save(update_fields=['is_superuser'])

            # Assign platform role
            role = Role.objects.filter(name=role_name, scope='PLATFORM').first()
            if role:
                _, rc = UserRole.objects.get_or_create(
                    user=user, role=role, organization=None,
                    defaults={'granted_by': user},
                )
                if rc:
                    count += 1

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {len(platform_users)} platform users, {count} role assignments'
        ))

    # ===================================================================
    # CORE: Assign owner roles to extra organizations
    # ===================================================================
    def _seed_extra_org_roles(self):
        from apps.core.models import Role, UserRole

        owner_role = Role.objects.filter(
            name='owner', scope='ORGANIZATION'
        ).first()
        if not owner_role:
            return

        extra_org_owners = [
            ('mehmet@bosphorusbistro.com', 'bosphorus-bistro'),
            ('ayse@cafenoir.com.tr', 'cafe-noir'),
            ('ali@sultankebap.com.tr', 'sultan-kebap'),
        ]

        count = 0
        for email, slug in extra_org_owners:
            from apps.core.models import Organization
            user = User.objects.filter(email=email).first()
            org = Organization.objects.filter(slug=slug).first()
            if user and org:
                _, created = UserRole.objects.get_or_create(
                    user=user, role=owner_role, organization=org,
                    defaults={'granted_by': user},
                )
                if created:
                    count += 1

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {count} extra org owner roles'
        ))

    # ===================================================================
    # CORE: Branches
    # ===================================================================
    def _seed_branches(self, org, owner):
        from apps.core.models import Branch

        data = [
            {
                'name': 'Kadikoy Merkez',
                'slug': 'kadikoy-merkez',
                'address': 'Caferaga Mah. Moda Cad. No:42',
                'city': 'Istanbul',
                'district': 'Kadikoy',
                'postal_code': '34710',
                'country': 'TR',
                'phone': '+90 216 345 67 89',
                'email': 'kadikoy@lezzetsarayi.com',
                'latitude': Decimal('40.9906'),
                'longitude': Decimal('29.0248'),
                'is_main': True,
                'status': 'ACTIVE',
                'operating_hours': {
                    'monday': {'open': '10:00', 'close': '23:00'},
                    'tuesday': {'open': '10:00', 'close': '23:00'},
                    'wednesday': {'open': '10:00', 'close': '23:00'},
                    'thursday': {'open': '10:00', 'close': '23:00'},
                    'friday': {'open': '10:00', 'close': '00:00'},
                    'saturday': {'open': '09:00', 'close': '00:00'},
                    'sunday': {'open': '09:00', 'close': '22:00'},
                },
            },
            {
                'name': 'Besiktas Sube',
                'slug': 'besiktas-sube',
                'address': 'Sinanpasa Mah. Ihlamurdere Cad. No:18',
                'city': 'Istanbul',
                'district': 'Besiktas',
                'postal_code': '34353',
                'country': 'TR',
                'phone': '+90 212 258 90 12',
                'email': 'besiktas@lezzetsarayi.com',
                'latitude': Decimal('41.0438'),
                'longitude': Decimal('29.0076'),
                'is_main': False,
                'status': 'ACTIVE',
                'operating_hours': {
                    'monday': {'open': '11:00', 'close': '23:00'},
                    'tuesday': {'open': '11:00', 'close': '23:00'},
                    'wednesday': {'open': '11:00', 'close': '23:00'},
                    'thursday': {'open': '11:00', 'close': '23:00'},
                    'friday': {'open': '11:00', 'close': '00:00'},
                    'saturday': {'open': '10:00', 'close': '00:00'},
                    'sunday': {'open': '10:00', 'close': '22:00'},
                },
            },
            {
                'name': 'Ankara Kizilay',
                'slug': 'ankara-kizilay',
                'address': 'Kizilay Mah. Ataturk Blv. No:55',
                'city': 'Ankara',
                'district': 'Cankaya',
                'postal_code': '06420',
                'country': 'TR',
                'phone': '+90 312 419 33 44',
                'email': 'ankara@lezzetsarayi.com',
                'latitude': Decimal('39.9208'),
                'longitude': Decimal('32.8541'),
                'is_main': False,
                'status': 'ACTIVE',
                'operating_hours': {
                    'monday': {'open': '10:00', 'close': '22:00'},
                    'tuesday': {'open': '10:00', 'close': '22:00'},
                    'wednesday': {'open': '10:00', 'close': '22:00'},
                    'thursday': {'open': '10:00', 'close': '22:00'},
                    'friday': {'open': '10:00', 'close': '23:00'},
                    'saturday': {'open': '09:00', 'close': '23:00'},
                    'sunday': {'open': '09:00', 'close': '21:00'},
                },
            },
        ]

        branches = []
        for d in data:
            b, created = Branch.objects.get_or_create(
                organization=org, slug=d['slug'],
                defaults={**d, 'organization': org},
            )
            branches.append(b)
            if created:
                self.stdout.write(f'  Branch: {b.name}')
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {len(branches)} branches'
        ))
        return branches

    # ===================================================================
    # CORE: Extra Users (staff)
    # ===================================================================
    def _seed_users(self, org, owner):
        staff_data = [
            {
                'email': 'mehmet.yilmaz@lezzetsarayi.com',
                'first_name': 'Mehmet',
                'last_name': 'Yilmaz',
                'is_staff': True,
                'phone': '+90 532 111 22 33',
            },
            {
                'email': 'ayse.demir@lezzetsarayi.com',
                'first_name': 'Ayse',
                'last_name': 'Demir',
                'is_staff': True,
                'phone': '+90 533 222 33 44',
            },
            {
                'email': 'fatma.kaya@lezzetsarayi.com',
                'first_name': 'Fatma',
                'last_name': 'Kaya',
                'is_staff': False,
                'phone': '+90 534 333 44 55',
            },
            {
                'email': 'ali.celik@lezzetsarayi.com',
                'first_name': 'Ali',
                'last_name': 'Celik',
                'is_staff': False,
                'phone': '+90 535 444 55 66',
            },
            {
                'email': 'zeynep.arslan@lezzetsarayi.com',
                'first_name': 'Zeynep',
                'last_name': 'Arslan',
                'is_staff': False,
                'phone': '+90 536 555 66 77',
            },
        ]
        users = []
        for d in staff_data:
            u, created = User.objects.get_or_create(
                email=d['email'],
                defaults={
                    **d,
                    'organization': org,
                    'status': 'ACTIVE',
                },
            )
            if created:
                u.set_password('Staff1234!emenum')
                u.save()
                self.stdout.write(f'  User: {u.email}')
            users.append(u)
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(users)} staff users'))
        return users

    # ===================================================================
    # CORE: User Roles
    # ===================================================================
    def _seed_user_roles(self, org, owner, staff_users):
        from apps.core.models import Role, UserRole

        role_map = {
            'owner': owner,
        }
        # Assign staff
        staff_roles = ['manager', 'staff', 'staff', 'staff', 'viewer']
        for i, user in enumerate(staff_users):
            role_name = staff_roles[i] if i < len(staff_roles) else 'viewer'
            role_map[f'{role_name}_{i}'] = (user, role_name)

        count = 0
        # Owner role
        owner_role = Role.objects.filter(name='owner', scope='ORGANIZATION').first()
        if owner_role:
            _, created = UserRole.objects.get_or_create(
                user=owner, role=owner_role, organization=org,
                defaults={'granted_by': owner},
            )
            if created:
                count += 1

        # Staff roles
        for i, user in enumerate(staff_users):
            role_name = staff_roles[i] if i < len(staff_roles) else 'viewer'
            role = Role.objects.filter(
                name=role_name, scope='ORGANIZATION'
            ).first()
            if role:
                _, created = UserRole.objects.get_or_create(
                    user=user, role=role, organization=org,
                    defaults={'granted_by': owner},
                )
                if created:
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} user roles'))

    # ===================================================================
    # CORE: Sessions
    # ===================================================================
    def _seed_sessions(self, staff_users):
        from apps.core.models import Session

        ips = [
            '85.101.45.67', '78.186.32.11', '176.42.98.201',
            '94.55.123.78', '31.206.44.15',
        ]
        agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605',
            'Mozilla/5.0 (Linux; Android 14) Chrome/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Safari/605',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120',
            'Mozilla/5.0 (iPad; CPU OS 17_0) AppleWebKit/605',
        ]

        count = 0
        for i, user in enumerate(staff_users[:4]):
            # Active session
            _, created = Session.objects.get_or_create(
                user=user,
                status='ACTIVE',
                defaults={
                    'refresh_token': uuid.uuid4().hex,
                    'ip_address': ips[i],
                    'user_agent': agents[i],
                    'expires_at': now() + timedelta(days=7),
                },
            )
            if created:
                count += 1

        # One expired session
        if staff_users:
            _, created = Session.objects.get_or_create(
                user=staff_users[0],
                status='EXPIRED',
                defaults={
                    'refresh_token': uuid.uuid4().hex,
                    'ip_address': '85.101.45.67',
                    'user_agent': agents[0],
                    'expires_at': now() - timedelta(days=1),
                },
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} sessions'))

    # ===================================================================
    # CORE: Audit Logs
    # ===================================================================
    def _seed_audit_logs(self, org, owner, staff_users):
        from apps.core.models import AuditLog

        if AuditLog.objects.filter(organization=org).exists():
            self.stdout.write('  Audit logs exist, skipping')
            return

        logs = [
            {'action': 'CREATE', 'resource': 'menu', 'description': 'Ana Menu olusturuldu', 'user': owner},
            {'action': 'UPDATE', 'resource': 'product', 'description': 'Adana Kebap fiyati guncellendi', 'user': owner},
            {'action': 'CREATE', 'resource': 'product', 'description': 'Yeni urun eklendi: Beyti Kebap', 'user': owner},
            {'action': 'LOGIN', 'resource': 'auth', 'description': 'Basarili giris', 'user': owner},
            {'action': 'UPDATE', 'resource': 'organization', 'description': 'Restoran ayarlari guncellendi', 'user': owner},
            {'action': 'CREATE', 'resource': 'category', 'description': 'Yeni kategori: Tatlilar', 'user': staff_users[0] if staff_users else owner},
            {'action': 'DELETE', 'resource': 'product', 'description': 'Urun silindi: Eski Yemek', 'user': owner},
            {'action': 'UPDATE', 'resource': 'theme', 'description': 'Tema renkleri degistirildi', 'user': owner},
            {'action': 'LOGIN', 'resource': 'auth', 'description': 'Basarili giris', 'user': staff_users[1] if len(staff_users) > 1 else owner},
            {'action': 'CREATE', 'resource': 'order', 'description': 'Yeni siparis #ORD-001', 'user': staff_users[2] if len(staff_users) > 2 else owner},
            {'action': 'LOGIN_FAILED', 'resource': 'auth', 'description': 'Basarisiz giris denemesi', 'user': None},
            {'action': 'UPDATE', 'resource': 'menu', 'description': 'Menu yayinlandi', 'user': owner},
        ]

        for i, log in enumerate(logs):
            AuditLog.objects.create(
                organization=org,
                user=log['user'],
                action=log['action'],
                resource=log['resource'],
                resource_id=str(uuid.uuid4()),
                description=log['description'],
                ip_address=f'85.101.{random.randint(1, 254)}.{random.randint(1, 254)}',
                user_agent='Mozilla/5.0',
                created_at=rand_past(60),
            )

        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(logs)} audit logs'))

    # ===================================================================
    # ORDERS: Zones
    # ===================================================================
    def _seed_zones(self, org, branches):
        from apps.orders.models import Zone

        branch = branches[0] if branches else None
        zone_data = [
            {
                'name': 'Ic Mekan',
                'slug': 'ic-mekan',
                'description': 'Klimali ic mekan bolumu',
                'color': '#3B82F6',
                'icon': 'ph-fill ph-house',
                'capacity': 60,
                'is_outdoor': False,
                'is_smoking_allowed': False,
                'is_reservable': True,
            },
            {
                'name': 'Bahce',
                'slug': 'bahce',
                'description': 'Acik hava bahce alani',
                'color': '#10B981',
                'icon': 'ph-fill ph-tree',
                'capacity': 40,
                'is_outdoor': True,
                'is_smoking_allowed': True,
                'is_reservable': True,
            },
            {
                'name': 'VIP Salon',
                'slug': 'vip-salon',
                'description': 'Ozel toplanti ve kutlama alani',
                'color': '#F59E0B',
                'icon': 'ph-fill ph-star',
                'capacity': 20,
                'is_outdoor': False,
                'is_smoking_allowed': False,
                'is_reservable': True,
            },
            {
                'name': 'Teras',
                'slug': 'teras',
                'description': 'Ust kat acik teras alani',
                'color': '#8B5CF6',
                'icon': 'ph-fill ph-sun',
                'capacity': 24,
                'is_outdoor': True,
                'is_smoking_allowed': False,
                'is_reservable': True,
            },
            {
                'name': 'Bar Bolumu',
                'slug': 'bar-bolumu',
                'description': 'Bar onundeki yuksek masalar',
                'color': '#EF4444',
                'icon': 'ph-fill ph-wine',
                'capacity': 16,
                'is_outdoor': False,
                'is_smoking_allowed': False,
                'is_reservable': False,
            },
        ]

        zones = []
        for i, d in enumerate(zone_data):
            z, created = Zone.objects.get_or_create(
                organization=org, slug=d['slug'],
                defaults={
                    **d, 'organization': org, 'branch': branch,
                    'sort_order': i,
                },
            )
            zones.append(z)
            if created:
                self.stdout.write(f'  Zone: {z.name}')
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(zones)} zones'))
        return zones

    # ===================================================================
    # ORDERS: Tables
    # ===================================================================
    def _seed_tables(self, org, zones):
        from apps.orders.models import Table

        statuses = ['AVAILABLE', 'AVAILABLE', 'AVAILABLE', 'OCCUPIED', 'RESERVED']
        tables = []
        table_num = 1

        table_configs = {
            # zone_index: (count, min_cap, max_cap)
            0: (8, 2, 6),    # Ic Mekan - 8 tables
            1: (6, 2, 4),    # Bahce - 6 tables
            2: (3, 4, 10),   # VIP - 3 tables
            3: (4, 2, 4),    # Teras - 4 tables
            4: (4, 1, 2),    # Bar - 4 tall tables
        }

        for zi, zone in enumerate(zones):
            count, min_c, max_c = table_configs.get(zi, (4, 2, 4))
            for j in range(count):
                cap = random.randint(min_c, max_c)
                name = f'Masa {table_num}'
                slug = f'masa-{table_num}'
                t, created = Table.objects.get_or_create(
                    organization=org, slug=slug,
                    defaults={
                        'organization': org,
                        'zone': zone,
                        'branch': zone.branch,
                        'name': name,
                        'number': table_num,
                        'capacity': cap,
                        'min_capacity': 1,
                        'status': random.choice(statuses),
                        'is_vip': zi == 2,
                        'shape': 'circle' if zi == 4 else 'rectangle',
                        'position_x': j * 120 + 50,
                        'position_y': zi * 100 + 50,
                        'sort_order': table_num,
                    },
                )
                tables.append(t)
                table_num += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(tables)} tables'))
        return tables

    # ===================================================================
    # ORDERS: QR Codes
    # ===================================================================
    def _seed_qr_codes(self, org, tables):
        from apps.menu.models import Menu
        from apps.orders.models import QRCode

        menu = Menu.objects.filter(
            organization=org, is_published=True
        ).first()

        qr_codes = []
        for table in tables[:12]:  # QR for first 12 tables
            code = f'LS-{table.number:03d}-{uuid.uuid4().hex[:6].upper()}'
            qr, created = QRCode.objects.get_or_create(
                organization=org, code=code,
                defaults={
                    'organization': org,
                    'branch': table.branch,
                    'menu': menu,
                    'table': table,
                    'type': 'TABLE',
                    'name': f'QR - {table.name}',
                    'description': f'{table.name} icin QR kod',
                    'short_url': f'https://e-menum.net/q/{code}',
                    'redirect_url': f'https://e-menum.net/m/ana-menu/?table={table.number}',
                    'scan_count': random.randint(5, 200),
                    'unique_scan_count': random.randint(3, 100),
                    'last_scanned_at': rand_recent(72),
                },
            )
            qr_codes.append(qr)

        # Campaign QR
        camp_code = f'LS-CAMP-{uuid.uuid4().hex[:6].upper()}'
        qr_camp, _ = QRCode.objects.get_or_create(
            organization=org, code=camp_code,
            defaults={
                'organization': org,
                'menu': menu,
                'type': 'CAMPAIGN',
                'name': 'Yaz Kampanyasi QR',
                'description': 'Yaz kampanyasi icin ozel QR kod',
                'short_url': f'https://e-menum.net/q/{camp_code}',
                'redirect_url': 'https://e-menum.net/m/ana-menu/?promo=summer',
                'scan_count': random.randint(50, 500),
                'unique_scan_count': random.randint(30, 200),
                'last_scanned_at': rand_recent(24),
            },
        )
        qr_codes.append(qr_camp)

        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(qr_codes)} QR codes'))
        return qr_codes

    # ===================================================================
    # CUSTOMERS: Customers
    # ===================================================================
    def _seed_customers(self, org):
        from apps.customers.models import Customer

        customer_data = [
            {'name': 'Burak Ozturk', 'email': 'burak@gmail.com', 'phone': '+90 541 111 22 33', 'source': 'QR_SCAN', 'total_orders': 12, 'total_spent': Decimal('1450.00')},
            {'name': 'Elif Sahin', 'email': 'elif.sahin@outlook.com', 'phone': '+90 542 222 33 44', 'source': 'QR_SCAN', 'total_orders': 8, 'total_spent': Decimal('920.00')},
            {'name': 'Emre Koc', 'email': 'emre.koc@gmail.com', 'phone': '+90 543 333 44 55', 'source': 'WEB', 'total_orders': 5, 'total_spent': Decimal('680.00')},
            {'name': 'Selin Yildiz', 'email': 'selin.y@hotmail.com', 'phone': '+90 544 444 55 66', 'source': 'QR_SCAN', 'total_orders': 15, 'total_spent': Decimal('2100.00')},
            {'name': 'Cem Dogan', 'email': 'cem.dogan@icloud.com', 'phone': '+90 545 555 66 77', 'source': 'STAFF', 'total_orders': 3, 'total_spent': Decimal('350.00')},
            {'name': 'Deniz Aktas', 'email': 'deniz.aktas@gmail.com', 'phone': '+90 546 666 77 88', 'source': 'QR_SCAN', 'total_orders': 7, 'total_spent': Decimal('890.00')},
            {'name': 'Gizem Polat', 'email': 'gizem.p@yahoo.com', 'phone': '+90 547 777 88 99', 'source': 'REFERRAL', 'total_orders': 4, 'total_spent': Decimal('520.00')},
            {'name': 'Hakan Erdogan', 'email': 'hakan.e@gmail.com', 'phone': '+90 548 888 99 00', 'source': 'QR_SCAN', 'total_orders': 20, 'total_spent': Decimal('3200.00')},
            {'name': 'Ipek Cetin', 'email': 'ipek.cetin@outlook.com', 'phone': '+90 549 999 00 11', 'source': 'WEB', 'total_orders': 2, 'total_spent': Decimal('190.00')},
            {'name': 'Kaan Arslan', 'email': 'kaan.a@gmail.com', 'phone': '+90 550 000 11 22', 'source': 'QR_SCAN', 'total_orders': 6, 'total_spent': Decimal('750.00')},
        ]

        customers = []
        for d in customer_data:
            c, created = Customer.objects.get_or_create(
                organization=org, email=d['email'],
                defaults={
                    **d,
                    'organization': org,
                    'loyalty_points_balance': random.randint(0, 500),
                    'first_visit_at': rand_past(120),
                    'last_visit_at': rand_recent(168),
                    'marketing_consent': random.choice([True, False]),
                },
            )
            customers.append(c)

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {len(customers)} customers'
        ))
        return customers

    # ===================================================================
    # ORDERS: Orders
    # ===================================================================
    def _seed_orders(self, org, tables, customers, staff_users):
        from apps.orders.models import Order

        if Order.objects.filter(organization=org).exists():
            self.stdout.write('  Orders exist, skipping')
            return list(Order.objects.filter(organization=org)[:10])

        order_statuses = [
            ('COMPLETED', 'PAID'),
            ('COMPLETED', 'PAID'),
            ('COMPLETED', 'PAID'),
            ('DELIVERED', 'PAID'),
            ('PREPARING', 'PENDING'),
            ('CONFIRMED', 'PENDING'),
            ('PENDING', 'PENDING'),
            ('CANCELLED', 'FAILED'),
            ('READY', 'PENDING'),
            ('COMPLETED', 'PAID'),
        ]

        orders = []
        for i in range(10):
            status, pay_status = order_statuses[i]
            table = random.choice(tables) if tables else None
            customer = random.choice(customers) if customers else None
            staff = random.choice(staff_users) if staff_users else None
            subtotal = Decimal(random.randint(80, 600))
            tax = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
            total = subtotal + tax

            placed_at = rand_past(30)
            o = Order.objects.create(
                organization=org,
                branch=table.branch if table else None,
                table=table,
                customer=customer,
                order_number=f'ORD-{1000 + i}',
                status=status,
                type=random.choice(['DINE_IN', 'DINE_IN', 'TAKEAWAY']),
                payment_status=pay_status,
                payment_method=random.choice([
                    'CASH', 'CREDIT_CARD', 'CREDIT_CARD', 'ONLINE',
                ]) if pay_status == 'PAID' else None,
                subtotal=subtotal,
                tax_amount=tax,
                total_amount=total,
                guest_count=random.randint(1, 4),
                placed_at=placed_at,
                placed_by=staff,
                assigned_to=staff,
                notes=random.choice([
                    '', '', 'Acele', 'Dogumlari kutluyorlar',
                    'Alerjisi var', '',
                ]),
            )
            # Set timestamps based on status
            if status in ('CONFIRMED', 'PREPARING', 'READY',
                          'DELIVERED', 'COMPLETED'):
                o.confirmed_at = placed_at + timedelta(minutes=2)
            if status in ('PREPARING', 'READY', 'DELIVERED', 'COMPLETED'):
                o.preparing_at = placed_at + timedelta(minutes=5)
            if status in ('READY', 'DELIVERED', 'COMPLETED'):
                o.ready_at = placed_at + timedelta(minutes=20)
            if status in ('DELIVERED', 'COMPLETED'):
                o.delivered_at = placed_at + timedelta(minutes=25)
            if status == 'COMPLETED':
                o.completed_at = placed_at + timedelta(minutes=60)
            if status == 'CANCELLED':
                o.cancelled_at = placed_at + timedelta(minutes=10)
                o.cancel_reason = 'Musteri iptal etti'
            o.save()
            orders.append(o)

        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(orders)} orders'))
        return orders

    # ===================================================================
    # ORDERS: Order Items
    # ===================================================================
    def _seed_order_items(self, orders):
        from apps.menu.models import Product
        from apps.orders.models import OrderItem

        if not orders:
            return

        products = list(Product.objects.filter(
            is_active=True, deleted_at__isnull=True
        )[:20])
        if not products:
            self.stdout.write('  No products found, skipping order items')
            return

        count = 0
        for order in orders:
            if OrderItem.objects.filter(order=order).exists():
                continue
            n_items = random.randint(1, 5)
            chosen = random.sample(products, min(n_items, len(products)))
            for product in chosen:
                qty = random.randint(1, 3)
                unit_price = product.base_price
                total = unit_price * qty
                item_status = order.status
                if item_status in ('COMPLETED', 'CANCELLED'):
                    item_status = 'DELIVERED' if order.status == 'COMPLETED' else 'CANCELLED'

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    unit_price=unit_price,
                    total_price=total,
                    status=item_status,
                    modifiers=[],
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} order items'))

    # ===================================================================
    # ORDERS: QR Scans
    # ===================================================================
    def _seed_qr_scans(self, org, qr_codes, customers):
        from apps.orders.models import QRScan

        if QRScan.objects.filter(organization=org).exists():
            self.stdout.write('  QR scans exist, skipping')
            return

        devices = ['MOBILE', 'MOBILE', 'MOBILE', 'TABLET', 'DESKTOP']
        browsers = ['Chrome', 'Safari', 'Samsung Internet', 'Firefox']
        oses = ['iOS 17', 'Android 14', 'Android 13', 'iOS 16', 'macOS 14']

        count = 0
        for qr in qr_codes[:8]:
            n_scans = random.randint(3, 8)
            for _ in range(n_scans):
                QRScan.objects.create(
                    qr_code=qr,
                    organization=org,
                    ip_address=f'{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}',
                    user_agent='Mozilla/5.0',
                    device_type=random.choice(devices),
                    browser=random.choice(browsers),
                    os=random.choice(oses),
                    country='TR',
                    city=random.choice(['Istanbul', 'Ankara', 'Izmir']),
                    is_unique=random.choice([True, True, False]),
                    customer=random.choice(customers) if customers and random.random() > 0.5 else None,
                    scanned_at=rand_past(30),
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} QR scans'))

    # ===================================================================
    # ORDERS: Service Requests
    # ===================================================================
    def _seed_service_requests(self, org, tables, customers, staff_users):
        from apps.orders.models import ServiceRequest

        if ServiceRequest.objects.filter(organization=org).exists():
            self.stdout.write('  Service requests exist, skipping')
            return

        types_msgs = [
            ('WAITER_CALL', 'Garson cagirildi'),
            ('BILL_REQUEST', 'Hesap istendi'),
            ('HELP', 'Menude yardim isteniyor'),
            ('WAITER_CALL', 'Su isteniyor'),
            ('BILL_REQUEST', 'Ayri hesap isteniyor'),
            ('HELP', 'Alerjen bilgisi sorgusu'),
            ('WAITER_CALL', 'Ekstra tabak isteniyor'),
            ('OTHER', 'Bebek sandalyesi isteniyor'),
        ]

        statuses_data = [
            ('COMPLETED', 120), ('COMPLETED', 85), ('COMPLETED', 200),
            ('IN_PROGRESS', None), ('PENDING', None),
            ('COMPLETED', 150), ('CANCELLED', None), ('PENDING', None),
        ]

        count = 0
        for i, (req_type, msg) in enumerate(types_msgs):
            if i >= len(tables):
                break
            status, resp_time = statuses_data[i]
            created_at = rand_recent(24)
            ServiceRequest.objects.create(
                organization=org,
                branch=tables[i].branch,
                table=tables[i],
                customer=random.choice(customers) if customers else None,
                type=req_type,
                status=status,
                message=msg,
                priority=random.randint(1, 5),
                assigned_to=random.choice(staff_users) if staff_users and status != 'PENDING' else None,
                response_time_seconds=resp_time,
                acknowledged_at=created_at + timedelta(seconds=30) if status != 'PENDING' else None,
                completed_at=created_at + timedelta(seconds=resp_time) if status == 'COMPLETED' and resp_time else None,
                cancelled_at=created_at + timedelta(minutes=5) if status == 'CANCELLED' else None,
                cancel_reason='Musteri ayrildi' if status == 'CANCELLED' else None,
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {count} service requests'
        ))

    # ===================================================================
    # CUSTOMERS: Visits
    # ===================================================================
    def _seed_customer_visits(self, org, customers, branches, tables):
        from apps.customers.models import CustomerVisit

        if CustomerVisit.objects.filter(organization=org).exists():
            self.stdout.write('  Customer visits exist, skipping')
            return

        sources = ['QR_SCAN', 'QR_SCAN', 'ORDER', 'CHECK_IN']
        count = 0
        for customer in customers[:8]:
            n_visits = random.randint(2, 6)
            for _ in range(n_visits):
                CustomerVisit.objects.create(
                    organization=org,
                    customer=customer,
                    branch=random.choice(branches) if branches else None,
                    visited_at=rand_past(60),
                    source=random.choice(sources),
                    table_id=random.choice(tables).id if tables else None,
                    duration_minutes=random.randint(20, 120),
                    ip_address=f'85.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}',
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} customer visits'))

    # ===================================================================
    # CUSTOMERS: Feedback
    # ===================================================================
    def _seed_feedback(self, org, customers, orders):
        from apps.customers.models import Feedback

        if Feedback.objects.filter(organization=org).exists():
            self.stdout.write('  Feedback exists, skipping')
            return

        feedback_data = [
            (5, 'FOOD', 'Harika lezzetler! Adana Kebap muhtesemdi.', 'RESPONDED', 'Tesekkurler, bizi tercih ettiginiz icin mutluyuz!'),
            (4, 'SERVICE', 'Garson cok ilgili, ama biraz beklettiler.', 'RESPONDED', 'Geri bildiriminiz icin tesekkurler, iyilestirmeye calisacagiz.'),
            (5, 'GENERAL', 'Her sey cok guzeldi, tekrar gelecegiz.', 'REVIEWED', None),
            (3, 'FOOD', 'Pizza biraz soguktu, ama lezzet iyiydi.', 'PENDING', None),
            (5, 'AMBIANCE', 'Dekorasyon ve atmosfer harika!', 'RESPONDED', 'Cok tesekkurler!'),
            (2, 'SERVICE', 'Cok uzun bekledik, servis yavas.', 'RESPONDED', 'Ozur dileriz, yogun saatlerde gecikme yasanabiliyor.'),
            (4, 'FOOD', 'Kunefe muhtesemdi! Kesinlikle tavsiye ederim.', 'REVIEWED', None),
            (5, 'VALUE', 'Fiyat performans orani cok iyi.', 'PENDING', None),
            (4, 'GENERAL', 'Guzel mekan, yemekler lezzetli.', 'ARCHIVED', None),
            (1, 'CLEANLINESS', 'Tuvalet temizligi yetersizdi.', 'RESPONDED', 'Geri bildiriminiz icin tesekkurler, hemen ilgileniyoruz.'),
        ]

        count = 0
        for i, (rating, f_type, comment, status, response) in enumerate(feedback_data):
            customer = customers[i] if i < len(customers) else None
            order = orders[i] if i < len(orders) else None
            Feedback.objects.create(
                organization=org,
                customer=customer,
                order_id=order.id if order else None,
                feedback_type=f_type,
                rating=rating,
                comment=comment,
                status=status,
                staff_response=response,
                responded_at=rand_recent(48) if response else None,
                is_public=rating >= 4,
                created_at=rand_past(45),
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} feedback entries'))

    # ===================================================================
    # CUSTOMERS: Loyalty Points
    # ===================================================================
    def _seed_loyalty_points(self, org, customers, orders):
        from apps.customers.models import LoyaltyPoint

        if LoyaltyPoint.objects.filter(organization=org).exists():
            self.stdout.write('  Loyalty points exist, skipping')
            return

        count = 0
        for customer in customers[:6]:
            balance = 0
            # Initial welcome bonus
            balance += 100
            LoyaltyPoint.objects.create(
                organization=org,
                customer=customer,
                transaction_type='BONUS',
                points=100,
                balance_after=balance,
                description='Hosgeldin bonusu',
                created_at=customer.first_visit_at or rand_past(90),
            )
            count += 1

            # Earned from orders
            for _ in range(random.randint(2, 5)):
                pts = random.randint(10, 80)
                balance += pts
                LoyaltyPoint.objects.create(
                    organization=org,
                    customer=customer,
                    transaction_type='EARNED',
                    points=pts,
                    balance_after=balance,
                    order_id=random.choice(orders).id if orders else None,
                    description=f'Siparis puani ({pts} puan)',
                    created_at=rand_past(60),
                )
                count += 1

            # One redemption
            if balance > 50:
                spent = random.randint(20, min(balance, 150))
                balance -= spent
                LoyaltyPoint.objects.create(
                    organization=org,
                    customer=customer,
                    transaction_type='REDEEMED',
                    points=-spent,
                    balance_after=balance,
                    description=f'{spent} puan harcandi',
                    created_at=rand_past(15),
                )
                count += 1

            # Update customer balance
            customer.loyalty_points_balance = balance
            customer.save(update_fields=['loyalty_points_balance'])

        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} loyalty points'))

    # ===================================================================
    # SUBSCRIPTIONS
    # ===================================================================
    def _seed_subscriptions(self, org):
        try:
            from apps.subscriptions.models import Invoice, Plan, Subscription
        except ImportError:
            self.stdout.write('  Subscriptions models not available, skipping')
            return

        plan = Plan.objects.filter(
            tier='GROWTH', is_active=True
        ).first()
        if not plan:
            plan = Plan.objects.filter(is_active=True).first()
        if not plan:
            self.stdout.write('  No plans found (run seed_plans), skipping')
            return

        sub, created = Subscription.objects.get_or_create(
            organization=org,
            defaults={
                'plan': plan,
                'status': 'ACTIVE',
                'billing_period': 'MONTHLY',
                'current_period_start': now() - timedelta(days=15),
                'current_period_end': now() + timedelta(days=15),
            },
        )
        if created:
            self.stdout.write(f'  Subscription: {plan.name}')

        # Invoices
        if not Invoice.objects.filter(subscription=sub).exists():
            for i in range(3):
                period_start = now() - timedelta(days=30 * (3 - i))
                period_end = period_start + timedelta(days=30)
                tax = (plan.price_monthly * Decimal('0.20')).quantize(Decimal('0.01'))
                total = plan.price_monthly + tax
                Invoice.objects.create(
                    organization=org,
                    subscription=sub,
                    invoice_number=f'INV-2026-{1000 + i}',
                    status='PAID' if i < 2 else 'PENDING',
                    period_start=period_start,
                    period_end=period_end,
                    amount_subtotal=plan.price_monthly,
                    amount_tax=tax,
                    amount_total=total,
                    amount_paid=total if i < 2 else Decimal('0'),
                    amount_refunded=Decimal('0'),
                    currency='TRY',
                    due_date=period_end,
                    paid_at=period_end - timedelta(days=2) if i < 2 else None,
                )
            self.stdout.write(self.style.SUCCESS('  ✓ 1 subscription + 3 invoices'))
        else:
            self.stdout.write('  Subscription/invoices exist, skipping')

    # ===================================================================
    # MEDIA
    # ===================================================================
    def _seed_media(self, org, owner):
        from apps.media.models import Media, MediaFolder

        # Folders
        folder_data = [
            ('Menu Gorselleri', 'menu-gorselleri', None, False),
            ('Logolar', 'logolar', None, False),
            ('Galeri', 'galeri', None, True),
            ('Sosyal Medya', 'sosyal-medya', None, True),
        ]

        folders = {}
        for name, slug, parent_slug, is_public in folder_data:
            parent = folders.get(parent_slug)
            f, created = MediaFolder.objects.get_or_create(
                organization=org, slug=slug, parent=parent,
                defaults={
                    'organization': org,
                    'name': name,
                    'is_public': is_public,
                },
            )
            folders[slug] = f

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {len(folders)} media folders'
        ))

        # Media files
        if Media.objects.filter(organization=org).exists():
            self.stdout.write('  Media files exist, skipping')
            return

        media_data = [
            {
                'name': 'Adana Kebap',
                'original_filename': 'adana-kebap.jpg',
                'folder': folders.get('menu-gorselleri'),
                'media_type': 'IMAGE',
                'mime_type': 'image/jpeg',
                'file_size': 245000,
                'width': 800, 'height': 600,
                'url': 'https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=600',
            },
            {
                'name': 'Burger Klasik',
                'original_filename': 'burger-classic.jpg',
                'folder': folders.get('menu-gorselleri'),
                'media_type': 'IMAGE',
                'mime_type': 'image/jpeg',
                'file_size': 312000,
                'width': 800, 'height': 600,
                'url': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600',
            },
            {
                'name': 'Restoran Logo',
                'original_filename': 'lezzet-sarayi-logo.png',
                'folder': folders.get('logolar'),
                'media_type': 'IMAGE',
                'mime_type': 'image/png',
                'file_size': 85000,
                'width': 512, 'height': 512,
                'url': 'https://via.placeholder.com/512x512/E85D04/fff?text=LS',
            },
            {
                'name': 'Bahce Gorunumu',
                'original_filename': 'bahce-gorunumu.jpg',
                'folder': folders.get('galeri'),
                'media_type': 'IMAGE',
                'mime_type': 'image/jpeg',
                'file_size': 520000,
                'width': 1200, 'height': 800,
                'url': 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800',
                'is_public': True,
            },
            {
                'name': 'Ic Mekan',
                'original_filename': 'ic-mekan.jpg',
                'folder': folders.get('galeri'),
                'media_type': 'IMAGE',
                'mime_type': 'image/jpeg',
                'file_size': 480000,
                'width': 1200, 'height': 800,
                'url': 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800',
                'is_public': True,
            },
            {
                'name': 'Sosyal Medya Banner',
                'original_filename': 'sm-banner.png',
                'folder': folders.get('sosyal-medya'),
                'media_type': 'IMAGE',
                'mime_type': 'image/png',
                'file_size': 150000,
                'width': 1080, 'height': 1080,
                'url': 'https://via.placeholder.com/1080x1080/E85D04/fff?text=Lezzet+Sarayi',
                'is_public': True,
            },
        ]

        count = 0
        for d in media_data:
            folder = d.pop('folder', None)
            Media.objects.create(
                organization=org,
                folder=folder,
                uploaded_by=owner,
                file_path=f'{org.id}/menu_items/{uuid.uuid4().hex[:12]}.jpg',
                storage='LOCAL',
                status='READY',
                alt_text=d['name'],
                title=d['name'],
                **d,
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} media files'))

    # ===================================================================
    # NOTIFICATIONS
    # ===================================================================
    def _seed_notifications(self, org, owner, staff_users):
        from apps.notifications.models import Notification

        if Notification.objects.filter(organization=org).exists():
            self.stdout.write('  Notifications exist, skipping')
            return

        notif_data = [
            {
                'user': owner,
                'notification_type': 'ORDER',
                'priority': 'HIGH',
                'title': 'Yeni siparis geldi!',
                'message': 'Masa 5\'ten yeni bir siparis alindi. Siparis #ORD-1005',
                'status': 'READ',
                'read_at': rand_recent(2),
            },
            {
                'user': owner,
                'notification_type': 'PAYMENT',
                'priority': 'NORMAL',
                'title': 'Odeme alindi',
                'message': 'Siparis #ORD-1003 icin ₺385.00 odeme basariyla alindi.',
                'status': 'READ',
                'read_at': rand_recent(6),
            },
            {
                'user': owner,
                'notification_type': 'SYSTEM',
                'priority': 'LOW',
                'title': 'Haftalik rapor hazir',
                'message': 'Bu haftanin performans raporu incelemeniz icin hazir.',
                'status': 'DELIVERED',
            },
            {
                'user': owner,
                'notification_type': 'FEEDBACK',
                'priority': 'NORMAL',
                'title': 'Yeni musteri yorumu',
                'message': 'Burak Ozturk 5 yildiz verdi: "Harika lezzetler!"',
                'status': 'SENT',
                'action_url': '/admin/customers/feedback/',
            },
            {
                'user': staff_users[0] if staff_users else owner,
                'notification_type': 'ORDER',
                'priority': 'URGENT',
                'title': 'Siparis iptal edildi',
                'message': 'Masa 3\'teki siparis musteri tarafindan iptal edildi.',
                'status': 'DELIVERED',
            },
            {
                'user': staff_users[0] if staff_users else owner,
                'notification_type': 'SYSTEM',
                'priority': 'NORMAL',
                'title': 'Menu guncellendi',
                'message': 'Ana Menu\'ye 3 yeni urun eklendi.',
                'status': 'READ',
                'read_at': rand_recent(12),
            },
            {
                'user': owner,
                'notification_type': 'SECURITY',
                'priority': 'HIGH',
                'title': 'Yeni cihazdan giris',
                'message': 'Hesabiniza yeni bir cihazdan giris yapildi (iPhone, Istanbul).',
                'status': 'READ',
                'read_at': rand_recent(24),
            },
            {
                'user': owner,
                'notification_type': 'PROMOTION',
                'priority': 'LOW',
                'title': 'Yeni ozellik: AI Icerik Uretimi',
                'message': 'Artik AI ile otomatik urun aciklamasi olusturabilirsiniz!',
                'status': 'PENDING',
                'scheduled_for': now() + timedelta(hours=6),
            },
            {
                'user': staff_users[1] if len(staff_users) > 1 else owner,
                'notification_type': 'ORDER',
                'priority': 'HIGH',
                'title': 'Garson cagrisi - Masa 7',
                'message': 'Masa 7\'den garson cagrisi yapildi.',
                'status': 'SENT',
            },
            {
                'user': owner,
                'notification_type': 'PAYMENT',
                'priority': 'URGENT',
                'title': 'Abonelik odeme hatirlatmasi',
                'message': 'Growth planinin aylık ödemesi 3 gun icinde doluyor.',
                'status': 'PENDING',
            },
        ]

        count = 0
        for d in notif_data:
            sent_at = rand_recent(48)
            Notification.objects.create(
                organization=org,
                channel='IN_APP',
                sent_at=sent_at if d['status'] != 'PENDING' else None,
                delivered_at=sent_at + timedelta(seconds=5) if d['status'] in ('DELIVERED', 'READ') else None,
                **d,
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {count} notifications'
        ))
