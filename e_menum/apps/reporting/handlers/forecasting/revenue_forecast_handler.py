"""
Revenue Forecast Report Handler (RPT-FOR-001).

Generates revenue forecasts using the ForecastService.
Registered with the report engine as feature_key 'RPT-FOR-001'.

Usage:
    # Via the ReportEngine (preferred):
    engine = ReportEngine()
    execution = engine.execute_report(
        org_id=org.id,
        feature_key='RPT-FOR-001',
        parameters={'days_ahead': 30},
        user=request.user,
    )

    # Direct handler usage (for testing):
    handler = RevenueForecastHandler()
    result = handler.generate(org_id=str(org.id), parameters={'days_ahead': 30})
"""

import logging
from typing import List

from apps.reporting.services.report_engine import BaseReportHandler, register_handler

logger = logging.getLogger(__name__)


@register_handler('RPT-FOR-001')
class RevenueForecastHandler(BaseReportHandler):
    """
    Report handler for revenue forecasting.

    Wraps ForecastService.forecast_revenue() with the standard
    BaseReportHandler interface for the report engine.

    Parameters:
        days_ahead (int): Number of days to forecast (default: 30, max: 90)
        lookback_days (int): Historical days for analysis (default: 90)
    """

    feature_key = 'RPT-FOR-001'

    def generate(self, org_id: str, parameters: dict) -> dict:
        """
        Generate a revenue forecast report.

        Args:
            org_id: Organization UUID string
            parameters: Report parameters (validated)

        Returns:
            dict: Forecast result with predictions, confidence, and summary
        """
        from apps.reporting.ai.forecast_service import ForecastService

        days_ahead = parameters.get('days_ahead', 30)
        lookback_days = parameters.get('lookback_days', 90)

        service = ForecastService()
        result = service.forecast_revenue(
            org_id=org_id,
            days_ahead=days_ahead,
            lookback_days=lookback_days,
        )

        return result

    def get_required_permissions(self) -> List[str]:
        """Return required permissions for this report."""
        return ['reporting.view']

    def validate_parameters(self, parameters: dict) -> dict:
        """
        Validate and normalize forecast parameters.

        Args:
            parameters: Raw parameters from the request

        Returns:
            dict: Validated parameters

        Raises:
            ValueError: If parameters are invalid
        """
        validated = super().validate_parameters(parameters)

        days_ahead = validated.get('days_ahead', 30)
        if not isinstance(days_ahead, int) or days_ahead < 1:
            days_ahead = 30
        elif days_ahead > 90:
            days_ahead = 90
        validated['days_ahead'] = days_ahead

        lookback_days = validated.get('lookback_days', 90)
        if not isinstance(lookback_days, int) or lookback_days < 14:
            lookback_days = 90
        elif lookback_days > 365:
            lookback_days = 365
        validated['lookback_days'] = lookback_days

        return validated

    def get_default_parameters(self) -> dict:
        """Return default parameters for revenue forecast."""
        return {
            'days_ahead': 30,
            'lookback_days': 90,
        }

    def get_supported_formats(self) -> List[str]:
        """Return supported export formats."""
        return ['JSON', 'PDF', 'EXCEL', 'CSV']

    def get_cache_ttl(self) -> int:
        """Forecasts can be cached for 1 hour."""
        return 3600
