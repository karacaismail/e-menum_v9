"""
Natural Language Query (NLQ) Service for the Reporting module.

Converts user questions about business data into Django ORM queries,
executes them with multi-tenant isolation, and returns AI-formatted
natural language answers.

Flow:
    1. User asks a question (e.g., "What was my revenue last week?")
    2. Build schema context describing available models/fields
    3. AI generates a structured query plan (JSON)
    4. Parse and validate the query plan into safe ORM operations
    5. Execute with organization_id filter (MANDATORY)
    6. AI formats the results into a human-readable answer

Usage:
    from apps.reporting.ai.nlq_service import NLQService

    service = NLQService()
    result = service.process_query(
        org_id=organization.id,
        question="What are my top 5 selling products this month?",
        user=request.user,
    )
    # result = {
    #     'question': 'What are my top 5 selling products this month?',
    #     'answer': 'Your top 5 products this month are...',
    #     'data': [...],
    #     'visualization_hint': 'bar',
    #     'query_type': 'aggregation',
    #     'confidence': 0.85,
    # }

Critical Rules:
    - EVERY query MUST filter by organization_id (multi-tenant isolation)
    - EVERY query MUST filter deleted_at__isnull=True (soft delete)
    - Only read-only operations are permitted (no create/update/delete)
    - Query results are limited to prevent excessive data transfer
"""

import json
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional

from django.conf import settings
from django.db.models import (
    Avg,
    Count,
    Max,
    Min,
    Sum,
)
from django.utils import timezone

logger = logging.getLogger(__name__)

# Maximum number of rows returned from any single NLQ query
MAX_QUERY_ROWS = 500

# Models that NLQ is allowed to query, mapped to their import paths
SUPPORTED_MODELS = {
    'Order': 'apps.orders.models.Order',
    'OrderItem': 'apps.orders.models.OrderItem',
    'Product': 'apps.menu.models.Product',
    'Category': 'apps.menu.models.Category',
    'Customer': 'apps.customers.models.Customer',
    'SalesAggregation': 'apps.analytics.models.SalesAggregation',
    'DashboardMetric': 'apps.analytics.models.DashboardMetric',
    'ProductPerformance': 'apps.analytics.models.ProductPerformance',
    'CustomerMetric': 'apps.analytics.models.CustomerMetric',
}

# Allowed aggregation functions (whitelist for safety)
ALLOWED_AGGREGATIONS = {
    'sum': Sum,
    'avg': Avg,
    'count': Count,
    'min': Min,
    'max': Max,
}

# Allowed ordering directions
ALLOWED_ORDERINGS = {'asc', 'desc'}


