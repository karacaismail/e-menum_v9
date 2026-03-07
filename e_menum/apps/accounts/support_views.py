"""Support ticket views for the restaurant owner portal."""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.core.choices import AuditAction
from apps.core.models import AuditLog
from apps.core.views import get_client_ip

from .support_models import (
    SupportTicket,
    TicketCategory,
    TicketComment,
    TicketPriority,
    TicketStatus,
)

logger = logging.getLogger(__name__)


def _get_org(request):
    """Get organization or None."""
    return getattr(request.user, "organization", None)


@login_required(login_url="/account/login/")
def support_list(request):
    """List support tickets for the user's organization."""
    org = _get_org(request)
    if not org:
        return redirect("accounts:profile")

    qs = (
        SupportTicket.objects.filter(
            organization=org,
        )
        .select_related("created_by", "assigned_to")
        .order_by("-created_at")
    )

    # Filter by status
    status_filter = request.GET.get("status", "").strip()
    if status_filter and status_filter in TicketStatus.values:
        qs = qs.filter(status=status_filter)

    context = {
        "tickets": qs,
        "current_status": status_filter,
        "status_choices": TicketStatus,
    }
    return render(request, "accounts/support/list.html", context)


@login_required(login_url="/account/login/")
def support_create(request):
    """Create a new support ticket."""
    org = _get_org(request)
    if not org:
        return redirect("accounts:profile")

    if request.method == "POST":
        subject = request.POST.get("subject", "").strip()
        description = request.POST.get("description", "").strip()
        category = request.POST.get("category", TicketCategory.GENERAL)
        priority = request.POST.get("priority", TicketPriority.MEDIUM)

        errors = {}
        if not subject:
            errors["subject"] = _("Konu alani zorunludur.")
        if not description:
            errors["description"] = _("Aciklama alani zorunludur.")
        if category not in TicketCategory.values:
            category = TicketCategory.GENERAL
        if priority not in TicketPriority.values:
            priority = TicketPriority.MEDIUM

        if not errors:
            ticket = SupportTicket.objects.create(
                organization=org,
                created_by=request.user,
                subject=subject,
                description=description,
                category=category,
                priority=priority,
            )

            AuditLog.log_action(
                action=AuditAction.CREATE,
                resource="support_ticket",
                resource_id=str(ticket.id),
                user=request.user,
                organization=org,
                description=f"User {request.user.email} created support ticket: {subject}",
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            )

            messages.success(request, _("Destek talebiniz basariyla olusturuldu."))
            return redirect("accounts:support-detail", ticket_id=ticket.id)
        else:
            for field, error in errors.items():
                messages.error(request, error)
            context = {
                "form_data": {
                    "subject": subject,
                    "description": description,
                    "category": category,
                    "priority": priority,
                },
                "category_choices": TicketCategory.choices,
                "priority_choices": TicketPriority.choices,
                "errors": errors,
            }
            return render(request, "accounts/support/create.html", context)

    context = {
        "form_data": {},
        "category_choices": TicketCategory.choices,
        "priority_choices": TicketPriority.choices,
        "errors": {},
    }
    return render(request, "accounts/support/create.html", context)


@login_required(login_url="/account/login/")
def support_detail(request, ticket_id):
    """View ticket detail with comments."""
    org = _get_org(request)
    if not org:
        return redirect("accounts:profile")

    ticket = get_object_or_404(
        SupportTicket,
        id=ticket_id,
        organization=org,
    )

    # Only show non-internal comments to restaurant owners
    comments = (
        ticket.comments.filter(
            is_internal=False,
        )
        .select_related("author")
        .order_by("created_at")
    )

    context = {
        "ticket": ticket,
        "comments": comments,
        "status_choices": TicketStatus,
    }
    return render(request, "accounts/support/detail.html", context)


@require_POST
@login_required(login_url="/account/login/")
def support_add_comment(request, ticket_id):
    """Add a comment to a support ticket."""
    org = _get_org(request)
    if not org:
        return redirect("accounts:profile")

    ticket = get_object_or_404(
        SupportTicket,
        id=ticket_id,
        organization=org,
    )

    message_text = request.POST.get("message", "").strip()
    if not message_text:
        messages.error(request, _("Yorum alani bos birakilamaz."))
        return redirect("accounts:support-detail", ticket_id=ticket.id)

    TicketComment.objects.create(
        ticket=ticket,
        author=request.user,
        message=message_text,
        is_internal=False,
    )

    # If ticket was resolved/closed, reopen it when owner adds a comment
    if ticket.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
        ticket.status = TicketStatus.OPEN
        ticket.resolved_at = None
        ticket.save(update_fields=["status", "resolved_at", "updated_at"])

    messages.success(request, _("Yorumunuz eklendi."))
    return redirect("accounts:support-detail", ticket_id=ticket.id)
