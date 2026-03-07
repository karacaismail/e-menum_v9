"""
Credit Service for managing AI feature credit balances.

Provides atomic credit operations with proper locking to prevent
race conditions in concurrent environments. All operations are
organization-scoped for multi-tenant isolation.

Usage:
    from apps.reporting.services.credit_service import CreditService

    service = CreditService()

    # Check balance
    balance = service.get_balance(org_id)
    print(f"Available: {balance.available_credits}")

    # Consume credits for a report
    tx = service.consume_credits(
        org_id=org_id,
        amount=5,
        description="Revenue report execution",
        reference_type="report_execution",
        reference_id=execution.id,
        user=request.user,
    )

    # Add credits from subscription
    tx = service.add_credits(
        org_id=org_id,
        amount=1000,
        description="Monthly subscription credit allocation",
        user=admin_user,
    )

Critical Rules:
    - EVERY query MUST filter by organization_id (multi-tenant isolation)
    - Use select_for_update() for atomic credit operations
    - Credit transactions are immutable (no updates/deletes)
"""

import logging
from datetime import date
from typing import Optional

from django.db import transaction

from apps.reporting.models import CreditBalance, CreditTransaction
from django.db.models import Sum

from shared.utils.exceptions import AppException

logger = logging.getLogger(__name__)


