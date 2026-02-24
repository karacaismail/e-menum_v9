"""
Management command to display current SEO Shield status.

Shows:
- IP tracking statistics (total, high-risk, whitelisted, blacklisted)
- BlockLog stats (today's totals, by reason, by action)
- Active bot whitelist entries
- Active rule sets

Usage:
    python manage.py shield_status
"""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Show current SEO Shield status and statistics'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n=========================================='
        ))
        self.stdout.write(self.style.MIGRATE_HEADING(
            '  Shield Status Report'
        ))
        self.stdout.write(self.style.MIGRATE_HEADING(
            '==========================================\n'
        ))

        self._show_ip_stats()
        self._show_block_log_stats()
        self._show_bot_whitelist()
        self._show_rule_sets()

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n=========================================='
        ))
        self.stdout.write(self.style.SUCCESS(
            '  Status report complete.'
        ))
        self.stdout.write(self.style.MIGRATE_HEADING(
            '==========================================\n'
        ))

    # ──────────────────────────────────────────────────────────────
    # IP Statistics
    # ──────────────────────────────────────────────────────────────

    def _show_ip_stats(self):
        self.stdout.write(self.style.HTTP_INFO('--- IP Tracking ---'))

        from apps.seo_shield.models import IPRiskScore

        total = IPRiskScore.objects.count()
        block_threshold = getattr(settings, 'SHIELD_BLOCK_THRESHOLD', 80)

        high_risk = IPRiskScore.objects.filter(
            risk_score__gte=block_threshold
        ).count()

        whitelisted = IPRiskScore.objects.filter(
            is_whitelisted=True
        ).count()

        blacklisted = IPRiskScore.objects.filter(
            is_blacklisted=True
        ).count()

        self.stdout.write(f'  Total IPs tracked: {total}')

        if high_risk > 0:
            self.stdout.write(self.style.WARNING(
                f'  IPs above threshold (>= {block_threshold}): {high_risk}'
            ))
        else:
            self.stdout.write(
                f'  IPs above threshold (>= {block_threshold}): 0'
            )

        self.stdout.write(f'  Whitelisted: {whitelisted}')
        self.stdout.write(f'  Blacklisted: {blacklisted}')
        self.stdout.write('')

    # ──────────────────────────────────────────────────────────────
    # Block Log Statistics
    # ──────────────────────────────────────────────────────────────

    def _show_block_log_stats(self):
        self.stdout.write(self.style.HTTP_INFO('--- Block Log (Today) ---'))

        from apps.seo_shield.models import BlockLog

        today_start = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        today_logs = BlockLog.objects.filter(created_at__gte=today_start)
        total_today = today_logs.count()

        self.stdout.write(f'  Total actions today: {total_today}')

        if total_today > 0:
            # By reason
            by_reason = today_logs.values('reason').annotate(
                count=Count('id')
            ).order_by('-count')

            self.stdout.write('')
            self.stdout.write('  By reason:')
            for entry in by_reason:
                self.stdout.write(
                    f'    - {entry["reason"]}: {entry["count"]}'
                )

            # By action taken
            by_action = today_logs.values('action_taken').annotate(
                count=Count('id')
            ).order_by('-count')

            self.stdout.write('')
            self.stdout.write('  By action:')
            for entry in by_action:
                self.stdout.write(
                    f'    - {entry["action_taken"]}: {entry["count"]}'
                )

        self.stdout.write('')

    # ──────────────────────────────────────────────────────────────
    # Bot Whitelist
    # ──────────────────────────────────────────────────────────────

    def _show_bot_whitelist(self):
        self.stdout.write(self.style.HTTP_INFO('--- Bot Whitelist ---'))

        from apps.seo_shield.models import BotWhitelist

        active_bots = BotWhitelist.objects.filter(is_active=True)
        total_active = active_bots.count()
        total_inactive = BotWhitelist.objects.filter(
            is_active=False
        ).count()

        self.stdout.write(f'  Active entries: {total_active}')
        self.stdout.write(f'  Inactive entries: {total_inactive}')

        if total_active > 0:
            self.stdout.write('')
            self.stdout.write('  Active bots:')
            for bot in active_bots:
                verified_info = ''
                if bot.last_verified:
                    verified_info = (
                        f', last verified: '
                        f'{bot.last_verified.strftime("%Y-%m-%d %H:%M")}'
                    )
                self.stdout.write(
                    f'    - {bot.name} '
                    f'(verify: {bot.get_verification_method_display()}'
                    f'{verified_info})'
                )

        self.stdout.write('')

    # ──────────────────────────────────────────────────────────────
    # Rule Sets
    # ──────────────────────────────────────────────────────────────

    def _show_rule_sets(self):
        self.stdout.write(self.style.HTTP_INFO('--- Rule Sets ---'))

        from apps.seo_shield.models import RuleSet

        active_rules = RuleSet.objects.filter(is_active=True)
        total_active = active_rules.count()
        total_inactive = RuleSet.objects.filter(
            is_active=False
        ).count()

        self.stdout.write(f'  Active rule sets: {total_active}')
        self.stdout.write(f'  Inactive rule sets: {total_inactive}')

        if total_active > 0:
            self.stdout.write('')
            self.stdout.write('  Active rules (by priority):')
            for rule in active_rules.order_by('priority'):
                match_info = ''
                if rule.match_count > 0:
                    match_info = f', {rule.match_count} matches'
                self.stdout.write(
                    f'    - [{rule.priority}] {rule.name} '
                    f'(action: {rule.get_action_display()}{match_info})'
                )

        self.stdout.write('')
