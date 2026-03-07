"""
Model translation options for website CMS models.

Uses django-modeltranslation to create per-language database columns
for all translatable text fields. Supported languages: TR, EN, AR, UK, FA.

Each registered model gets _tr, _en, _ar, _uk, _fa suffixed columns.
The admin uses TabbedTranslationAdmin to show language tabs.
"""

from modeltranslation.translator import translator, TranslationOptions

from .models import (
    SiteSettings,
    PageHero,
    HomeSection,
    FeatureCategory,
    FeatureBullet,
    Testimonial,
    TrustBadge,
    TrustLocation,
    FAQ,
    TeamMember,
    CompanyValue,
    CompanyStat,
    LegalPage,
    BlogPost,
    PlanDisplayFeature,
    NavigationLink,
    Sector,
    SolutionPage,
    CaseStudy,
    ROICalculatorConfig,
    ResourceCategory,
    IndustryReport,
    FreeTool,
    Webinar,
    CareerPosition,
    PressRelease,
    Milestone,
    BrandAsset,
    InvestorPage,
    InvestorPresentation,
    InvestorFinancial,
    PartnerProgram,
    PartnerTier,
    PartnerBenefit,
    HelpCategory,
    HelpArticle,
)


# =============================================================================
# SITE SETTINGS
# =============================================================================


class SiteSettingsTranslationOptions(TranslationOptions):
    fields = (
        "company_name",
        "tagline",
        "description",
        "address",
        "whatsapp_message",
        "cta_primary_text",
        "cta_secondary_text",
        "cta_trust_text",
        "announcement_text",
        "cookie_banner_title",
        "cookie_banner_text",
    )


# =============================================================================
# PAGE HERO
# =============================================================================


class PageHeroTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "subtitle",
        "badge_text",
        "cta_primary_text",
        "cta_secondary_text",
        "trust_text",
    )


# =============================================================================
# HOME SECTION
# =============================================================================


class HomeSectionTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "description",
    )


# =============================================================================
# FEATURE CATEGORY + BULLET
# =============================================================================


class FeatureCategoryTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "description",
        "badge_text",
        "image_alt",
    )


class FeatureBulletTranslationOptions(TranslationOptions):
    fields = ("text",)


# =============================================================================
# TESTIMONIAL
# =============================================================================


class TestimonialTranslationOptions(TranslationOptions):
    fields = (
        "author_name",
        "author_role_or_business",
        "author_location",
        "business_type_label",
        "quote",
    )


# =============================================================================
# TRUST BADGE + LOCATION
# =============================================================================


class TrustBadgeTranslationOptions(TranslationOptions):
    fields = ("label",)


class TrustLocationTranslationOptions(TranslationOptions):
    fields = ("text",)


# =============================================================================
# FAQ
# =============================================================================


class FAQTranslationOptions(TranslationOptions):
    fields = (
        "question",
        "answer",
    )


# =============================================================================
# TEAM MEMBER
# =============================================================================


class TeamMemberTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "title",
    )


# =============================================================================
# COMPANY VALUE
# =============================================================================


class CompanyValueTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "description",
    )


# =============================================================================
# COMPANY STAT
# =============================================================================


class CompanyStatTranslationOptions(TranslationOptions):
    fields = (
        "value",
        "label",
    )


# =============================================================================
# LEGAL PAGE
# =============================================================================


class LegalPageTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "content",
        "last_updated_display",
        "meta_description",
    )


# =============================================================================
# BLOG POST
# =============================================================================


class BlogPostTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "excerpt",
        "content",
        "category",
        "meta_description",
    )


# =============================================================================
# PLAN DISPLAY FEATURE
# =============================================================================


class PlanDisplayFeatureTranslationOptions(TranslationOptions):
    fields = ("text",)


# =============================================================================
# NAVIGATION LINK
# =============================================================================


class NavigationLinkTranslationOptions(TranslationOptions):
    fields = (
        "label",
        "description",
    )


# =============================================================================
# SECTOR
# =============================================================================


class SectorTranslationOptions(TranslationOptions):
    fields = ("name", "description")


# =============================================================================
# SOLUTION PAGE
# =============================================================================


class SolutionPageTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "subtitle",
        "content",
        "key_benefits",
        "pain_points",
        "target_audience",
    )


# =============================================================================
# CASE STUDY
# =============================================================================


class CaseStudyTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "excerpt",
        "challenge",
        "solution",
        "results",
        "stat_1_label",
        "stat_2_label",
        "stat_3_label",
        "quote",
        "quote_author",
        "quote_author_title",
    )


# =============================================================================
# ROI CALCULATOR CONFIG
# =============================================================================


class ROICalculatorConfigTranslationOptions(TranslationOptions):
    fields = ("title", "description")


# =============================================================================
# RESOURCE CATEGORY
# =============================================================================


class ResourceCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


# =============================================================================
# INDUSTRY REPORT
# =============================================================================


class IndustryReportTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "excerpt",
        "content",
    )


# =============================================================================
# FREE TOOL
# =============================================================================


class FreeToolTranslationOptions(TranslationOptions):
    fields = ("title", "description")


# =============================================================================
# WEBINAR
# =============================================================================


class WebinarTranslationOptions(TranslationOptions):
    fields = ("title", "description")


# =============================================================================
# CAREER POSITION
# =============================================================================


class CareerPositionTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "department",
        "location",
        "description",
        "requirements",
        "benefits",
    )


# =============================================================================
# PRESS RELEASE
# =============================================================================


class PressReleaseTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "excerpt",
        "content",
    )


# =============================================================================
# MILESTONE
# =============================================================================


class MilestoneTranslationOptions(TranslationOptions):
    fields = ("title", "description")


# =============================================================================
# BRAND ASSET
# =============================================================================


class BrandAssetTranslationOptions(TranslationOptions):
    fields = ("title", "description")


# =============================================================================
# INVESTOR PAGE
# =============================================================================


class InvestorPageTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "subtitle",
        "overview_content",
        "investment_thesis",
    )


# =============================================================================
# INVESTOR PRESENTATION
# =============================================================================


class InvestorPresentationTranslationOptions(TranslationOptions):
    fields = ("title", "description")


# =============================================================================
# INVESTOR FINANCIAL
# =============================================================================


class InvestorFinancialTranslationOptions(TranslationOptions):
    fields = ("metric_name",)


# =============================================================================
# PARTNER PROGRAM
# =============================================================================


class PartnerProgramTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "description",
        "commission_info",
        "requirements",
    )


# =============================================================================
# PARTNER TIER
# =============================================================================


class PartnerTierTranslationOptions(TranslationOptions):
    fields = ("name", "description")


# =============================================================================
# PARTNER BENEFIT
# =============================================================================


class PartnerBenefitTranslationOptions(TranslationOptions):
    fields = ("text",)


# =============================================================================
# HELP CATEGORY
# =============================================================================


class HelpCategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


# =============================================================================
# HELP ARTICLE
# =============================================================================


class HelpArticleTranslationOptions(TranslationOptions):
    fields = ("title", "content")


# =============================================================================
# REGISTER ALL
# =============================================================================

translator.register(SiteSettings, SiteSettingsTranslationOptions)
translator.register(PageHero, PageHeroTranslationOptions)
translator.register(HomeSection, HomeSectionTranslationOptions)
translator.register(FeatureCategory, FeatureCategoryTranslationOptions)
translator.register(FeatureBullet, FeatureBulletTranslationOptions)
translator.register(Testimonial, TestimonialTranslationOptions)
translator.register(TrustBadge, TrustBadgeTranslationOptions)
translator.register(TrustLocation, TrustLocationTranslationOptions)
translator.register(FAQ, FAQTranslationOptions)
translator.register(TeamMember, TeamMemberTranslationOptions)
translator.register(CompanyValue, CompanyValueTranslationOptions)
translator.register(CompanyStat, CompanyStatTranslationOptions)
translator.register(LegalPage, LegalPageTranslationOptions)
translator.register(BlogPost, BlogPostTranslationOptions)
translator.register(PlanDisplayFeature, PlanDisplayFeatureTranslationOptions)
translator.register(NavigationLink, NavigationLinkTranslationOptions)
translator.register(Sector, SectorTranslationOptions)
translator.register(SolutionPage, SolutionPageTranslationOptions)
translator.register(CaseStudy, CaseStudyTranslationOptions)
translator.register(ROICalculatorConfig, ROICalculatorConfigTranslationOptions)
translator.register(ResourceCategory, ResourceCategoryTranslationOptions)
translator.register(IndustryReport, IndustryReportTranslationOptions)
translator.register(FreeTool, FreeToolTranslationOptions)
translator.register(Webinar, WebinarTranslationOptions)
translator.register(CareerPosition, CareerPositionTranslationOptions)
translator.register(PressRelease, PressReleaseTranslationOptions)
translator.register(Milestone, MilestoneTranslationOptions)
translator.register(BrandAsset, BrandAssetTranslationOptions)
translator.register(InvestorPage, InvestorPageTranslationOptions)
translator.register(InvestorPresentation, InvestorPresentationTranslationOptions)
translator.register(InvestorFinancial, InvestorFinancialTranslationOptions)
translator.register(PartnerProgram, PartnerProgramTranslationOptions)
translator.register(PartnerTier, PartnerTierTranslationOptions)
translator.register(PartnerBenefit, PartnerBenefitTranslationOptions)
translator.register(HelpCategory, HelpCategoryTranslationOptions)
translator.register(HelpArticle, HelpArticleTranslationOptions)
