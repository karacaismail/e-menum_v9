"""
Celery tasks for the Reporting application.

Tasks:
    - execute_report_task: Execute a single report (async dispatch)
    - process_scheduled_reports: Check and execute due scheduled reports
    - cleanup_old_executions: Clean up expired execution data
"""

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name='apps.reporting.tasks.execute_report_task',
    queue='reporting',
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=300,
    time_limit=600,
)
def execute_report_task(self, execution_id: str):
    """
    Execute a report asynchronously.

    Called by ReportEngine.execute_report_async() to process a report
    in the background via Celery.

    Args:
        execution_id: UUID string of the ReportExecution record
    """
    import time

    from apps.reporting.models import ReportExecution
    from apps.reporting.services.report_engine import handler_registry

    try:
        execution = ReportExecution.objects.select_related(
            'report_definition', 'organization',
        ).get(id=execution_id)
    except ReportExecution.DoesNotExist:
        logger.error('Execution not found: %s', execution_id)
        return {'error': f'Execution not found: {execution_id}'}

    # Skip if not pending
    if execution.status != 'PENDING':
        logger.warning(
            'Execution %s is in status %s, skipping',
            execution_id, execution.status,
        )
        return {'skipped': True, 'reason': f'Status is {execution.status}'}

    feature_key = execution.report_definition.feature_key

    # Get handler
    handler_class = handler_registry.get(feature_key)
    if not handler_class:
        execution.status = 'FAILED'
        execution.error_message = f'No handler registered for {feature_key}'
        execution.completed_at = timezone.now()
        execution.save(update_fields=['status', 'error_message', 'completed_at', 'updated_at'])
        logger.error('No handler for %s', feature_key)
        return {'error': f'No handler for {feature_key}'}

    # Mark as processing
    execution.status = 'PROCESSING'
    execution.started_at = timezone.now()
    execution.save(update_fields=['status', 'started_at', 'updated_at'])

    # Execute
    handler = handler_class()
    handler.set_context(
        user=execution.requested_by,
        org_id=str(execution.organization_id),
        execution=execution,
    )

    start_time = time.monotonic()

    try:
        validated_params = handler.validate_parameters(execution.parameters)
        result_data = handler.generate(
            str(execution.organization_id),
            validated_params,
        )

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        execution.status = 'COMPLETED'
        execution.result_data = result_data
        execution.completed_at = timezone.now()
        execution.duration_ms = elapsed_ms
        execution.credits_consumed = execution.report_definition.credit_cost
        execution.save(update_fields=[
            'status', 'result_data', 'completed_at',
            'duration_ms', 'credits_consumed', 'updated_at',
        ])

        logger.info(
            'Async report completed: key=%s org=%s duration=%dms',
            feature_key, execution.organization_id, elapsed_ms,
        )

        return {
            'execution_id': str(execution.id),
            'feature_key': feature_key,
            'status': 'COMPLETED',
            'duration_ms': elapsed_ms,
        }

    except Exception as exc:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        execution.status = 'FAILED'
        execution.error_message = str(exc)
        execution.completed_at = timezone.now()
        execution.duration_ms = elapsed_ms
        execution.save(update_fields=[
            'status', 'error_message', 'completed_at',
            'duration_ms', 'updated_at',
        ])

        logger.error(
            'Async report failed: key=%s org=%s error=%s',
            feature_key, execution.organization_id, str(exc),
            exc_info=True,
        )

        # Retry on transient failures
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        return {
            'execution_id': str(execution.id),
            'feature_key': feature_key,
            'status': 'FAILED',
            'error': str(exc),
        }


@shared_task(
    bind=True,
    name='apps.reporting.tasks.process_scheduled_reports',
    queue='reporting',
    max_retries=1,
    soft_time_limit=300,
    time_limit=600,
)
def process_scheduled_reports(self):
    """
    Check for due scheduled reports and execute them.

    Runs every 5 minutes via Celery Beat (configured in config/celery.py).
    """
    from apps.reporting.models import ReportSchedule
    from apps.reporting.services.report_engine import ReportEngine
    from apps.reporting.services.scheduler_service import SchedulerService

    scheduler = SchedulerService()
    engine = ReportEngine()

    now = timezone.now()
    due_schedules = ReportSchedule.objects.filter(
        is_active=True,
        deleted_at__isnull=True,
        next_run_at__lte=now,
    ).select_related('report_definition', 'organization')

    executed = 0
    failed = 0

    for schedule in due_schedules:
        try:
            # Execute the report
            execution = engine.execute_report(
                org_id=str(schedule.organization_id),
                feature_key=schedule.report_definition.feature_key,
                parameters=schedule.parameters,
                user=schedule.created_by,
                export_format=schedule.export_format,
            )

            # Update schedule state
            schedule.last_run_at = now
            schedule.run_count += 1
            schedule.failure_count = 0
            schedule.next_run_at = scheduler.calculate_next_run(schedule)
            schedule.save(update_fields=[
                'last_run_at', 'run_count', 'failure_count',
                'next_run_at', 'updated_at',
            ])

            # Deliver the report
            scheduler.deliver_report(
                execution=execution,
                channels=schedule.delivery_channels,
                emails=schedule.delivery_emails,
                webhook_url=schedule.delivery_webhook_url,
            )

            executed += 1

        except Exception as exc:
            failed += 1
            schedule.failure_count += 1
            schedule.last_run_at = now

            # Auto-disable after max failures
            if schedule.failure_count >= schedule.max_failures:
                schedule.is_active = False
                logger.warning(
                    'Schedule %s auto-disabled after %d failures',
                    schedule.id, schedule.failure_count,
                )
            else:
                schedule.next_run_at = scheduler.calculate_next_run(schedule)

            schedule.save(update_fields=[
                'failure_count', 'last_run_at', 'is_active',
                'next_run_at', 'updated_at',
            ])

            logger.error(
                'Scheduled report failed: schedule=%s error=%s',
                schedule.id, str(exc),
                exc_info=True,
            )

    logger.info(
        'Scheduled reports processed: executed=%d failed=%d',
        executed, failed,
    )

    return {
        'executed': executed,
        'failed': failed,
    }


@shared_task(
    name='apps.reporting.tasks.cleanup_old_executions',
    queue='maintenance',
    soft_time_limit=300,
    time_limit=600,
)
def cleanup_old_executions(days=90):
    """
    Clean up old report execution data to free storage.

    Removes result_data from completed executions older than specified days.
    Does NOT delete the execution records themselves (audit trail).

    Args:
        days: Number of days after which to clean result data (default: 90)
    """
    from datetime import timedelta
    from apps.reporting.models import ReportExecution

    cutoff = timezone.now() - timedelta(days=days)

    updated = ReportExecution.objects.filter(
        status='COMPLETED',
        completed_at__lt=cutoff,
        result_data__isnull=False,
    ).update(
        result_data=None,
        export_file_url='',
    )

    logger.info('Cleaned up %d old report executions (>%d days)', updated, days)

    return {'cleaned': updated, 'days': days}
