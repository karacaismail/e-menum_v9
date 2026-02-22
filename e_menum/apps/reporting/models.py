"""
Models for the Reporting application.

Core models for the report engine:
    - ReportDefinition: Platform-level report catalog (feature_key, category, AI model, etc.)
    - ReportExecution: Tenant-scoped execution records (status, result, credits)
    - ReportSchedule: Recurring report schedules (frequency, delivery channels)
    - ReportFavorite: User-bookmarked reports

All tenant-scoped models use TimeStampedMixin + SoftDeleteMixin with UUID PKs.
ReportDefinition is platform-level (no organization FK).
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteManager, SoftDeleteMixin, TimeStampedMixin
from apps.reporting.choices import (
    AIModel,
    DeliveryChannel,
    ExportFormat,
    PlanTier,
    ReportCategory,
    ReportPriority,
    ReportStatus,
    ScheduleFrequency,
)


# =============================================================================
# REPORT DEFINITION (Platform-level catalog)
# =============================================================================

class ReportDefinition(TimeStampedMixin):
    """
    Platform-level report catalog entry.

    Defines what reports are available, which plans can access them,
    which AI model they use, and their credit cost.

    NOT organization-scoped - this is a platform-wide catalog.
    No SoftDeleteMixin - report definitions are permanent.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    feature_key = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_('Unique feature key, e.g., RPT-SAL-001'),
    )
    name = models.CharField(
        max_length=200,
        help_text=_('Human-readable report name'),
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text=_('Report description'),
    )
    category = models.CharField(
        max_length=20,
        choices=ReportCategory.choices,
        db_index=True,
        help_text=_('Report category'),
    )
    priority = models.CharField(
        max_length=5,
        choices=ReportPriority.choices,
        default=ReportPriority.P2,
        help_text=_('Implementation priority'),
    )

    # AI Configuration
    ai_model = models.CharField(
        max_length=10,
        choices=AIModel.choices,
        default=AIModel.NONE,
        help_text=_('AI model used for this report'),
    )
    credit_cost = models.PositiveIntegerField(
        default=0,
        help_text=_('Credit cost per execution'),
    )

    # Plan availability
    min_plan = models.CharField(
        max_length=20,
        choices=PlanTier.choices,
        default=PlanTier.STARTER,
        help_text=_('Minimum plan required to access this report'),
    )

    # Report configuration
    default_parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Default parameters for this report'),
    )
    supported_formats = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Supported export formats, e.g., ["PDF", "EXCEL", "CSV"]'),
    )
    supported_dimensions = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Supported grouping dimensions'),
    )
    handler_class = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text=_('Dotted path to handler class'),
    )

    # Flags
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this report is available'),
    )
    is_periodic = models.BooleanField(
        default=False,
        help_text=_('Whether this report can be scheduled'),
    )
    requires_ai = models.BooleanField(
        default=False,
        help_text=_('Whether this report requires AI processing'),
    )

    class Meta:
        db_table = 'reporting_definitions'
        ordering = ['category', 'feature_key']
        verbose_name = _('Report Definition')
        verbose_name_plural = _('Report Definitions')

    def __str__(self):
        return f'{self.feature_key}: {self.name}'


# =============================================================================
# REPORT EXECUTION (Tenant-scoped)
# =============================================================================

