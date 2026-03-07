"""
Management command to seed default SEO Shield data.

Creates:
- BotWhitelist entries for major search engine and social media bots
- Default RuleSet entries for common security patterns

Usage:
    python manage.py seed_shield_data
    python manage.py seed_shield_data --clear
"""

import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Seed default Shield data (bot whitelist, rule sets)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing Shield seed data before re-creating",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\nSeeding Shield data...\n"))

        if options["clear"]:
            self._clear()

        bot_count = self._seed_bot_whitelist()
        rule_count = self._seed_rule_sets()

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Shield seed complete: "
                f"{bot_count} bot whitelist entries, "
                f"{rule_count} rule sets"
            )
        )

    # ──────────────────────────────────────────────────────────────
    # Clear
    # ──────────────────────────────────────────────────────────────

    def _clear(self):
        from apps.seo_shield.models import BotWhitelist, RuleSet

        bot_deleted, _ = BotWhitelist.objects.all().delete()
        rule_deleted, _ = RuleSet.all_objects.all().delete()

        self.stdout.write(
            self.style.WARNING(
                f"  Cleared {bot_deleted} bot whitelist entries, "
                f"{rule_deleted} rule sets"
            )
        )

    # ──────────────────────────────────────────────────────────────
    # Bot Whitelist
    # ──────────────────────────────────────────────────────────────

    def _seed_bot_whitelist(self):
        from apps.seo_shield.models import BotWhitelist

        bots = [
            {
                "name": "Googlebot",
                "user_agent_pattern": r"Googlebot|Googlebot-Image|Googlebot-News|Googlebot-Video|Storebot-Google|Google-InspectionTool",
                "dns_domain": "googlebot.com",
                "verification_method": BotWhitelist.VerificationMethod.DNS,
                "is_active": True,
                "ip_ranges": [],
            },
            {
                "name": "Bingbot",
                "user_agent_pattern": r"bingbot|msnbot|BingPreview",
                "dns_domain": "search.msn.com",
                "verification_method": BotWhitelist.VerificationMethod.DNS,
                "is_active": True,
                "ip_ranges": [],
            },
            {
                "name": "DuckDuckBot",
                "user_agent_pattern": r"DuckDuckBot",
                "dns_domain": "duckduckgo.com",
                "verification_method": BotWhitelist.VerificationMethod.IP_RANGE,
                "is_active": True,
                "ip_ranges": [
                    "20.191.45.212/32",
                    "40.88.21.235/32",
                    "40.76.173.151/32",
                    "40.76.163.7/32",
                    "20.185.79.47/32",
                ],
            },
            {
                "name": "YandexBot",
                "user_agent_pattern": r"YandexBot|YandexImages|YandexAccessibilityBot",
                "dns_domain": "yandex.ru",
                "verification_method": BotWhitelist.VerificationMethod.DNS,
                "is_active": True,
                "ip_ranges": [],
            },
            {
                "name": "Baiduspider",
                "user_agent_pattern": r"Baiduspider|Baiduspider-image|Baiduspider-video",
                "dns_domain": "baidu.com",
                "verification_method": BotWhitelist.VerificationMethod.DNS,
                "is_active": True,
                "ip_ranges": [],
            },
            {
                "name": "Facebook",
                "user_agent_pattern": r"facebookexternalhit|facebookcatalog|Facebot",
                "dns_domain": "facebook.com",
                "verification_method": BotWhitelist.VerificationMethod.USER_AGENT,
                "is_active": True,
                "ip_ranges": [],
            },
            {
                "name": "Twitterbot",
                "user_agent_pattern": r"Twitterbot",
                "dns_domain": "twitter.com",
                "verification_method": BotWhitelist.VerificationMethod.USER_AGENT,
                "is_active": True,
                "ip_ranges": [],
            },
            {
                "name": "LinkedInBot",
                "user_agent_pattern": r"LinkedInBot",
                "dns_domain": "linkedin.com",
                "verification_method": BotWhitelist.VerificationMethod.USER_AGENT,
                "is_active": True,
                "ip_ranges": [],
            },
        ]

        count = 0
        for bot_data in bots:
            obj, created = BotWhitelist.objects.get_or_create(
                name=bot_data["name"],
                defaults=bot_data,
            )
            if created:
                count += 1
                self.stdout.write(
                    f"  BotWhitelist: {obj.name} "
                    f"(verify: {obj.get_verification_method_display()})"
                )
            else:
                self.stdout.write(
                    f"  BotWhitelist: {obj.name} (already exists, skipped)"
                )

        self.stdout.write(
            self.style.SUCCESS(f"  -> {count} bot whitelist entries created")
        )
        return count

    # ──────────────────────────────────────────────────────────────
    # Rule Sets
    # ──────────────────────────────────────────────────────────────

    def _seed_rule_sets(self):
        from apps.seo_shield.models import RuleSet

        rule_sets = [
            {
                "name": "Block Scanner UAs",
                "description": (
                    "Blocks requests from known vulnerability scanner "
                    "and attack tool user agents such as sqlmap, nikto, "
                    "nmap, and similar automated scanners."
                ),
                "rules": [
                    {
                        "field": "user_agent",
                        "operator": "regex_match",
                        "value": r"sqlmap|nikto|nmap|masscan|ZmEu|w3af|Acunetix|Nessus|OpenVAS|dirbuster|gobuster|nuclei|httpx|subfinder",
                        "description": "Known vulnerability scanner UA patterns",
                    },
                ],
                "is_active": True,
                "priority": 10,
                "action": RuleSet.Action.BLOCK,
            },
            {
                "name": "Log Suspicious Paths",
                "description": (
                    "Logs access attempts to sensitive or commonly probed "
                    "paths such as wp-admin, .env, .git, and phpMyAdmin. "
                    "These are typically targeted by automated scanners."
                ),
                "rules": [
                    {
                        "field": "path",
                        "operator": "regex_match",
                        "value": r"\.(env|git|svn|htaccess|htpasswd|DS_Store)|wp-admin|wp-login|phpMyAdmin|phpmyadmin|administrator|xmlrpc\.php|/\.well-known/(?!security\.txt|acme-challenge)",
                        "description": "Commonly probed sensitive paths",
                    },
                ],
                "is_active": True,
                "priority": 50,
                "action": RuleSet.Action.LOG,
            },
            {
                "name": "Rate Limit Violators",
                "description": (
                    "Throttles IPs that have been flagged for exceeding "
                    "rate limits. Applied to repeat offenders who continue "
                    "sending excessive traffic after initial rate limiting."
                ),
                "rules": [
                    {
                        "field": "risk_score",
                        "operator": "gte",
                        "value": 60,
                        "description": "IPs with elevated risk score from rate limiting",
                    },
                    {
                        "field": "signal",
                        "operator": "has_key",
                        "value": "rate_limit",
                        "description": "IP must have a rate_limit signal",
                    },
                ],
                "is_active": True,
                "priority": 30,
                "action": RuleSet.Action.THROTTLE,
            },
        ]

        count = 0
        for rule_data in rule_sets:
            obj, created = RuleSet.objects.get_or_create(
                name=rule_data["name"],
                defaults=rule_data,
            )
            if created:
                count += 1
                self.stdout.write(
                    f'  RuleSet: "{obj.name}" '
                    f"(priority: {obj.priority}, action: {obj.get_action_display()})"
                )
            else:
                self.stdout.write(f'  RuleSet: "{obj.name}" (already exists, skipped)')

        self.stdout.write(self.style.SUCCESS(f"  -> {count} rule sets created"))
        return count
