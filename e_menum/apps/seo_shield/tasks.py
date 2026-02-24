"""
Celery tasks for the SEO Shield application.

Periodic tasks for shield maintenance and reporting:
    - decay_risk_scores:      Gradually reduce IP risk scores over time
    - cleanup_block_logs:     Delete old block log entries
    - verify_bot_whitelist:   Re-verify bot whitelist entries via DNS
    - generate_shield_report: Generate daily shield activity report

Task schedule (configured in config/celery.py):
    - decay_risk_scores:      every 6 hours
    - cleanup_block_logs:     daily at 05:00 UTC
    - verify_bot_whitelist:   daily at 06:00 UTC
    - generate_shield_report: daily at 07:00 UTC
"""

import logging
import socket
from datetime import timedelta

from celery import shared_task
from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger('apps.seo_shield')


# =============================================================================
# RISK SCORE DECAY
# =============================================================================

@shared_task(
    bind=True,
    name='seo_shield.decay_risk_scores',
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=300,
    time_limit=600,
)
def decay_risk_scores(self, decay_factor: float = 0.9):
    """
    Decay all IP risk scores by a configurable factor.

    Calls IPReputationManager.decay_scores() to gradually reduce risk
    scores for IPs that have stopped misbehaving. This ensures that
    temporarily flagged IPs can recover over time.

    Args:
        decay_factor: Multiplier applied to each signal value (default 0.9).
                      0.9 means scores decay by 10% per cycle.

    Returns:
        dict: Summary with records_updated count and decay_factor used.
    """
    from apps.seo_shield.ip_reputation import IPReputationManager

    logger.info(
        'Starting risk score decay with factor %.2f',
        decay_factor,
    )

    try:
        manager = IPReputationManager()
        updated_count = manager.decay_scores(decay_factor=decay_factor)

        summary = {
            'records_updated': updated_count,
            'decay_factor': decay_factor,
        }
        logger.info(
            'Risk score decay complete: %d records updated (factor=%.2f)',
            updated_count, decay_factor,
        )
        return summary

    except Exception as exc:
        logger.exception('Risk score decay failed: %s', exc)
        raise self.retry(exc=exc)


# =============================================================================
# BLOCK LOG CLEANUP
# =============================================================================

@shared_task(
    bind=True,
    name='seo_shield.cleanup_block_logs',
    max_retries=1,
    default_retry_delay=120,
    soft_time_limit=300,
    time_limit=600,
)
def cleanup_block_logs(self, retention_days: int = 30):
    """
    Delete BlockLog entries older than the retention period.

    Block logs are append-only audit records. To prevent unbounded
    storage growth, this task permanently deletes entries older than
    the configured retention period (default 30 days).

    Args:
        retention_days: Number of days to retain logs (default 30).

    Returns:
        dict: Summary with logs_deleted count and cutoff_date.
    """
    from apps.seo_shield.models import BlockLog

    cutoff_date = timezone.now() - timedelta(days=retention_days)

    # Use a queryset delete for efficiency
    old_logs = BlockLog.objects.filter(created_at__lt=cutoff_date)
    count = old_logs.count()

    if count > 0:
        # Delete in batches to avoid long-running transactions
        deleted_total = 0
        batch_size = 5000
        while True:
            batch_ids = list(
                BlockLog.objects.filter(
                    created_at__lt=cutoff_date,
                ).values_list('id', flat=True)[:batch_size]
            )
            if not batch_ids:
                break
            deleted, _ = BlockLog.objects.filter(id__in=batch_ids).delete()
            deleted_total += deleted
            logger.debug('Deleted batch of %d block logs', deleted)

        logger.info(
            'Block log cleanup complete: %d entries deleted (older than %s)',
            deleted_total, cutoff_date.strftime('%Y-%m-%d'),
        )
        count = deleted_total
    else:
        logger.info('No block logs older than %d days found for cleanup', retention_days)

    return {
        'logs_deleted': count,
        'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
        'retention_days': retention_days,
    }


# =============================================================================
# BOT WHITELIST VERIFICATION
# =============================================================================

