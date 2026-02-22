"""
Daily AI Insights Report Handler (RPT-AII-001).

Generates automated daily business insights using the InsightService.
Registered with the report engine as feature_key 'RPT-AII-001'.

Usage:
    # Via the ReportEngine (preferred):
    engine = ReportEngine()
    execution = engine.execute_report(
        org_id=org.id,
        feature_key='RPT-AII-001',
        parameters={'date': '2026-02-15'},
        user=request.user,
    )

    # Direct handler usage (for testing):
    handler = DailyInsightsHandler()
    result = handler.generate(org_id=str(org.id), parameters={})
"""

import logging
from datetime import date, datetime
from typing import List, Optional

from django.utils import timezone

from apps.reporting.services.report_engine import BaseReportHandler, register_handler

logger = logging.getLogger(__name__)


@register_handler('RPT-AII-001')
class DailyInsightsHandler(BaseReportHandler):
    """
    Report handler for daily AI-powered business insights.

    Wraps InsightService.generate_daily_insights() with the standard
    BaseReportHandler interface for the report engine.

    Parameters:
        date (str): Target date in ISO format (default: today)
    """

    feature_key = 'RPT-AII-001'

    def generate(self, org_id: str, parameters: dict) -> dict:
        """
        Generate daily insights report.

        Args:
            org_id: Organization UUID string
            parameters: Report parameters (validated)

        Returns:
            dict: Report result with insights list
        """
        from apps.reporting.ai.insight_service import InsightService

        target_date = parameters.get('date')
        if isinstance(target_date, str):
            try:
                target_date = date.fromisoformat(target_date)
            except ValueError:
                target_date = None

        if not isinstance(target_date, date):
            target_date = timezone.localdate()

        service = InsightService()
        insights = service.generate_daily_insights(
            org_id=org_id,
            date_val=target_date,
        )

        # Build summary counts by type and severity
        type_counts = {}
        severity_counts = {}
        for insight in insights:
            itype = insight.get('type', 'unknown')
            isev = insight.get('severity', 'info')
            type_counts[itype] = type_counts.get(itype, 0) + 1
            severity_counts[isev] = severity_counts.get(isev, 0) + 1

        return {
            'date': target_date.isoformat(),
            'insights': insights,
            'summary': {
                'total_insights': len(insights),
                'by_type': type_counts,
                'by_severity': severity_counts,
            },
        }

    def get_required_permissions(self) -> List[str]:
        """Return required permissions for this report."""
        return ['reporting.view']

    def validate_parameters(self, parameters: dict) -> dict:
        """
        Validate and normalize insight parameters.

        Args:
            parameters: Raw parameters from the request

        Returns:
            dict: Validated parameters
        """
        validated = super().validate_parameters(parameters)

        # Validate date parameter if provided
        date_val = validated.get('date')
        if date_val is not None:
            if isinstance(date_val, str):
                try:
                    date.fromisoformat(date_val)
                except ValueError:
                    validated['date'] = None
            elif not isinstance(date_val, date):
                validated['date'] = None

        return validated

    def get_default_parameters(self) -> dict:
        """Return default parameters for daily insights."""
        return {
            'date': None,  # Defaults to today in generate()
        }

    def get_supported_formats(self) -> List[str]:
        """Return supported export formats."""
        return ['JSON', 'PDF']

    def get_cache_ttl(self) -> int:
        """Insights can be cached for 30 minutes."""
        return 1800
