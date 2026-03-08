"""
Admin registration for Website marketing models.

Provides read/manage interface for:
- Contact form submissions
- Demo requests (with status workflow)
- Newsletter subscribers

CMS Content Management:
- SiteSettings (singleton)
- PageHero, HomeSection
- FeatureCategory + FeatureBullet (inline)
- Testimonial, TrustBadge, TrustLocation
- FAQ, TeamMember, CompanyValue, CompanyStat
- LegalPage, BlogPost
- PlanDisplayFeature (inline on Plan)
- NavigationLink
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline

from shared.permissions.admin_permission_mixin import EMenumPermissionMixin

from .models import (
    BlogPost,
    BrandAsset,
    CareerPosition,
    CaseStudy,
    CompanyStat,
    CompanyValue,
    ContactSubmission,
    DemoRequest,
    FAQ,
    FeatureBullet,
    FeatureCategory,
    FreeTool,
    HelpArticle,
    HelpCategory,
    HomeSection,
    IndustryReport,
    InvestorFinancial,
    InvestorPage,
    InvestorPresentation,
    LegalPage,
    Milestone,
    NavigationLink,
    NewsletterSubscriber,
    PageHero,
    PartnerBenefit,
    PartnerProgram,
    PartnerTier,
    PlanDisplayFeature,
    PressRelease,
    ResourceCategory,
    ROICalculatorConfig,
    Sector,
    SiteSettings,
    SolutionPage,
    TeamMember,
    Testimonial,
    TrustBadge,
    TrustLocation,
    Webinar,
)


# #############################################################################
#   FORM SUBMISSION ADMINS (existing)
# #############################################################################


# =============================================================================
# CONTACT SUBMISSION ADMIN
# =============================================================================


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject_badge", "is_read_icon", "created_at"]
    list_filter = ["subject", "is_read", "created_at"]
    search_fields = ["name", "email", "message"]
    readonly_fields = ["id", "created_at", "updated_at"]
    list_per_page = 25
    date_hierarchy = "created_at"

    actions = ["mark_as_read", "mark_as_unread"]

    def subject_badge(self, obj):
        colors = {
            "general": "#6B7280",
            "sales": "#10B981",
            "support": "#F59E0B",
            "partnership": "#8B5CF6",
            "press": "#3B82F6",
            "other": "#6B7280",
        }
        color = colors.get(obj.subject, "#6B7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_subject_display(),
        )

    subject_badge.short_description = _("Konu")

    def is_read_icon(self, obj):
        if obj.is_read:
            return format_html('<span style="color:#10B981;">&#10003;</span>')
        return format_html('<span style="color:#EF4444;">&#9679;</span>')

    is_read_icon.short_description = _("Okundu")

    @admin.action(description=_("Secilenleri okundu isaretle"))
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description=_("Secilenleri okunmadi isaretle"))
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)


# =============================================================================
# DEMO REQUEST ADMIN
# =============================================================================


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = [
        "business_name",
        "name",
        "business_type",
        "branch_count",
        "status_badge",
        "created_at",
    ]
    list_filter = ["status", "business_type", "created_at"]
    search_fields = ["name", "business_name", "email", "phone"]
    readonly_fields = ["id", "created_at", "updated_at"]
    list_per_page = 25
    date_hierarchy = "created_at"
    list_editable = []

    fieldsets = (
        (
            _("Iletisim Bilgileri"),
            {
                "fields": ("name", "email", "phone"),
            },
        ),
        (
            _("Isletme Bilgileri"),
            {
                "fields": ("business_name", "business_type", "branch_count", "message"),
            },
        ),
        (
            _("Durum Takibi"),
            {
                "fields": ("status", "notes"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["set_contacted", "set_demo_done", "set_converted"]

    def status_badge(self, obj):
        colors = {
            "pending": "#F59E0B",
            "contacted": "#3B82F6",
            "demo_done": "#8B5CF6",
            "converted": "#10B981",
            "rejected": "#EF4444",
        }
        color = colors.get(obj.status, "#6B7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Durum")

    @admin.action(description=_("Iletisime gecildi olarak isaretle"))
    def set_contacted(self, request, queryset):
        queryset.update(status="contacted")

    @admin.action(description=_("Demo yapildi olarak isaretle"))
    def set_demo_done(self, request, queryset):
        queryset.update(status="demo_done")

    @admin.action(description=_("Musteri oldu olarak isaretle"))
    def set_converted(self, request, queryset):
        queryset.update(status="converted")


# =============================================================================
# NEWSLETTER SUBSCRIBER ADMIN
# =============================================================================


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "language", "is_active", "created_at"]
    list_filter = ["is_active", "language", "created_at"]
    search_fields = ["email"]
    readonly_fields = ["id", "created_at", "updated_at"]
    list_per_page = 50


# #############################################################################
#   CMS CONTENT ADMINS
# #############################################################################


# =============================================================================
# SITE SETTINGS ADMIN (Singleton)
# =============================================================================


@admin.register(SiteSettings)
class SiteSettingsAdmin(TabbedTranslationAdmin):
    list_display = ["company_name", "email", "phone"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Marka & Logo"),
            {
                "fields": ("logo_url", "logo_icon_url", "logo_dark_url", "favicon_url"),
                "description": _(
                    "Logo URL'lerini girin. PNG/SVG formatinda, tercihen seffaf arkaplanli."
                ),
            },
        ),
        (
            _("Sirket Bilgileri"),
            {
                "fields": ("company_name", "tagline", "description"),
            },
        ),
        (
            _("Iletisim"),
            {
                "fields": ("phone", "email", "address"),
            },
        ),
        (
            _("Sosyal Medya"),
            {
                "fields": (
                    "social_instagram",
                    "social_twitter",
                    "social_linkedin",
                    "social_youtube",
                ),
            },
        ),
        (
            _("WhatsApp"),
            {
                "fields": ("whatsapp_number", "whatsapp_message"),
            },
        ),
        (
            _("CTA Varsayilanlari"),
            {
                "fields": (
                    "cta_primary_text",
                    "cta_primary_url",
                    "cta_secondary_text",
                    "cta_secondary_url",
                    "cta_trust_text",
                ),
            },
        ),
        (
            _("Duyuru Bandi"),
            {
                "fields": (
                    "announcement_is_active",
                    "announcement_text",
                    "announcement_url",
                ),
            },
        ),
        (
            _("Cerez Banneri"),
            {
                "fields": ("cookie_banner_title", "cookie_banner_text"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Yasal Bilgiler"),
            {
                "fields": ("vat_no", "mersis_no", "trade_registry"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Fiyatlandirma Promosyon"),
            {
                "fields": ("pricing_yearly_badge", "pricing_yearly_note"),
                "description": _(
                    "Fiyatlandirma sayfasindaki yillik toggle rozeti ve aciklama metni."
                ),
            },
        ),
        (
            _("Diger"),
            {
                "fields": ("login_url", "status_page_url"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        # Only allow adding if no SiteSettings exists
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# =============================================================================
# PAGE HERO ADMIN
# =============================================================================


@admin.register(PageHero)
class PageHeroAdmin(TabbedTranslationAdmin):
    list_display = ["page_badge", "title_short", "is_active"]
    list_filter = ["page", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Sayfa & Icerik"),
            {
                "fields": ("page", "title", "subtitle", "badge_text", "gradient_class"),
            },
        ),
        (
            _("CTA Ozellestirme"),
            {
                "description": _(
                    "Bos birakilirsa Site Ayarlari'ndaki varsayilanlar kullanilir."
                ),
                "fields": (
                    "cta_primary_text",
                    "cta_primary_url",
                    "cta_secondary_text",
                    "cta_secondary_url",
                    "trust_text",
                ),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("show_hero_image", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def page_badge(self, obj):
        colors = {
            "home": "#10B981",
            "features": "#3B82F6",
            "pricing": "#8B5CF6",
            "about": "#F59E0B",
            "contact": "#EC4899",
            "demo": "#EF4444",
            "blog": "#6366F1",
        }
        color = colors.get(obj.page, "#6B7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_page_display(),
        )

    page_badge.short_description = _("Sayfa")

    def title_short(self, obj):
        return obj.title[:60] + ("..." if len(obj.title) > 60 else "")

    title_short.short_description = _("Baslik")


# =============================================================================
# HOME SECTION ADMIN
# =============================================================================


@admin.register(HomeSection)
class HomeSectionAdmin(TabbedTranslationAdmin):
    list_display = [
        "title_short",
        "section_type_badge",
        "card_variant",
        "sort_order",
        "is_active",
    ]
    list_filter = ["section_type", "is_active"]
    list_editable = ["sort_order", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]
    list_per_page = 30

    fieldsets = (
        (
            _("Icerik"),
            {
                "fields": ("section_type", "title", "description", "icon", "color"),
            },
        ),
        (
            _("Istatistik Sayac"),
            {
                "fields": ("stat_value", "stat_suffix"),
                "classes": ("collapse",),
                "description": _('Sadece "Istatistik Sayac" tipi icin'),
            },
        ),
        (
            _("Nasil Calisir"),
            {
                "fields": ("step_number",),
                "classes": ("collapse",),
                "description": _('Sadece "Nasil Calisir" tipi icin'),
            },
        ),
        (
            _("Problem / Cozum"),
            {
                "fields": ("card_variant",),
                "classes": ("collapse",),
                "description": _('Sadece "Problem / Cozum" tipi icin'),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def section_type_badge(self, obj):
        colors = {
            "problem_solution": "#EF4444",
            "feature_card": "#3B82F6",
            "how_it_works": "#10B981",
            "stat_counter": "#F59E0B",
        }
        color = colors.get(obj.section_type, "#6B7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_section_type_display(),
        )

    section_type_badge.short_description = _("Tip")

    def title_short(self, obj):
        return obj.title[:50] + ("..." if len(obj.title) > 50 else "")

    title_short.short_description = _("Baslik")


# =============================================================================
# FEATURE CATEGORY + BULLET ADMIN
# =============================================================================


class FeatureBulletInline(TranslationTabularInline):
    model = FeatureBullet
    extra = 1
    ordering = ["sort_order"]


@admin.register(FeatureCategory)
class FeatureCategoryAdmin(TabbedTranslationAdmin):
    list_display = ["title", "badge_text", "bullet_count", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [FeatureBulletInline]

    fieldsets = (
        (
            _("Icerik"),
            {
                "fields": ("title", "description", "icon"),
            },
        ),
        (
            _("Badge"),
            {
                "fields": ("badge_text", "badge_color"),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("image_alt", "layout_reversed", "sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def bullet_count(self, obj):
        count = obj.bullets.filter(is_active=True).count()
        return format_html(
            '<span style="background:#3B82F6;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            count,
        )

    bullet_count.short_description = _("Madde Sayisi")


# =============================================================================
# TESTIMONIAL ADMIN
# =============================================================================


@admin.register(Testimonial)
class TestimonialAdmin(TabbedTranslationAdmin):
    list_display = [
        "author_name",
        "author_role_or_business",
        "rating_stars",
        "sort_order",
        "is_active",
    ]
    list_filter = ["rating", "is_active"]
    list_editable = ["sort_order", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Yazar"),
            {
                "fields": (
                    "author_name",
                    "initials",
                    "author_role_or_business",
                    "author_location",
                ),
            },
        ),
        (
            _("Isletme"),
            {
                "fields": ("business_type_label", "badge_color", "avatar_color"),
            },
        ),
        (
            _("Yorum"),
            {
                "fields": ("quote", "rating"),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def rating_stars(self, obj):
        stars = "\u2605" * obj.rating + "\u2606" * (5 - obj.rating)
        return format_html(
            '<span style="color:#F59E0B;font-size:14px;">{}</span>', stars
        )

    rating_stars.short_description = _("Puan")


# =============================================================================
# TRUST BADGE ADMIN
# =============================================================================


@admin.register(TrustBadge)
class TrustBadgeAdmin(TabbedTranslationAdmin):
    list_display = ["label", "icon", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]


# =============================================================================
# TRUST LOCATION ADMIN
# =============================================================================


@admin.register(TrustLocation)
class TrustLocationAdmin(TabbedTranslationAdmin):
    list_display = ["text", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]


# =============================================================================
# FAQ ADMIN
# =============================================================================


@admin.register(FAQ)
class FAQAdmin(TabbedTranslationAdmin):
    list_display = ["question_short", "page_badge", "sort_order", "is_active"]
    list_filter = ["page", "is_active"]
    list_editable = ["sort_order", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def question_short(self, obj):
        return obj.question[:60] + ("..." if len(obj.question) > 60 else "")

    question_short.short_description = _("Soru")

    def page_badge(self, obj):
        colors = {
            "pricing": "#8B5CF6",
            "contact": "#EC4899",
            "both": "#10B981",
        }
        color = colors.get(obj.page, "#6B7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_page_display(),
        )

    page_badge.short_description = _("Sayfa")


# =============================================================================
# TEAM MEMBER ADMIN
# =============================================================================


@admin.register(TeamMember)
class TeamMemberAdmin(TabbedTranslationAdmin):
    list_display = ["name", "title", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]


# =============================================================================
# COMPANY VALUE ADMIN
# =============================================================================


@admin.register(CompanyValue)
class CompanyValueAdmin(TabbedTranslationAdmin):
    list_display = ["title", "icon", "color", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]


# =============================================================================
# COMPANY STAT ADMIN
# =============================================================================


@admin.register(CompanyStat)
class CompanyStatAdmin(TabbedTranslationAdmin):
    list_display = ["value", "label", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]


# =============================================================================
# LEGAL PAGE ADMIN
# =============================================================================


@admin.register(LegalPage)
class LegalPageAdmin(TabbedTranslationAdmin):
    list_display = ["slug_badge", "title", "last_updated_display", "is_active"]
    list_filter = ["slug", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Sayfa"),
            {
                "fields": ("slug", "title", "meta_description", "last_updated_display"),
            },
        ),
        (
            _("Icerik"),
            {
                "fields": ("content",),
                "description": _(
                    "HTML icerik desteklenir. Basliklar icin <h3>, paragraflar icin <p>, listeler icin <ul><li> kullanin."
                ),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("is_active",),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def slug_badge(self, obj):
        colors = {
            "privacy": "#3B82F6",
            "terms": "#10B981",
            "kvkk": "#8B5CF6",
        }
        color = colors.get(obj.slug, "#6B7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_slug_display(),
        )

    slug_badge.short_description = _("Sayfa")


# =============================================================================
# BLOG POST ADMIN
# =============================================================================


@admin.register(BlogPost)
class BlogPostAdmin(TabbedTranslationAdmin):
    list_display = [
        "title_short",
        "category",
        "status_badge",
        "is_featured",
        "published_at",
    ]
    list_filter = ["status", "category", "is_featured"]
    search_fields = ["title", "excerpt", "content"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"
    list_per_page = 25

    actions = ["publish_posts", "archive_posts"]

    fieldsets = (
        (
            _("Icerik"),
            {
                "fields": ("title", "slug", "excerpt", "content"),
            },
        ),
        (
            _("Meta"),
            {
                "fields": (
                    "category",
                    "author_name",
                    "meta_description",
                    "is_featured",
                ),
            },
        ),
        (
            _("Yayin"),
            {
                "fields": ("status", "published_at"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def title_short(self, obj):
        return obj.title[:60] + ("..." if len(obj.title) > 60 else "")

    title_short.short_description = _("Baslik")

    def status_badge(self, obj):
        colors = {
            "draft": "#F59E0B",
            "published": "#10B981",
            "archived": "#6B7280",
        }
        color = colors.get(obj.status, "#6B7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Durum")

    @admin.action(description=_("Secilenleri yayinla"))
    def publish_posts(self, request, queryset):
        queryset.update(status="published", published_at=timezone.now())

    @admin.action(description=_("Secilenleri arsivle"))
    def archive_posts(self, request, queryset):
        queryset.update(status="archived")


# =============================================================================
# PLAN DISPLAY FEATURE ADMIN (Inline — used in subscriptions.PlanAdmin)
# =============================================================================


class PlanDisplayFeatureInline(TranslationTabularInline):
    """Inline for PlanDisplayFeature on subscriptions.PlanAdmin."""

    model = PlanDisplayFeature
    extra = 1
    ordering = ["sort_order"]


@admin.register(PlanDisplayFeature)
class PlanDisplayFeatureAdmin(TabbedTranslationAdmin):
    list_display = [
        "plan_name",
        "text_short",
        "has_icon",
        "is_highlighted",
        "sort_order",
        "is_active",
    ]
    list_filter = ["plan", "is_highlighted", "is_active"]
    list_editable = ["sort_order", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Icerik"),
            {
                "fields": ("plan", "text", "icon_svg"),
                "description": _(
                    "icon_svg alani: SVG markup yapistirin (orn. <svg ...>...</svg>). "
                    "Bos birakirsaniz varsayilan onay ikonu kullanilir."
                ),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("is_highlighted", "sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def plan_name(self, obj):
        return obj.plan.name

    plan_name.short_description = _("Plan")

    def text_short(self, obj):
        return obj.text[:50] + ("..." if len(obj.text) > 50 else "")

    text_short.short_description = _("Metin")

    def has_icon(self, obj):
        if obj.icon_svg:
            return format_html(
                '<span style="color:#22c55e;font-weight:700;">✓ SVG</span>'
            )
        return format_html('<span style="color:#6b7280;">—</span>')

    has_icon.short_description = _("Ikon")


# =============================================================================
# NAVIGATION LINK ADMIN
# =============================================================================


@admin.register(NavigationLink)
class NavigationLinkAdmin(TabbedTranslationAdmin):
    list_display = [
        "label",
        "location_badge",
        "url",
        "parent_label",
        "sort_order",
        "is_active",
    ]
    list_filter = ["location", "is_active"]
    list_editable = ["sort_order", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Link"),
            {
                "fields": ("location", "label", "url", "icon", "description"),
            },
        ),
        (
            _("Hiyerarsi"),
            {
                "fields": ("parent",),
                "description": _("Header dropdown'lar icin ust linki secin."),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def location_badge(self, obj):
        colors = {
            "header": "#10B981",
            "footer_product": "#3B82F6",
            "footer_solutions": "#8B5CF6",
            "footer_company": "#F59E0B",
            "footer_support": "#EC4899",
            "footer_legal": "#6B7280",
        }
        color = colors.get(obj.location, "#6B7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_location_display(),
        )

    location_badge.short_description = _("Konum")

    def parent_label(self, obj):
        if obj.parent:
            return obj.parent.label
        return "—"

    parent_label.short_description = _("Ust Link")


# #############################################################################
#   STOREFRONT CONTENT ADMINS
# #############################################################################


# =============================================================================
# SECTOR ADMIN
# =============================================================================


@admin.register(Sector)
class SectorAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = ["name", "slug", "icon", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "slug", "description", "icon", "color"),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


# =============================================================================
# SOLUTION PAGE ADMIN
# =============================================================================


@admin.register(SolutionPage)
class SolutionPageAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = [
        "title",
        "slug",
        "solution_type_badge",
        "sector",
        "is_featured",
        "sort_order",
        "is_active",
    ]
    list_filter = ["solution_type", "sector", "is_featured", "is_active"]
    search_fields = ["title", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ["sort_order", "is_active", "is_featured"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "subtitle",
                    "content",
                    "hero_image",
                    "hero_gradient_class",
                    "sector",
                    "solution_type",
                    "key_benefits",
                    "pain_points",
                    "target_audience",
                    "is_featured",
                    "sort_order",
                    "is_active",
                ),
            },
        ),
        (
            _("SEO"),
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                    "meta_keywords",
                    "og_title",
                    "og_description",
                    "og_image",
                    "og_type",
                    "canonical_url",
                    "robots_index",
                    "robots_follow",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def solution_type_badge(self, obj):
        colors = {
            "sector": ("#0ea5e9", "14,165,233", "ph-buildings"),
            "size": ("#a855f7", "168,85,247", "ph-chart-bar"),
            "use_case": ("#f59e0b", "245,158,11", "ph-lightbulb"),
        }
        hex_color, rgb, icon = colors.get(
            obj.solution_type, ("#6B7280", "107,114,128", "ph-question")
        )
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;'
            "border-radius:6px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">'
            '<i class="ph {}"></i> {}</span>',
            rgb,
            hex_color,
            icon,
            obj.get_solution_type_display(),
        )

    solution_type_badge.short_description = _("Cozum Tipi")


# =============================================================================
# CASE STUDY ADMIN
# =============================================================================


@admin.register(CaseStudy)
class CaseStudyAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = ["title", "company_name", "sector", "is_featured_icon", "is_active"]
    list_filter = ["sector", "is_featured", "is_active"]
    search_fields = ["title", "company_name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (
            _("Sirket Bilgileri"),
            {
                "fields": (
                    "company_name",
                    "company_logo",
                    "sector",
                    "company_size",
                    "location",
                ),
            },
        ),
        (
            _("Icerik"),
            {
                "fields": (
                    "title",
                    "slug",
                    "excerpt",
                    "challenge",
                    "solution",
                    "results",
                    "hero_image",
                ),
            },
        ),
        (
            _("Istatistikler"),
            {
                "fields": (
                    "stat_1_value",
                    "stat_1_label",
                    "stat_2_value",
                    "stat_2_label",
                    "stat_3_value",
                    "stat_3_label",
                ),
            },
        ),
        (
            _("Musteri Yorumu"),
            {
                "fields": ("quote", "quote_author", "quote_author_title"),
            },
        ),
        (
            _("Ayarlar"),
            {
                "fields": ("is_featured", "published_at", "sort_order", "is_active"),
            },
        ),
        (
            _("SEO"),
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                    "meta_keywords",
                    "og_title",
                    "og_description",
                    "og_image",
                    "og_type",
                    "canonical_url",
                    "robots_index",
                    "robots_follow",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def is_featured_icon(self, obj):
        if obj.is_featured:
            return format_html(
                '<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;'
                "border-radius:6px;font-size:11px;font-weight:600;"
                'background:rgba(34,197,94,0.12);color:#22c55e;">'
                '<i class="ph ph-star"></i> Evet</span>'
            )
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;'
            "border-radius:6px;font-size:11px;font-weight:600;"
            'background:rgba(107,114,128,0.12);color:#6B7280;">'
            "—</span>"
        )

    is_featured_icon.short_description = _("One Cikan")


# =============================================================================
# ROI CALCULATOR CONFIG ADMIN (Singleton)
# =============================================================================


@admin.register(ROICalculatorConfig)
class ROICalculatorConfigAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = [
        "title",
        "avg_order_increase_pct",
        "avg_cost_reduction_pct",
        "is_active",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            None,
            {
                "fields": ("title", "description"),
            },
        ),
        (
            _("Hesaplama Parametreleri"),
            {
                "fields": (
                    "avg_order_increase_pct",
                    "avg_cost_reduction_pct",
                    "avg_time_saved_hours",
                    "avg_menu_print_cost",
                ),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("is_active",),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return not ROICalculatorConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# =============================================================================
# RESOURCE CATEGORY ADMIN
# =============================================================================


@admin.register(ResourceCategory)
class ResourceCategoryAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = ["name", "slug", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "slug"),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


# =============================================================================
# INDUSTRY REPORT ADMIN
# =============================================================================


@admin.register(IndustryReport)
class IndustryReportAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = [
        "title",
        "category",
        "download_count_badge",
        "requires_email",
        "is_active",
    ]
    list_filter = ["category", "requires_email", "is_active"]
    search_fields = ["title", "slug"]
    readonly_fields = ["id", "created_at", "updated_at", "download_count"]
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (
            _("Icerik"),
            {
                "fields": ("title", "slug", "excerpt", "content", "category"),
            },
        ),
        (
            _("Dosyalar"),
            {
                "fields": ("cover_image", "file"),
            },
        ),
        (
            _("Ayarlar"),
            {
                "fields": (
                    "requires_email",
                    "download_count",
                    "published_at",
                    "is_active",
                ),
            },
        ),
        (
            _("SEO"),
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                    "meta_keywords",
                    "og_title",
                    "og_description",
                    "og_image",
                    "og_type",
                    "canonical_url",
                    "robots_index",
                    "robots_follow",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def download_count_badge(self, obj):
        count = obj.download_count
        if count >= 100:
            hex_color, rgb = "#22c55e", "34,197,94"
        elif count >= 10:
            hex_color, rgb = "#f59e0b", "245,158,11"
        else:
            hex_color, rgb = "#0ea5e9", "14,165,233"
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;'
            "border-radius:6px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-download-simple"></i> {}</span>',
            rgb,
            hex_color,
            count,
        )

    download_count_badge.short_description = _("Indirmeler")


# =============================================================================
# FREE TOOL ADMIN
# =============================================================================


@admin.register(FreeTool)
class FreeToolAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = ["title", "tool_type_badge", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    search_fields = ["title", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (
            _("Icerik"),
            {
                "fields": (
                    "title",
                    "slug",
                    "description",
                    "icon",
                    "tool_type",
                    "template_name",
                ),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("SEO"),
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                    "meta_keywords",
                    "og_title",
                    "og_description",
                    "og_image",
                    "og_type",
                    "canonical_url",
                    "robots_index",
                    "robots_follow",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def tool_type_badge(self, obj):
        colors = {
            "menu_cost": ("#0ea5e9", "14,165,233", "ph-calculator"),
            "qr_preview": ("#a855f7", "168,85,247", "ph-qr-code"),
            "roi_calc": ("#22c55e", "34,197,94", "ph-chart-line-up"),
            "qr_designer": ("#f59e0b", "245,158,11", "ph-paint-brush"),
        }
        hex_color, rgb, icon = colors.get(
            obj.tool_type, ("#6B7280", "107,114,128", "ph-wrench")
        )
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;'
            "border-radius:6px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">'
            '<i class="ph {}"></i> {}</span>',
            rgb,
            hex_color,
            icon,
            obj.get_tool_type_display(),
        )

    tool_type_badge.short_description = _("Arac Tipi")


# =============================================================================
# WEBINAR ADMIN
# =============================================================================


@admin.register(Webinar)
class WebinarAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = ["title", "speaker_name", "status_badge", "event_date", "is_active"]
    list_filter = ["status", "is_active"]
    search_fields = ["title", "speaker_name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (
            _("Icerik"),
            {
                "fields": ("title", "slug", "description"),
            },
        ),
        (
            _("Konusmaci"),
            {
                "fields": ("speaker_name", "speaker_title", "speaker_avatar"),
            },
        ),
        (
            _("Etkinlik"),
            {
                "fields": (
                    "event_date",
                    "duration_minutes",
                    "status",
                    "video_url",
                    "registration_url",
                    "cover_image",
                ),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("SEO"),
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                    "meta_keywords",
                    "og_title",
                    "og_description",
                    "og_image",
                    "og_type",
                    "canonical_url",
                    "robots_index",
                    "robots_follow",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def status_badge(self, obj):
        colors = {
            "upcoming": ("#0ea5e9", "14,165,233", "ph-calendar"),
            "live": ("#22c55e", "34,197,94", "ph-broadcast"),
            "recorded": ("#f59e0b", "245,158,11", "ph-video-camera"),
            "cancelled": ("#ef4444", "239,68,68", "ph-x-circle"),
        }
        hex_color, rgb, icon = colors.get(
            obj.status, ("#6B7280", "107,114,128", "ph-question")
        )
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;'
            "border-radius:6px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">'
            '<i class="ph {}"></i> {}</span>',
            rgb,
            hex_color,
            icon,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Durum")


# =============================================================================
# CAREER POSITION ADMIN
# =============================================================================


@admin.register(CareerPosition)
class CareerPositionAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = [
        "title",
        "department",
        "location",
        "employment_type_badge",
        "is_active",
    ]
    list_filter = ["department", "employment_type", "is_active"]
    search_fields = ["title", "department"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (
            _("Pozisyon"),
            {
                "fields": (
                    "title",
                    "slug",
                    "department",
                    "location",
                    "employment_type",
                ),
            },
        ),
        (
            _("Icerik"),
            {
                "fields": ("description", "requirements", "benefits"),
            },
        ),
        (
            _("Ayarlar"),
            {
                "fields": (
                    "apply_url",
                    "is_featured",
                    "published_at",
                    "expires_at",
                    "sort_order",
                    "is_active",
                ),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def employment_type_badge(self, obj):
        colors = {
            "full_time": ("#22c55e", "34,197,94", "ph-briefcase"),
            "part_time": ("#f59e0b", "245,158,11", "ph-clock"),
            "contract": ("#a855f7", "168,85,247", "ph-file-text"),
            "remote": ("#0ea5e9", "14,165,233", "ph-house"),
            "intern": ("#ef4444", "239,68,68", "ph-graduation-cap"),
        }
        hex_color, rgb, icon = colors.get(
            obj.employment_type, ("#6B7280", "107,114,128", "ph-question")
        )
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;'
            "border-radius:6px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">'
            '<i class="ph {}"></i> {}</span>',
            rgb,
            hex_color,
            icon,
            obj.get_employment_type_display(),
        )

    employment_type_badge.short_description = _("Calisma Sekli")


# =============================================================================
# PRESS RELEASE ADMIN
# =============================================================================


@admin.register(PressRelease)
class PressReleaseAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = ["title", "source", "published_at", "is_featured", "is_active"]
    list_filter = ["is_featured", "is_active"]
    search_fields = ["title", "source"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"

    fieldsets = (
        (
            _("Icerik"),
            {
                "fields": ("title", "slug", "excerpt", "content"),
            },
        ),
        (
            _("Kaynak"),
            {
                "fields": ("source", "source_url", "cover_image"),
            },
        ),
        (
            _("Ayarlar"),
            {
                "fields": ("published_at", "is_featured", "sort_order", "is_active"),
            },
        ),
        (
            _("SEO"),
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                    "meta_keywords",
                    "og_title",
                    "og_description",
                    "og_image",
                    "og_type",
                    "canonical_url",
                    "robots_index",
                    "robots_follow",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


# =============================================================================
# MILESTONE ADMIN
# =============================================================================


@admin.register(Milestone)
class MilestoneAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = ["year", "quarter", "title", "sort_order", "is_active"]
    list_filter = ["year", "is_active"]
    list_editable = ["sort_order", "is_active"]
    search_fields = ["title"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            None,
            {
                "fields": ("year", "quarter", "title", "description", "icon"),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


# =============================================================================
# BRAND ASSET ADMIN
# =============================================================================


@admin.register(BrandAsset)
class BrandAssetAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = [
        "title",
        "asset_type_badge",
        "file_format",
        "sort_order",
        "is_active",
    ]
    list_filter = ["asset_type", "is_active"]
    list_editable = ["sort_order", "is_active"]
    search_fields = ["title"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Icerik"),
            {
                "fields": ("title", "description", "asset_type", "file_format"),
            },
        ),
        (
            _("Dosyalar"),
            {
                "fields": ("file", "preview_image"),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def asset_type_badge(self, obj):
        colors = {
            "logo": ("#22c55e", "34,197,94", "ph-image"),
            "icon": ("#0ea5e9", "14,165,233", "ph-shapes"),
            "guideline": ("#a855f7", "168,85,247", "ph-book-open"),
            "press_kit": ("#f59e0b", "245,158,11", "ph-newspaper"),
            "color_palette": ("#ef4444", "239,68,68", "ph-palette"),
            "font": ("#6B7280", "107,114,128", "ph-text-aa"),
        }
        hex_color, rgb, icon = colors.get(
            obj.asset_type, ("#6B7280", "107,114,128", "ph-file")
        )
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;'
            "border-radius:6px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">'
            '<i class="ph {}"></i> {}</span>',
            rgb,
            hex_color,
            icon,
            obj.get_asset_type_display(),
        )

    asset_type_badge.short_description = _("Varlik Tipi")


# =============================================================================
# INVESTOR PAGE ADMIN (Singleton)
# =============================================================================


@admin.register(InvestorPage)
class InvestorPageAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = ["title", "contact_email", "is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            None,
            {
                "fields": ("title", "subtitle", "overview_content"),
            },
        ),
        (
            _("Pazar Buyuklugu"),
            {
                "fields": ("market_size_tam", "market_size_sam", "market_size_som"),
            },
        ),
        (
            _("Yatirim Tezi"),
            {
                "fields": ("investment_thesis", "contact_email"),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("is_active",),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return not InvestorPage.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# =============================================================================
# INVESTOR PRESENTATION ADMIN
# =============================================================================


@admin.register(InvestorPresentation)
class InvestorPresentationAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = ["title", "presentation_date", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    search_fields = ["title"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Icerik"),
            {
                "fields": (
                    "title",
                    "description",
                    "file",
                    "cover_image",
                    "presentation_date",
                ),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


# =============================================================================
# INVESTOR FINANCIAL ADMIN
# =============================================================================


@admin.register(InvestorFinancial)
class InvestorFinancialAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = [
        "period",
        "metric_name",
        "metric_value",
        "change_pct_badge",
        "is_active",
    ]
    list_filter = ["is_active"]
    search_fields = ["period", "metric_name"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            None,
            {
                "fields": ("period", "metric_name", "metric_value", "change_pct"),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def change_pct_badge(self, obj):
        if obj.change_pct is None:
            return "—"
        pct = float(obj.change_pct)
        if pct > 0:
            hex_color, rgb, icon = "#22c55e", "34,197,94", "ph-trend-up"
            sign = "+"
        elif pct < 0:
            hex_color, rgb, icon = "#ef4444", "239,68,68", "ph-trend-down"
            sign = ""
        else:
            hex_color, rgb, icon = "#6B7280", "107,114,128", "ph-minus"
            sign = ""
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;'
            "border-radius:6px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">'
            '<i class="ph {}"></i> {}{}%</span>',
            rgb,
            hex_color,
            icon,
            sign,
            pct,
        )

    change_pct_badge.short_description = _("Degisim %")


# =============================================================================
# PARTNER PROGRAM ADMIN (with PartnerTier inline)
# =============================================================================


class PartnerTierInline(TranslationTabularInline):
    model = PartnerTier
    extra = 0
    fields = ["name", "commission_pct", "color", "sort_order", "is_active"]
    ordering = ["sort_order"]


class PartnerBenefitInline(TranslationTabularInline):
    model = PartnerBenefit
    extra = 0
    fields = ["text", "icon", "sort_order", "is_active"]
    ordering = ["sort_order"]


@admin.register(PartnerProgram)
class PartnerProgramAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = ["title", "program_type_badge", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    search_fields = ["title"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PartnerTierInline]

    fieldsets = (
        (
            _("Icerik"),
            {
                "fields": (
                    "title",
                    "slug",
                    "description",
                    "program_type",
                    "icon",
                    "hero_image",
                ),
            },
        ),
        (
            _("Detaylar"),
            {
                "fields": ("commission_info", "requirements", "contact_email"),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def program_type_badge(self, obj):
        colors = {
            "reseller": ("#22c55e", "34,197,94", "ph-storefront"),
            "referral": ("#0ea5e9", "14,165,233", "ph-megaphone"),
            "white_label": ("#a855f7", "168,85,247", "ph-tag"),
            "technology": ("#f59e0b", "245,158,11", "ph-cpu"),
            "integration": ("#ef4444", "239,68,68", "ph-plugs-connected"),
        }
        hex_color, rgb, icon = colors.get(
            obj.program_type, ("#6B7280", "107,114,128", "ph-question")
        )
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;'
            "border-radius:6px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">'
            '<i class="ph {}"></i> {}</span>',
            rgb,
            hex_color,
            icon,
            obj.get_program_type_display(),
        )

    program_type_badge.short_description = _("Program Tipi")


# =============================================================================
# PARTNER TIER ADMIN (standalone with PartnerBenefit inline)
# =============================================================================


@admin.register(PartnerTier)
class PartnerTierAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = ["name", "program", "commission_pct", "sort_order", "is_active"]
    list_filter = ["program", "is_active"]
    list_editable = ["sort_order", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [PartnerBenefitInline]

    fieldsets = (
        (
            None,
            {
                "fields": ("program", "name", "description", "commission_pct", "color"),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


# =============================================================================
# HELP CATEGORY ADMIN
# =============================================================================


@admin.register(HelpCategory)
class HelpCategoryAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = ["name", "slug", "icon", "article_count", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "slug", "description", "icon", "color"),
            },
        ),
        (
            _("Gorunum"),
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def article_count(self, obj):
        count = obj.articles.filter(is_active=True).count()
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;'
            "border-radius:6px;font-size:11px;font-weight:600;"
            'background:rgba(14,165,233,0.12);color:#0ea5e9;">'
            '<i class="ph ph-article"></i> {}</span>',
            count,
        )

    article_count.short_description = _("Makale Sayisi")


# =============================================================================
# HELP ARTICLE ADMIN
# =============================================================================


@admin.register(HelpArticle)
class HelpArticleAdmin(TabbedTranslationAdmin, EMenumPermissionMixin):
    list_display = [
        "title",
        "category",
        "view_count",
        "helpful_count",
        "is_featured",
        "is_active",
    ]
    list_filter = ["category", "is_featured", "is_active"]
    search_fields = ["title", "content"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "view_count",
        "helpful_count",
        "not_helpful_count",
    ]
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (
            _("Icerik"),
            {
                "fields": ("category", "title", "slug", "content"),
            },
        ),
        (
            _("Istatistikler"),
            {
                "fields": ("view_count", "helpful_count", "not_helpful_count"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Ayarlar"),
            {
                "fields": ("is_featured", "sort_order", "is_active"),
            },
        ),
        (
            _("SEO"),
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                    "meta_keywords",
                    "og_title",
                    "og_description",
                    "og_image",
                    "og_type",
                    "canonical_url",
                    "robots_index",
                    "robots_follow",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Sistem"),
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
