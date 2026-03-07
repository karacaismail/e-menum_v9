"""
Conversational Analytics Service for the Reporting module.

Manages multi-turn conversation sessions where users can ask
natural language questions about their business data, with
context maintained across turns for follow-up questions.

Flow:
    1. User starts a session -> session_id
    2. User sends a message -> service determines intent
    3. Service calls NLQ or report handlers as needed
    4. Response includes data + natural language summary
    5. Context is accumulated for follow-up questions

Usage:
    from apps.reporting.ai.conversational_service import ConversationalAnalyticsService

    service = ConversationalAnalyticsService()

    # Start a session
    session_id = service.start_session(org_id=org.id, user=request.user)

    # Process messages
    response = service.process_message(
        session_id=session_id,
        message="What was my revenue last week?"
    )
    # response = {
    #     'session_id': '...',
    #     'message_id': '...',
    #     'answer': 'Your revenue last week was ...',
    #     'data': {...},
    #     'visualization_hint': 'bar',
    #     'intent': 'query_revenue',
    #     'confidence': 0.85,
    # }

    # Follow-up with context
    response = service.process_message(
        session_id=session_id,
        message="What about last month?"
    )

Critical Rules:
    - EVERY query MUST filter by organization_id (multi-tenant isolation)
    - EVERY query MUST filter deleted_at__isnull=True (soft delete)
"""

import logging
from datetime import timedelta
from typing import Any, Dict, List

from django.utils import timezone

logger = logging.getLogger(__name__)

# Maximum messages to include in AI context window
MAX_CONTEXT_MESSAGES = 20

# Session auto-expire after inactivity (hours)
SESSION_INACTIVITY_HOURS = 24

# Intent keywords for routing
INTENT_PATTERNS = {
    'query_revenue': [
        'revenue', 'gelir', 'ciro', 'satış', 'sales', 'income',
        'kazanç', 'hasılat',
    ],
    'query_orders': [
        'order', 'sipariş', 'siparis', 'how many orders', 'kaç sipariş',
        'kac siparis',
    ],
    'query_products': [
        'product', 'ürün', 'urun', 'menu item', 'top seller',
        'en çok satan', 'best selling', 'popular',
    ],
    'query_customers': [
        'customer', 'müşteri', 'musteri', 'client', 'visitor',
        'ziyaretçi',
    ],
    'query_trends': [
        'trend', 'growth', 'büyüme', 'decline', 'düşüş',
        'change', 'değişim', 'comparison', 'karşılaştırma',
    ],
    'query_forecast': [
        'forecast', 'tahmin', 'predict', 'öngörü', 'projection',
        'next week', 'next month', 'gelecek',
    ],
    'query_benchmark': [
        'benchmark', 'karşılaştır', 'sektör', 'industry',
        'average', 'ortalama', 'compare',
    ],
    'help': [
        'help', 'yardım', 'ne sorabilir', 'what can',
        'capabilities', 'özellikler',
    ],
}


