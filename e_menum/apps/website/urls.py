"""
URL patterns for website marketing pages.

All marketing pages are served with i18n_patterns language prefix.
URL slugs are translatable via gettext_lazy → .po files.
"""

from django.urls import path
from django.utils.translation import gettext_lazy as _

from . import views

app_name = "website"

urlpatterns = [
    # =========================================================================
    # Main Marketing Pages
    # =========================================================================
    path("", views.HomeView.as_view(), name="home"),
    path(_("ozellikler/"), views.FeaturesView.as_view(), name="features"),
    path(_("fiyatlandirma/"), views.PricingView.as_view(), name="pricing"),
    path(_("hakkimizda/"), views.AboutView.as_view(), name="about"),
    path(_("blog/"), views.BlogView.as_view(), name="blog"),
    path(
        _("blog/") + "<slug:slug>/", views.BlogDetailView.as_view(), name="blog_detail"
    ),
    # =========================================================================
    # Form Pages
    # =========================================================================
    path(_("iletisim/"), views.ContactView.as_view(), name="contact"),
    path(_("demo/"), views.DemoRequestView.as_view(), name="demo"),
    # =========================================================================
    # Newsletter (AJAX POST only)
    # =========================================================================
    path("newsletter/", views.NewsletterView.as_view(), name="newsletter"),
    # =========================================================================
    # Legal Pages
    # =========================================================================
    path(_("gizlilik/"), views.PrivacyView.as_view(), name="privacy"),
    path(_("kullanim-sartlari/"), views.TermsView.as_view(), name="terms"),
    path(_("kvkk/"), views.KvkkView.as_view(), name="kvkk"),
    path(
        _("cerez-politikasi/"), views.CookiePolicyView.as_view(), name="cookie_policy"
    ),
    path(_("sla/"), views.SlaView.as_view(), name="sla"),
    path(_("veri-isleme-sozlesmesi/"), views.DpaView.as_view(), name="dpa"),
    path(
        _("guvenlik-politikasi/"), views.SecurityPolicyView.as_view(), name="security"
    ),
    path(_("sorumluluk-reddi/"), views.DisclaimerView.as_view(), name="disclaimer"),
    # =========================================================================
    # Solutions
    # =========================================================================
    path(_("cozumler/"), views.SolutionsIndexView.as_view(), name="solutions"),
    path(
        _("cozumler/") + "<slug:slug>/",
        views.SolutionDetailView.as_view(),
        name="solution_detail",
    ),
    # =========================================================================
    # Customers
    # =========================================================================
    path(_("musteriler/"), views.CustomersView.as_view(), name="customers"),
    path(
        _("musteriler/basari-hikayeleri/") + "<slug:slug>/",
        views.CaseStudyDetailView.as_view(),
        name="case_study_detail",
    ),
    path(
        _("musteriler/roi-hesaplayici/"),
        views.ROICalculatorView.as_view(),
        name="roi_calculator",
    ),
    # =========================================================================
    # Resources
    # =========================================================================
    path(_("kaynaklar/"), views.ResourcesView.as_view(), name="resources"),
    path(
        _("kaynaklar/raporlar/") + "<slug:slug>/",
        views.ReportDetailView.as_view(),
        name="report_detail",
    ),
    path(
        _("kaynaklar/araclar/") + "<slug:slug>/",
        views.ToolDetailView.as_view(),
        name="tool_detail",
    ),
    path(
        _("kaynaklar/webinarlar/") + "<slug:slug>/",
        views.WebinarDetailView.as_view(),
        name="webinar_detail",
    ),
    # =========================================================================
    # Company — Careers
    # =========================================================================
    path(_("kariyer/"), views.CareersView.as_view(), name="careers"),
    path(
        _("kariyer/") + "<slug:slug>/",
        views.CareerDetailView.as_view(),
        name="career_detail",
    ),
    # =========================================================================
    # Company — Press
    # =========================================================================
    path(_("basin/"), views.PressView.as_view(), name="press"),
    path(
        _("basin/marka-kaynaklari/"),
        views.BrandAssetsView.as_view(),
        name="brand_assets",
    ),
    path(
        _("basin/") + "<slug:slug>/",
        views.PressDetailView.as_view(),
        name="press_detail",
    ),
    # =========================================================================
    # Investor Relations
    # =========================================================================
    path(_("yatirimci/"), views.InvestorView.as_view(), name="investor"),
    # =========================================================================
    # Partners
    # =========================================================================
    path(_("partnerler/"), views.PartnersView.as_view(), name="partners"),
    path(
        _("partnerler/") + "<slug:slug>/",
        views.PartnerProgramDetailView.as_view(),
        name="partner_detail",
    ),
    # =========================================================================
    # HTML Sitemap (user-facing)
    # =========================================================================
    path(_("site-haritasi/"), views.SitemapHTMLView.as_view(), name="sitemap_html"),
    # =========================================================================
    # Support / Help Center
    # =========================================================================
    path(_("destek/"), views.SupportView.as_view(), name="support"),
    path(
        _("destek/") + "<slug:slug>/",
        views.HelpCategoryView.as_view(),
        name="help_category",
    ),
    path(
        _("destek/") + "<slug:category_slug>/<slug:article_slug>/",
        views.HelpArticleView.as_view(),
        name="help_article",
    ),
]
