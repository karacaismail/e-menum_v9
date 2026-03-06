"""
Server-rendered views for the restaurant account portal.

Uses Django session authentication (not JWT).
All protected views use LoginRequiredMixin.
Templates extend layouts/accounts.html.

URL Namespace: 'accounts'
    /account/login/        → AccountLoginView
    /account/logout/       → AccountLogoutView
    /account/profile/      → ProfileView
    /account/settings/     → AccountSettingsView
    /account/subscription/ → SubscriptionView
    /account/invoices/     → InvoicesView
"""

import logging

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView

from apps.core.choices import AuditAction, SessionStatus
from apps.core.models import AuditLog, Session
from apps.core.views import get_client_ip

from .forms import LoginForm, PasswordChangeForm, ProfileForm, UsernameForm

logger = logging.getLogger(__name__)


# =============================================================================
# LOGIN
# =============================================================================

class AccountLoginView(FormView):
    """
    Restaurant portal login page.

    GET  /account/login/ → renders login form
    POST /account/login/ → authenticates, creates session, redirects

    Supports ?next= parameter for post-login redirect.
    Already-authenticated users are redirected to profile.
    """

    template_name = 'accounts/login.html'
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        user = form.get_user()

        # Create Django session
        login(
            self.request,
            user,
            backend='apps.core.backends.EmailOrUsernameBackend',
        )

        # Record login timestamp
        user.record_login()

        # Audit log
        AuditLog.log_action(
            action=AuditAction.LOGIN,
            resource='user',
            resource_id=str(user.id),
            user=user,
            organization=user.organization,
            description=f'User {user.email} logged in via portal',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500],
        )

        messages.success(self.request, _('Başarıyla giriş yaptınız.'))

        # Redirect to ?next= or default dashboard
        next_url = self.request.GET.get('next', '')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect('accounts:dashboard')

    def form_invalid(self, form):
        messages.error(self.request, _('Giriş bilgilerinizi kontrol ediniz.'))
        return super().form_invalid(form)


# =============================================================================
# LOGOUT
# =============================================================================

class AccountLogoutView(View):
    """
    Logout and redirect to login page.

    Supports both GET and POST for convenience (link click vs form submit).
    """

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            AuditLog.log_action(
                action=AuditAction.LOGOUT,
                resource='user',
                resource_id=str(request.user.id),
                user=request.user,
                organization=request.user.organization,
                description=f'User {request.user.email} logged out via portal',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )
        logout(request)
        messages.info(request, _('Başarıyla çıkış yaptınız.'))
        return redirect('accounts:login')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


# =============================================================================
# PROFILE (Personal Info)
# =============================================================================

class ProfileView(LoginRequiredMixin, FormView):
    """
    Profile editing page — personal information.

    GET  /account/profile/ → renders profile form with current data
    POST /account/profile/ → validates and updates profile fields
    """

    template_name = 'accounts/profile.html'
    form_class = ProfileForm
    login_url = '/account/login/'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()

        AuditLog.log_action(
            action=AuditAction.UPDATE,
            resource='user',
            resource_id=str(self.request.user.id),
            user=self.request.user,
            organization=self.request.user.organization,
            description=f'User {self.request.user.email} updated profile via portal',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500],
        )

        messages.success(self.request, _('Profiliniz güncellendi.'))
        return redirect('accounts:profile')

    def form_invalid(self, form):
        messages.error(self.request, _('Lütfen formdaki hataları düzeltiniz.'))
        return super().form_invalid(form)


# =============================================================================
# ACCOUNT SETTINGS (Username, Password, Sessions)
# =============================================================================

