"""Support ticket models for the restaurant owner portal."""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    Organization,
    SoftDeleteManager,
    SoftDeleteMixin,
    TimeStampedMixin,
    User,
)


class TicketStatus(models.TextChoices):
    OPEN = "OPEN", _("Acik")
    IN_PROGRESS = "IN_PROGRESS", _("Isleniyor")
    RESOLVED = "RESOLVED", _("Cozuldu")
    CLOSED = "CLOSED", _("Kapatildi")


class TicketPriority(models.TextChoices):
    LOW = "LOW", _("Dusuk")
    MEDIUM = "MEDIUM", _("Orta")
    HIGH = "HIGH", _("Yuksek")
    URGENT = "URGENT", _("Acil")


class TicketCategory(models.TextChoices):
    GENERAL = "GENERAL", _("Genel")
    BILLING = "BILLING", _("Faturalama")
    TECHNICAL = "TECHNICAL", _("Teknik")
    FEATURE_REQUEST = "FEATURE_REQUEST", _("Ozellik Talebi")
    BUG_REPORT = "BUG_REPORT", _("Hata Bildirimi")
    OTHER = "OTHER", _("Diger")


class SupportTicket(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """Support ticket created by restaurant owner."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="support_tickets",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_tickets",
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.OPEN,
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=TicketPriority.choices,
        default=TicketPriority.MEDIUM,
    )
    category = models.CharField(
        max_length=30,
        choices=TicketCategory.choices,
        default=TicketCategory.GENERAL,
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "support_tickets"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["organization", "status"], name="ticket_org_status_idx"
            ),
        ]

    def __str__(self):
        return f"#{str(self.id)[:8]} - {self.subject}"


class TicketComment(TimeStampedMixin, models.Model):
    """Comment on a support ticket."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ticket_comments",
    )
    message = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text=_("Internal notes not visible to restaurant owner"),
    )

    class Meta:
        db_table = "ticket_comments"
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.email} on {self.ticket}"
