"""
Choices/enums for the Analytics application.

Defines metric types, period types, and granularity levels
used across analytics models and aggregation services.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class MetricType(models.TextChoices):
    """Types of dashboard metrics tracked."""
    REVENUE = 'REVENUE', _('Revenue')
    ORDERS = 'ORDERS', _('Orders')
    CUSTOMERS = 'CUSTOMERS', _('Customers')
    AVG_ORDER = 'AVG_ORDER', _('Average Order Value')
    RATING = 'RATING', _('Rating')
    NEW_CUSTOMERS = 'NEW_CUSTOMERS', _('New Customers')
    RETURNING_CUSTOMERS = 'RETURNING_CUSTOMERS', _('Returning Customers')
    ITEMS_SOLD = 'ITEMS_SOLD', _('Items Sold')


class PeriodType(models.TextChoices):
    """Time period types for aggregation."""
    DAILY = 'DAILY', _('Daily')
    WEEKLY = 'WEEKLY', _('Weekly')
    MONTHLY = 'MONTHLY', _('Monthly')
    QUARTERLY = 'QUARTERLY', _('Quarterly')
    YEARLY = 'YEARLY', _('Yearly')


class Granularity(models.TextChoices):
    """Granularity levels for sales aggregation."""
    HOURLY = 'HOURLY', _('Hourly')
    DAILY = 'DAILY', _('Daily')
