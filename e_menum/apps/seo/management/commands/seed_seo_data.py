"""
Management command to seed default SEO data.

Creates:
- TXTFileConfig entries for each file type (robots, humans, security, ads, llms)
- Example Redirect entries for common old URL patterns

Usage:
    python manage.py seed_seo_data
    python manage.py seed_seo_data --clear
"""

import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Seed default SEO data (TXT file configs, example redirects)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing SEO seed data before re-creating",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\nSeeding SEO data...\n"))

        if options["clear"]:
            self._clear()

        txt_count = self._seed_txt_file_configs()
        redirect_count = self._seed_redirects()

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"SEO seed complete: "
                f"{txt_count} TXT configs, "
                f"{redirect_count} redirects"
            )
        )

    # ──────────────────────────────────────────────────────────────
    # Clear
    # ──────────────────────────────────────────────────────────────

    def _clear(self):
        from apps.seo.models import Redirect, TXTFileConfig

        txt_deleted, _ = TXTFileConfig.objects.all().delete()
        redirect_deleted, _ = Redirect.all_objects.all().delete()

        self.stdout.write(
            self.style.WARNING(
                f"  Cleared {txt_deleted} TXT configs, {redirect_deleted} redirects"
            )
        )

    # ──────────────────────────────────────────────────────────────
    # TXT File Configs
    # ──────────────────────────────────────────────────────────────

    def _seed_txt_file_configs(self):
        from apps.seo.models import TXTFileConfig, TXTFileType

        configs = [
            {
                "file_type": TXTFileType.ROBOTS,
                "content": (
                    "User-agent: *\n"
                    "Allow: /\n"
                    "Disallow: /admin/\n"
                    "Disallow: /api/\n"
                    "Disallow: /accounts/\n"
                    "Disallow: /dashboard/\n"
                    "\n"
                    "Sitemap: https://e-menum.net/sitemap.xml\n"
                ),
                "auto_generate": True,
                "is_active": True,
            },
            {
                "file_type": TXTFileType.HUMANS,
                "content": (
                    "/* TEAM */\n"
                    "Developer: E-Menum Engineering\n"
                    "Contact: dev@e-menum.net\n"
                    "Location: Istanbul, Turkey\n"
                    "\n"
                    "/* SITE */\n"
                    "Last update: 2026/01/31\n"
                    "Language: Turkish, English\n"
                    "Standards: HTML5, CSS3\n"
                    "Framework: Django\n"
                    "Components: Tailwind CSS, Alpine.js\n"
                ),
                "auto_generate": True,
                "is_active": True,
            },
            {
                "file_type": TXTFileType.SECURITY,
                "content": (
                    "Contact: mailto:security@e-menum.net\n"
                    "Expires: 2027-01-31T23:59:00.000Z\n"
                    "Preferred-Languages: tr, en\n"
                    "Canonical: https://e-menum.net/.well-known/security.txt\n"
                    "Policy: https://e-menum.net/security-policy\n"
                ),
                "auto_generate": False,
                "is_active": True,
            },
            {
                "file_type": TXTFileType.ADS,
                "content": (
                    "# ads.txt - Authorized Digital Sellers\n"
                    "# E-Menum does not currently run programmatic ads.\n"
                    "# This file is intentionally minimal.\n"
                ),
                "auto_generate": False,
                "is_active": True,
            },
            {
                "file_type": TXTFileType.LLMS,
                "content": (
                    "# E-Menum - Dijital QR Menu Platformu\n"
                    "\n"
                    "## Overview\n"
                    "E-Menum is an AI-powered digital menu platform for restaurants\n"
                    "and cafes in Turkey. It provides QR code menus, analytics,\n"
                    "and AI content generation for F&B businesses.\n"
                    "\n"
                    "## Key Features\n"
                    "- QR Code digital menus\n"
                    "- AI-powered content generation\n"
                    "- Real-time analytics and reporting\n"
                    "- Multi-branch management\n"
                    "- Customer loyalty programs\n"
                    "\n"
                    "## Contact\n"
                    "Website: https://e-menum.net\n"
                    "Support: destek@e-menum.net\n"
                ),
                "auto_generate": True,
                "is_active": True,
            },
        ]

        count = 0
        for config_data in configs:
            obj, created = TXTFileConfig.objects.get_or_create(
                file_type=config_data["file_type"],
                defaults=config_data,
            )
            if created:
                count += 1
                self.stdout.write(f"  TXTFileConfig: {obj.get_file_type_display()}")
            else:
                self.stdout.write(
                    f"  TXTFileConfig: {obj.get_file_type_display()} "
                    f"(already exists, skipped)"
                )

        self.stdout.write(self.style.SUCCESS(f"  -> {count} TXT file configs created"))
        return count

    # ──────────────────────────────────────────────────────────────
    # Redirects
    # ──────────────────────────────────────────────────────────────

    def _seed_redirects(self):
        from apps.seo.models import Redirect, RedirectType

        redirects = [
            {
                "source_path": "/hakkimizda",
                "target_path": "/about",
                "redirect_type": RedirectType.PERMANENT,
                "is_active": True,
                "note": "Legacy Turkish URL redirected to new about page",
            },
            {
                "source_path": "/blog/dijital-menu-nedir",
                "target_path": "/blog/qr-menu-rehberi",
                "redirect_type": RedirectType.PERMANENT,
                "is_active": True,
                "note": "Old blog post slug consolidated into comprehensive guide",
            },
            {
                "source_path": "/fiyatlandirma",
                "target_path": "/pricing",
                "redirect_type": RedirectType.PERMANENT,
                "is_active": True,
                "note": "Legacy Turkish pricing page URL to new path",
            },
            {
                "source_path": "/demo-talep",
                "target_path": "/demo",
                "redirect_type": RedirectType.PERMANENT,
                "is_active": True,
                "note": "Old demo request form URL simplified",
            },
            {
                "source_path": "/iletisim",
                "target_path": "/contact",
                "redirect_type": RedirectType.PERMANENT,
                "is_active": True,
                "note": "Legacy Turkish contact page URL to new path",
            },
        ]

        count = 0
        for redirect_data in redirects:
            obj, created = Redirect.objects.get_or_create(
                source_path=redirect_data["source_path"],
                defaults=redirect_data,
            )
            if created:
                count += 1
                self.stdout.write(f"  Redirect: {obj.source_path} -> {obj.target_path}")
            else:
                self.stdout.write(
                    f"  Redirect: {obj.source_path} (already exists, skipped)"
                )

        self.stdout.write(self.style.SUCCESS(f"  -> {count} redirects created"))
        return count
