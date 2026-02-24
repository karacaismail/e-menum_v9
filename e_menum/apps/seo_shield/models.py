"""
Django ORM models for the SEO Shield application.

This module defines models for bot management, IP risk scoring,
security rule sets, and block logging:
- BotWhitelist: Known legitimate bot definitions and verification
- IPRiskScore: Per-IP risk assessment and tracking
- RuleSet: Configurable security rule definitions
- BlockLog: Audit trail of shield actions taken
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteManager, SoftDeleteMixin, TimeStampedMixin


class BotWhitelist(TimeStampedMixin, models.Model):
    """Known legitimate bot definitions with verification methods."""

    class VerificationMethod(models.TextChoices):
        DNS = 'dns', _('DNS reverse lookup')
        IP_RANGE = 'ip_range', _('IP range')
        USER_AGENT = 'user_agent', _('User-Agent string')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Bot identifier (e.g., Googlebot, Bingbot)'),
    )

    user_agent_pattern = models.CharField(
        max_length=300,
        verbose_name=_('User-Agent pattern'),
        help_text=_('Regex pattern to match the bot User-Agent string'),
    )

    dns_domain = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('DNS domain'),
        help_text=_('Expected reverse DNS domain (e.g., googlebot.com)'),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is active'),
        help_text=_('Whether this bot whitelist entry is active'),
    )

    verification_method = models.CharField(
        max_length=20,
        choices=VerificationMethod.choices,
        default=VerificationMethod.DNS,
        verbose_name=_('Verification method'),
        help_text=_('How to verify the bot identity'),
    )

    ip_ranges = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('IP ranges'),
        help_text=_('CIDR blocks for IP range verification'),
    )

    last_verified = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last verified'),
        help_text=_('When the bot identity was last verified'),
    )

    class Meta:
        db_table = 'shield_bot_whitelist'
        verbose_name = _('Bot Whitelist')
        verbose_name_plural = _('Bot Whitelist')
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<BotWhitelist(id={self.id}, name='{self.name}')>"


class IPRiskScore(TimeStampedMixin, models.Model):
    """Per-IP risk assessment with signal breakdown and request counters."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )

    ip_address = models.GenericIPAddressField(
        unique=True,
        db_index=True,
        verbose_name=_('IP address'),
    )

    risk_score = models.IntegerField(
        default=0,
        verbose_name=_('Risk score'),
        help_text=_('0-100 risk score'),
    )

    signals = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Signals'),
        help_text=_('Signal breakdown (e.g., {rate_limit: 30, header_anomaly: 20})'),
    )

    total_requests = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total requests'),
    )

    blocked_requests = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Blocked requests'),
    )

    first_seen = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('First seen'),
    )

    last_seen = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last seen'),
    )

    is_whitelisted = models.BooleanField(
        default=False,
        verbose_name=_('Is whitelisted'),
    )

    is_blacklisted = models.BooleanField(
        default=False,
        verbose_name=_('Is blacklisted'),
    )

    country_code = models.CharField(
        max_length=2,
        blank=True,
        verbose_name=_('Country code'),
        help_text=_('ISO 3166-1 alpha-2 country code'),
    )

    asn = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('ASN'),
        help_text=_('Autonomous System Number and name'),
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
    )

    class Meta:
        db_table = 'shield_ip_risk_scores'
        verbose_name = _('IP Risk Score')
        verbose_name_plural = _('IP Risk Scores')
        indexes = [
            models.Index(fields=['risk_score'], name='shield_ip_risk_score_idx'),
            models.Index(fields=['is_blacklisted'], name='shield_ip_blacklisted_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.ip_address} (score={self.risk_score})"

    def __repr__(self) -> str:
        return f"<IPRiskScore(ip={self.ip_address}, score={self.risk_score})>"


class RuleSet(SoftDeleteMixin, TimeStampedMixin, models.Model):
    """Configurable security rule definitions with priority and action."""

    class Action(models.TextChoices):
        BLOCK = 'block', _('Block')
        CHALLENGE = 'challenge', _('Challenge')
        LOG = 'log', _('Log only')
        THROTTLE = 'throttle', _('Throttle')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Name'),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
    )

    rules = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Rules'),
        help_text=_('List of rule definitions (JSON)'),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is active'),
    )

    priority = models.IntegerField(
        default=100,
        verbose_name=_('Priority'),
        help_text=_('Lower value = higher priority'),
    )

    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        default=Action.LOG,
        verbose_name=_('Action'),
        help_text=_('Action to take when rules match'),
    )

    match_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Match count'),
        help_text=_('Number of times this rule set has matched'),
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'shield_rule_sets'
        verbose_name = _('Rule Set')
        verbose_name_plural = _('Rule Sets')
        ordering = ['priority']

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<RuleSet(id={self.id}, name='{self.name}', priority={self.priority})>"


class BlockLog(TimeStampedMixin, models.Model):
    """Audit trail of shield actions taken against requests."""

    class ActionTaken(models.TextChoices):
        BLOCKED = 'blocked', _('Blocked')
        CHALLENGED = 'challenged', _('Challenged')
        THROTTLED = 'throttled', _('Throttled')
        LOGGED = 'logged', _('Logged')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )

    ip_address = models.GenericIPAddressField(
        db_index=True,
        verbose_name=_('IP address'),
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User-Agent'),
    )

    path = models.CharField(
        max_length=500,
        verbose_name=_('Path'),
        help_text=_('Requested URL path'),
    )

    method = models.CharField(
        max_length=10,
        verbose_name=_('Method'),
        help_text=_('HTTP method (GET, POST, etc.)'),
    )

    reason = models.CharField(
        max_length=50,
        verbose_name=_('Reason'),
        help_text=_('Why the action was taken (e.g., rate_limit, bot_impersonation)'),
    )

    risk_score = models.IntegerField(
        default=0,
        verbose_name=_('Risk score'),
    )

    signals = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Signals'),
        help_text=_('Signal breakdown at time of action'),
    )

    rule = models.ForeignKey(
        RuleSet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='block_logs',
        verbose_name=_('Rule'),
        help_text=_('Rule set that triggered this action'),
    )

    action_taken = models.CharField(
        max_length=20,
        choices=ActionTaken.choices,
        default=ActionTaken.LOGGED,
        verbose_name=_('Action taken'),
    )

    response_code = models.IntegerField(
        default=200,
        verbose_name=_('Response code'),
        help_text=_('HTTP response status code returned'),
    )

    country_code = models.CharField(
        max_length=2,
        blank=True,
        verbose_name=_('Country code'),
    )

    class Meta:
        db_table = 'shield_block_logs'
        verbose_name = _('Block Log')
        verbose_name_plural = _('Block Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['ip_address', 'created_at'],
                name='shield_log_ip_created_idx',
            ),
            models.Index(
                fields=['reason', 'created_at'],
                name='shield_log_reason_created_idx',
            ),
            models.Index(
                fields=['action_taken'],
                name='shield_log_action_idx',
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.action_taken}] {self.ip_address} {self.method} {self.path}"

    def __repr__(self) -> str:
        return (
            f"<BlockLog(ip={self.ip_address}, action={self.action_taken}, "
            f"reason='{self.reason}')>"
        )
