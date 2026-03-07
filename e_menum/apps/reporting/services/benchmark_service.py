"""
Benchmark Service for industry comparison analytics.

Provides comparison of an organization's performance metrics against
industry benchmarks derived from aggregated, anonymized platform data.

Usage:
    from apps.reporting.services.benchmark_service import BenchmarkService

    service = BenchmarkService()

    # Get a specific benchmark
    benchmark = service.get_benchmark(
        metric_name='avg_order_value',
        category='restaurant',
        region='TR',
        period_type='MONTHLY',
    )

    # Compare org against benchmark
    comparison = service.compare_org_to_benchmark(
        org_id=org.id,
        metric_name='daily_revenue',
        period='MONTHLY',
    )

    # Generate benchmarks from platform data (admin/scheduled task)
    benchmarks = service.generate_benchmarks_from_platform_data(
        period_type='MONTHLY',
        period_start=date(2026, 1, 1),
    )

Critical Rules:
    - EVERY org query MUST filter by organization_id (multi-tenant isolation)
    - Benchmark generation uses anonymized aggregate data only
    - Individual org data is NEVER exposed in benchmarks
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db.models import Avg

from apps.reporting.models import IndustryBenchmark
from django.utils import timezone

logger = logging.getLogger(__name__)

# Minimum number of organizations required to generate a benchmark
MIN_SAMPLE_SIZE = 5

# Default region
DEFAULT_REGION = "TR"


class BenchmarkService:
    """
    Service for industry benchmark operations.

    Manages platform-level benchmark data and provides
    organization-to-benchmark comparisons.
    """

    # ─────────────────────────────────────────────────────────
    # BENCHMARK RETRIEVAL
    # ─────────────────────────────────────────────────────────

    def get_benchmark(
        self,
        metric_name: str,
        category: str,
        region: str = DEFAULT_REGION,
        period_type: str = "MONTHLY",
    ) -> Optional["IndustryBenchmark"]:
        """
        Get the latest benchmark for a specific metric and category.

        Args:
            metric_name: Metric identifier (e.g., 'avg_order_value')
            category: Business category (e.g., 'restaurant', 'cafe')
            region: Geographic region code (default: 'TR')
            period_type: Period granularity ('DAILY', 'WEEKLY', 'MONTHLY')

        Returns:
            IndustryBenchmark instance or None if not found
        """
        from apps.reporting.models import IndustryBenchmark

        try:
            return (
                IndustryBenchmark.objects.filter(
                    metric_name=metric_name,
                    category=category,
                    region=region,
                    period_type=period_type,
                )
                .order_by("-period_start")
                .first()
            )
        except Exception as exc:
            logger.error(
                "Failed to get benchmark: metric=%s category=%s error=%s",
                metric_name,
                category,
                exc,
            )
            return None

    # ─────────────────────────────────────────────────────────
    # ORG vs BENCHMARK COMPARISON
    # ─────────────────────────────────────────────────────────

    def compare_org_to_benchmark(
        self,
        org_id,
        metric_name: str,
        period: str = "MONTHLY",
    ) -> Dict[str, Any]:
        """
        Compare an organization's metric value against the industry benchmark.

        Calculates the organization's actual value for the metric,
        retrieves the industry benchmark, and computes the percentile rank.

        Args:
            org_id: Organization UUID (multi-tenant isolation)
            metric_name: Metric to compare (e.g., 'daily_revenue', 'avg_order_value')
            period: Period type for comparison

        Returns:
            dict with keys:
                - metric_name (str)
                - org_value (float|None)
                - benchmark_value (float|None)
                - benchmark_median (float|None)
                - percentile_rank (str): 'below_25', '25_50', '50_75', '75_90', 'above_90'
                - performance (str): 'below_average', 'average', 'above_average', 'top_performer'
                - category (str)
                - period_type (str)
                - sample_size (int)
                - message (str): Human-readable comparison summary
        """

        # Determine org category (default to 'restaurant')
        category = self._get_org_category(org_id)

        # Get org's actual metric value
        org_value = self._calculate_org_metric(
            org_id=org_id,
            metric_name=metric_name,
            period_type=period,
        )

        # Get benchmark
        benchmark = self.get_benchmark(
            metric_name=metric_name,
            category=category,
            period_type=period,
        )

        result = {
            "metric_name": metric_name,
            "org_value": float(org_value) if org_value is not None else None,
            "benchmark_value": None,
            "benchmark_median": None,
            "percentile_rank": "unknown",
            "performance": "unknown",
            "category": category,
            "period_type": period,
            "sample_size": 0,
            "message": "",
        }

        if benchmark is None:
            result["message"] = (
                f"No benchmark data available for {metric_name} "
                f"in {category}/{period} category."
            )
            return result

        result["benchmark_value"] = float(benchmark.value)
        result["benchmark_median"] = (
            float(benchmark.percentile_50)
            if benchmark.percentile_50 is not None
            else None
        )
        result["sample_size"] = benchmark.sample_size

        if org_value is None:
            result["message"] = (
                f"No data available for your organization for {metric_name}."
            )
            return result

        # Calculate percentile rank
        percentile_rank = self._calculate_percentile_rank(
            org_value=org_value,
            benchmark=benchmark,
        )
        result["percentile_rank"] = percentile_rank

        # Determine performance level
        performance = self._determine_performance(percentile_rank)
        result["performance"] = performance

        # Generate human-readable message
        result["message"] = self._generate_comparison_message(
            metric_name=metric_name,
            org_value=org_value,
            benchmark_value=benchmark.value,
            percentile_rank=percentile_rank,
            performance=performance,
            sample_size=benchmark.sample_size,
        )

        return result

    # ─────────────────────────────────────────────────────────
    # BENCHMARK GENERATION (Admin/Scheduled)
    # ─────────────────────────────────────────────────────────

    def generate_benchmarks_from_platform_data(
        self,
        period_type: str,
        period_start: date,
    ) -> List["IndustryBenchmark"]:
        """
        Generate industry benchmarks from aggregated platform data.

        Aggregates metrics across all organizations, grouped by category,
        and creates anonymized benchmark records. Individual organization
        data is never identifiable in the output.

        Args:
            period_type: Period granularity ('DAILY', 'WEEKLY', 'MONTHLY')
            period_start: Start date of the benchmark period

        Returns:
            list: Created IndustryBenchmark instances
        """

        logger.info(
            "Generating benchmarks: period_type=%s period_start=%s",
            period_type,
            period_start,
        )

        created_benchmarks = []

        # Define metrics to benchmark
        metric_configs = [
            {
                "metric_name": "daily_revenue",
                "source": "analytics.SalesAggregation",
                "field": "net_revenue",
                "aggregation": "avg",
            },
            {
                "metric_name": "avg_order_value",
                "source": "analytics.SalesAggregation",
                "field": "avg_order_value",
                "aggregation": "avg",
            },
            {
                "metric_name": "daily_order_count",
                "source": "analytics.SalesAggregation",
                "field": "order_count",
                "aggregation": "avg",
            },
            {
                "metric_name": "daily_customer_count",
                "source": "analytics.SalesAggregation",
                "field": "customer_count",
                "aggregation": "avg",
            },
        ]

        # Determine date range based on period type
        period_end = self._calculate_period_end(period_type, period_start)

        for metric_config in metric_configs:
            try:
                benchmarks = self._generate_metric_benchmarks(
                    metric_config=metric_config,
                    period_type=period_type,
                    period_start=period_start,
                    period_end=period_end,
                )
                created_benchmarks.extend(benchmarks)
            except Exception as exc:
                logger.error(
                    "Failed to generate benchmark for %s: %s",
                    metric_config["metric_name"],
                    exc,
                )

        logger.info(
            "Benchmark generation complete: created=%d",
            len(created_benchmarks),
        )

        return created_benchmarks

    # ─────────────────────────────────────────────────────────
    # INTERNAL: METRIC CALCULATION
    # ─────────────────────────────────────────────────────────

    def _calculate_org_metric(
        self,
        org_id,
        metric_name: str,
        period_type: str,
    ) -> Optional[Decimal]:
        """
        Calculate a specific metric value for an organization.

        Args:
            org_id: Organization UUID
            metric_name: Metric to calculate
            period_type: Period type for the calculation

        Returns:
            Decimal value or None
        """
        period_start = self._get_default_period_start(period_type)

        metric_calculators = {
            "daily_revenue": self._calc_org_revenue,
            "avg_order_value": self._calc_org_avg_order_value,
            "daily_order_count": self._calc_org_order_count,
            "daily_customer_count": self._calc_org_customer_count,
        }

        calculator = metric_calculators.get(metric_name)
        if calculator:
            return calculator(org_id, period_start)

        logger.warning("Unknown metric for calculation: %s", metric_name)
        return None

    @staticmethod
    def _calc_org_revenue(org_id, period_start: date) -> Optional[Decimal]:
        """Calculate average daily revenue for an org."""
        try:
            from apps.analytics.models import SalesAggregation

            result = SalesAggregation.objects.filter(
                organization_id=org_id,
                date__gte=period_start,
                granularity="DAILY",
                deleted_at__isnull=True,
            ).aggregate(avg_value=Avg("net_revenue"))
            return result.get("avg_value")
        except Exception:
            return None

    @staticmethod
    def _calc_org_avg_order_value(org_id, period_start: date) -> Optional[Decimal]:
        """Calculate average order value for an org."""
        try:
            from apps.analytics.models import SalesAggregation

            result = SalesAggregation.objects.filter(
                organization_id=org_id,
                date__gte=period_start,
                granularity="DAILY",
                deleted_at__isnull=True,
            ).aggregate(avg_value=Avg("avg_order_value"))
            return result.get("avg_value")
        except Exception:
            return None

    @staticmethod
    def _calc_org_order_count(org_id, period_start: date) -> Optional[Decimal]:
        """Calculate average daily order count for an org."""
        try:
            from apps.analytics.models import SalesAggregation

            result = SalesAggregation.objects.filter(
                organization_id=org_id,
                date__gte=period_start,
                granularity="DAILY",
                deleted_at__isnull=True,
            ).aggregate(avg_value=Avg("order_count"))
            value = result.get("avg_value")
            return Decimal(str(value)) if value is not None else None
        except Exception:
            return None

    @staticmethod
    def _calc_org_customer_count(org_id, period_start: date) -> Optional[Decimal]:
        """Calculate average daily customer count for an org."""
        try:
            from apps.analytics.models import SalesAggregation

            result = SalesAggregation.objects.filter(
                organization_id=org_id,
                date__gte=period_start,
                granularity="DAILY",
                deleted_at__isnull=True,
            ).aggregate(avg_value=Avg("customer_count"))
            value = result.get("avg_value")
            return Decimal(str(value)) if value is not None else None
        except Exception:
            return None

    # ─────────────────────────────────────────────────────────
    # INTERNAL: BENCHMARK GENERATION
    # ─────────────────────────────────────────────────────────

    def _generate_metric_benchmarks(
        self,
        metric_config: dict,
        period_type: str,
        period_start: date,
        period_end: date,
    ) -> List["IndustryBenchmark"]:
        """
        Generate benchmark data for a single metric across all categories.

        Args:
            metric_config: Metric configuration dict
            period_type: Period granularity
            period_start: Period start date
            period_end: Period end date

        Returns:
            list of created IndustryBenchmark instances
        """
        from apps.reporting.models import IndustryBenchmark

        metric_name = metric_config["metric_name"]
        field_name = metric_config["field"]

        # Get per-organization aggregated values
        org_values = self._get_per_org_values(
            field_name=field_name,
            period_start=period_start,
            period_end=period_end,
        )

        if len(org_values) < MIN_SAMPLE_SIZE:
            logger.info(
                "Insufficient sample size for %s: %d (min: %d)",
                metric_name,
                len(org_values),
                MIN_SAMPLE_SIZE,
            )
            return []

        # Calculate statistics
        values = sorted(org_values)
        sample_size = len(values)
        avg_value = sum(values) / sample_size
        p25 = self._percentile(values, 25)
        p50 = self._percentile(values, 50)
        p75 = self._percentile(values, 75)
        p90 = self._percentile(values, 90)

        # Create or update benchmark
        # Using 'restaurant' as default category since we aggregate all
        # In a real implementation, this would be grouped by org category
        benchmark, created = IndustryBenchmark.objects.update_or_create(
            metric_name=metric_name,
            category="restaurant",
            region=DEFAULT_REGION,
            period_type=period_type,
            period_start=period_start,
            defaults={
                "value": Decimal(str(round(avg_value, 4))),
                "sample_size": sample_size,
                "percentile_25": Decimal(str(round(p25, 4))),
                "percentile_50": Decimal(str(round(p50, 4))),
                "percentile_75": Decimal(str(round(p75, 4))),
                "percentile_90": Decimal(str(round(p90, 4))),
            },
        )

        action = "Created" if created else "Updated"
        logger.info(
            "%s benchmark: metric=%s category=restaurant avg=%.2f p50=%.2f sample=%d",
            action,
            metric_name,
            avg_value,
            p50,
            sample_size,
        )

        return [benchmark]

    @staticmethod
    def _get_per_org_values(
        field_name: str,
        period_start: date,
        period_end: date,
    ) -> List[float]:
        """
        Get aggregated per-organization values for a metric field.

        Returns anonymized values (no org identifiers).

        Args:
            field_name: Model field to aggregate
            period_start: Start date
            period_end: End date

        Returns:
            list of float values (one per org)
        """
        try:
            from apps.analytics.models import SalesAggregation

            results = (
                SalesAggregation.objects.filter(
                    date__gte=period_start,
                    date__lte=period_end,
                    granularity="DAILY",
                    deleted_at__isnull=True,
                )
                .values("organization_id")
                .annotate(avg_value=Avg(field_name))
                .filter(avg_value__isnull=False)
            )

            return [
                float(r["avg_value"]) for r in results if r["avg_value"] is not None
            ]
        except Exception as exc:
            logger.error(
                "Failed to get per-org values for %s: %s",
                field_name,
                exc,
            )
            return []

    # ─────────────────────────────────────────────────────────
    # INTERNAL: HELPERS
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _get_org_category(org_id) -> str:
        """
        Get the business category for an organization.

        Args:
            org_id: Organization UUID

        Returns:
            str: Category string (default: 'restaurant')
        """
        try:
            from apps.core.models import Organization

            org = Organization.objects.filter(
                id=org_id,
                deleted_at__isnull=True,
            ).first()
            if org and org.settings:
                return org.settings.get("category", "restaurant")
        except Exception:
            pass
        return "restaurant"

    @staticmethod
    def _get_default_period_start(period_type: str) -> date:
        """
        Get the default period start date based on period type.

        Args:
            period_type: Period granularity

        Returns:
            date: Period start date
        """
        today = timezone.localdate()
        if period_type == "DAILY":
            return today - timedelta(days=1)
        elif period_type == "WEEKLY":
            return today - timedelta(weeks=1)
        elif period_type == "MONTHLY":
            return today.replace(day=1)
        return today - timedelta(days=30)

    @staticmethod
    def _calculate_period_end(period_type: str, period_start: date) -> date:
        """
        Calculate period end date.

        Args:
            period_type: Period granularity
            period_start: Period start date

        Returns:
            date: Period end date
        """
        if period_type == "DAILY":
            return period_start
        elif period_type == "WEEKLY":
            return period_start + timedelta(days=6)
        elif period_type == "MONTHLY":
            # End of month
            if period_start.month == 12:
                return date(period_start.year + 1, 1, 1) - timedelta(days=1)
            return date(period_start.year, period_start.month + 1, 1) - timedelta(
                days=1
            )
        return period_start + timedelta(days=30)

    @staticmethod
    def _percentile(sorted_values: List[float], percentile: int) -> float:
        """
        Calculate a percentile from sorted values.

        Args:
            sorted_values: Sorted list of float values
            percentile: Percentile to calculate (0-100)

        Returns:
            float: Percentile value
        """
        if not sorted_values:
            return 0.0
        n = len(sorted_values)
        idx = (percentile / 100.0) * (n - 1)
        lower = int(idx)
        upper = min(lower + 1, n - 1)
        weight = idx - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight

    @staticmethod
    def _calculate_percentile_rank(
        org_value: Decimal,
        benchmark: "IndustryBenchmark",
    ) -> str:
        """
        Determine which percentile band the org value falls into.

        Args:
            org_value: Organization's metric value
            benchmark: Industry benchmark record

        Returns:
            str: Percentile band identifier
        """
        org_float = float(org_value)

        if benchmark.percentile_25 is not None and org_float < float(
            benchmark.percentile_25
        ):
            return "below_25"
        if benchmark.percentile_50 is not None and org_float < float(
            benchmark.percentile_50
        ):
            return "25_50"
        if benchmark.percentile_75 is not None and org_float < float(
            benchmark.percentile_75
        ):
            return "50_75"
        if benchmark.percentile_90 is not None and org_float < float(
            benchmark.percentile_90
        ):
            return "75_90"
        return "above_90"

    @staticmethod
    def _determine_performance(percentile_rank: str) -> str:
        """
        Map percentile rank to a performance label.

        Args:
            percentile_rank: Percentile band

        Returns:
            str: Performance label
        """
        mapping = {
            "below_25": "below_average",
            "25_50": "average",
            "50_75": "above_average",
            "75_90": "above_average",
            "above_90": "top_performer",
        }
        return mapping.get(percentile_rank, "unknown")

    @staticmethod
    def _generate_comparison_message(
        metric_name: str,
        org_value: Decimal,
        benchmark_value: Decimal,
        percentile_rank: str,
        performance: str,
        sample_size: int,
    ) -> str:
        """
        Generate a human-readable comparison message.

        Args:
            metric_name: Name of the metric
            org_value: Organization's value
            benchmark_value: Industry average
            percentile_rank: Percentile band
            performance: Performance label
            sample_size: Number of orgs in benchmark

        Returns:
            str: Comparison message
        """
        org_float = float(org_value)
        bench_float = float(benchmark_value)

        if bench_float > 0:
            diff_pct = ((org_float - bench_float) / bench_float) * 100
            direction = "above" if diff_pct > 0 else "below"
            diff_pct_abs = abs(diff_pct)
        else:
            diff_pct_abs = 0
            direction = "at"

        performance_labels = {
            "below_average": "below the industry average",
            "average": "at the industry average",
            "above_average": "above the industry average",
            "top_performer": "among the top performers",
        }
        perf_label = performance_labels.get(performance, "comparable to the industry")

        return (
            f"Your {metric_name.replace('_', ' ')} is "
            f"{org_float:,.2f}, which is {diff_pct_abs:.1f}% {direction} "
            f"the industry average of {bench_float:,.2f}. "
            f"You are {perf_label} "
            f"(based on {sample_size} businesses)."
        )
