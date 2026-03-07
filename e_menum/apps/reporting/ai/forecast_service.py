"""
Forecasting Service for the Reporting module.

Provides revenue, order, and customer forecasting using statistical methods:
    - Weighted Moving Average (WMA) for short-term level estimation
    - Linear Regression for trend detection and extrapolation
    - Combined WMA + Trend for final forecasts with confidence bounds

Uses Python stdlib only (no numpy, scipy, or prophet dependencies).

Usage:
    from apps.reporting.ai.forecast_service import ForecastService

    service = ForecastService()
    result = service.forecast_revenue(
        org_id=organization.id,
        days_ahead=30,
    )
    # result = {
    #     'forecast': [
    #         {'date': '2026-02-01', 'predicted_value': 12500.0,
    #          'lower_bound': 10000.0, 'upper_bound': 15000.0},
    #         ...
    #     ],
    #     'confidence': 0.75,
    #     'method': 'wma_linear_trend',
    #     'historical_summary': {
    #         'mean': 11200.0, 'std': 2100.0, 'min': 5400.0,
    #         'max': 18000.0, 'trend': 'rising',
    #     },
    # }

Critical Rules:
    - EVERY query MUST filter by organization_id (multi-tenant isolation)
    - EVERY query MUST filter deleted_at__isnull=True (soft delete)
    - Uses Python stdlib math/statistics only
    - No external forecasting libraries required
"""

import logging
import math
import statistics
from datetime import date, timedelta
from typing import List, Tuple

from django.utils import timezone

logger = logging.getLogger(__name__)

# Default number of historical days to use for forecasting
DEFAULT_LOOKBACK_DAYS = 90

# Minimum data points required for a meaningful forecast
MIN_DATA_POINTS = 14

# Default WMA window size
DEFAULT_WMA_WINDOW = 7

# Confidence interval multiplier (approx. 95% CI for normal distribution)
CONFIDENCE_MULTIPLIER = 1.96