class NLQService:
    """
    Converts natural language questions to Django ORM queries.

    Provides a safe, tenant-isolated interface for querying business data
    using natural language. All queries are read-only and organization-scoped.
    """

    def __init__(self):
        self._model_cache: Dict[str, Any] = {}

    # ─────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────

    def process_query(
        self,
        org_id,
        question: str,
        user=None,
    ) -> dict:
        """
        Process a natural language question about business data.

        Args:
            org_id: Organization UUID (tenant isolation)
            question: Natural language question from the user
            user: Optional user object for audit/context

        Returns:
            dict with keys:
                - question (str): Original question
                - answer (str): AI-generated natural language answer
                - data (list|dict): Raw query result data
                - visualization_hint (str): Suggested chart type
                - query_type (str): Type of query executed
                - confidence (float): AI confidence in the interpretation

        Raises:
            ValueError: If the question is empty or query plan is invalid
        """
        if not question or not question.strip():
            return {
                'question': question,
                'answer': 'Please provide a question about your business data.',
                'data': [],
                'visualization_hint': 'text',
                'query_type': 'error',
                'confidence': 0.0,
            }

        question = question.strip()

        # Step 1: Build schema context for the AI
        schema_context = self._build_schema_context()

        # Step 2: Generate query plan via AI
        query_plan = self._generate_query_plan(question, schema_context)
        if not query_plan:
            return {
                'question': question,
                'answer': (
                    'I was unable to interpret your question. '
                    'Please try rephrasing it or ask about revenue, '
                    'orders, products, or customers.'
                ),
                'data': [],
                'visualization_hint': 'text',
                'query_type': 'error',
                'confidence': 0.0,
            }

        # Step 3: Validate and execute the query plan
        try:
            data = self._execute_query_plan(org_id, query_plan)
        except Exception as exc:
            logger.warning(
                'NLQ query execution failed for org=%s question=%r error=%s',
                org_id, question, exc,
            )
            return {
                'question': question,
                'answer': (
                    'I understood your question but encountered an error '
                    'running the query. Please try a simpler question.'
                ),
                'data': [],
                'visualization_hint': 'text',
                'query_type': query_plan.get('query_type', 'unknown'),
                'confidence': query_plan.get('confidence', 0.0),
            }

        # Step 4: Generate a natural language answer from the results
        answer = self._generate_answer(question, data, query_plan)

        return {
            'question': question,
            'answer': answer or self._fallback_answer(data, query_plan),
            'data': data,
            'visualization_hint': query_plan.get('visualization', 'table'),
            'query_type': query_plan.get('query_type', 'query'),
            'confidence': query_plan.get('confidence', 0.7),
        }

    # ─────────────────────────────────────────────────────────
    # SCHEMA CONTEXT
    # ─────────────────────────────────────────────────────────

    def _build_schema_context(self) -> str:
        """
        Build a text description of available models and fields for AI context.

        Returns:
            str: Human-readable schema description for the AI system prompt.
        """
        return """
Available models and their key fields:

1. Order (apps.orders.models.Order)
   - organization_id (UUID, FK): Tenant identifier
   - order_number (str): Human-readable order number
   - status (str): PENDING, CONFIRMED, PREPARING, READY, DELIVERED, COMPLETED, CANCELLED
   - type (str): DINE_IN, TAKEAWAY, DELIVERY
   - payment_status (str): PENDING, PARTIAL, PAID, REFUNDED
   - payment_method (str): CASH, CREDIT_CARD, DEBIT_CARD, ONLINE
   - subtotal (Decimal): Before tax/discount
   - tax_amount (Decimal): Tax amount
   - discount_amount (Decimal): Discount applied
   - total_amount (Decimal): Final total
   - customer_id (UUID, FK): Optional customer reference
   - table_id (UUID, FK): Optional table reference
   - guest_count (int): Number of guests
   - placed_at (datetime): When the order was placed
   - completed_at (datetime): When the order was completed
   - created_at (datetime): Record creation time
   - deleted_at (datetime, nullable): Soft delete timestamp

2. OrderItem (apps.orders.models.OrderItem)
   - order_id (UUID, FK): Parent order
   - product_id (UUID, FK): Product ordered
   - quantity (int): Quantity ordered
   - unit_price (Decimal): Price per unit at order time
   - total_price (Decimal): Total for this line item
   - status (str): PENDING, PREPARING, READY, DELIVERED, CANCELLED

3. Product (apps.menu.models.Product)
   - organization_id (UUID, FK): Tenant identifier
   - category_id (UUID, FK): Category reference
   - name (str): Product name
   - price (Decimal): Base price
   - is_available (bool): Availability flag
   - created_at (datetime): Record creation time
   - deleted_at (datetime, nullable): Soft delete timestamp

4. Category (apps.menu.models.Category)
   - organization_id (UUID, FK): Tenant identifier
   - menu_id (UUID, FK): Menu reference
   - name (str): Category name
   - deleted_at (datetime, nullable): Soft delete timestamp

5. Customer (apps.customers.models.Customer)
   - organization_id (UUID, FK): Tenant identifier
   - name (str): Customer name
   - email (str): Customer email
   - phone (str): Customer phone
   - total_orders (int): Denormalized total orders
   - total_spent (Decimal): Denormalized total spend
   - first_visit_at (datetime): First visit date
   - last_visit_at (datetime): Most recent visit
   - created_at (datetime): Record creation time
   - deleted_at (datetime, nullable): Soft delete timestamp

6. SalesAggregation (apps.analytics.models.SalesAggregation)
   - organization_id (UUID, FK): Tenant identifier
   - date (date): Aggregation date
   - hour (int, nullable): Hour (0-23) for hourly granularity
   - granularity (str): HOURLY, DAILY
   - gross_revenue (Decimal): Total revenue before discounts
   - net_revenue (Decimal): Revenue after discounts
   - order_count (int): Number of orders
   - item_count (int): Total items sold
   - avg_order_value (Decimal): Average order value
   - customer_count (int): Distinct customer count
   - new_customer_count (int): First-time customers
   - deleted_at (datetime, nullable): Soft delete timestamp

7. DashboardMetric (apps.analytics.models.DashboardMetric)
   - organization_id (UUID, FK): Tenant identifier
   - metric_type (str): REVENUE, ORDERS, CUSTOMERS, AVG_ORDER, etc.
   - period_type (str): DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY
   - period_start (date): Period start date
   - period_end (date): Period end date
   - value (Decimal): Current period value
   - previous_value (Decimal): Previous period value
   - change_percent (Decimal): Percentage change
   - deleted_at (datetime, nullable): Soft delete timestamp

8. ProductPerformance (apps.analytics.models.ProductPerformance)
   - organization_id (UUID, FK): Tenant identifier
   - product_id (UUID, FK): Product reference
   - period_type (str): DAILY, WEEKLY, MONTHLY, etc.
   - period_start (date): Period start
   - period_end (date): Period end
   - quantity_sold (int): Units sold
   - revenue (Decimal): Revenue generated
   - cost (Decimal, nullable): Cost if known
   - profit_margin (Decimal, nullable): Profit margin %
   - sales_mix_percent (Decimal): Share of total sales
   - deleted_at (datetime, nullable): Soft delete timestamp

9. CustomerMetric (apps.analytics.models.CustomerMetric)
   - organization_id (UUID, FK): Tenant identifier
   - date (date): Metric date
   - total_customers (int): Total registered customers
   - new_customers (int): New customers on this date
   - returning_customers (int): Returning customers
   - churn_count (int): Churned customers
   - avg_lifetime_value (Decimal, nullable): Average CLV
   - deleted_at (datetime, nullable): Soft delete timestamp
""".strip()

    # ─────────────────────────────────────────────────────────
    # AI QUERY PLAN GENERATION
    # ─────────────────────────────────────────────────────────

    def _generate_query_plan(self, question: str, schema_context: str) -> Optional[dict]:
        """
        Use AI to convert a natural language question into a structured query plan.

        Args:
            question: The user's natural language question
            schema_context: Text description of available data models

        Returns:
            dict: Structured query plan or None if AI call failed
        """
        system_prompt = f"""You are a data analyst assistant for a restaurant management platform.
Your job is to convert natural language questions into structured JSON query plans.

{schema_context}

IMPORTANT RULES:
1. ALWAYS use organization_id for tenant isolation - you do NOT need to specify it, it is added automatically.
2. ALWAYS filter deleted_at__isnull=True - this is added automatically.
3. Only return SELECT/READ operations. No mutations allowed.
4. Use SalesAggregation for time-based revenue/sales queries (it's pre-aggregated).
5. Use ProductPerformance for product-level metrics.
6. Use Order/OrderItem for detailed order analysis.
7. Use Customer for customer demographics/counts.
8. Use CustomerMetric for customer trends over time.

Return ONLY valid JSON with this structure:
{{
    "model": "ModelName",
    "query_type": "aggregation" | "list" | "count" | "single_value",
    "filters": {{"field__lookup": "value"}},
    "annotations": {{"alias": {{"func": "sum|avg|count|min|max", "field": "field_name"}}}},
    "values": ["field1", "field2"],
    "order_by": ["-field"],
    "limit": 10,
    "visualization": "bar" | "line" | "pie" | "table" | "number",
    "confidence": 0.0-1.0
}}

For date filters, use these relative keywords:
- "today", "yesterday", "last_7_days", "last_30_days", "this_month", "last_month", "this_year"

Examples:
- "Revenue last 7 days" -> model: SalesAggregation, filters: {{"date__gte": "last_7_days"}}, annotations: {{"total": {{"func": "sum", "field": "net_revenue"}}}}
- "Top 5 products" -> model: ProductPerformance, order_by: ["-revenue"], limit: 5, values: ["product__name", "revenue", "quantity_sold"]
- "How many orders today" -> model: SalesAggregation, filters: {{"date": "today", "granularity": "DAILY"}}, query_type: "single_value", annotations: {{"total": {{"func": "sum", "field": "order_count"}}}}
"""

        user_prompt = f"Convert this question to a query plan:\n\n\"{question}\""

        response_text = self._call_ai(system_prompt, user_prompt)
        if not response_text:
            # Fallback: attempt simple keyword-based plan generation
            return self._keyword_fallback_plan(question)

        return self._parse_json_response(response_text)

    def _generate_answer(
        self,
        question: str,
        data: list,
        query_plan: dict,
    ) -> Optional[str]:
        """
        Use AI to generate a natural language answer from query results.

        Args:
            question: The original user question
            data: Query result data
            query_plan: The executed query plan

        Returns:
            str: Natural language answer, or None if AI is not available
        """
        if not data:
            return 'No data found matching your query for the specified time period.'

        # Truncate data for the AI prompt to avoid token limits
        data_preview = data[:20] if len(data) > 20 else data
        data_str = json.dumps(data_preview, default=str, ensure_ascii=False)

        system_prompt = """You are a data analyst assistant for a restaurant.
Generate a concise, helpful natural language answer based on the query results.
Include key numbers and insights. Use Turkish Lira (TL) for currency.
Be specific with numbers. Round decimals to 2 places.
Keep the answer to 2-4 sentences maximum.
If the data is a list, summarize the key findings.
Respond in the same language as the question."""

        user_prompt = (
            f"Question: \"{question}\"\n\n"
            f"Query type: {query_plan.get('query_type', 'query')}\n"
            f"Results ({len(data)} rows):\n{data_str}"
        )

        return self._call_ai(system_prompt, user_prompt)

    # ─────────────────────────────────────────────────────────
    # QUERY EXECUTION
    # ─────────────────────────────────────────────────────────

    def _execute_query_plan(self, org_id, query_plan: dict) -> list:
        """
        Execute a validated query plan using Django ORM.

        ALWAYS adds organization_id and deleted_at__isnull=True filters.

        Args:
            org_id: Organization UUID
            query_plan: Structured query plan dict

        Returns:
            list: Query results as list of dicts

        Raises:
            ValueError: If the model name is not in the supported list
        """
        model_name = query_plan.get('model', '')
        if model_name not in SUPPORTED_MODELS:
            raise ValueError(f'Unsupported model: {model_name}')

        model_class = self._get_model_class(model_name)
        if model_class is None:
            raise ValueError(f'Could not import model: {model_name}')

        # Start with base queryset -- ALWAYS org-scoped and soft-delete aware
        qs = model_class.objects.filter(deleted_at__isnull=True)

        # Apply organization filter
        # Some models have organization_id directly, OrderItem uses order__organization_id
        if model_name == 'OrderItem':
            qs = qs.filter(order__organization_id=org_id)
        else:
            qs = qs.filter(organization_id=org_id)

        # Apply user-specified filters
        filters = query_plan.get('filters', {})
        resolved_filters = self._resolve_filters(filters)
        if resolved_filters:
            qs = qs.filter(**resolved_filters)

        # Apply annotations (aggregations)
        annotations = query_plan.get('annotations', {})
        orm_annotations = self._build_annotations(annotations)
        if orm_annotations:
            qs = qs.annotate(**orm_annotations)

        # Apply values (GROUP BY)
        values = query_plan.get('values', [])
        if values:
            safe_values = self._validate_field_names(values)
            qs = qs.values(*safe_values)

        # Apply annotations after values for proper GROUP BY
        if orm_annotations and values:
            qs = qs.annotate(**orm_annotations)
        elif orm_annotations and not values:
            # Aggregate without grouping
            result = qs.aggregate(**orm_annotations)
            return [self._serialize_row(result)]

        # Apply ordering
        order_by = query_plan.get('order_by', [])
        if order_by:
            safe_order = self._validate_order_fields(order_by)
            qs = qs.order_by(*safe_order)

        # Apply limit
        limit = min(
            int(query_plan.get('limit', MAX_QUERY_ROWS)),
            MAX_QUERY_ROWS,
        )
        qs = qs[:limit]

        # Execute and serialize
        results = list(qs)
        return [self._serialize_row(row) for row in results]

    def _get_model_class(self, model_name: str):
        """
        Import and cache a model class by its name.

        Args:
            model_name: Key from SUPPORTED_MODELS dict

        Returns:
            Django model class or None
        """
        if model_name in self._model_cache:
            return self._model_cache[model_name]

        model_path = SUPPORTED_MODELS.get(model_name)
        if not model_path:
            return None

        try:
            module_path, class_name = model_path.rsplit('.', 1)
            from importlib import import_module
            module = import_module(module_path)
            model_class = getattr(module, class_name)
            self._model_cache[model_name] = model_class
            return model_class
        except (ImportError, AttributeError) as exc:
            logger.error('Failed to import model %s: %s', model_name, exc)
            return None

    def _resolve_filters(self, filters: dict) -> dict:
        """
        Resolve relative date keywords in filter values to actual dates.

        Supported keywords: today, yesterday, last_7_days, last_30_days,
        this_month, last_month, this_year.

        Args:
            filters: Raw filter dict from the query plan

        Returns:
            dict: Resolved filter dict with actual date values
        """
        today = timezone.localdate()
        resolved = {}

        date_keywords = {
            'today': today,
            'yesterday': today - timedelta(days=1),
            'last_7_days': today - timedelta(days=7),
            'last_14_days': today - timedelta(days=14),
            'last_30_days': today - timedelta(days=30),
            'last_90_days': today - timedelta(days=90),
            'this_month': today.replace(day=1),
            'last_month': (today.replace(day=1) - timedelta(days=1)).replace(day=1),
            'this_year': today.replace(month=1, day=1),
        }

        for key, value in filters.items():
            # Validate the field name part (before __lookup)
            field_base = key.split('__')[0]
            if not field_base.replace('_', '').isalnum():
                logger.warning('Skipping suspicious filter key: %s', key)
                continue

            if isinstance(value, str) and value in date_keywords:
                # For __gte lookups with range keywords, use the start date
                if key.endswith('__gte') or key.endswith('__gt'):
                    resolved[key] = date_keywords[value]
                elif key.endswith('__lte') or key.endswith('__lt'):
                    resolved[key] = date_keywords.get(value, value)
                else:
                    # Exact match
                    resolved[key] = date_keywords[value]
            elif isinstance(value, str) and value.startswith('last_month_end'):
                # End of last month
                resolved[key] = today.replace(day=1) - timedelta(days=1)
            else:
                resolved[key] = value

        return resolved

    def _build_annotations(self, annotations: dict) -> dict:
        """
        Convert annotation specifications to Django ORM aggregation objects.

        Args:
            annotations: Dict of {alias: {"func": "sum", "field": "field_name"}}

        Returns:
            dict: Django ORM annotation kwargs
        """
        orm_annotations = {}

        for alias, spec in annotations.items():
            if not isinstance(spec, dict):
                continue

            func_name = spec.get('func', '').lower()
            field_name = spec.get('field', '')

            if func_name not in ALLOWED_AGGREGATIONS:
                logger.warning('Skipping unsupported aggregation: %s', func_name)
                continue

            if not self._is_safe_field_name(field_name):
                logger.warning('Skipping suspicious field name: %s', field_name)
                continue

            safe_alias = alias.replace('-', '_').replace(' ', '_')
            if not safe_alias.isidentifier():
                safe_alias = f'agg_{safe_alias}'

            agg_class = ALLOWED_AGGREGATIONS[func_name]

            if func_name == 'count' and field_name == '*':
                orm_annotations[safe_alias] = Count('id')
            else:
                orm_annotations[safe_alias] = agg_class(field_name)

        return orm_annotations

    def _validate_field_names(self, fields: list) -> list:
        """
        Validate and sanitize field names for use in .values() calls.

        Args:
            fields: List of field name strings

        Returns:
            list: Validated field names
        """
        safe_fields = []
        for field in fields:
            if isinstance(field, str) and self._is_safe_field_name(field):
                safe_fields.append(field)
            else:
                logger.warning('Skipping invalid field name: %s', field)
        return safe_fields

    def _validate_order_fields(self, order_by: list) -> list:
        """
        Validate ordering field specifications.

        Args:
            order_by: List of order field strings (may start with '-')

        Returns:
            list: Validated order fields
        """
        safe_order = []
        for field in order_by:
            if not isinstance(field, str):
                continue
            clean = field.lstrip('-')
            if self._is_safe_field_name(clean):
                prefix = '-' if field.startswith('-') else ''
                safe_order.append(f'{prefix}{clean}')
        return safe_order

    @staticmethod
    def _is_safe_field_name(name: str) -> bool:
        """
        Check if a field name is safe for ORM usage (no SQL injection risk).

        Allows alphanumeric, underscores, and double-underscore lookups
        (e.g., product__name, order__organization_id).

        Args:
            name: Field name to validate

        Returns:
            bool: True if the field name is safe
        """
        if not name or not isinstance(name, str):
            return False
        # Allow Django's double-underscore lookups
        parts = name.split('__')
        return all(part.replace('_', '').isalnum() for part in parts if part)

    @staticmethod
    def _serialize_row(row) -> dict:
        """
        Convert a query result row to a JSON-serializable dict.

        Handles Decimal, date, datetime, UUID, and other non-serializable types.

        Args:
            row: A dict or model instance from the queryset

        Returns:
            dict: JSON-serializable dictionary
        """
        if isinstance(row, dict):
            serialized = {}
            for key, value in row.items():
                if isinstance(value, Decimal):
                    serialized[key] = float(value)
                elif isinstance(value, (date, datetime)):
                    serialized[key] = value.isoformat()
                elif hasattr(value, 'hex'):
                    # UUID
                    serialized[key] = str(value)
                else:
                    serialized[key] = value
            return serialized
        # Model instance -- convert relevant fields
        return {'id': str(row.pk), 'str': str(row)}

    # ─────────────────────────────────────────────────────────
    # FALLBACK KEYWORD PLAN
    # ─────────────────────────────────────────────────────────

    def _keyword_fallback_plan(self, question: str) -> Optional[dict]:
        """
        Generate a simple query plan based on keyword matching when AI is unavailable.

        Args:
            question: The user's question

        Returns:
            dict: A basic query plan or None
        """
        q = question.lower()

        # Revenue / sales questions
        if any(kw in q for kw in ['revenue', 'gelir', 'ciro', 'satis', 'sales']):
            plan = {
                'model': 'SalesAggregation',
                'query_type': 'aggregation',
                'filters': {'granularity': 'DAILY'},
                'annotations': {
                    'total_revenue': {'func': 'sum', 'field': 'net_revenue'},
                },
                'values': [],
                'order_by': [],
                'limit': 1,
                'visualization': 'number',
                'confidence': 0.4,
            }
            # Time range detection
            if any(kw in q for kw in ['today', 'bugun', 'bugunku']):
                plan['filters']['date'] = 'today'
            elif any(kw in q for kw in ['yesterday', 'dun', 'dunku']):
                plan['filters']['date'] = 'yesterday'
            elif any(kw in q for kw in ['week', 'hafta']):
                plan['filters']['date__gte'] = 'last_7_days'
            elif any(kw in q for kw in ['month', 'ay']):
                plan['filters']['date__gte'] = 'last_30_days'
            else:
                plan['filters']['date__gte'] = 'last_30_days'
            return plan

        # Order count questions
        if any(kw in q for kw in ['order', 'siparis', 'how many orders', 'kac siparis']):
            plan = {
                'model': 'SalesAggregation',
                'query_type': 'aggregation',
                'filters': {'granularity': 'DAILY'},
                'annotations': {
                    'total_orders': {'func': 'sum', 'field': 'order_count'},
                },
                'values': [],
                'order_by': [],
                'limit': 1,
                'visualization': 'number',
                'confidence': 0.4,
            }
            if any(kw in q for kw in ['today', 'bugun']):
                plan['filters']['date'] = 'today'
            else:
                plan['filters']['date__gte'] = 'last_7_days'
            return plan

        # Top products
        if any(kw in q for kw in ['top', 'best', 'en cok', 'populer', 'popular']):
            return {
                'model': 'ProductPerformance',
                'query_type': 'list',
                'filters': {'period_type': 'MONTHLY'},
                'annotations': {},
                'values': ['product__name', 'revenue', 'quantity_sold'],
                'order_by': ['-revenue'],
                'limit': 10,
                'visualization': 'bar',
                'confidence': 0.3,
            }

        # Customer questions
        if any(kw in q for kw in ['customer', 'musteri', 'musteriler']):
            return {
                'model': 'CustomerMetric',
                'query_type': 'list',
                'filters': {'date__gte': 'last_30_days'},
                'annotations': {},
                'values': ['date', 'total_customers', 'new_customers', 'returning_customers'],
                'order_by': ['-date'],
                'limit': 30,
                'visualization': 'line',
                'confidence': 0.3,
            }

        return None

    def _fallback_answer(self, data: list, query_plan: dict) -> str:
        """
        Generate a basic answer without AI when AI is not available.

        Args:
            data: Query result data
            query_plan: The executed query plan

        Returns:
            str: Simple text summary of the results
        """
        if not data:
            return 'No data found for your query.'

        if len(data) == 1 and query_plan.get('query_type') in ('aggregation', 'single_value'):
            row = data[0]
            parts = []
            for key, value in row.items():
                if key in ('id', 'str'):
                    continue
                if isinstance(value, float):
                    parts.append(f'{key}: {value:,.2f}')
                else:
                    parts.append(f'{key}: {value}')
            return 'Result: ' + ', '.join(parts) if parts else str(row)

        return f'Found {len(data)} results. Check the data field for details.'

    # ─────────────────────────────────────────────────────────
    # AI CALL HELPER
    # ─────────────────────────────────────────────────────────

    def _call_ai(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Call AI service for text generation.

        Uses the same provider configuration as AIContentService (Anthropic/OpenAI/Gemini).
        Falls back to None if AI is not configured.

        Args:
            system_prompt: System instruction for the AI
            user_prompt: User message to process

        Returns:
            str: AI response text, or None if AI is unavailable
        """
        try:
            from apps.ai.services.content_generator import AIContentService
            ai_svc = AIContentService()

            if not ai_svc.api_key:
                logger.info('NLQ: No AI API key configured, using fallback')
                return None

            result = ai_svc._call_llm_with_system(system_prompt, user_prompt, max_tokens=1000)
            return result.get('text') if result else None

        except AttributeError:
            # _call_llm_with_system doesn't exist; use direct provider calls
            pass
        except Exception as exc:
            logger.warning('NLQ AI call via AIContentService failed: %s', exc)

        # Direct provider fallback
        return self._call_ai_direct(system_prompt, user_prompt)

    def _call_ai_direct(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Direct AI provider call when AIContentService doesn't support system prompts.

        Reads provider configuration from Django settings or the AI provider config model.

        Args:
            system_prompt: System instruction
            user_prompt: User message

        Returns:
            str: AI response text, or None if unavailable
        """
        # Try to get config from the AI provider config model
        api_key = None
        provider = None
        model = None

        try:
            from apps.ai.models import AIProviderConfig
            config = AIProviderConfig.get_active_text_provider()
            if config and config.has_api_key:
                api_key = config.get_api_key()
                provider = config.provider
                model = config.default_model
        except Exception:
            pass

        if not api_key:
            api_key = getattr(settings, 'OPENAI_API_KEY', None) or getattr(settings, 'AI_API_KEY', '')
            provider = getattr(settings, 'AI_PROVIDER', 'openai')
            model = getattr(settings, 'AI_MODEL', 'gpt-4o-mini')

        if not api_key:
            return None

        try:
            if provider == 'anthropic':
                return self._call_anthropic_direct(api_key, model, system_prompt, user_prompt)
            elif provider == 'openai':
                return self._call_openai_direct(api_key, model, system_prompt, user_prompt)
            elif provider == 'gemini':
                return self._call_gemini_direct(api_key, model, system_prompt, user_prompt)
        except Exception as exc:
            logger.error('NLQ direct AI call failed (%s): %s', provider, exc)

        return None

    @staticmethod
    def _call_anthropic_direct(
        api_key: str, model: str, system_prompt: str, user_prompt: str,
    ) -> Optional[str]:
        """Call Anthropic Messages API directly."""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model or 'claude-3-haiku-20240307',
                max_tokens=1000,
                system=system_prompt,
                messages=[{'role': 'user', 'content': user_prompt}],
            )
            return response.content[0].text.strip()
        except ImportError:
            logger.warning('anthropic package not installed')
            return None

    @staticmethod
    def _call_openai_direct(
        api_key: str, model: str, system_prompt: str, user_prompt: str,
    ) -> Optional[str]:
        """Call OpenAI Chat Completions API directly."""
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model or 'gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except ImportError:
            logger.warning('openai package not installed')
            return None

    @staticmethod
    def _call_gemini_direct(
        api_key: str, model: str, system_prompt: str, user_prompt: str,
    ) -> Optional[str]:
        """Call Google Generative AI (Gemini) API directly."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            gen_model = genai.GenerativeModel(
                model or 'gemini-1.5-flash',
                system_instruction=system_prompt,
            )
            response = gen_model.generate_content(
                user_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1000,
                    temperature=0.3,
                ),
            )
            return response.text.strip()
        except ImportError:
            logger.warning('google-generativeai package not installed')
            return None

    # ─────────────────────────────────────────────────────────
    # JSON PARSING
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _parse_json_response(text: str) -> Optional[dict]:
        """
        Parse a JSON response from AI, handling markdown code blocks.

        Args:
            text: Raw AI response text

        Returns:
            dict: Parsed JSON or None
        """
        if not text:
            return None

        cleaned = text.strip()

        # Strip markdown code fences
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            # Remove first line (```json) and last line (```)
            start = 1
            end = len(lines)
            if lines[-1].strip().startswith('```'):
                end = -1
            cleaned = '\n'.join(lines[start:end]).strip()

        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, ValueError):
            # Try to find JSON within the text
            brace_start = cleaned.find('{')
            brace_end = cleaned.rfind('}')
            if brace_start != -1 and brace_end > brace_start:
                try:
                    return json.loads(cleaned[brace_start:brace_end + 1])
                except (json.JSONDecodeError, ValueError):
                    pass

        logger.warning('Failed to parse AI response as JSON: %s', text[:200])
        return None