class ConversationalAnalyticsService:
    """
    Service for managing conversational analytics sessions.

    Provides a multi-turn conversation interface where users can ask
    business questions in natural language. Maintains context across
    turns so follow-up questions work naturally.
    """

    def __init__(self):
        self._nlq_service = None
        self._report_engine = None

    @property
    def nlq_service(self):
        """Lazy-load NLQ service."""
        if self._nlq_service is None:
            from apps.reporting.ai.nlq_service import NLQService
            self._nlq_service = NLQService()
        return self._nlq_service

    @property
    def report_engine(self):
        """Lazy-load report engine."""
        if self._report_engine is None:
            from apps.reporting.services.report_engine import ReportEngine
            self._report_engine = ReportEngine()
        return self._report_engine

    # ─────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────

    def start_session(
        self,
        org_id,
        user,
        title: str = '',
    ) -> str:
        """
        Start a new conversation session.

        Args:
            org_id: Organization UUID (multi-tenant isolation)
            user: User starting the session
            title: Optional session title

        Returns:
            str: Session UUID as string
        """
        from apps.reporting.models import ConversationSession

        session = ConversationSession.objects.create(
            organization_id=org_id,
            user=user,
            title=title or '',
            context_data={
                'org_id': str(org_id),
                'started_at': timezone.now().isoformat(),
                'last_intent': None,
                'last_query_params': {},
                'last_model': None,
                'accumulated_context': [],
            },
            is_active=True,
            last_message_at=timezone.now(),
        )

        logger.info(
            'Conversation session started: session=%s org=%s user=%s',
            session.id, org_id, user.email if hasattr(user, 'email') else user,
        )

        return str(session.id)

    def process_message(
        self,
        session_id: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Process a user message within a conversation session.

        Determines intent, resolves context from previous turns,
        executes the appropriate query or report, and returns
        a structured response with data and natural language summary.

        Args:
            session_id: UUID string of the conversation session
            message: User's natural language message

        Returns:
            dict with keys:
                - session_id (str)
                - message_id (str)
                - answer (str): Natural language response
                - data (dict|list|None): Associated report/query data
                - visualization_hint (str): Suggested chart type
                - intent (str): Detected intent
                - confidence (float): Confidence in interpretation
        """
        from apps.reporting.models import (
            ConversationMessage,
            ConversationSession,
        )

        # Validate and load session
        try:
            session = ConversationSession.objects.get(
                id=session_id,
                is_active=True,
                deleted_at__isnull=True,
            )
        except ConversationSession.DoesNotExist:
            return {
                'session_id': session_id,
                'message_id': None,
                'answer': 'Session not found or expired. Please start a new session.',
                'data': None,
                'visualization_hint': 'text',
                'intent': 'error',
                'confidence': 0.0,
            }

        # Check session expiry
        if session.last_message_at and (
            timezone.now() - session.last_message_at
            > timedelta(hours=SESSION_INACTIVITY_HOURS)
        ):
            session.is_active = False
            session.save(update_fields=['is_active', 'updated_at'])
            return {
                'session_id': session_id,
                'message_id': None,
                'answer': 'Session expired due to inactivity. Please start a new session.',
                'data': None,
                'visualization_hint': 'text',
                'intent': 'expired',
                'confidence': 0.0,
            }

        org_id = session.organization_id

        # Save user message
        ConversationMessage.objects.create(
            session=session,
            role='user',
            content=message,
            metadata={'timestamp': timezone.now().isoformat()},
        )

        # Detect intent
        intent = self._detect_intent(message)

        # Resolve context-aware query
        resolved_message = self._resolve_context(
            message=message,
            intent=intent,
            context_data=session.context_data,
        )

        # Route to appropriate handler
        if intent == 'help':
            response = self._handle_help_intent()
        elif intent.startswith('query_'):
            response = self._handle_query_intent(
                org_id=org_id,
                message=resolved_message,
                intent=intent,
                context_data=session.context_data,
                user=session.user,
            )
        else:
            response = self._handle_general_intent(
                org_id=org_id,
                message=resolved_message,
                context_data=session.context_data,
                user=session.user,
            )

        # Save assistant response
        assistant_msg = ConversationMessage.objects.create(
            session=session,
            role='assistant',
            content=response.get('answer', ''),
            metadata={
                'intent': intent,
                'confidence': response.get('confidence', 0.0),
                'visualization_hint': response.get('visualization_hint', 'text'),
            },
            report_data=response.get('data'),
        )

        # Update session context
        context_data = session.context_data or {}
        context_data['last_intent'] = intent
        context_data['last_query_params'] = response.get('query_params', {})
        context_data['last_model'] = response.get('model_used', None)

        # Maintain accumulated context (last N turns)
        accumulated = context_data.get('accumulated_context', [])
        accumulated.append({
            'intent': intent,
            'message': message,
            'answer_preview': (response.get('answer', ''))[:200],
        })
        if len(accumulated) > MAX_CONTEXT_MESSAGES:
            accumulated = accumulated[-MAX_CONTEXT_MESSAGES:]
        context_data['accumulated_context'] = accumulated

        session.context_data = context_data
        session.last_message_at = timezone.now()

        # Auto-generate title from first question if empty
        if not session.title and intent != 'help':
            session.title = message[:100]

        session.save(update_fields=[
            'context_data', 'last_message_at', 'title', 'updated_at',
        ])

        return {
            'session_id': str(session.id),
            'message_id': str(assistant_msg.id),
            'answer': response.get('answer', ''),
            'data': response.get('data'),
            'visualization_hint': response.get('visualization_hint', 'text'),
            'intent': intent,
            'confidence': response.get('confidence', 0.0),
        }

    def get_session_history(
        self,
        session_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get the message history for a conversation session.

        Args:
            session_id: UUID string of the session

        Returns:
            list of dicts with message details
        """
        from apps.reporting.models import ConversationMessage, ConversationSession

        try:
            session = ConversationSession.objects.get(
                id=session_id,
                deleted_at__isnull=True,
            )
        except ConversationSession.DoesNotExist:
            return []

        messages = ConversationMessage.objects.filter(
            session=session,
        ).order_by('created_at')

        return [
            {
                'id': str(msg.id),
                'role': msg.role,
                'content': msg.content,
                'metadata': msg.metadata,
                'report_data': msg.report_data,
                'created_at': msg.created_at.isoformat(),
            }
            for msg in messages
        ]

    def end_session(self, session_id: str) -> None:
        """
        End a conversation session.

        Args:
            session_id: UUID string of the session
        """
        from apps.reporting.models import ConversationSession

        try:
            session = ConversationSession.objects.get(
                id=session_id,
                deleted_at__isnull=True,
            )
            session.is_active = False
            session.save(update_fields=['is_active', 'updated_at'])
            logger.info('Conversation session ended: %s', session_id)
        except ConversationSession.DoesNotExist:
            logger.warning(
                'Attempted to end non-existent session: %s', session_id,
            )

    # ─────────────────────────────────────────────────────────
    # INTENT DETECTION
    # ─────────────────────────────────────────────────────────

    def _detect_intent(self, message: str) -> str:
        """
        Detect the user's intent from their message using keyword matching.

        Args:
            message: User's natural language message

        Returns:
            str: Detected intent key
        """
        message_lower = message.lower().strip()

        best_intent = 'general'
        best_score = 0

        for intent, keywords in INTENT_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > best_score:
                best_score = score
                best_intent = intent

        logger.debug(
            'Intent detected: message=%r intent=%s score=%d',
            message[:50], best_intent, best_score,
        )

        return best_intent

    # ─────────────────────────────────────────────────────────
    # CONTEXT RESOLUTION
    # ─────────────────────────────────────────────────────────

    def _resolve_context(
        self,
        message: str,
        intent: str,
        context_data: dict,
    ) -> str:
        """
        Resolve contextual references in the message using conversation history.

        Handles cases like:
            - "What about last month?" -> uses previous query's subject
            - "Show me that as a chart" -> uses previous query's data
            - "Compare with yesterday" -> adds comparison to previous query

        Args:
            message: Raw user message
            intent: Detected intent
            context_data: Accumulated session context

        Returns:
            str: Context-enriched message
        """
        message_lower = message.lower().strip()

        # Check for context-dependent phrases
        context_phrases = [
            'what about', 'how about', 'and for', 'show me',
            'ne olacak', 'peki', 'ya', 'aynısı',
            'same for', 'same thing', 'compare with',
        ]

        needs_context = any(phrase in message_lower for phrase in context_phrases)

        if not needs_context:
            return message

        # Try to enrich message with previous context
        last_intent = context_data.get('last_intent', '')
        accumulated = context_data.get('accumulated_context', [])

        if not accumulated:
            return message

        # Get the last meaningful query
        last_turn = accumulated[-1] if accumulated else {}
        last_message = last_turn.get('message', '')

        if last_intent and last_intent.startswith('query_'):
            # Extract the subject from the last query
            subject = self._extract_subject(last_message, last_intent)
            if subject:
                enriched = f'{subject}. {message}'
                logger.debug(
                    'Context-enriched message: %r -> %r',
                    message[:50], enriched[:80],
                )
                return enriched

        return message

    @staticmethod
    def _extract_subject(message: str, intent: str) -> str:
        """
        Extract the subject/topic from a previous query message.

        Args:
            message: Previous query message
            intent: Intent of the previous message

        Returns:
            str: Extracted subject or empty string
        """
        intent_subjects = {
            'query_revenue': 'revenue data',
            'query_orders': 'order data',
            'query_products': 'product performance',
            'query_customers': 'customer data',
            'query_trends': 'trend analysis',
            'query_forecast': 'forecast data',
            'query_benchmark': 'benchmark comparison',
        }
        return intent_subjects.get(intent, '')

    # ─────────────────────────────────────────────────────────
    # INTENT HANDLERS
    # ─────────────────────────────────────────────────────────

    def _handle_help_intent(self) -> Dict[str, Any]:
        """Handle help/capability queries."""
        help_text = (
            'I can help you analyze your business data. You can ask me about:\n\n'
            '- **Revenue & Sales**: "What was my revenue last week?"\n'
            '- **Orders**: "How many orders did I get today?"\n'
            '- **Products**: "What are my top selling products?"\n'
            '- **Customers**: "How many new customers this month?"\n'
            '- **Trends**: "Show me revenue trends for the last 30 days"\n'
            '- **Forecasts**: "What is my predicted revenue for next week?"\n'
            '- **Benchmarks**: "How do I compare to the industry average?"\n\n'
            'You can also ask follow-up questions like '
            '"What about last month?" and I will use the context '
            'from your previous question.'
        )
        return {
            'answer': help_text,
            'data': None,
            'visualization_hint': 'text',
            'confidence': 1.0,
        }

    def _handle_query_intent(
        self,
        org_id,
        message: str,
        intent: str,
        context_data: dict,
        user=None,
    ) -> Dict[str, Any]:
        """
        Handle data query intents by routing to NLQ service.

        Args:
            org_id: Organization UUID
            message: Context-resolved message
            intent: Detected intent
            context_data: Session context
            user: Current user

        Returns:
            dict: Response with answer, data, visualization hint
        """
        try:
            nlq_result = self.nlq_service.process_query(
                org_id=org_id,
                question=message,
                user=user,
            )

            return {
                'answer': nlq_result.get('answer', ''),
                'data': nlq_result.get('data'),
                'visualization_hint': nlq_result.get('visualization_hint', 'table'),
                'confidence': nlq_result.get('confidence', 0.0),
                'query_params': {
                    'query_type': nlq_result.get('query_type', ''),
                },
                'model_used': 'nlq',
            }

        except Exception as exc:
            logger.error(
                'NLQ query failed in conversation: org=%s message=%r error=%s',
                org_id, message[:50], exc,
            )
            return {
                'answer': (
                    'I encountered an issue processing your question. '
                    'Please try rephrasing it or ask a simpler question.'
                ),
                'data': None,
                'visualization_hint': 'text',
                'confidence': 0.0,
            }

    def _handle_general_intent(
        self,
        org_id,
        message: str,
        context_data: dict,
        user=None,
    ) -> Dict[str, Any]:
        """
        Handle general/unclassified messages.

        Falls back to NLQ service for best-effort interpretation.

        Args:
            org_id: Organization UUID
            message: User message
            context_data: Session context
            user: Current user

        Returns:
            dict: Response
        """
        try:
            nlq_result = self.nlq_service.process_query(
                org_id=org_id,
                question=message,
                user=user,
            )

            if nlq_result.get('query_type') == 'error':
                return {
                    'answer': (
                        'I am not sure I understand your question. '
                        'Try asking about revenue, orders, products, '
                        'or customers. Type "help" to see what I can do.'
                    ),
                    'data': None,
                    'visualization_hint': 'text',
                    'confidence': 0.1,
                }

            return {
                'answer': nlq_result.get('answer', ''),
                'data': nlq_result.get('data'),
                'visualization_hint': nlq_result.get('visualization_hint', 'table'),
                'confidence': nlq_result.get('confidence', 0.0),
                'model_used': 'nlq',
            }

        except Exception as exc:
            logger.error(
                'General intent handling failed: org=%s error=%s',
                org_id, exc,
            )
            return {
                'answer': (
                    'Something went wrong processing your request. '
                    'Please try again or type "help" for available commands.'
                ),
                'data': None,
                'visualization_hint': 'text',
                'confidence': 0.0,
            }
