"""
Automated Insight & Anomaly Detection Service for the Reporting module.

Generates daily/weekly insights by analyzing aggregated business data
for anomalies, trends, and opportunities. Uses statistical methods
(Z-score, linear regression) with optional AI narrative generation.

Usage:
    from apps.reporting.ai.insight_service import InsightService

    service = InsightService()
    insights = service.generate_daily_insights(
        org_id=organization.id,
        date=date.today(),
    )
    # insights = [
    #     {
    #         'type': 'anomaly',
    #         'severity': 'warning',
    #         'title': 'Revenue significantly above average',
    #         'description': 'Today's net revenue of 15,230 TL is ...',
    #         'metric': 'net_revenue',
    #         'value': 15230.0,
    #         'expected_value': 8500.0,
    #         'recommendation': 'Investigate what drove...',
    #         'data': {...},
    #     },
    #     ...
    # ]

Critical Rules:
    - EVERY query MUST filter by organization_id (multi-tenant isolation)
    - EVERY query MUST filter deleted_at__isnull=True (soft delete)
    - Uses Python stdlib math/statistics only (no numpy/scipy)
"""

import logging
import statistics
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from django.db.models import Avg
from django.utils import timezone

logger = logging.getLogger(__name__)

# Z-score threshold for anomaly detection (number of std deviations)
ANOMALY_Z_THRESHOLD = 2.0

# Minimum data points needed for statistical analysis
MIN_DATA_POINTS = 7

# Number of historical days for anomaly detection baseline
ANOMALY_LOOKBACK_DAYS = 30

# Number of historical days for trend detection
TREND_LOOKBACK_DAYS = 14