class AccountSettingsView(LoginRequiredMixin, View):
    """
    Account settings page — username, password change, active sessions.

    GET  /account/settings/ → renders settings with multiple form sections
    POST /account/settings/ → handles username or password change (via hidden 'action' field)
    """

    template_name = 'accounts/settings.html'
    login_url = '/account/login/'

    def get(self, request):
        context = self._build_context(request)
        return render(request, self.template_name, context)

    def post(self, request):
        action = request.POST.get('action', '')

        if action == 'change_password':
            return self._handle_password_change(request)
        elif action == 'change_username':
            return self._handle_username_change(request)
        else:
            return redirect('accounts:settings')

    def _build_context(self, request):
        """Build template context with forms and active sessions."""
        sessions = Session.objects.filter(
            user=request.user,
            status=SessionStatus.ACTIVE,
        ).order_by('-created_at')[:10]

        return {
            'username_form': UsernameForm(instance=request.user),
            'password_form': PasswordChangeForm(user=request.user),
            'sessions': sessions,
        }

    def _handle_password_change(self, request):
        """Process password change form submission."""
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Keep user logged in after password change
            update_session_auth_hash(request, request.user)

            AuditLog.log_action(
                action=AuditAction.PASSWORD_CHANGE,
                resource='user',
                resource_id=str(request.user.id),
                user=request.user,
                organization=request.user.organization,
                description=f'User {request.user.email} changed password via portal',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )

            messages.success(request, _('Şifreniz başarıyla değiştirildi.'))
            return redirect('accounts:settings')
        else:
            context = self._build_context(request)
            context['password_form'] = form
            messages.error(request, _('Şifre değiştirme başarısız.'))
            return render(request, self.template_name, context)

    def _handle_username_change(self, request):
        """Process username change form submission."""
        form = UsernameForm(data=request.POST, instance=request.user)
        if form.is_valid():
            form.save()

            AuditLog.log_action(
                action=AuditAction.UPDATE,
                resource='user',
                resource_id=str(request.user.id),
                user=request.user,
                organization=request.user.organization,
                description=f'User {request.user.email} updated username via portal',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )

            messages.success(request, _('Kullanıcı adınız güncellendi.'))
            return redirect('accounts:settings')
        else:
            context = self._build_context(request)
            context['username_form'] = form
            messages.error(request, _('Kullanıcı adı güncellenirken hata oluştu.'))
            return render(request, self.template_name, context)


# =============================================================================
# SUBSCRIPTION MANAGEMENT
# =============================================================================

class SubscriptionView(LoginRequiredMixin, View):
    """
    Subscription management page - shows current plan and usage.

    GET /account/subscription/ → Display current subscription, plan details
    """

    template_name = 'accounts/subscription.html'
    login_url = '/account/login/'

    def get(self, request):
        organization = request.user.organization

        # Get current subscription
        subscription = None
        plan = None
        try:
            from apps.subscriptions.models import Subscription
            subscription = Subscription.objects.filter(
                organization=organization,
                deleted_at__isnull=True,
            ).select_related('plan').order_by('-created_at').first()
            if subscription:
                plan = subscription.plan
        except Exception:
            pass

        # Get usage summary
        usage_items = []
        try:
            from apps.subscriptions.models import OrganizationUsage
            usage_items = OrganizationUsage.objects.filter(
                organization=organization,
            ).select_related('feature').order_by('feature__category', 'feature__sort_order')
        except Exception:
            pass

        # Load available plans for upgrade comparison
        available_plans = []
        try:
            from apps.subscriptions.models import Plan
            available_plans = list(
                Plan.objects.filter(
                    is_active=True,
                    is_public=True,
                    deleted_at__isnull=True,
                ).order_by('sort_order', 'price_monthly')
            )
        except Exception:
            pass

        # Determine current plan tier order for upgrade logic
        tier_order = ['FREE', 'STARTER', 'GROWTH', 'PROFESSIONAL', 'ENTERPRISE']
        current_tier_index = -1
        if plan:
            try:
                current_tier_index = tier_order.index(plan.tier)
            except ValueError:
                current_tier_index = -1

        context = {
            'subscription': subscription,
            'plan': plan,
            'usage_items': usage_items,
            'available_plans': available_plans,
            'current_tier_index': current_tier_index,
            'tier_order': tier_order,
        }
        return render(request, self.template_name, context)


# =============================================================================
# INVOICE HISTORY
# =============================================================================

