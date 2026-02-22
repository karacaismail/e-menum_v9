"""
RFM Customer Segmentation Service for the Reporting module.

Implements RFM (Recency, Frequency, Monetary) analysis to segment customers
into actionable groups. Uses quintile scoring (1-5) for each dimension and
maps combinations to predefined business segments.

Segments:
    - Champions: Best customers (high R, F, M)
    - Loyal Customers: Frequent, recent buyers
    - Potential Loyalists: Recent but not yet frequent
    - New Customers: Very recent, first-time buyers
    - At Risk: Previously good customers going cold
    - Hibernating: Low activity across the board
    - Lost: Worst scores in all dimensions

Usage:
    from apps.reporting.ai.segmentation_service import SegmentationService

    service = SegmentationService()
    result = service.calculate_rfm(org_id=organization.id)
    # result = {
    #     'total_customers': 250,
    #     'segments': {
    #         'Champions': {'count': 25, 'percentage': 10.0, 'avg_value': 5200.0},
    #         'Loyal Customers': {'count': 40, 'percentage': 16.0, 'avg_value': 3800.0},
    #         ...
    #     },
    #     'updated_count': 250,
    # }

Critical Rules:
    - EVERY query MUST filter by organization_id (multi-tenant isolation)
    - EVERY query MUST filter deleted_at__isnull=True (soft delete)
    - Uses Python stdlib only (no numpy/scipy)
"""

import logging
import math
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from django.db.models import Avg, Count, Max, Q, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)

# Segment definitions based on RFM score combinations
# Each segment is defined by score ranges for R, F, M
# Format: segment_name -> (r_min, r_max, f_min, f_max, m_min, m_max)
SEGMENT_RULES = [
    # name, r_range, f_range, m_range (inclusive)
    ('Champions', (5, 5), (5, 5), (4, 5)),
    ('Champions', (5, 5), (4, 5), (5, 5)),
    ('Loyal Customers', (4, 5), (4, 5), (3, 5)),
    ('Loyal Customers', (3, 5), (4, 5), (4, 5)),
    ('Potential Loyalists', (4, 5), (2, 3), (2, 5)),
    ('Potential Loyalists', (4, 5), (1, 3), (4, 5)),
    ('New Customers', (5, 5), (1, 1), (1, 5)),
    ('Promising', (4, 4), (1, 1), (1, 5)),
    ('Need Attention', (3, 3), (3, 4), (3, 4)),
    ('Need Attention', (3, 4), (2, 3), (3, 4)),
    ('About to Sleep', (3, 3), (1, 2), (1, 3)),
    ('At Risk', (2, 3), (3, 5), (3, 5)),
    ('At Risk', (2, 3), (4, 5), (2, 5)),
    ("Can't Lose Them", (1, 2), (4, 5), (4, 5)),
    ('Hibernating', (1, 2), (1, 2), (1, 3)),
    ('Hibernating', (2, 2), (1, 2), (2, 3)),
    ('Lost', (1, 1), (1, 1), (1, 2)),
    ('Lost', (1, 1), (1, 2), (1, 1)),
]