class ForecastService:
    """
    Forecasting service using statistical methods.

    Combines Weighted Moving Average with Linear Trend for predictions.
    No external dependencies beyond Python stdlib.
    """

    # ─────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────

    def forecast_revenue(
        self,
        org_id,
        days_ahead: int = 30,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ) -> dict:
        """
        Forecast daily net revenue for the next N days.

        Args:
            org_id: Organization UUID (tenant isolation)
            days_ahead: Number of days to forecast (default: 30)
            lookback_days: Historical days to analyze (default: 90)

        Returns:
            dict with keys:
                - forecast: list of daily predictions
                - confidence: overall confidence score (0-1)
                - method: forecasting method used
                - historical_summary: summary statistics of historical data
        """
        historical = self._get_historical_data(org_id, "net_revenue", lookback_days)
        return self._build_forecast(historical, days_ahead, "net_revenue")

    def forecast_orders(
        self,
        org_id,
        days_ahead: int = 30,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ) -> dict:
        """
        Forecast daily order count for the next N days.

        Args:
            org_id: Organization UUID (tenant isolation)
            days_ahead: Number of days to forecast (default: 30)
            lookback_days: Historical days to analyze (default: 90)

        Returns:
            dict: Forecast result with predictions and confidence
        """
        historical = self._get_historical_data(org_id, "order_count", lookback_days)
        return self._build_forecast(historical, days_ahead, "order_count")

    def forecast_customers(
        self,
        org_id,
        days_ahead: int = 30,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ) -> dict:
        """
        Forecast daily customer count for the next N days.

        Args:
            org_id: Organization UUID (tenant isolation)
            days_ahead: Number of days to forecast (default: 30)
            lookback_days: Historical days to analyze (default: 90)

        Returns:
            dict: Forecast result with predictions and confidence
        """
        historical = self._get_historical_data(org_id, "customer_count", lookback_days)
        return self._build_forecast(historical, days_ahead, "customer_count")

    # ─────────────────────────────────────────────────────────
    # DATA RETRIEVAL
    # ─────────────────────────────────────────────────────────

    def _get_historical_data(
        self,
        org_id,
        metric_field: str,
        days_back: int = DEFAULT_LOOKBACK_DAYS,
    ) -> List[dict]:
        """
        Get historical daily data from SalesAggregation.

        Always filters by organization_id and deleted_at__isnull=True.

        Args:
            org_id: Organization UUID
            metric_field: Field name to retrieve (e.g., 'net_revenue')
            days_back: Number of historical days to fetch

        Returns:
            list[dict]: Sorted list of {'date': date, 'value': float} dicts
        """
        from apps.analytics.models import SalesAggregation

        end_date = timezone.localdate()
        start_date = end_date - timedelta(days=days_back)

        rows = list(
            SalesAggregation.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                granularity="DAILY",
                date__gte=start_date,
                date__lte=end_date,
            )
            .order_by("date")
            .values("date", metric_field)
        )

        result = []
        for row in rows:
            value = row.get(metric_field, 0)
            result.append(
                {
                    "date": row["date"],
                    "value": float(value) if value is not None else 0.0,
                }
            )

        return result

    # ─────────────────────────────────────────────────────────
    # FORECAST BUILDER
    # ─────────────────────────────────────────────────────────

    def _build_forecast(
        self,
        historical: List[dict],
        days_ahead: int,
        metric_name: str,
    ) -> dict:
        """
        Build a forecast from historical data using WMA + linear trend.

        Args:
            historical: List of {'date': date, 'value': float}
            days_ahead: Number of days to forecast
            metric_name: Name of the metric being forecast

        Returns:
            dict: Complete forecast result
        """
        if len(historical) < MIN_DATA_POINTS:
            return {
                "forecast": [],
                "confidence": 0.0,
                "method": "insufficient_data",
                "historical_summary": self._historical_summary(historical),
                "error": (
                    f"Insufficient data: {len(historical)} data points found, "
                    f"minimum {MIN_DATA_POINTS} required for forecasting."
                ),
            }

        values = [h["value"] for h in historical]
        dates = [h["date"] for h in historical]

        # Calculate components
        wma = self._weighted_moving_average(values, window=DEFAULT_WMA_WINDOW)
        slope, intercept = self._linear_trend(values)

        # Calculate residual standard deviation for confidence bounds
        residual_std = self._residual_std(values, slope, intercept)

        # Generate forecast
        forecast = self._forecast_with_trend(
            values=values,
            last_date=dates[-1],
            days_ahead=days_ahead,
            wma=wma,
            slope=slope,
            intercept=intercept,
            residual_std=residual_std,
            metric_name=metric_name,
        )

        # Calculate confidence score based on data quality
        confidence = self._calculate_confidence(values, slope, intercept)

        return {
            "forecast": forecast,
            "confidence": round(confidence, 3),
            "method": "wma_linear_trend",
            "historical_summary": self._historical_summary(historical),
        }

    # ─────────────────────────────────────────────────────────
    # STATISTICAL METHODS
    # ─────────────────────────────────────────────────────────

    def _weighted_moving_average(self, data: List[float], window: int = 7) -> float:
        """
        Calculate weighted moving average of the most recent data points.

        More recent values get higher weights (linearly increasing).
        Weights: [1, 2, 3, ..., window]

        Args:
            data: Time series values
            window: Number of recent data points to consider

        Returns:
            float: Weighted moving average
        """
        if not data:
            return 0.0

        actual_window = min(window, len(data))
        recent = data[-actual_window:]

        # Linear weights: 1, 2, 3, ..., actual_window
        weights = list(range(1, actual_window + 1))
        total_weight = sum(weights)

        weighted_sum = sum(v * w for v, w in zip(recent, weights))
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _linear_trend(self, data: List[float]) -> Tuple[float, float]:
        """
        Calculate linear trend using simple least-squares regression.

        y = slope * x + intercept

        Args:
            data: Time series values (chronological order)

        Returns:
            tuple: (slope, intercept)
        """
        n = len(data)
        if n < 2:
            return (0.0, data[0] if data else 0.0)

        x_values = list(range(n))
        x_mean = sum(x_values) / n
        y_mean = sum(data) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, data))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return (0.0, y_mean)

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        return (slope, intercept)

    def _residual_std(
        self,
        values: List[float],
        slope: float,
        intercept: float,
    ) -> float:
        """
        Calculate the standard deviation of residuals from the trend line.

        Used to compute prediction confidence intervals.

        Args:
            values: Observed values
            slope: Trend line slope
            intercept: Trend line intercept

        Returns:
            float: Residual standard deviation
        """
        if len(values) < 3:
            return 0.0

        residuals = []
        for i, val in enumerate(values):
            predicted = slope * i + intercept
            residuals.append(val - predicted)

        return statistics.stdev(residuals) if len(residuals) > 1 else 0.0

    def _forecast_with_trend(
        self,
        values: List[float],
        last_date: date,
        days_ahead: int,
        wma: float,
        slope: float,
        intercept: float,
        residual_std: float,
        metric_name: str,
    ) -> List[dict]:
        """
        Combine WMA level with linear trend for forecasting.

        The forecast blends:
        1. WMA (recent level) - what the recent average looks like
        2. Linear trend (direction) - the rate of change

        The prediction for day t (after the last data point) is:
            predicted = wma + slope * t

        Confidence bounds widen with the forecast horizon.

        Args:
            values: Historical time series
            last_date: Last date in historical data
            days_ahead: Number of days to forecast
            wma: Weighted moving average (recent level)
            slope: Linear trend slope (daily change)
            intercept: Linear trend intercept
            residual_std: Standard deviation of trend residuals
            metric_name: Name of the metric

        Returns:
            list[dict]: Daily forecasts with bounds
        """
        len(values)
        forecast = []

        for t in range(1, days_ahead + 1):
            forecast_date = last_date + timedelta(days=t)

            # Base prediction: WMA level + trend adjustment
            # The trend adjustment grows linearly with time
            predicted = wma + slope * t

            # Ensure non-negative predictions for count-based metrics
            if metric_name in ("order_count", "customer_count", "item_count"):
                predicted = max(0.0, predicted)

            # Confidence interval widens with forecast horizon
            # Standard error increases with sqrt(t)
            horizon_factor = math.sqrt(t)
            margin = CONFIDENCE_MULTIPLIER * residual_std * horizon_factor

            lower_bound = predicted - margin
            upper_bound = predicted + margin

            # Ensure non-negative bounds for count metrics
            if metric_name in ("order_count", "customer_count", "item_count"):
                lower_bound = max(0.0, lower_bound)
                upper_bound = max(0.0, upper_bound)

            forecast.append(
                {
                    "date": forecast_date.isoformat(),
                    "predicted_value": round(predicted, 2),
                    "lower_bound": round(lower_bound, 2),
                    "upper_bound": round(upper_bound, 2),
                }
            )

        return forecast

    def _calculate_confidence(
        self,
        values: List[float],
        slope: float,
        intercept: float,
    ) -> float:
        """
        Calculate an overall confidence score for the forecast.

        Factors considered:
        1. Amount of historical data (more data = higher confidence)
        2. R-squared of the trend fit (better fit = higher confidence)
        3. Coefficient of variation (lower variability = higher confidence)

        Args:
            values: Historical time series
            slope: Trend slope
            intercept: Trend intercept

        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        n = len(values)

        # Factor 1: Data sufficiency (0-0.3)
        # Full score at 60+ days, linear ramp from MIN_DATA_POINTS
        data_score = min(1.0, (n - MIN_DATA_POINTS) / (60 - MIN_DATA_POINTS))
        data_score = max(0.0, data_score) * 0.3

        # Factor 2: R-squared (0-0.4)
        y_mean = sum(values) / n if n > 0 else 0
        y_predicted = [slope * i + intercept for i in range(n)]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(values, y_predicted))
        ss_tot = sum((y - y_mean) ** 2 for y in values)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        r_squared = max(0.0, r_squared)
        r_score = r_squared * 0.4

        # Factor 3: Low variability (0-0.3)
        # Use coefficient of variation (CV = std/mean)
        if y_mean != 0 and n > 1:
            cv = statistics.stdev(values) / abs(y_mean)
            # CV < 0.2 = perfect, CV > 1.0 = terrible
            variability_score = max(0.0, 1.0 - cv)
        else:
            variability_score = 0.0
        var_score = variability_score * 0.3

        confidence = data_score + r_score + var_score
        return min(1.0, max(0.0, confidence))

    # ─────────────────────────────────────────────────────────
    # HISTORICAL SUMMARY
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _historical_summary(historical: List[dict]) -> dict:
        """
        Generate summary statistics of the historical data.

        Args:
            historical: List of {'date': date, 'value': float}

        Returns:
            dict: Summary with mean, std, min, max, count, trend direction
        """
        if not historical:
            return {
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0,
                "trend": "insufficient_data",
                "first_date": None,
                "last_date": None,
            }

        values = [h["value"] for h in historical]
        n = len(values)

        mean_val = statistics.mean(values) if values else 0.0
        std_val = statistics.stdev(values) if n > 1 else 0.0
        min_val = min(values) if values else 0.0
        max_val = max(values) if values else 0.0

        # Simple trend determination
        if n >= 7:
            first_half = statistics.mean(values[: n // 2])
            second_half = statistics.mean(values[n // 2 :])
            if first_half > 0:
                change = (second_half - first_half) / first_half
                if change > 0.05:
                    trend = "rising"
                elif change < -0.05:
                    trend = "falling"
                else:
                    trend = "stable"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "min": round(min_val, 2),
            "max": round(max_val, 2),
            "count": n,
            "trend": trend,
            "first_date": historical[0]["date"].isoformat() if historical else None,
            "last_date": historical[-1]["date"].isoformat() if historical else None,
        }
