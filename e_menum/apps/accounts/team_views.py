"""Team management views for the restaurant owner portal."""

import logging
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.core.choices import AuditAction, RoleScope, UserStatus
from apps.core.models import AuditLog, Role, User, UserRole
from apps.core.views import get_client_ip

logger = logging.getLogger(__name__)


def _get_org(request):
    return getattr(request.user, "organization", None)


@login_required(login_url="/account/login/")
def team_list(request):
    """List all team members in the organization."""
    org = _get_org(request)
    if not org:
        return redirect("accounts:profile")

    members = list(
        User.objects.filter(
            organization=org,
            deleted_at__isnull=True,
        ).order_by("-created_at")
    )

    # Build a role map: user_id -> list of Role objects
    user_roles = UserRole.objects.filter(
        organization=org,
    ).select_related("role", "user")

    role_map = {}
    for ur in user_roles:
        if ur.user_id not in role_map:
            role_map[ur.user_id] = []
        role_map[ur.user_id].append(ur.role)

    # Attach roles directly to each member for easy template access
    for member in members:
        member.assigned_roles = role_map.get(member.id, [])

    # Available org roles for invitation
    available_roles = Role.objects.filter(
        scope=RoleScope.ORGANIZATION,
    ).order_by("name")

    return render(
        request,
        "accounts/team/list.html",
        {
            "members": members,
            "available_roles": available_roles,
        },
    )


@login_required(login_url="/account/login/")
@require_POST
def team_invite(request):
    """Invite a new team member."""
    org = _get_org(request)
    if not org:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    email = request.POST.get("email", "").strip().lower()
    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    role_id = (request.POST.get("role_id") or request.POST.get("role") or "").strip()

    if not email or not first_name or not last_name:
        return JsonResponse({"error": "E-posta, ad ve soyad zorunludur."}, status=400)

    # Check if user already exists in org
    if User.objects.filter(
        email=email, organization=org, deleted_at__isnull=True
    ).exists():
        messages.error(request, _("Bu e-posta adresi zaten ekipte."))
        return redirect("accounts:team-list")

    # Create invited user
    temp_password = str(uuid.uuid4())[:16]
    user = User.objects.create_user(
        email=email,
        password=temp_password,
        first_name=first_name,
        last_name=last_name,
        status=UserStatus.INVITED,
        organization=org,
    )

    # Assign role if provided
    if role_id:
        try:
            role = Role.objects.get(id=role_id, scope=RoleScope.ORGANIZATION)
            UserRole.objects.create(
                user=user,
                role=role,
                organization=org,
                granted_by=request.user,
            )
        except Role.DoesNotExist:
            pass

    # Audit log
    AuditLog.log_action(
        action=AuditAction.INVITE_SENT,
        resource="user",
        resource_id=str(user.id),
        user=request.user,
        organization=org,
        description=f"{request.user.email} invited {email} to {org.name}",
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
    )

    messages.success(request, _("Davet gonderildi: %(email)s") % {"email": email})
    return redirect("accounts:team-list")


@login_required(login_url="/account/login/")
@require_POST
def team_assign_role(request, user_id):
    """Assign a role to a team member."""
    org = _get_org(request)
    if not org:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    member = get_object_or_404(
        User, id=user_id, organization=org, deleted_at__isnull=True
    )
    role_id = (request.POST.get("role_id") or request.POST.get("role") or "").strip()

    if not role_id:
        return JsonResponse({"error": "role or role_id required"}, status=400)

    role = get_object_or_404(Role, id=role_id, scope=RoleScope.ORGANIZATION)

    # Remove existing roles first
    UserRole.objects.filter(user=member, organization=org).delete()

    # Assign new role
    UserRole.objects.create(
        user=member,
        role=role,
        organization=org,
        granted_by=request.user,
    )

    AuditLog.log_action(
        action=AuditAction.ROLE_ASSIGN,
        resource="user_role",
        resource_id=str(member.id),
        user=request.user,
        organization=org,
        description=f"{request.user.email} assigned role {role.name} to {member.email}",
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
    )

    messages.success(request, _("Rol atandi."))
    return redirect("accounts:team-list")


@login_required(login_url="/account/login/")
@require_POST
def team_remove(request, user_id):
    """Remove a team member (soft delete from org)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    member = get_object_or_404(
        User, id=user_id, organization=org, deleted_at__isnull=True
    )

    # Cannot remove self
    if member.id == request.user.id:
        messages.error(request, _("Kendinizi ekipten cikaramazsiniz."))
        return redirect("accounts:team-list")

    # Soft delete user roles
    UserRole.objects.filter(user=member, organization=org).delete()

    # Soft delete user
    member.soft_delete()

    AuditLog.log_action(
        action=AuditAction.ROLE_REMOVE,
        resource="user",
        resource_id=str(member.id),
        user=request.user,
        organization=org,
        description=f"{request.user.email} removed {member.email} from {org.name}",
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
    )

    messages.success(request, _("Ekip uyesi cikarildi."))
    return redirect("accounts:team-list")
