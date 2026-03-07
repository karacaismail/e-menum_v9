"""
Report Engine - Core orchestration service for report generation.

The ReportEngine is the central coordinator for all reporting:
    1. Maintains a registry of handler classes keyed by feature_key
    2. Validates permissions, plan access, and credit availability
    3. Creates ReportExecution records
    4. Dispatches handler execution (sync or async via Celery)
    5. Handles errors and updates execution status

BaseReportHandler is the abstract base class that all report handlers
must implement. Each handler encapsulates the logic for one report type.

Usage:
    # Register a handler
    engine = ReportEngine()
    engine.register_handler('RPT-SAL-001', RevenueReportHandler)

    # Execute a report
    execution = engine.execute_report(
        org_id=org.id,
        feature_key='RPT-SAL-001',
        parameters={'period': 'DAILY', 'date': '2026-01-15'},
        user=request.user,
    )
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type

from django.utils import timezone

from shared.utils.exceptions import AppException

if TYPE_CHECKING:
    from apps.reporting.models import ReportExecution

logger = logging.getLogger(__name__)


# =============================================================================
# BASE REPORT HANDLER (ABC)
# =============================================================================

class BaseReportHandler(ABC):
    """
    Abstract base class for all report handlers.

    Each report type (e.g., Revenue Report, Top Sellers, etc.) must
    implement a concrete handler that extends this class.

    Subclasses MUST implement:
        - generate(org_id, parameters) -> dict
        - get_required_permissions() -> list[str]

    Subclasses MAY override:
        - validate_parameters(parameters) -> dict
        - get_default_parameters() -> dict
        - get_supported_formats() -> list[str]
        - get_cache_key(org_id, parameters) -> str
        - get_cache_ttl() -> int

    Usage:
        class RevenueReportHandler(BaseReportHandler):
            feature_key = 'RPT-SAL-001'

            def generate(self, org_id, parameters):
                # ... query data, compute metrics ...
                return {'revenue': ..., 'comparison': ...}

            def get_required_permissions(self):
                return ['reporting.view']
    """

    # Must be set by subclass
    feature_key: str = ''

    def __init__(self):
        """Initialize handler with empty context."""
        self._context = {}

    @abstractmethod
    def generate(self, org_id: str, parameters: dict) -> dict:
        """
        Generate the report data.

        Args:
            org_id: Organization UUID string
            parameters: Report parameters (validated)

        Returns:
            dict: Report result data. Must be JSON-serializable.

        Raises:
            AppException: If report generation fails
        """
        raise NotImplementedError

    @abstractmethod
    def get_required_permissions(self) -> List[str]:
        """
        Return the list of permission codes required to run this report.

        Returns:
            list[str]: Permission codes (e.g., ['reporting.view', 'sales.view'])
        """
        raise NotImplementedError

    def validate_parameters(self, parameters: dict) -> dict:
        """
        Validate and normalize input parameters.

        Override in subclass to add custom validation.
        Default implementation merges with defaults and returns.

        Args:
            parameters: Raw parameters from the request

        Returns:
            dict: Validated and normalized parameters

        Raises:
            AppException: If parameters are invalid
        """
        defaults = self.get_default_parameters()
        merged = {**defaults, **parameters}
        return merged

    def get_default_parameters(self) -> dict:
        """
        Return default parameter values for this report.

        Returns:
            dict: Default parameters
        """
        return {}

    def get_supported_formats(self) -> List[str]:
        """
        Return supported export formats.

        Returns:
            list[str]: Format strings (e.g., ['JSON', 'PDF', 'EXCEL'])
        """
        return ['JSON', 'PDF', 'EXCEL', 'CSV']

    def get_cache_key(self, org_id: str, parameters: dict) -> Optional[str]:
        """
        Return a cache key for this report result.

        Returns None to disable caching. Override to enable caching.

        Args:
            org_id: Organization UUID string
            parameters: Validated parameters

        Returns:
            str or None: Cache key, or None to skip caching
        """
        return None

    def get_cache_ttl(self) -> int:
        """
        Return cache TTL in seconds.

        Returns:
            int: Cache time-to-live (default: 300 = 5 minutes)
        """
        return 300

    def set_context(self, **kwargs):
        """
        Set additional context for the handler (e.g., user, request).

        Args:
            **kwargs: Context key-value pairs
        """
        self._context.update(kwargs)


# =============================================================================
# HANDLER REGISTRY
# =============================================================================

class _HandlerRegistry:
    """
    Singleton registry for report handler classes.

    Maps feature_key -> handler_class.
    Thread-safe: Django processes run in single-thread per request.
    """

    _instance = None
    _handlers: Dict[str, Type[BaseReportHandler]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._handlers = {}
        return cls._instance

    def register(self, feature_key: str, handler_class: Type[BaseReportHandler]):
        """Register a handler class for a feature key."""
        if feature_key in self._handlers:
            logger.warning(
                'Overwriting handler for %s: %s -> %s',
                feature_key,
                self._handlers[feature_key].__name__,
                handler_class.__name__,
            )
        self._handlers[feature_key] = handler_class
        logger.debug('Registered handler: %s -> %s', feature_key, handler_class.__name__)

    def get(self, feature_key: str) -> Optional[Type[BaseReportHandler]]:
        """Get handler class by feature key."""
        return self._handlers.get(feature_key)

    def get_all(self) -> Dict[str, Type[BaseReportHandler]]:
        """Get all registered handlers."""
        return dict(self._handlers)

    def is_registered(self, feature_key: str) -> bool:
        """Check if a handler is registered for the given feature key."""
        return feature_key in self._handlers

    def clear(self):
        """Clear all registrations. Used in testing."""
        self._handlers.clear()


# Module-level registry instance
handler_registry = _HandlerRegistry()


def register_handler(feature_key: str):
    """
    Decorator to register a report handler class.

    Usage:
        @register_handler('RPT-SAL-001')
        class RevenueReportHandler(BaseReportHandler):
            ...
    """
    def decorator(cls):
        cls.feature_key = feature_key
        handler_registry.register(feature_key, cls)
        return cls
    return decorator


# =============================================================================
# REPORT ENGINE
# =============================================================================

class ReportEngine:
    """
    Central orchestration service for report generation.

    Responsibilities:
        1. Look up ReportDefinition by feature_key
        2. Validate plan access and credits
        3. Instantiate the registered handler
        4. Create ReportExecution record
        5. Execute handler.generate() (sync or async)
        6. Update execution status with results

    Usage:
        engine = ReportEngine()

        # Sync execution (for quick reports)
        execution = engine.execute_report(
            org_id=org.id,
            feature_key='RPT-SAL-001',
            parameters={'period': 'DAILY'},
            user=request.user,
        )

        # Async execution (dispatched to Celery)
        execution = engine.execute_report_async(
            org_id=org.id,
            feature_key='RPT-SAL-001',
            parameters={'period': 'MONTHLY'},
            user=request.user,
        )
    """

    def __init__(self):
        self.registry = handler_registry

    def register_handler(
        self,
        feature_key: str,
        handler_class: Type[BaseReportHandler],
    ):
        """
        Register a handler class for a feature key.

        Args:
            feature_key: The report feature key (e.g., 'RPT-SAL-001')
            handler_class: The handler class to register
        """
        self.registry.register(feature_key, handler_class)

    def get_available_reports(self, org_id: str, plan_tier: str = None) -> list:
        """
        Get all available reports for an organization, optionally filtered by plan.

        Args:
            org_id: Organization UUID string
            plan_tier: Plan tier to filter by (e.g., 'STARTER')

        Returns:
            list: List of ReportDefinition instances
        """
        from apps.reporting.models import ReportDefinition

        qs = ReportDefinition.objects.filter(is_active=True)

        if plan_tier:
            # Filter by plan tier hierarchy
            tier_order = ['FREE', 'STARTER', 'PROFESSIONAL', 'BUSINESS', 'ENTERPRISE']
            try:
                tier_idx = tier_order.index(plan_tier)
                allowed_tiers = tier_order[:tier_idx + 1]
                qs = qs.filter(min_plan__in=allowed_tiers)
            except ValueError:
                pass

        return list(qs)

    def execute_report(
        self,
        org_id: str,
        feature_key: str,
        parameters: dict = None,
        user=None,
        export_format: str = '',
    ) -> 'ReportExecution':
        """
        Execute a report synchronously.

        Args:
            org_id: Organization UUID string
            feature_key: Report feature key
            parameters: Report parameters
            user: User requesting the report
            export_format: Optional export format

        Returns:
            ReportExecution: The completed execution record

        Raises:
            AppException: If report not found, handler not registered, etc.
        """
        from apps.reporting.models import ReportDefinition, ReportExecution

        parameters = parameters or {}

        # 1. Look up report definition
        try:
            report_def = ReportDefinition.objects.get(
                feature_key=feature_key,
                is_active=True,
            )
        except ReportDefinition.DoesNotExist:
            raise AppException(
                code='REPORT_NOT_FOUND',
                message=f'Report definition not found: {feature_key}',
                status_code=404,
            )

        # 2. Check handler registration
        handler_class = self.registry.get(feature_key)
        if not handler_class:
            raise AppException(
                code='HANDLER_NOT_REGISTERED',
                message=f'No handler registered for report: {feature_key}',
                status_code=501,
            )

        # 3. Create execution record
        execution = ReportExecution.objects.create(
            organization_id=org_id,
            report_definition=report_def,
            requested_by=user,
            status='PENDING',
            parameters=parameters,
            export_format=export_format,
        )

        # 4. Instantiate handler and validate parameters
        handler = handler_class()
        handler.set_context(user=user, org_id=org_id, execution=execution)

        try:
            validated_params = handler.validate_parameters(parameters)
        except Exception as exc:
            execution.status = 'FAILED'
            execution.error_message = f'Parameter validation failed: {str(exc)}'
            execution.save(update_fields=['status', 'error_message', 'updated_at'])
            raise

        # 5. Execute the handler
        execution.status = 'PROCESSING'
        execution.started_at = timezone.now()
        execution.save(update_fields=['status', 'started_at', 'updated_at'])

        start_time = time.monotonic()

        try:
            result_data = handler.generate(org_id, validated_params)

            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            execution.status = 'COMPLETED'
            execution.result_data = result_data
            execution.completed_at = timezone.now()
            execution.duration_ms = elapsed_ms
            execution.credits_consumed = report_def.credit_cost
            execution.save(update_fields=[
                'status', 'result_data', 'completed_at',
                'duration_ms', 'credits_consumed', 'updated_at',
            ])

            logger.info(
                'Report executed: key=%s org=%s duration=%dms',
                feature_key, org_id, elapsed_ms,
            )

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
                'Report execution failed: key=%s org=%s error=%s',
                feature_key, org_id, str(exc),
                exc_info=True,
            )
            raise AppException(
                code='REPORT_EXECUTION_FAILED',
                message=f'Report execution failed: {str(exc)}',
                status_code=500,
            )

        return execution

    def execute_report_async(
        self,
        org_id: str,
        feature_key: str,
        parameters: dict = None,
        user=None,
        export_format: str = '',
    ) -> 'ReportExecution':
        """
        Create execution record and dispatch to Celery for async processing.

        Args:
            org_id: Organization UUID string
            feature_key: Report feature key
            parameters: Report parameters
            user: User requesting the report
            export_format: Optional export format

        Returns:
            ReportExecution: The pending execution record (not yet completed)
        """
        from apps.reporting.models import ReportDefinition, ReportExecution
        from apps.reporting.tasks import execute_report_task

        parameters = parameters or {}

        # Look up report definition
        try:
            report_def = ReportDefinition.objects.get(
                feature_key=feature_key,
                is_active=True,
            )
        except ReportDefinition.DoesNotExist:
            raise AppException(
                code='REPORT_NOT_FOUND',
                message=f'Report definition not found: {feature_key}',
                status_code=404,
            )

        # Check handler registration
        if not self.registry.is_registered(feature_key):
            raise AppException(
                code='HANDLER_NOT_REGISTERED',
                message=f'No handler registered for report: {feature_key}',
                status_code=501,
            )

        # Create execution record
        execution = ReportExecution.objects.create(
            organization_id=org_id,
            report_definition=report_def,
            requested_by=user,
            status='PENDING',
            parameters=parameters,
            export_format=export_format,
        )

        # Dispatch to Celery
        task = execute_report_task.delay(str(execution.id))
        execution.celery_task_id = task.id
        execution.save(update_fields=['celery_task_id', 'updated_at'])

        logger.info(
            'Report dispatched async: key=%s org=%s execution=%s task=%s',
            feature_key, org_id, execution.id, task.id,
        )

        return execution

    def cancel_execution(self, execution_id: str):
        """
        Cancel a pending or processing execution.

        Args:
            execution_id: ReportExecution UUID string
        """
        from apps.reporting.models import ReportExecution

        try:
            execution = ReportExecution.objects.get(id=execution_id)
        except ReportExecution.DoesNotExist:
            raise AppException(
                code='EXECUTION_NOT_FOUND',
                message=f'Execution not found: {execution_id}',
                status_code=404,
            )

        if execution.status not in ('PENDING', 'PROCESSING'):
            raise AppException(
                code='EXECUTION_NOT_CANCELLABLE',
                message=f'Execution in status {execution.status} cannot be cancelled',
                status_code=400,
            )

        execution.status = 'CANCELLED'
        execution.completed_at = timezone.now()
        execution.save(update_fields=['status', 'completed_at', 'updated_at'])

        # Revoke Celery task if exists
        if execution.celery_task_id:
            from config.celery import app
            app.control.revoke(execution.celery_task_id, terminate=True)

        logger.info('Report execution cancelled: %s', execution_id)
