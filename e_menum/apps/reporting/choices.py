"""
Choices/enums for the Reporting application.

Defines report categories, statuses, schedule frequencies,
and other enum types used across reporting models.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class ReportCategory(models.TextChoices):
    """Categories of reports in the catalog."""

    SALES = "SALES", _("Sales")
    ORDERS = "ORDERS", _("Orders")
    MENU = "MENU", _("Menu")
    CUSTOMERS = "CUSTOMERS", _("Customers")
    OPERATIONS = "OPERATIONS", _("Operations")
    DIGITAL = "DIGITAL", _("Digital")
    PERIODIC = "PERIODIC", _("Periodic")
    STAFF = "STAFF", _("Staff")
    BRANCH = "BRANCH", _("Branch")
    INVENTORY = "INVENTORY", _("Inventory")
    CAMPAIGNS = "CAMPAIGNS", _("Campaigns")
    PLATFORM = "PLATFORM", _("Platform")
    AI_INSIGHTS = "AI_INSIGHTS", _("AI Insights")
    AI_QUERY = "AI_QUERY", _("AI Query")
    FORECASTING = "FORECASTING", _("Forecasting")


class ReportStatus(models.TextChoices):
    """Status of a report execution."""

    PENDING = "PENDING", _("Pending")
    PROCESSING = "PROCESSING", _("Processing")
    COMPLETED = "COMPLETED", _("Completed")
    FAILED = "FAILED", _("Failed")
    CANCELLED = "CANCELLED", _("Cancelled")
    EXPIRED = "EXPIRED", _("Expired")


class ScheduleFrequency(models.TextChoices):
    """Frequency for scheduled report generation."""

    DAILY = "DAILY", _("Daily")
    WEEKLY = "WEEKLY", _("Weekly")
    BIWEEKLY = "BIWEEKLY", _("Bi-weekly")
    MONTHLY = "MONTHLY", _("Monthly")
    QUARTERLY = "QUARTERLY", _("Quarterly")
    YEARLY = "YEARLY", _("Yearly")
    CUSTOM = "CUSTOM", _("Custom")


class DeliveryChannel(models.TextChoices):
    """Delivery channels for scheduled reports."""

    DASHBOARD = "DASHBOARD", _("Dashboard")
    EMAIL = "EMAIL", _("Email")
    PUSH = "PUSH", _("Push Notification")
    WEBHOOK = "WEBHOOK", _("Webhook")


class ExportFormat(models.TextChoices):
    """Export formats for reports."""

    JSON = "JSON", _("JSON")
    PDF = "PDF", _("PDF")
    EXCEL = "EXCEL", _("Excel")
    CSV = "CSV", _("CSV")


class AIModel(models.TextChoices):
    """AI model choices for report generation."""

    HAIKU = "HAIKU", _("Claude Haiku")
    SONNET = "SONNET", _("Claude Sonnet")
    OPUS = "OPUS", _("Claude Opus")
    NONE = "NONE", _("No AI")


class PlanTier(models.TextChoices):
    """Plan tiers for report availability."""

    FREE = "FREE", _("Free")
    STARTER = "STARTER", _("Starter")
    PROFESSIONAL = "PROFESSIONAL", _("Professional")
    BUSINESS = "BUSINESS", _("Business")
    ENTERPRISE = "ENTERPRISE", _("Enterprise")


class ReportPriority(models.TextChoices):
    """Priority levels for report features."""

    P0 = "P0", _("P0 - Critical")
    P1 = "P1", _("P1 - High")
    P2 = "P2", _("P2 - Medium")
    P3 = "P3", _("P3 - Low")