class ReportExecution(TimeStampedMixin, SoftDeleteMixin):
    """
    Record of a report execution for a specific organization.

    Tracks the request, processing status, result data, and credits consumed.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='report_executions',
        help_text=_('Organization that requested this report'),
    )
    report_definition = models.ForeignKey(
        ReportDefinition,
        on_delete=models.CASCADE,
        related_name='executions',
        help_text=_('The report definition being executed'),
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='report_executions',
        help_text=_('User who requested the report'),
    )

    # Execution state
    status = models.CharField(
        max_length=15,
        choices=ReportStatus.choices,
        default=ReportStatus.PENDING,
        db_index=True,
        help_text=_('Current execution status'),
    )
    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Parameters used for this execution'),
    )
    result_data = models.JSONField(
        null=True,
        blank=True,
        help_text=_('Report result data (JSON)'),
    )
    error_message = models.TextField(
        blank=True,
        default='',
        help_text=_('Error message if execution failed'),
    )

    # Timing
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When processing started'),
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When processing completed'),
    )
    duration_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Execution duration in milliseconds'),
    )

    # Credit tracking
    credits_consumed = models.PositiveIntegerField(
        default=0,
        help_text=_('Credits consumed for this execution'),
    )
    ai_model_used = models.CharField(
        max_length=10,
        choices=AIModel.choices,
        blank=True,
        default='',
        help_text=_('AI model actually used (may differ from definition)'),
    )
    ai_tokens_used = models.PositiveIntegerField(
        default=0,
        help_text=_('AI tokens consumed'),
    )

    # Export
    export_format = models.CharField(
        max_length=10,
        choices=ExportFormat.choices,
        blank=True,
        default='',
        help_text=_('Export format if exported'),
    )
    export_file_url = models.URLField(
        blank=True,
        default='',
        help_text=_('URL to exported file'),
    )

    # Schedule reference
    schedule = models.ForeignKey(
        'reporting.ReportSchedule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executions',
        help_text=_('Schedule that triggered this execution (if scheduled)'),
    )

    # Celery task tracking
    celery_task_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text=_('Celery task ID for tracking'),
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'reporting_executions'
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['organization', 'status'],
                name='idx_rpt_exec_org_status',
            ),
            models.Index(
                fields=['organization', 'report_definition'],
                name='idx_rpt_exec_org_def',
            ),
            models.Index(
                fields=['organization', '-created_at'],
                name='idx_rpt_exec_org_created',
            ),
        ]
        verbose_name = _('Report Execution')
        verbose_name_plural = _('Report Executions')

    def __str__(self):
        return (
            f'{self.report_definition.feature_key} - '
            f'{self.organization} - {self.status}'
        )


# =============================================================================
# REPORT SCHEDULE (Tenant-scoped)
# =============================================================================

class ReportSchedule(TimeStampedMixin, SoftDeleteMixin):
    """
    Recurring report schedule for automatic report generation.

    Defines when a report should be automatically generated
    and how to deliver the results.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='report_schedules',
        help_text=_('Organization that owns this schedule'),
    )
    report_definition = models.ForeignKey(
        ReportDefinition,
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text=_('The report to generate'),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_report_schedules',
        help_text=_('User who created the schedule'),
    )

    # Schedule configuration
    name = models.CharField(
        max_length=200,
        help_text=_('Schedule name'),
    )
    frequency = models.CharField(
        max_length=15,
        choices=ScheduleFrequency.choices,
        help_text=_('How often to generate the report'),
    )
    trigger_time = models.TimeField(
        help_text=_('Time of day to generate (local timezone)'),
    )
    trigger_day_of_week = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text=_('Day of week for weekly schedules (0=Monday, 6=Sunday)'),
    )
    trigger_day_of_month = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text=_('Day of month for monthly schedules (1-28)'),
    )
    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Report parameters to use'),
    )

    # Delivery
    delivery_channels = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Delivery channels: ["DASHBOARD", "EMAIL", "PUSH", "WEBHOOK"]'),
    )
    delivery_emails = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Email addresses for EMAIL delivery'),
    )
    delivery_webhook_url = models.URLField(
        blank=True,
        default='',
        help_text=_('Webhook URL for WEBHOOK delivery'),
    )
    export_format = models.CharField(
        max_length=10,
        choices=ExportFormat.choices,
        default=ExportFormat.JSON,
        help_text=_('Export format for delivery'),
    )

    # State
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this schedule is active'),
    )
    next_run_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Next scheduled run time'),
    )
    last_run_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the schedule was last executed'),
    )
    run_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of times this schedule has run'),
    )
    failure_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of consecutive failures'),
    )
    max_failures = models.PositiveSmallIntegerField(
        default=3,
        help_text=_('Max consecutive failures before auto-disable'),
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'reporting_schedules'
        ordering = ['organization', 'name']
        indexes = [
            models.Index(
                fields=['is_active', 'next_run_at'],
                name='idx_rpt_sched_active_next',
            ),
        ]
        verbose_name = _('Report Schedule')
        verbose_name_plural = _('Report Schedules')

    def __str__(self):
        return f'{self.name} ({self.frequency})'


# =============================================================================
# REPORT FAVORITE (Tenant-scoped)
# =============================================================================

class ReportFavorite(TimeStampedMixin):
    """
    User-bookmarked report for quick access.

    No SoftDeleteMixin - favorites are physically deleted when removed.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='report_favorites',
        help_text=_('Organization context'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='report_favorites',
        help_text=_('User who favorited this report'),
    )
    report_definition = models.ForeignKey(
        ReportDefinition,
        on_delete=models.CASCADE,
        related_name='favorites',
        help_text=_('The favorited report'),
    )
    custom_name = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text=_('Custom name for this favorite'),
    )
    custom_parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Saved parameters for quick access'),
    )
    display_order = models.PositiveSmallIntegerField(
        default=0,
        help_text=_('Display order in favorites list'),
    )

    class Meta:
        db_table = 'reporting_favorites'
        ordering = ['display_order', 'created_at']
        unique_together = [['user', 'report_definition', 'organization']]
        verbose_name = _('Report Favorite')
        verbose_name_plural = _('Report Favorites')

    def __str__(self):
        display_name = self.custom_name or self.report_definition.name
        return f'{self.user} - {display_name}'


# =============================================================================
# CONVERSATION SESSION (Tenant-scoped)
# =============================================================================

class ConversationSession(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Multi-turn conversation session for conversational analytics.

    Tracks a conversation between a user and the AI analytics assistant,
    maintaining context across multiple messages for follow-up questions.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='conversation_sessions',
        help_text=_('Organization that owns this session'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversation_sessions',
        help_text=_('User who initiated this conversation'),
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text=_('Session title (auto-generated or user-defined)'),
    )
    context_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Accumulated context from conversation turns'),
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this session is still active'),
    )
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp of the last message in this session'),
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'reporting_conversation_sessions'
        ordering = ['-last_message_at']
        indexes = [
            models.Index(
                fields=['organization', 'user', '-last_message_at'],
                name='idx_conv_sess_org_user_last',
            ),
            models.Index(
                fields=['organization', 'is_active'],
                name='idx_conv_sess_org_active',
            ),
        ]
        verbose_name = _('Conversation Session')
        verbose_name_plural = _('Conversation Sessions')

    def __str__(self):
        return f'Session {self.id} - {self.user} ({self.title or "Untitled"})'


# =============================================================================
# CONVERSATION MESSAGE
# =============================================================================

class ConversationMessage(TimeStampedMixin, models.Model):
    """
    Individual message within a conversation session.

    Stores user queries, assistant responses, and system messages.
    Messages may include associated report data and metadata.

    No SoftDeleteMixin - messages are tied to session lifecycle.
    """

    ROLE_CHOICES = [
        ('user', _('User')),
        ('assistant', _('Assistant')),
        ('system', _('System')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    session = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text=_('Parent conversation session'),
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text=_('Message role: user, assistant, or system'),
    )
    content = models.TextField(
        help_text=_('Message text content'),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional message metadata (intent, confidence, etc.)'),
    )
    report_data = models.JSONField(
        null=True,
        blank=True,
        help_text=_('Associated report data returned with this message'),
    )

    class Meta:
        db_table = 'reporting_conversation_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(
                fields=['session', 'created_at'],
                name='idx_conv_msg_session_created',
            ),
        ]
        verbose_name = _('Conversation Message')
        verbose_name_plural = _('Conversation Messages')

    def __str__(self):
        return f'[{self.role}] {self.content[:50]}...'


# =============================================================================
# CREDIT BALANCE (Tenant-scoped)
# =============================================================================

class CreditBalance(TimeStampedMixin, models.Model):
    """
    Credit balance for an organization's AI feature usage.

    Tracks total purchased credits, consumed credits, and reserved credits.
    Reserved credits are temporarily held during report execution and
    either consumed on success or released on failure.

    No SoftDeleteMixin - credit balances are permanent financial records.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='credit_balance',
        help_text=_('Organization this balance belongs to'),
    )
    total_credits = models.IntegerField(
        default=0,
        help_text=_('Total credits ever purchased/granted'),
    )
    used_credits = models.IntegerField(
        default=0,
        help_text=_('Total credits consumed'),
    )
    reserved_credits = models.IntegerField(
        default=0,
        help_text=_('Credits currently reserved for in-progress operations'),
    )

    class Meta:
        db_table = 'reporting_credit_balances'
        verbose_name = _('Credit Balance')
        verbose_name_plural = _('Credit Balances')
        constraints = [
            models.UniqueConstraint(
                fields=['organization'],
                name='unique_org_credit_balance',
            ),
        ]

    def __str__(self):
        return (
            f'CreditBalance for {self.organization}: '
            f'{self.available_credits} available'
        )

    @property
    def available_credits(self) -> int:
        """Return credits available for consumption."""
        return self.total_credits - self.used_credits - self.reserved_credits


