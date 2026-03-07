"""Website views package — re-exports all views for backward compatibility."""

from .mixins import CmsContextMixin
from .home import HomeView
from .features import FeaturesView
from .pricing import PricingView
from .about import AboutView
from .blog import BlogView, BlogDetailView
from .contact import ContactView, DemoRequestView
from .legal import LegalPageView, PrivacyView, TermsView, KvkkView, CookiePolicyView
from .newsletter import NewsletterView
from .solutions import SolutionsIndexView, SolutionDetailView
from .customers import CustomersView, CaseStudyDetailView, ROICalculatorView
from .resources import (
    ResourcesView,
    ReportDetailView,
    ToolDetailView,
    WebinarDetailView,
)
from .company import (
    CareersView,
    CareerDetailView,
    PressView,
    PressDetailView,
    BrandAssetsView,
)
from .investor import InvestorView
from .partners import PartnersView, PartnerProgramDetailView
from .support import SupportView, HelpCategoryView, HelpArticleView

__all__ = [
    "CmsContextMixin",
    "HomeView",
    "FeaturesView",
    "PricingView",
    "AboutView",
    "BlogView",
    "BlogDetailView",
    "ContactView",
    "DemoRequestView",
    "LegalPageView",
    "PrivacyView",
    "TermsView",
    "KvkkView",
    "CookiePolicyView",
    "NewsletterView",
    "SolutionsIndexView",
    "SolutionDetailView",
    "CustomersView",
    "CaseStudyDetailView",
    "ROICalculatorView",
    "ResourcesView",
    "ReportDetailView",
    "ToolDetailView",
    "WebinarDetailView",
    "CareersView",
    "CareerDetailView",
    "PressView",
    "PressDetailView",
    "BrandAssetsView",
    "InvestorView",
    "PartnersView",
    "PartnerProgramDetailView",
    "SupportView",
    "HelpCategoryView",
    "HelpArticleView",
]