class SegmentationService:
    """
    RFM (Recency, Frequency, Monetary) customer segmentation.

    Analyzes customer order patterns to classify them into actionable
    business segments for targeted marketing and retention.
    """

    # ─────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────

    def calculate_rfm(self, org_id) -> dict:
        """
        Calculate RFM scores for all customers in an organization.

        Steps:
            1. Query customer order data (last order date, order count, total spend)
            2. Calculate quintile scores (1-5) for Recency, Frequency, Monetary
            3. Assign segment labels based on RFM score combinations
            4. Update Customer model settings with RFM data

        Args:
            org_id: Organization UUID (tenant isolation)

        Returns:
            dict with keys:
                - total_customers: Total customers analyzed
                - segments: {segment_name: {count, percentage, avg_value}}
                - updated_count: Number of customer records updated
                - rfm_distribution: Distribution of R, F, M scores
        """
        # Step 1: Get customer order data
        customer_data = self._get_customer_order_data(org_id)

        if not customer_data:
            return {
                'total_customers': 0,
                'segments': {},
                'updated_count': 0,
                'rfm_distribution': {},
            }

        total_customers = len(customer_data)

        # Step 2: Calculate RFM values
        today = timezone.localdate()
        rfm_records = []

        for cust in customer_data:
            customer_id = cust['customer_id']
            last_order_date = cust['last_order_date']
            order_count = cust['order_count'] or 0
            total_spent = float(cust['total_spent'] or 0)

            # Recency: days since last order (lower is better)
            if last_order_date:
                if hasattr(last_order_date, 'date'):
                    last_order_date = last_order_date.date()
                recency_days = (today - last_order_date).days
            else:
                recency_days = 365  # Default to 1 year if no orders

            rfm_records.append({
                'customer_id': customer_id,
                'recency_days': recency_days,
                'frequency': order_count,
                'monetary': total_spent,
            })

        # Step 3: Calculate quintile scores
        recency_values = [r['recency_days'] for r in rfm_records]
        frequency_values = [r['frequency'] for r in rfm_records]
        monetary_values = [r['monetary'] for r in rfm_records]

        # For recency, LOWER is better, so we REVERSE the scoring
        recency_quintiles = self._calculate_quintiles(recency_values, reverse=True)
        frequency_quintiles = self._calculate_quintiles(frequency_values, reverse=False)
        monetary_quintiles = self._calculate_quintiles(monetary_values, reverse=False)

        # Assign scores to each customer
        for i, record in enumerate(rfm_records):
            record['r_score'] = recency_quintiles[i]
            record['f_score'] = frequency_quintiles[i]
            record['m_score'] = monetary_quintiles[i]
            record['rfm_score'] = f"{record['r_score']}{record['f_score']}{record['m_score']}"
            record['segment'] = self._assign_segment(
                record['r_score'],
                record['f_score'],
                record['m_score'],
            )

        # Step 4: Build segment summary
        segments = self._build_segment_summary(rfm_records, total_customers)

        # Step 5: Update customer records
        updated_count = self._update_customer_records(org_id, rfm_records)

        # Step 6: Build RFM distribution
        rfm_distribution = self._build_rfm_distribution(rfm_records)

        return {
            'total_customers': total_customers,
            'segments': segments,
            'updated_count': updated_count,
            'rfm_distribution': rfm_distribution,
        }

    # ─────────────────────────────────────────────────────────
    # DATA RETRIEVAL
    # ─────────────────────────────────────────────────────────

    def _get_customer_order_data(self, org_id) -> List[dict]:
        """
        Get customer order aggregation data for RFM calculation.

        Queries the Order model to get per-customer:
        - Last order date (Recency)
        - Total order count (Frequency)
        - Total spend (Monetary)

        Args:
            org_id: Organization UUID

        Returns:
            list[dict]: Customer order aggregation data
        """
        from apps.customers.models import Customer

        # Build filter for valid (non-deleted, non-cancelled) orders
        valid_order_filter = Q(
            orders__deleted_at__isnull=True,
        ) & ~Q(
            orders__status='CANCELLED',
        )

        # Get all active customers for this organization
        customers_with_orders = (
            Customer.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
            )
            .annotate(
                last_order_date=Max(
                    'orders__placed_at',
                    filter=valid_order_filter,
                ),
                order_count=Count(
                    'orders',
                    filter=valid_order_filter,
                ),
                total_spent=Sum(
                    'orders__total_amount',
                    filter=valid_order_filter,
                ),
            )
            .values('id', 'last_order_date', 'order_count', 'total_spent')
        )

        result = []
        for cust in customers_with_orders:
            result.append({
                'customer_id': cust['id'],
                'last_order_date': cust['last_order_date'],
                'order_count': cust['order_count'] or 0,
                'total_spent': cust['total_spent'] or Decimal('0.00'),
            })

        return result

    # ─────────────────────────────────────────────────────────
    # QUINTILE CALCULATION
    # ─────────────────────────────────────────────────────────

    def _calculate_quintiles(
        self,
        values: List[float],
        reverse: bool = False,
    ) -> List[int]:
        """
        Assign quintile scores (1-5) to a list of values.

        Uses percentile-based binning. Score 5 is best, 1 is worst.

        For most metrics (frequency, monetary), HIGHER value = HIGHER score.
        For recency (days since last order), LOWER value = HIGHER score,
        so pass reverse=True.

        Args:
            values: List of numeric values to score
            reverse: If True, lower values get higher scores

        Returns:
            list[int]: Quintile scores (1-5) aligned with input values
        """
        n = len(values)
        if n == 0:
            return []

        if n < 5:
            # Not enough data for meaningful quintiles; use simple ranking
            return self._simple_rank_scores(values, reverse)

        # Create sorted index pairs
        indexed = list(enumerate(values))
        indexed.sort(key=lambda x: x[1], reverse=reverse)

        # Assign scores based on position
        scores = [0] * n
        quintile_size = n / 5

        for rank, (original_idx, _) in enumerate(indexed):
            # Which quintile does this rank fall in?
            quintile = min(int(rank / quintile_size), 4)  # 0-4
            score = quintile + 1  # 1-5
            scores[original_idx] = score

        return scores

    @staticmethod
    def _simple_rank_scores(values: List[float], reverse: bool) -> List[int]:
        """
        Assign scores when there are fewer than 5 data points.

        Maps ranks directly to 1-5 range.

        Args:
            values: List of values
            reverse: If True, lower values get higher scores

        Returns:
            list[int]: Scores 1-5
        """
        n = len(values)
        if n == 0:
            return []

        indexed = list(enumerate(values))
        indexed.sort(key=lambda x: x[1], reverse=reverse)

        scores = [0] * n
        for rank, (original_idx, _) in enumerate(indexed):
            # Map rank (0 to n-1) to score (1 to 5)
            if n == 1:
                scores[original_idx] = 3  # Middle score for single customer
            else:
                score = int(1 + (rank / (n - 1)) * 4)
                scores[original_idx] = max(1, min(5, score))

        return scores

    # ─────────────────────────────────────────────────────────
    # SEGMENT ASSIGNMENT
    # ─────────────────────────────────────────────────────────

    def _assign_segment(self, r_score: int, f_score: int, m_score: int) -> str:
        """
        Assign customer segment based on RFM score combination.

        Uses the SEGMENT_RULES lookup to find the first matching rule.
        Falls back to 'Other' if no rule matches.

        Args:
            r_score: Recency score (1-5)
            f_score: Frequency score (1-5)
            m_score: Monetary score (1-5)

        Returns:
            str: Segment name
        """
        for name, r_range, f_range, m_range in SEGMENT_RULES:
            r_min, r_max = r_range
            f_min, f_max = f_range
            m_min, m_max = m_range

            if (r_min <= r_score <= r_max
                    and f_min <= f_score <= f_max
                    and m_min <= m_score <= m_max):
                return name

        # Fallback segment based on overall score
        total = r_score + f_score + m_score
        if total >= 12:
            return 'Loyal Customers'
        elif total >= 9:
            return 'Need Attention'
        elif total >= 6:
            return 'Hibernating'
        else:
            return 'Lost'

    # ─────────────────────────────────────────────────────────
    # SEGMENT SUMMARY
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _build_segment_summary(
        rfm_records: List[dict],
        total_customers: int,
    ) -> Dict[str, dict]:
        """
        Build summary statistics per segment.

        Args:
            rfm_records: List of RFM records with segment assignments
            total_customers: Total number of customers

        Returns:
            dict: {segment_name: {count, percentage, avg_value, avg_frequency, avg_recency}}
        """
        segment_data: Dict[str, List[dict]] = {}

        for record in rfm_records:
            segment = record['segment']
            if segment not in segment_data:
                segment_data[segment] = []
            segment_data[segment].append(record)

        summary = {}
        for segment_name, records in sorted(segment_data.items()):
            count = len(records)
            monetary_values = [r['monetary'] for r in records]
            frequency_values = [r['frequency'] for r in records]
            recency_values = [r['recency_days'] for r in records]

            avg_value = sum(monetary_values) / count if count > 0 else 0.0
            avg_frequency = sum(frequency_values) / count if count > 0 else 0.0
            avg_recency = sum(recency_values) / count if count > 0 else 0.0

            percentage = (count / total_customers * 100) if total_customers > 0 else 0.0

            summary[segment_name] = {
                'count': count,
                'percentage': round(percentage, 1),
                'avg_value': round(avg_value, 2),
                'avg_frequency': round(avg_frequency, 1),
                'avg_recency_days': round(avg_recency, 0),
            }

        return summary

    # ─────────────────────────────────────────────────────────
    # CUSTOMER RECORD UPDATE
    # ─────────────────────────────────────────────────────────

    def _update_customer_records(
        self,
        org_id,
        rfm_records: List[dict],
    ) -> int:
        """
        Update Customer model settings field with RFM data.

        Stores the RFM scores and segment in the customer's settings JSON
        for use in other parts of the application.

        Args:
            org_id: Organization UUID
            rfm_records: List of RFM records with scores and segments

        Returns:
            int: Number of customer records updated
        """
        from apps.customers.models import Customer

        updated_count = 0

        # Batch update in chunks to avoid memory issues
        chunk_size = 100
        for i in range(0, len(rfm_records), chunk_size):
            chunk = rfm_records[i:i + chunk_size]

            for record in chunk:
                try:
                    customer = Customer.objects.filter(
                        id=record['customer_id'],
                        organization_id=org_id,
                        deleted_at__isnull=True,
                    ).first()

                    if customer is None:
                        continue

                    # Update the settings JSON with RFM data
                    settings = customer.settings or {}
                    settings['rfm'] = {
                        'r_score': record['r_score'],
                        'f_score': record['f_score'],
                        'm_score': record['m_score'],
                        'rfm_score': record['rfm_score'],
                        'segment': record['segment'],
                        'recency_days': record['recency_days'],
                        'frequency': record['frequency'],
                        'monetary': record['monetary'],
                        'calculated_at': timezone.now().isoformat(),
                    }

                    customer.settings = settings
                    customer.save(update_fields=['settings', 'updated_at'])
                    updated_count += 1

                except Exception as exc:
                    logger.warning(
                        'Failed to update RFM for customer %s: %s',
                        record['customer_id'], exc,
                    )

        logger.info(
            'RFM update completed: org=%s total=%d updated=%d',
            org_id, len(rfm_records), updated_count,
        )

        return updated_count

    # ─────────────────────────────────────────────────────────
    # RFM DISTRIBUTION
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _build_rfm_distribution(rfm_records: List[dict]) -> dict:
        """
        Build distribution of R, F, M scores for visualization.

        Args:
            rfm_records: List of RFM records with scores

        Returns:
            dict: Distribution data for each dimension
        """
        r_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        f_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        m_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for record in rfm_records:
            r_dist[record['r_score']] = r_dist.get(record['r_score'], 0) + 1
            f_dist[record['f_score']] = f_dist.get(record['f_score'], 0) + 1
            m_dist[record['m_score']] = m_dist.get(record['m_score'], 0) + 1

        return {
            'recency': r_dist,
            'frequency': f_dist,
            'monetary': m_dist,
        }