# =============================================================================
# CREDIT TRANSACTION
# =============================================================================

class CreditTransaction(TimeStampedMixin, models.Model):
    """
    Individual credit transaction log entry.

    Records every credit movement (purchase, consumption, refund, bonus, expiry)
    for audit and billing purposes.

    No SoftDeleteMixin - transactions are immutable financial records.
    """

    TRANSACTION_TYPE_CHOICES = [
        ('PURCHASE', _('Purchase')),
        ('CONSUME', _('Consume')),
        ('REFUND', _('Refund')),
        ('BONUS', _('Bonus')),
        ('EXPIRE', _('Expire')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='credit_transactions',
        help_text=_('Organization this transaction belongs to'),
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text=_('Type of credit transaction'),
    )
    amount = models.IntegerField(
        help_text=_('Credit amount (positive=addition, negative=consumption)'),
    )
    balance_after = models.IntegerField(
        help_text=_('Available balance after this transaction'),
    )
    description = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text=_('Human-readable description of the transaction'),
    )
    reference_type = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text=_('Reference type (e.g., report_execution, subscription)'),
    )
    reference_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=_('UUID of the referenced entity'),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_transactions',
        help_text=_('User who initiated this transaction'),
    )

    class Meta:
        db_table = 'reporting_credit_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['organization', '-created_at'],
                name='idx_credit_tx_org_created',
            ),
            models.Index(
                fields=['organization', 'transaction_type'],
                name='idx_credit_tx_org_type',
            ),
            models.Index(
                fields=['reference_type', 'reference_id'],
                name='idx_credit_tx_ref',
            ),
        ]
        verbose_name = _('Credit Transaction')
        verbose_name_plural = _('Credit Transactions')

    def __str__(self):
        return (
            f'{self.transaction_type} {self.amount:+d} credits '
            f'for {self.organization}'
        )