class InsightService:
    """
    Automated daily/weekly insight generation with anomaly detection.

    Analyzes SalesAggregation, ProductPerformance, and CustomerMetric
    data to produce actionable business insights.
    """

    # ─────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────

    def generate_daily_insights(
        self,
        org_id,
        date_val: date = None,
    ) -> List[dict]:
        """
        Generate insights for a given date.

        Runs multiple detection checks and returns a combined list of insights
        sorted by severity (critical > warning > info).

        Args:
            org_id: Organization UUID (tenant isolation)
            date_val: Target date (defaults to today)

        Returns:
            list[dict]: List of insight dictionaries with keys:
                - type: 'anomaly' | 'trend' | 'opportunity' | 'alert'
                - severity: 'info' | 'warning' | 'critical'
                - title: Short human-readable title
                - description: Detailed explanation
                - metric: Metric name involved
                - value: Current value
                - expected_value: Expected/baseline value
                - recommendation: Suggested action
                - data: Additional context data
        """
        if date_val is None:
            date_val = timezone.localdate()

        insights: List[dict] = []

        # 1. Revenue and order count anomalies
        try:
            anomaly_insights = self._detect_anomalies(org_id, date_val)
            insights.extend(anomaly_insights)
        except Exception as exc:
            logger.warning('Anomaly detection failed for org=%s: %s', org_id, exc)

        # 2. Trend detection (rising/falling/stable)
        try:
            trend_insights = self._detect_trends(org_id, date_val)
            insights.extend(trend_insights)
        except Exception as exc:
            logger.warning('Trend detection failed for org=%s: %s', org_id, exc)

        # 3. Opportunity finder (low-sales + high-margin items)
        try:
            opportunity_insights = self._find_opportunities(org_id, date_val)
            insights.extend(opportunity_insights)
        except Exception as exc:
            logger.warning('Opportunity detection failed for org=%s: %s', org_id, exc)

        # 4. Customer change alerts
        try:
            customer_insights = self._detect_customer_changes(org_id, date_val)
            insights.extend(customer_insights)
        except Exception as exc:
            logger.warning('Customer change detection failed for org=%s: %s', org_id, exc)

        # 5. AI narrative insights (optional, if AI is configured)
        try:
            if insights:
                ai_insights = self._generate_ai_insights(org_id, insights, date_val)
                insights.extend(ai_insights)
        except Exception as exc:
            logger.warning('AI insight generation failed for org=%s: %s', org_id, exc)

        # Sort by severity: critical first, then warning, then info
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        insights.sort(key=lambda x: severity_order.get(x.get('severity', 'info'), 2))

        return insights

    # ─────────────────────────────────────────────────────────
    # ANOMALY DETECTION (Z-Score)
    # ─────────────────────────────────────────────────────────

    def _detect_anomalies(self, org_id, date_val: date) -> List[dict]:
        """
        Z-score anomaly detection on key sales metrics.

        Compares today's values against the trailing 30-day mean and std dev.
        Flags values that are more than ANOMALY_Z_THRESHOLD standard deviations
        from the mean.

        Args:
            org_id: Organization UUID
            date_val: Target date

        Returns:
            list[dict]: Anomaly insights
        """
        from apps.analytics.models import SalesAggregation

        insights = []

        # Get the last 30 days of daily aggregation data
        start_date = date_val - timedelta(days=ANOMALY_LOOKBACK_DAYS)
        historical = list(
            SalesAggregation.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                granularity='DAILY',
                date__gte=start_date,
                date__lt=date_val,
            )
            .order_by('date')
            .values('date', 'net_revenue', 'order_count', 'customer_count', 'avg_order_value')
        )

        if len(historical) < MIN_DATA_POINTS:
            return insights

        # Get today's data
        today_data = (
            SalesAggregation.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                granularity='DAILY',
                date=date_val,
            )
            .values('net_revenue', 'order_count', 'customer_count', 'avg_order_value')
            .first()
        )

        if not today_data:
            return insights

        # Check each metric for anomalies
        metrics_to_check = [
            ('net_revenue', 'Revenue', 'TL'),
            ('order_count', 'Order count', ''),
            ('customer_count', 'Customer count', ''),
            ('avg_order_value', 'Average order value', 'TL'),
        ]

        for field, label, unit in metrics_to_check:
            historical_values = [
                float(row[field]) for row in historical
                if row[field] is not None
            ]

            if len(historical_values) < MIN_DATA_POINTS:
                continue

            current_value = float(today_data[field] or 0)
            mean = statistics.mean(historical_values)
            stdev = statistics.stdev(historical_values)

            if stdev == 0:
                continue

            z_score = (current_value - mean) / stdev

            if abs(z_score) >= ANOMALY_Z_THRESHOLD:
                direction = 'above' if z_score > 0 else 'below'
                severity = 'critical' if abs(z_score) >= 3.0 else 'warning'

                unit_str = f' {unit}' if unit else ''
                insights.append({
                    'type': 'anomaly',
                    'severity': severity,
                    'title': f'{label} significantly {direction} average',
                    'description': (
                        f"Today's {label.lower()} of {current_value:,.2f}{unit_str} "
                        f"is {abs(z_score):.1f} standard deviations {direction} "
                        f"the 30-day average of {mean:,.2f}{unit_str}."
                    ),
                    'metric': field,
                    'value': current_value,
                    'expected_value': round(mean, 2),
                    'recommendation': self._anomaly_recommendation(
                        field, direction, z_score
                    ),
                    'data': {
                        'z_score': round(z_score, 2),
                        'mean': round(mean, 2),
                        'stdev': round(stdev, 2),
                        'date': date_val.isoformat(),
                    },
                })

        return insights

    @staticmethod
    def _anomaly_recommendation(metric: str, direction: str, z_score: float) -> str:
        """Generate a recommendation based on the anomaly detected."""
        if metric == 'net_revenue':
            if direction == 'above':
                return (
                    'Investigate what drove higher revenue today. '
                    'Check for special events, promotions, or unusually large orders '
                    'that could be replicated.'
                )
            return (
                'Revenue is significantly lower than usual. '
                'Check for operational issues, staff shortages, or '
                'external factors that may have reduced foot traffic.'
            )
        elif metric == 'order_count':
            if direction == 'above':
                return (
                    'Order volume is unusually high. Ensure kitchen '
                    'and staff capacity is adequate to maintain service quality.'
                )
            return (
                'Order volume dropped significantly. Review if there '
                'were any service disruptions or negative customer experiences.'
            )
        elif metric == 'customer_count':
            if direction == 'above':
                return (
                    'Customer traffic spiked today. Consider what attracted '
                    'more customers and try to sustain this momentum.'
                )
            return (
                'Fewer customers than usual visited today. Review marketing '
                'campaigns and customer engagement strategies.'
            )
        elif metric == 'avg_order_value':
            if direction == 'above':
                return (
                    'Customers are spending more per order. Check if '
                    'upselling strategies or menu changes are driving this.'
                )
            return (
                'Average order value dropped. Consider reviewing pricing, '
                'promotions, or product bundling strategies.'
            )
        return 'Review the metric and investigate the root cause.'

    # ─────────────────────────────────────────────────────────
    # TREND DETECTION (Linear Regression)
    # ─────────────────────────────────────────────────────────

    def _detect_trends(self, org_id, date_val: date) -> List[dict]:
        """
        Linear regression trend detection on the last 14 days of sales data.

        Calculates the slope of a simple least-squares line to determine
        whether key metrics are rising, falling, or stable.

        Args:
            org_id: Organization UUID
            date_val: Target date

        Returns:
            list[dict]: Trend insights
        """
        from apps.analytics.models import SalesAggregation

        insights = []
        start_date = date_val - timedelta(days=TREND_LOOKBACK_DAYS)

        historical = list(
            SalesAggregation.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                granularity='DAILY',
                date__gte=start_date,
                date__lte=date_val,
            )
            .order_by('date')
            .values('date', 'net_revenue', 'order_count')
        )

        if len(historical) < MIN_DATA_POINTS:
            return insights

        # Analyze revenue trend
        revenue_values = [float(row['net_revenue']) for row in historical]
        revenue_trend = self._calculate_trend(revenue_values)

        if revenue_trend['direction'] != 'stable':
            daily_change = abs(revenue_trend['slope'])
            insights.append({
                'type': 'trend',
                'severity': 'info',
                'title': f"Revenue is {revenue_trend['direction']}",
                'description': (
                    f"Over the last {TREND_LOOKBACK_DAYS} days, revenue shows a "
                    f"{revenue_trend['direction']} trend with an average daily "
                    f"change of {daily_change:,.2f} TL ({revenue_trend['change_percent']:+.1f}%)."
                ),
                'metric': 'net_revenue',
                'value': revenue_values[-1] if revenue_values else 0,
                'expected_value': revenue_trend['intercept'] + revenue_trend['slope'] * len(revenue_values),
                'recommendation': self._trend_recommendation('revenue', revenue_trend['direction']),
                'data': {
                    'slope': round(revenue_trend['slope'], 2),
                    'r_squared': round(revenue_trend['r_squared'], 4),
                    'direction': revenue_trend['direction'],
                    'change_percent': round(revenue_trend['change_percent'], 2),
                    'period_days': TREND_LOOKBACK_DAYS,
                },
            })

        # Analyze order count trend
        order_values = [float(row['order_count']) for row in historical]
        order_trend = self._calculate_trend(order_values)

        if order_trend['direction'] != 'stable':
            insights.append({
                'type': 'trend',
                'severity': 'info',
                'title': f"Order volume is {order_trend['direction']}",
                'description': (
                    f"Over the last {TREND_LOOKBACK_DAYS} days, order count shows a "
                    f"{order_trend['direction']} trend ({order_trend['change_percent']:+.1f}% change)."
                ),
                'metric': 'order_count',
                'value': order_values[-1] if order_values else 0,
                'expected_value': order_trend['intercept'] + order_trend['slope'] * len(order_values),
                'recommendation': self._trend_recommendation('orders', order_trend['direction']),
                'data': {
                    'slope': round(order_trend['slope'], 2),
                    'r_squared': round(order_trend['r_squared'], 4),
                    'direction': order_trend['direction'],
                    'change_percent': round(order_trend['change_percent'], 2),
                    'period_days': TREND_LOOKBACK_DAYS,
                },
            })

        return insights

    @staticmethod
    def _calculate_trend(values: List[float]) -> dict:
        """
        Calculate linear trend using simple least-squares regression.

        y = slope * x + intercept

        Args:
            values: Time series values (chronological order)

        Returns:
            dict with slope, intercept, r_squared, direction, change_percent
        """
        n = len(values)
        if n < 2:
            return {
                'slope': 0.0,
                'intercept': 0.0,
                'r_squared': 0.0,
                'direction': 'stable',
                'change_percent': 0.0,
            }

        # x values are 0, 1, 2, ..., n-1
        x_values = list(range(n))
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n

        # Numerator and denominator for slope
        numerator = sum(
            (x - x_mean) * (y - y_mean)
            for x, y in zip(x_values, values)
        )
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return {
                'slope': 0.0,
                'intercept': y_mean,
                'r_squared': 0.0,
                'direction': 'stable',
                'change_percent': 0.0,
            }

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # R-squared
        y_predicted = [slope * x + intercept for x in x_values]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(values, y_predicted))
        ss_tot = sum((y - y_mean) ** 2 for y in values)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Calculate percentage change over the period
        first_value = intercept  # predicted value at x=0
        last_value = slope * (n - 1) + intercept  # predicted value at x=n-1
        if first_value != 0:
            change_percent = ((last_value - first_value) / abs(first_value)) * 100
        else:
            change_percent = 0.0

        # Classify direction based on significance
        # Require R-squared >= 0.3 and change >= 5% to call it a trend
        if r_squared >= 0.3 and abs(change_percent) >= 5.0:
            direction = 'rising' if slope > 0 else 'falling'
        else:
            direction = 'stable'

        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_squared,
            'direction': direction,
            'change_percent': change_percent,
        }

    @staticmethod
    def _trend_recommendation(metric: str, direction: str) -> str:
        """Generate a recommendation based on the trend detected."""
        if metric == 'revenue':
            if direction == 'rising':
                return (
                    'Revenue is trending upward. Continue current strategies '
                    'and consider capitalizing on momentum with targeted promotions.'
                )
            return (
                'Revenue is trending downward. Review recent changes in '
                'menu, pricing, or marketing. Consider launching a promotion '
                'to reverse the trend.'
            )
        elif metric == 'orders':
            if direction == 'rising':
                return (
                    'Order volume is increasing. Ensure operational capacity '
                    '(staff, kitchen, inventory) can handle growing demand.'
                )
            return (
                'Order volume is declining. Investigate potential causes '
                'such as seasonal factors, competition, or service issues.'
            )
        return 'Monitor this trend and investigate root causes.'

    # ─────────────────────────────────────────────────────────
    # OPPORTUNITY FINDER
    # ─────────────────────────────────────────────────────────

    def _find_opportunities(self, org_id, date_val: date) -> List[dict]:
        """
        Find products with high profit margins but low sales volume.

        These represent menu items that could benefit from better placement,
        promotion, or marketing to increase their contribution.

        Args:
            org_id: Organization UUID
            date_val: Target date

        Returns:
            list[dict]: Opportunity insights
        """
        from apps.analytics.models import ProductPerformance

        insights = []

        # Get recent monthly product performance data
        period_start = date_val.replace(day=1)
        performances = list(
            ProductPerformance.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                period_type='MONTHLY',
                period_start=period_start,
                profit_margin__isnull=False,
            )
            .select_related('product')
            .values(
                'product__name',
                'quantity_sold',
                'revenue',
                'profit_margin',
                'sales_mix_percent',
            )
        )

        if len(performances) < 3:
            # Not enough data for meaningful analysis
            return insights

        # Calculate median quantity sold
        quantities = [p['quantity_sold'] for p in performances if p['quantity_sold'] > 0]
        if not quantities:
            return insights

        quantities_sorted = sorted(quantities)
        median_qty = quantities_sorted[len(quantities_sorted) // 2]

        # Find high-margin, low-volume items
        # Definition: profit_margin > 40% and quantity_sold < median
        margin_threshold = Decimal('40.0')
        opportunities = []

        for perf in performances:
            margin = perf.get('profit_margin')
            qty = perf.get('quantity_sold', 0)
            if margin is not None and float(margin) > float(margin_threshold) and qty < median_qty:
                opportunities.append(perf)

        # Sort by margin descending to highlight best opportunities first
        opportunities.sort(key=lambda x: float(x.get('profit_margin', 0)), reverse=True)

        for opp in opportunities[:5]:  # Limit to top 5
            product_name = opp.get('product__name', 'Unknown')
            margin = float(opp.get('profit_margin', 0))
            qty = opp.get('quantity_sold', 0)
            revenue = float(opp.get('revenue', 0))

            insights.append({
                'type': 'opportunity',
                'severity': 'info',
                'title': f'Underperforming high-margin item: {product_name}',
                'description': (
                    f'{product_name} has a profit margin of {margin:.1f}% '
                    f'but only sold {qty} units this month (median: {median_qty}). '
                    f'Current revenue: {revenue:,.2f} TL.'
                ),
                'metric': 'product_opportunity',
                'value': qty,
                'expected_value': median_qty,
                'recommendation': (
                    f'Consider promoting "{product_name}" through better menu '
                    f'placement, staff recommendations, or a featured item campaign. '
                    f'With its {margin:.0f}% margin, increasing volume could '
                    f'significantly boost profitability.'
                ),
                'data': {
                    'product_name': product_name,
                    'profit_margin': margin,
                    'quantity_sold': qty,
                    'median_quantity': median_qty,
                    'revenue': revenue,
                },
            })

        return insights

    # ─────────────────────────────────────────────────────────
    # CUSTOMER CHANGE DETECTION
    # ─────────────────────────────────────────────────────────

    def _detect_customer_changes(self, org_id, date_val: date) -> List[dict]:
        """
        Detect significant changes in customer metrics.

        Compares current day's customer metrics against recent averages.

        Args:
            org_id: Organization UUID
            date_val: Target date

        Returns:
            list[dict]: Customer-related insights
        """
        from apps.analytics.models import CustomerMetric

        insights = []

        # Get today's customer metrics
        today_metric = (
            CustomerMetric.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                date=date_val,
            )
            .values('new_customers', 'returning_customers', 'churn_count', 'total_customers')
            .first()
        )

        if not today_metric:
            return insights

        # Get 7-day average for comparison
        start_date = date_val - timedelta(days=7)
        avg_metrics = (
            CustomerMetric.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                date__gte=start_date,
                date__lt=date_val,
            )
            .aggregate(
                avg_new=Avg('new_customers'),
                avg_returning=Avg('returning_customers'),
                avg_churn=Avg('churn_count'),
            )
        )

        # Check new customers
        new_today = today_metric.get('new_customers', 0)
        avg_new = float(avg_metrics.get('avg_new') or 0)
        if avg_new > 0 and new_today > avg_new * 1.5:
            insights.append({
                'type': 'alert',
                'severity': 'info',
                'title': 'New customer surge',
                'description': (
                    f'{new_today} new customers today, '
                    f'{((new_today / avg_new) - 1) * 100:.0f}% above the '
                    f'7-day average of {avg_new:.0f}.'
                ),
                'metric': 'new_customers',
                'value': new_today,
                'expected_value': round(avg_new, 1),
                'recommendation': (
                    'Great customer acquisition today! Investigate what '
                    'marketing or promotional activities contributed to this '
                    'and consider repeating them.'
                ),
                'data': {
                    'new_customers': new_today,
                    'avg_new_7d': round(avg_new, 1),
                    'date': date_val.isoformat(),
                },
            })

        # Check churn
        churn_today = today_metric.get('churn_count', 0)
        avg_churn = float(avg_metrics.get('avg_churn') or 0)
        if avg_churn > 0 and churn_today > avg_churn * 2:
            insights.append({
                'type': 'alert',
                'severity': 'warning',
                'title': 'Elevated customer churn',
                'description': (
                    f'{churn_today} customers churned today, '
                    f'significantly above the 7-day average of {avg_churn:.0f}.'
                ),
                'metric': 'churn_count',
                'value': churn_today,
                'expected_value': round(avg_churn, 1),
                'recommendation': (
                    'Customer churn is elevated. Review recent customer '
                    'feedback, service quality, and any operational issues '
                    'that may be causing dissatisfaction.'
                ),
                'data': {
                    'churn_count': churn_today,
                    'avg_churn_7d': round(avg_churn, 1),
                    'date': date_val.isoformat(),
                },
            })

        return insights

    # ─────────────────────────────────────────────────────────
    # AI-POWERED NARRATIVE INSIGHTS
    # ─────────────────────────────────────────────────────────

    def _generate_ai_insights(
        self,
        org_id,
        existing_insights: List[dict],
        date_val: date,
    ) -> List[dict]:
        """
        Use AI to generate contextual narrative insights from the detected patterns.

        Takes the statistical insights already found and asks AI to provide
        additional business context and cross-metric correlations.

        Args:
            org_id: Organization UUID
            existing_insights: List of already-detected insights
            date_val: Target date

        Returns:
            list[dict]: AI-generated narrative insights (may be empty)
        """
        if not existing_insights:
            return []

        # Build a summary for the AI
        summary_parts = []
        for insight in existing_insights:
            summary_parts.append(
                f"- [{insight['type'].upper()}] {insight['title']}: "
                f"{insight['description']}"
            )
        summary = '\n'.join(summary_parts)

        system_prompt = """You are a restaurant business analyst.
Given the following automated insights for a restaurant, provide 1-2 additional
observations that connect these findings and give actionable business advice.

Focus on:
1. Correlations between the metrics (e.g., revenue up + customers down = higher avg order)
2. Actionable next steps the restaurant owner should take
3. Potential root causes

Return ONLY a JSON array of insight objects:
[
    {
        "title": "Short insight title",
        "description": "Detailed explanation (2-3 sentences)",
        "recommendation": "Specific action to take"
    }
]

Do NOT repeat the existing insights. Add NEW observations only."""

        user_prompt = (
            f"Date: {date_val.isoformat()}\n\n"
            f"Detected insights:\n{summary}"
        )

        response_text = self._call_ai(system_prompt, user_prompt)
        if not response_text:
            return []

        return self._parse_ai_insights(response_text)

    def _parse_ai_insights(self, response_text: str) -> List[dict]:
        """
        Parse AI response into insight dictionaries.

        Args:
            response_text: Raw AI response (expected JSON array)

        Returns:
            list[dict]: Parsed insights
        """
        import json

        cleaned = response_text.strip()

        # Strip markdown code fences if present
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            start = 1
            end = len(lines)
            if lines[-1].strip().startswith('```'):
                end = -1
            cleaned = '\n'.join(lines[start:end]).strip()

        try:
            data = json.loads(cleaned)
            if not isinstance(data, list):
                data = [data]
        except (json.JSONDecodeError, ValueError):
            # Try to find JSON array
            bracket_start = cleaned.find('[')
            bracket_end = cleaned.rfind(']')
            if bracket_start != -1 and bracket_end > bracket_start:
                try:
                    data = json.loads(cleaned[bracket_start:bracket_end + 1])
                except (json.JSONDecodeError, ValueError):
                    return []
            else:
                return []

        insights = []
        for item in data[:3]:  # Limit to 3 AI insights
            if isinstance(item, dict) and item.get('title'):
                insights.append({
                    'type': 'trend',
                    'severity': 'info',
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'metric': 'ai_observation',
                    'value': 0,
                    'expected_value': 0,
                    'recommendation': item.get('recommendation', ''),
                    'data': {'source': 'ai_analysis'},
                })

        return insights

    # ─────────────────────────────────────────────────────────
    # AI CALL HELPER
    # ─────────────────────────────────────────────────────────

    def _call_ai(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Call AI service for text generation.

        Uses the same provider configuration as AIContentService.
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
                return None

            # Try using the _call_llm_with_system method if available
            try:
                result = ai_svc._call_llm_with_system(system_prompt, user_prompt, max_tokens=800)
                return result.get('text') if result else None
            except AttributeError:
                pass

            # Direct provider call fallback
            return self._call_ai_direct(ai_svc, system_prompt, user_prompt)

        except Exception as exc:
            logger.warning('InsightService AI call failed: %s', exc)
            return None

    @staticmethod
    def _call_ai_direct(ai_svc, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Direct provider call when the convenience method is not available.

        Args:
            ai_svc: AIContentService instance (has api_key, provider, model)
            system_prompt: System instruction
            user_prompt: User message

        Returns:
            str: AI response text, or None
        """
        try:
            if ai_svc.provider == 'anthropic':
                import anthropic
                client = anthropic.Anthropic(api_key=ai_svc.api_key)
                response = client.messages.create(
                    model=ai_svc.model or 'claude-3-haiku-20240307',
                    max_tokens=800,
                    system=system_prompt,
                    messages=[{'role': 'user', 'content': user_prompt}],
                )
                return response.content[0].text.strip()

            elif ai_svc.provider == 'openai':
                import openai
                client = openai.OpenAI(api_key=ai_svc.api_key)
                response = client.chat.completions.create(
                    model=ai_svc.model or 'gpt-4o-mini',
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt},
                    ],
                    max_tokens=800,
                    temperature=0.3,
                )
                return response.choices[0].message.content.strip()

            elif ai_svc.provider == 'gemini':
                import google.generativeai as genai
                genai.configure(api_key=ai_svc.api_key)
                model = genai.GenerativeModel(
                    ai_svc.model or 'gemini-1.5-flash',
                    system_instruction=system_prompt,
                )
                response = model.generate_content(
                    user_prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=800,
                        temperature=0.3,
                    ),
                )
                return response.text.strip()

        except ImportError as exc:
            logger.warning('AI provider package not installed: %s', exc)
        except Exception as exc:
            logger.error('InsightService direct AI call failed: %s', exc)

        return None
