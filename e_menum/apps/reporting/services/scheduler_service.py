"""
Scheduler Service for report scheduling.

Manages report schedule lifecycle:
    - Calculate next run times based on frequency
    - Get due schedules
    - Deliver report results via configured channels

Usage:
    scheduler = SchedulerService()
    next_run = scheduler.calculate_next_run(schedule)
    scheduler.deliver_report(execution, channels, emails)
"""

import logging
from datetime import datetime, timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for managing report schedules and delivery.
    """

    def calculate_next_run(self, schedule) -> datetime:
        """
        Calculate the next run time for a schedule based on its frequency.

        Args:
            schedule: ReportSchedule instance

        Returns:
            datetime: Timezone-aware next run time
        """
        now = timezone.now()
        trigger_time = schedule.trigger_time

        # Base: today at trigger_time
        base_date = now.date()
        base_dt = timezone.make_aware(
            datetime.combine(base_date, trigger_time),
            timezone.get_current_timezone(),
        )

        # If the base time is in the past, move to next possible slot
        if base_dt <= now:
            base_date += timedelta(days=1)
            base_dt = timezone.make_aware(
                datetime.combine(base_date, trigger_time),
                timezone.get_current_timezone(),
            )

        frequency = schedule.frequency

        if frequency == 'DAILY':
            return base_dt

        elif frequency == 'WEEKLY':
            day_of_week = schedule.trigger_day_of_week or 0  # Monday default
            current_dow = base_date.weekday()
            days_until = (day_of_week - current_dow) % 7
            if days_until == 0 and base_dt <= now:
                days_until = 7
            target_date = base_date + timedelta(days=days_until)
            return timezone.make_aware(
                datetime.combine(target_date, trigger_time),
                timezone.get_current_timezone(),
            )

        elif frequency == 'BIWEEKLY':
            day_of_week = schedule.trigger_day_of_week or 0
            current_dow = base_date.weekday()
            days_until = (day_of_week - current_dow) % 7
            if days_until == 0 and base_dt <= now:
                days_until = 14
            elif days_until > 0:
                # Check if next occurrence is within 2 weeks
                pass
            target_date = base_date + timedelta(days=days_until)
            # Ensure at least 2 weeks from last run
            if schedule.last_run_at:
                min_date = (schedule.last_run_at + timedelta(days=13)).date()
                if target_date < min_date:
                    target_date = min_date
                    # Adjust to correct day of week
                    current_dow = target_date.weekday()
                    days_until = (day_of_week - current_dow) % 7
                    target_date += timedelta(days=days_until)
            return timezone.make_aware(
                datetime.combine(target_date, trigger_time),
                timezone.get_current_timezone(),
            )

        elif frequency == 'MONTHLY':
            day_of_month = schedule.trigger_day_of_month or 1
            # Clamp to valid range
            day_of_month = min(day_of_month, 28)

            year = base_date.year
            month = base_date.month

            target_date = base_date.replace(day=day_of_month)
            if target_date <= now.date():
                # Move to next month
                month += 1
                if month > 12:
                    month = 1
                    year += 1
                target_date = target_date.replace(year=year, month=month)

            return timezone.make_aware(
                datetime.combine(target_date, trigger_time),
                timezone.get_current_timezone(),
            )

        elif frequency == 'QUARTERLY':
            day_of_month = schedule.trigger_day_of_month or 1
            day_of_month = min(day_of_month, 28)

            year = base_date.year
            month = base_date.month

            # Next quarter start month
            quarter_months = [1, 4, 7, 10]
            next_quarter = None
            for qm in quarter_months:
                if qm > month or (qm == month and base_date.day < day_of_month):
                    next_quarter = qm
                    break
            if next_quarter is None:
                next_quarter = 1
                year += 1

            target_date = base_date.replace(year=year, month=next_quarter, day=day_of_month)
            return timezone.make_aware(
                datetime.combine(target_date, trigger_time),
                timezone.get_current_timezone(),
            )

        elif frequency == 'YEARLY':
            day_of_month = schedule.trigger_day_of_month or 1
            day_of_month = min(day_of_month, 28)

            year = base_date.year + 1
            target_date = base_date.replace(year=year, month=1, day=day_of_month)
            return timezone.make_aware(
                datetime.combine(target_date, trigger_time),
                timezone.get_current_timezone(),
            )

        else:
            # CUSTOM or unknown: default to daily
            return base_dt

    def get_due_schedules(self):
        """
        Get all schedules that are due for execution.

        Returns:
            QuerySet: Due ReportSchedule instances
        """
        from apps.reporting.models import ReportSchedule

        now = timezone.now()
        return ReportSchedule.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
            next_run_at__lte=now,
        ).select_related('report_definition', 'organization')

    def deliver_report(
        self,
        execution,
        channels: list,
        emails: list = None,
        webhook_url: str = '',
    ):
        """
        Deliver a completed report via configured channels.

        Args:
            execution: ReportExecution instance
            channels: List of delivery channel strings
            emails: Email addresses for EMAIL channel
            webhook_url: URL for WEBHOOK channel
        """
        emails = emails or []

        for channel in channels:
            try:
                if channel == 'DASHBOARD':
                    self._deliver_dashboard(execution)
                elif channel == 'EMAIL':
                    self._deliver_email(execution, emails)
                elif channel == 'PUSH':
                    self._deliver_push(execution)
                elif channel == 'WEBHOOK':
                    self._deliver_webhook(execution, webhook_url)
                else:
                    logger.warning('Unknown delivery channel: %s', channel)
            except Exception as exc:
                logger.error(
                    'Delivery failed: channel=%s execution=%s error=%s',
                    channel, execution.id, str(exc),
                    exc_info=True,
                )

    def _deliver_dashboard(self, execution):
        """
        Mark the execution as delivered to dashboard.
        Dashboard delivery is implicit - the execution is queryable via API.
        """
        logger.info('Report delivered to dashboard: %s', execution.id)

    def _deliver_email(self, execution, emails: list):
        """
        Send report results via email.

        Args:
            execution: ReportExecution instance
            emails: List of email addresses
        """
        if not emails:
            logger.warning('No email addresses for delivery: %s', execution.id)
            return

        from django.core.mail import send_mail
        from django.conf import settings

        subject = f'E-Menum Rapor: {execution.report.name if hasattr(execution, "report") and execution.report else "Rapor"}'
        message = (
            f'Raporunuz hazir.\n\n'
            f'Rapor ID: {execution.id}\n'
            f'Durum: {execution.status}\n'
            f'Tamamlanma: {execution.finished_at}\n\n'
            f'Sonuclari goruntulemek icin panele giris yapin.'
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=emails,
                fail_silently=False,
            )
            logger.info(
                'Report email delivered: %s to %s',
                execution.id, ', '.join(emails),
            )
        except Exception as e:
            logger.error(
                'Report email delivery failed: %s - %s',
                execution.id, str(e),
            )

    def _deliver_push(self, execution):
        """
        Send push notification about completed report.

        Args:
            execution: ReportExecution instance
        """
        from apps.notifications.models import Notification

        schedule = execution.schedule if hasattr(execution, 'schedule') else None
        if not schedule or not schedule.organization:
            logger.warning('No organization for push notification: %s', execution.id)
            return

        # Create in-app notification for all active users of the organization
        users = schedule.organization.users.filter(
            is_active=True,
            deleted_at__isnull=True,
        )
        for user in users:
            Notification.objects.create(
                organization=schedule.organization,
                user=user,
                notification_type='SYSTEM',
                title=f'Rapor hazir: {schedule.report.name if hasattr(schedule, "report") and schedule.report else "Rapor"}',
                message='Zamanlanmis raporunuz tamamlandi. Sonuclari goruntulemek icin tiklayiniz.',
                priority='NORMAL',
                channel='IN_APP',
                status='PENDING',
                action_url=f'/admin/reporting/reportexecution/{execution.id}/change/',
            )
        logger.info('Report push notification created: %s', execution.id)

    def _deliver_webhook(self, execution, webhook_url: str):
        """
        Send report results to a webhook URL.

        Args:
            execution: ReportExecution instance
            webhook_url: Destination URL
        """
        if not webhook_url:
            logger.warning('No webhook URL for delivery: %s', execution.id)
            return

        import json
        from urllib.request import urlopen, Request
        from urllib.error import URLError

        payload = {
            'event': 'report.completed',
            'execution_id': str(execution.id),
            'status': execution.status,
            'finished_at': execution.finished_at.isoformat() if execution.finished_at else None,
            'result_summary': execution.result_data.get('summary', {}) if execution.result_data else {},
        }

        try:
            req = Request(
                webhook_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urlopen(req, timeout=30) as response:
                logger.info(
                    'Report webhook delivered: %s to %s (status %d)',
                    execution.id, webhook_url, response.status,
                )
        except (URLError, Exception) as e:
            logger.error(
                'Report webhook delivery failed: %s to %s - %s',
                execution.id, webhook_url, str(e),
            )