@shared_task(
    bind=True,
    name='seo_shield.verify_bot_whitelist',
    max_retries=1,
    default_retry_delay=120,
    soft_time_limit=300,
    time_limit=600,
)
def verify_bot_whitelist(self):
    """
    Re-verify all active bot whitelist entries.

    For each active BotWhitelist entry with DNS verification method,
    attempts a DNS lookup of the configured domain to confirm it is
    still valid. Updates the last_verified timestamp on success.

    Returns:
        dict: Summary with total_checked, verified, and failed counts.
    """
    from apps.seo_shield.models import BotWhitelist

    now = timezone.now()
    entries = BotWhitelist.objects.filter(is_active=True)

    total_checked = 0
    verified_count = 0
    failed_count = 0
    results = []

    for entry in entries:
        total_checked += 1

        if entry.verification_method == BotWhitelist.VerificationMethod.DNS and entry.dns_domain:
            # Attempt DNS resolution of the bot's domain
            try:
                socket.gethostbyname(entry.dns_domain)
                entry.last_verified = now
                entry.save(update_fields=['last_verified', 'updated_at'])
                verified_count += 1
                results.append({
                    'name': entry.name,
                    'status': 'verified',
                    'domain': entry.dns_domain,
                })
                logger.debug(
                    'Bot whitelist verified via DNS: %s (%s)',
                    entry.name, entry.dns_domain,
                )
            except (socket.gaierror, socket.herror, OSError) as exc:
                failed_count += 1
                results.append({
                    'name': entry.name,
                    'status': 'failed',
                    'domain': entry.dns_domain,
                    'error': str(exc),
                })
                logger.warning(
                    'Bot whitelist DNS verification failed for %s (%s): %s',
                    entry.name, entry.dns_domain, exc,
                )

        elif entry.verification_method == BotWhitelist.VerificationMethod.IP_RANGE:
            # IP range bots don't need periodic re-verification
            entry.last_verified = now
            entry.save(update_fields=['last_verified', 'updated_at'])
            verified_count += 1
            results.append({
                'name': entry.name,
                'status': 'verified',
                'method': 'ip_range',
            })

        elif entry.verification_method == BotWhitelist.VerificationMethod.USER_AGENT:
            # User-Agent only bots are always considered verified
            entry.last_verified = now
            entry.save(update_fields=['last_verified', 'updated_at'])
            verified_count += 1
            results.append({
                'name': entry.name,
                'status': 'verified',
                'method': 'user_agent',
            })

    summary = {
        'total_checked': total_checked,
        'verified': verified_count,
        'failed': failed_count,
        'details': results,
    }
    logger.info(
        'Bot whitelist verification complete: %d checked, %d verified, %d failed',
        total_checked, verified_count, failed_count,
    )
    return summary


# =============================================================================
# SHIELD REPORT GENERATION
# =============================================================================

@shared_task(
    bind=True,
    name='seo_shield.generate_shield_report',
    max_retries=1,
    default_retry_delay=60,
    soft_time_limit=120,
    time_limit=300,
)
def generate_shield_report(self):
    """
    Generate a daily shield activity report.

    Aggregates the last 24 hours of shield activity including:
    - Total requests blocked, challenged, throttled, logged
    - Top 10 blocked IPs by occurrence
    - Top 5 block reasons by frequency
    - Risk score distribution across all tracked IPs

    The report is logged at INFO level for monitoring and alerting
    integration. Can be extended to send email or Slack notifications.

    Returns:
        dict: Full report data structure.
    """
    from apps.seo_shield.models import BlockLog, IPRiskScore

    now = timezone.now()
    last_24h = now - timedelta(hours=24)

    # -- Action breakdown --
    action_counts = dict(
        BlockLog.objects.filter(
            created_at__gte=last_24h,
        ).values_list('action_taken').annotate(
            count=Count('id'),
        ).values_list('action_taken', 'count')
    )

    total_actions = sum(action_counts.values())

    # -- Top IPs --
    top_ips = list(
        BlockLog.objects.filter(
            created_at__gte=last_24h,
        ).values('ip_address').annotate(
            count=Count('id'),
        ).order_by('-count')[:10]
    )

    # -- Top reasons --
    top_reasons = list(
        BlockLog.objects.filter(
            created_at__gte=last_24h,
        ).values('reason').annotate(
            count=Count('id'),
        ).order_by('-count')[:5]
    )

    # -- Risk score distribution --
    risk_distribution = {
        'low_0_29': IPRiskScore.objects.filter(
            risk_score__gte=0, risk_score__lt=30,
        ).count(),
        'medium_30_59': IPRiskScore.objects.filter(
            risk_score__gte=30, risk_score__lt=60,
        ).count(),
        'high_60_100': IPRiskScore.objects.filter(
            risk_score__gte=60,
        ).count(),
        'whitelisted': IPRiskScore.objects.filter(
            is_whitelisted=True,
        ).count(),
        'blacklisted': IPRiskScore.objects.filter(
            is_blacklisted=True,
        ).count(),
    }

    total_tracked_ips = IPRiskScore.objects.count()

    report = {
        'period': {
            'start': last_24h.isoformat(),
            'end': now.isoformat(),
        },
        'summary': {
            'total_actions': total_actions,
            'blocked': action_counts.get('blocked', 0),
            'challenged': action_counts.get('challenged', 0),
            'throttled': action_counts.get('throttled', 0),
            'logged': action_counts.get('logged', 0),
        },
        'top_ips': top_ips,
        'top_reasons': top_reasons,
        'risk_distribution': risk_distribution,
        'total_tracked_ips': total_tracked_ips,
    }

    # Log the report
    logger.info(
        'Shield Daily Report (%s to %s)\n'
        '  Total actions: %d (blocked=%d, challenged=%d, throttled=%d, logged=%d)\n'
        '  Top IPs: %s\n'
        '  Top reasons: %s\n'
        '  Risk distribution: low=%d, medium=%d, high=%d\n'
        '  Tracked IPs: %d (whitelisted=%d, blacklisted=%d)',
        last_24h.strftime('%Y-%m-%d %H:%M'),
        now.strftime('%Y-%m-%d %H:%M'),
        total_actions,
        action_counts.get('blocked', 0),
        action_counts.get('challenged', 0),
        action_counts.get('throttled', 0),
        action_counts.get('logged', 0),
        ', '.join(f"{ip['ip_address']}({ip['count']})" for ip in top_ips[:5]),
        ', '.join(f"{r['reason']}({r['count']})" for r in top_reasons),
        risk_distribution['low_0_29'],
        risk_distribution['medium_30_59'],
        risk_distribution['high_60_100'],
        total_tracked_ips,
        risk_distribution['whitelisted'],
        risk_distribution['blacklisted'],
    )

    return report