# =============================================================================
# INDUSTRY BENCHMARK (Platform-level)
# =============================================================================

class IndustryBenchmark(TimeStampedMixin, models.Model):
    """
    Platform-level industry benchmark data.

    Stores anonymized, aggregated performance metrics across all organizations
    for industry comparison. NOT organization-scoped.

    No SoftDeleteMixin - benchmarks are permanent reference data.
    """

    PERIOD_TYPE_CHOICES = [
        ('DAILY', _('Daily')),
        ('WEEKLY', _('Weekly')),
        ('MONTHLY', _('Monthly')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    metric_name = models.CharField(
        max_length=100,
        help_text=_('Metric identifier (e.g., avg_order_value, daily_revenue)'),
    )
    category = models.CharField(
        max_length=50,
        help_text=_('Business category (e.g., cafe, restaurant, fast_food)'),
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        default='TR',
        help_text=_('Geographic region (ISO country code or city)'),
    )
    period_type = models.CharField(
        max_length=20,
        choices=PERIOD_TYPE_CHOICES,
        help_text=_('Period granularity'),
    )
    period_start = models.DateField(
        help_text=_('Start date of the benchmark period'),
    )
    value = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text=_('Benchmark mean/average value'),
    )
    sample_size = models.IntegerField(
        default=0,
        help_text=_('Number of organizations in this benchmark'),
    )
    percentile_25 = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        help_text=_('25th percentile value'),
    )
    percentile_50 = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        help_text=_('50th percentile (median) value'),
    )
    percentile_75 = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        help_text=_('75th percentile value'),
    )
    percentile_90 = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        help_text=_('90th percentile value'),
    )

    class Meta:
        db_table = 'reporting_industry_benchmarks'
        ordering = ['-period_start', 'metric_name']
        unique_together = [
            ['metric_name', 'category', 'region', 'period_type', 'period_start'],
        ]
        indexes = [
            models.Index(
                fields=['metric_name', 'category', 'period_type'],
                name='idx_benchmark_metric_cat_type',
            ),
        ]
        verbose_name = _('Industry Benchmark')
        verbose_name_plural = _('Industry Benchmarks')

    def __str__(self):
        return (
            f'{self.metric_name} ({self.category}/{self.region}) '
            f'{self.period_type} {self.period_start}'
        )