class CreditService:
    """
    Service for managing organization credit balances and transactions.

    Provides thread-safe credit operations using database-level locking
    (select_for_update) to prevent race conditions.
    """

    # ─────────────────────────────────────────────────────────
    # BALANCE QUERIES
    # ─────────────────────────────────────────────────────────

    def get_balance(self, org_id) -> "CreditBalance":
        """
        Get or create the credit balance for an organization.

        Args:
            org_id: Organization UUID

        Returns:
            CreditBalance: The organization's credit balance record
        """
        from apps.reporting.models import CreditBalance

        balance, created = CreditBalance.objects.get_or_create(
            organization_id=org_id,
            defaults={
                "total_credits": 0,
                "used_credits": 0,
                "reserved_credits": 0,
            },
        )

        if created:
            logger.info(
                "Created initial credit balance for org=%s",
                org_id,
            )

        return balance

    def has_sufficient_credits(self, org_id, amount: int) -> bool:
        """
        Check if an organization has enough available credits.

        Args:
            org_id: Organization UUID
            amount: Required credit amount

        Returns:
            bool: True if sufficient credits are available
        """
        balance = self.get_balance(org_id)
        return balance.available_credits >= amount

    # ─────────────────────────────────────────────────────────
    # CREDIT OPERATIONS (Atomic)
    # ─────────────────────────────────────────────────────────

    @transaction.atomic
    def reserve_credits(
        self,
        org_id,
        amount: int,
        reference_type: str = "",
        reference_id=None,
    ) -> "CreditTransaction":
        """
        Reserve credits for an in-progress operation.

        Reserved credits are subtracted from available balance but not
        permanently consumed. They can be either consumed (on success)
        or released (on failure).

        Args:
            org_id: Organization UUID
            amount: Number of credits to reserve (must be positive)
            reference_type: Type of the referencing entity
            reference_id: UUID of the referencing entity

        Returns:
            CreditTransaction: The reservation transaction record

        Raises:
            AppException: If insufficient credits
        """
        from apps.reporting.models import CreditBalance, CreditTransaction

        if amount <= 0:
            raise AppException(
                code="INVALID_CREDIT_AMOUNT",
                message="Credit amount must be positive",
                status_code=400,
            )

        # Lock the balance row for atomic update
        balance = CreditBalance.objects.select_for_update().get_or_create(
            organization_id=org_id,
            defaults={
                "total_credits": 0,
                "used_credits": 0,
                "reserved_credits": 0,
            },
        )[0]

        if balance.available_credits < amount:
            raise AppException(
                code="INSUFFICIENT_CREDITS",
                message=(
                    f"Insufficient credits. Available: {balance.available_credits}, "
                    f"required: {amount}"
                ),
                status_code=402,
            )

        balance.reserved_credits += amount
        balance.save(update_fields=["reserved_credits", "updated_at"])

        # Create transaction record
        tx = CreditTransaction.objects.create(
            organization_id=org_id,
            transaction_type="CONSUME",
            amount=-amount,
            balance_after=balance.available_credits,
            description=f"Credits reserved: {amount}",
            reference_type=reference_type,
            reference_id=reference_id,
        )

        logger.info(
            "Credits reserved: org=%s amount=%d available=%d",
            org_id,
            amount,
            balance.available_credits,
        )

        return tx

    @transaction.atomic
    def consume_credits(
        self,
        org_id,
        amount: int,
        description: str = "",
        reference_type: str = "",
        reference_id=None,
        user=None,
    ) -> "CreditTransaction":
        """
        Consume credits for a completed operation.

        Permanently deducts credits from the organization's balance.

        Args:
            org_id: Organization UUID
            amount: Number of credits to consume (must be positive)
            description: Human-readable description
            reference_type: Type of the referencing entity
            reference_id: UUID of the referencing entity
            user: User who initiated the consumption

        Returns:
            CreditTransaction: The consumption transaction record

        Raises:
            AppException: If insufficient credits
        """
        from apps.reporting.models import CreditBalance, CreditTransaction

        if amount <= 0:
            raise AppException(
                code="INVALID_CREDIT_AMOUNT",
                message="Credit amount must be positive",
                status_code=400,
            )

        # Lock the balance row for atomic update
        balance = CreditBalance.objects.select_for_update().get_or_create(
            organization_id=org_id,
            defaults={
                "total_credits": 0,
                "used_credits": 0,
                "reserved_credits": 0,
            },
        )[0]

        if balance.available_credits < amount:
            raise AppException(
                code="INSUFFICIENT_CREDITS",
                message=(
                    f"Insufficient credits. Available: {balance.available_credits}, "
                    f"required: {amount}"
                ),
                status_code=402,
            )

        balance.used_credits += amount
        balance.save(update_fields=["used_credits", "updated_at"])

        # Create transaction record
        tx = CreditTransaction.objects.create(
            organization_id=org_id,
            transaction_type="CONSUME",
            amount=-amount,
            balance_after=balance.available_credits,
            description=description or f"Credits consumed: {amount}",
            reference_type=reference_type,
            reference_id=reference_id,
            created_by=user,
        )

        logger.info(
            "Credits consumed: org=%s amount=%d remaining=%d user=%s",
            org_id,
            amount,
            balance.available_credits,
            user.email if user and hasattr(user, "email") else "system",
        )

        return tx

    @transaction.atomic
    def release_reserved(self, org_id, amount: int) -> None:
        """
        Release previously reserved credits back to available balance.

        Used when an operation that reserved credits fails or is cancelled.

        Args:
            org_id: Organization UUID
            amount: Number of credits to release (must be positive)
        """
        from apps.reporting.models import CreditBalance

        if amount <= 0:
            return

        balance = CreditBalance.objects.select_for_update().get_or_create(
            organization_id=org_id,
            defaults={
                "total_credits": 0,
                "used_credits": 0,
                "reserved_credits": 0,
            },
        )[0]

        # Release cannot exceed current reservations
        release_amount = min(amount, balance.reserved_credits)
        balance.reserved_credits -= release_amount
        balance.save(update_fields=["reserved_credits", "updated_at"])

        logger.info(
            "Credits released: org=%s amount=%d reserved_remaining=%d",
            org_id,
            release_amount,
            balance.reserved_credits,
        )

    @transaction.atomic
    def add_credits(
        self,
        org_id,
        amount: int,
        description: str = "",
        user=None,
    ) -> "CreditTransaction":
        """
        Add credits to an organization's balance.

        Used for subscription allocations, bonus credits, or manual top-ups.

        Args:
            org_id: Organization UUID
            amount: Number of credits to add (must be positive)
            description: Human-readable description
            user: User who initiated the addition

        Returns:
            CreditTransaction: The addition transaction record

        Raises:
            AppException: If amount is invalid
        """
        from apps.reporting.models import CreditBalance, CreditTransaction

        if amount <= 0:
            raise AppException(
                code="INVALID_CREDIT_AMOUNT",
                message="Credit amount must be positive",
                status_code=400,
            )

        balance = CreditBalance.objects.select_for_update().get_or_create(
            organization_id=org_id,
            defaults={
                "total_credits": 0,
                "used_credits": 0,
                "reserved_credits": 0,
            },
        )[0]

        balance.total_credits += amount
        balance.save(update_fields=["total_credits", "updated_at"])

        tx = CreditTransaction.objects.create(
            organization_id=org_id,
            transaction_type="PURCHASE",
            amount=amount,
            balance_after=balance.available_credits,
            description=description or f"Credits added: {amount}",
            reference_type="manual",
            created_by=user,
        )

        logger.info(
            "Credits added: org=%s amount=%d total=%d user=%s",
            org_id,
            amount,
            balance.total_credits,
            user.email if user and hasattr(user, "email") else "system",
        )

        return tx

    @transaction.atomic
    def refund_credits(
        self,
        org_id,
        amount: int,
        description: str = "",
        reference_type: str = "",
        reference_id=None,
    ) -> "CreditTransaction":
        """
        Refund credits to an organization's balance.

        Reduces used_credits and records a refund transaction.

        Args:
            org_id: Organization UUID
            amount: Number of credits to refund (must be positive)
            description: Reason for refund
            reference_type: Type of the original entity
            reference_id: UUID of the original entity

        Returns:
            CreditTransaction: The refund transaction record
        """
        from apps.reporting.models import CreditBalance, CreditTransaction

        if amount <= 0:
            raise AppException(
                code="INVALID_CREDIT_AMOUNT",
                message="Credit amount must be positive",
                status_code=400,
            )

        balance = CreditBalance.objects.select_for_update().get_or_create(
            organization_id=org_id,
            defaults={
                "total_credits": 0,
                "used_credits": 0,
                "reserved_credits": 0,
            },
        )[0]

        # Refund cannot exceed used credits
        refund_amount = min(amount, balance.used_credits)
        balance.used_credits -= refund_amount
        balance.save(update_fields=["used_credits", "updated_at"])

        tx = CreditTransaction.objects.create(
            organization_id=org_id,
            transaction_type="REFUND",
            amount=refund_amount,
            balance_after=balance.available_credits,
            description=description or f"Credits refunded: {refund_amount}",
            reference_type=reference_type,
            reference_id=reference_id,
        )

        logger.info(
            "Credits refunded: org=%s amount=%d available=%d",
            org_id,
            refund_amount,
            balance.available_credits,
        )

        return tx

    # ─────────────────────────────────────────────────────────
    # USAGE REPORTING
    # ─────────────────────────────────────────────────────────

    def get_usage_summary(
        self,
        org_id,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Get a credit usage summary for an organization over a period.

        Args:
            org_id: Organization UUID
            start_date: Start of the reporting period (inclusive)
            end_date: End of the reporting period (inclusive)

        Returns:
            dict with:
                - balance: Current balance snapshot
                - total_consumed: Total credits consumed in period
                - total_added: Total credits added in period
                - total_refunded: Total credits refunded in period
                - breakdown_by_type: Dict of consumption by reference_type
                - transaction_count: Number of transactions in period
        """
        from apps.reporting.models import CreditTransaction

        balance = self.get_balance(org_id)

        # Build date filter
        qs = CreditTransaction.objects.filter(
            organization_id=org_id,
        )

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        # Aggregate by transaction type
        aggregates = qs.values("transaction_type").annotate(
            total_amount=Sum("amount"),
        )

        type_totals = {}
        for agg in aggregates:
            type_totals[agg["transaction_type"]] = agg["total_amount"] or 0

        # Breakdown by reference type for consumption
        consume_qs = qs.filter(transaction_type="CONSUME")
        breakdown = (
            consume_qs.values("reference_type")
            .annotate(
                total_amount=Sum("amount"),
            )
            .order_by("reference_type")
        )

        breakdown_dict = {}
        for item in breakdown:
            ref_type = item["reference_type"] or "unspecified"
            breakdown_dict[ref_type] = abs(item["total_amount"] or 0)

        return {
            "balance": {
                "total_credits": balance.total_credits,
                "used_credits": balance.used_credits,
                "reserved_credits": balance.reserved_credits,
                "available_credits": balance.available_credits,
            },
            "total_consumed": abs(type_totals.get("CONSUME", 0)),
            "total_added": type_totals.get("PURCHASE", 0) + type_totals.get("BONUS", 0),
            "total_refunded": type_totals.get("REFUND", 0),
            "breakdown_by_type": breakdown_dict,
            "transaction_count": qs.count(),
        }