class InvoicesView(LoginRequiredMixin, View):
    """
    Invoice history page - shows billing records.

    GET /account/invoices/ → Display invoice list
    """

    template_name = 'accounts/invoices.html'
    login_url = '/account/login/'

    def get(self, request):
        organization = request.user.organization

        invoices = []
        try:
            from apps.subscriptions.models import Invoice
            invoices = Invoice.objects.filter(
                organization=organization,
                deleted_at__isnull=True,
            ).order_by('-created_at')[:50]
        except Exception:
            pass

        context = {
            'invoices': invoices,
        }
        return render(request, self.template_name, context)


# =============================================================================
# SELF-SERVICE REGISTRATION
# =============================================================================

class RegisterView(FormView):
    """
    Self-service registration for restaurant owners.

    Creates User + Organization + Subscription(TRIALING) atomically.
    Auto-logs in the user and redirects to dashboard.
    """

    template_name = 'accounts/register.html'
    form_class = None  # Will import RegistrationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        from .forms import RegistrationForm
        return RegistrationForm

    def form_valid(self, form):
        from django.db import transaction
        from django.utils.text import slugify
        from datetime import timedelta
        from apps.core.models import Organization, User
        from apps.core.choices import UserStatus

        data = form.cleaned_data

        with transaction.atomic():
            # Create organization
            base_slug = slugify(data['business_name'])[:80] or 'restaurant'
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1

            org = Organization.objects.create(
                name=data['business_name'],
                slug=slug,
                email=data['email'],
                phone=data.get('phone', ''),
                settings={'currency': 'TRY', 'language': 'tr'},
            )

            # Set trial period
            org.trial_ends_at = timezone.now() + timedelta(days=14)
            org.save(update_fields=['trial_ends_at'])

            # Create user
            user = User.objects.create_user(
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone=data.get('phone', ''),
                status=UserStatus.ACTIVE,
                organization=org,
            )

            # Create trial subscription
            try:
                from apps.subscriptions.models import Subscription, Plan
                from apps.subscriptions.choices import SubscriptionStatus

                # Get default/free plan
                plan = Plan.objects.filter(
                    is_active=True, is_default=True, deleted_at__isnull=True
                ).first()
                if not plan:
                    plan = Plan.objects.filter(
                        is_active=True, deleted_at__isnull=True
                    ).order_by('price_monthly').first()

                if plan:
                    sub = Subscription.objects.create(
                        organization=org,
                        plan=plan,
                        status=SubscriptionStatus.TRIALING if hasattr(SubscriptionStatus, 'TRIALING') else 'TRIALING',
                        trial_ends_at=org.trial_ends_at,
                        current_period_start=timezone.now(),
                        current_period_end=org.trial_ends_at,
                    )
                    org.subscription = sub
                    org.save(update_fields=['subscription'])
            except Exception as e:
                logger.warning(f'Could not create trial subscription: {e}')

            # Assign owner role
            try:
                from apps.core.models import Role, UserRole
                from apps.core.choices import RoleScope
                owner_role = Role.objects.filter(
                    name='owner', scope=RoleScope.ORGANIZATION
                ).first()
                if owner_role:
                    UserRole.objects.create(
                        user=user,
                        role=owner_role,
                        organization=org,
                        granted_by=user,
                    )
            except Exception as e:
                logger.warning(f'Could not assign owner role: {e}')

            # Audit log
            AuditLog.log_action(
                action=AuditAction.CREATE,
                resource='registration',
                resource_id=str(user.id),
                user=user,
                organization=org,
                description=f'New registration: {user.email} / {org.name}',
                ip_address=get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500],
            )

        # Auto-login
        login(
            self.request,
            user,
            backend='apps.core.backends.EmailOrUsernameBackend',
        )

        messages.success(self.request, _('Hesabınız oluşturuldu! 14 günlük deneme süreniz başladı.'))
        return redirect('accounts:dashboard')

    def form_invalid(self, form):
        messages.error(self.request, _('Lütfen formdaki hataları düzeltiniz.'))
        return super().form_invalid(form)
