"""
Natural Language Query Report Handler (RPT-AIQ-001).

Enables natural language questions about business data via the NLQService.
Registered with the report engine as feature_key 'RPT-AIQ-001'.

Usage:
    # Via the ReportEngine (preferred):
    engine = ReportEngine()
    execution = engine.execute_report(
        org_id=org.id,
        feature_key='RPT-AIQ-001',
        parameters={'question': 'What was my revenue last week?'},
        user=request.user,
    )

    # Direct handler usage (for testing):
    handler = NLQHandler()
    result = handler.generate(
        org_id=str(org.id),
        parameters={'question': 'Top 5 selling products'},
    )
"""

import logging
from typing import List

from apps.reporting.services.report_engine import BaseReportHandler, register_handler
from shared.utils.exceptions import AppException

logger = logging.getLogger(__name__)


@register_handler('RPT-AIQ-001')
class NLQHandler(BaseReportHandler):
    """
    Report handler for natural language data queries.

    Wraps NLQService.process_query() with the standard
    BaseReportHandler interface for the report engine.

    Parameters:
        question (str): Natural language question (required)
    """

    feature_key = 'RPT-AIQ-001'

    def generate(self, org_id: str, parameters: dict) -> dict:
        """
        Process a natural language query.

        Args:
            org_id: Organization UUID string
            parameters: Report parameters (must include 'question')

        Returns:
            dict: NLQ result with answer, data, and visualization hints

        Raises:
            AppException: If 'question' parameter is missing
        """
        from apps.reporting.ai.nlq_service import NLQService

        question = parameters.get('question', '').strip()
        if not question:
            raise AppException(
                code='VALIDATION_ERROR',
                message='The "question" parameter is required for NLQ reports.',
                status_code=400,
            )

        user = self._context.get('user')

        service = NLQService()
        result = service.process_query(
            org_id=org_id,
            question=question,
            user=user,
        )

        return result

    def get_required_permissions(self) -> List[str]:
        """Return required permissions for this report."""
        return ['reporting.view']

    def validate_parameters(self, parameters: dict) -> dict:
        """
        Validate NLQ parameters.

        Args:
            parameters: Raw parameters from the request

        Returns:
            dict: Validated parameters

        Raises:
            AppException: If question is missing or empty
        """
        validated = super().validate_parameters(parameters)

        question = validated.get('question', '')
        if not isinstance(question, str) or not question.strip():
            raise AppException(
                code='VALIDATION_ERROR',
                message='A non-empty "question" string is required.',
                status_code=400,
            )

        # Limit question length to prevent abuse
        validated['question'] = question.strip()[:500]

        return validated

    def get_default_parameters(self) -> dict:
        """Return default parameters (none; question is required)."""
        return {}

    def get_supported_formats(self) -> List[str]:
        """NLQ results are JSON only."""
        return ['JSON']

    def get_cache_ttl(self) -> int:
        """NLQ results are not cached (each query is unique)."""
        return 0
