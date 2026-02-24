"""
Management command to seed CMS content from hardcoded template data.

Usage:
    python manage.py seed_cms_content

Idempotent: uses get_or_create so it can be run multiple times safely.
Transfers all hardcoded marketing content from templates into the database.
"""

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from apps.website.models import (
    BlogPost,
    BrandAsset,
    CareerPosition,
    CaseStudy,
    CompanyStat,
    CompanyValue,
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


class Command(BaseCommand):
    help = 'Seed CMS content with marketing page data (idempotent)'

    def handle(self, *args, **options):
        self.stdout.write('Seeding CMS content...\n')

        self._seed_site_settings()
        self._seed_page_heroes()
        self._seed_home_sections()
        self._seed_feature_categories()
        self._seed_testimonials()
        self._seed_trust_badges()
        self._seed_trust_locations()
        self._seed_faqs()
        self._seed_team_members()
        self._seed_company_values()
        self._seed_company_stats()
        self._seed_legal_pages()
        self._seed_blog_posts()
        self._seed_plan_display_features()
        self._seed_navigation_links()
        self._seed_sectors()
        self._seed_solutions()
        self._seed_case_studies()
        self._seed_roi_config()
        self._seed_resource_categories()
        self._seed_help_categories()
        self._seed_help_articles()
        self._seed_career_positions()
        self._seed_milestones()
        self._seed_investor_page()
        self._seed_partner_programs()
        self._seed_new_page_heroes()
        self._seed_storefront_nav_links()

        self.stdout.write(self.style.SUCCESS('\nAll CMS content seeded successfully!'))

    def _seed_site_settings(self):
        obj = SiteSettings.load()
        # company_name
        obj.company_name_tr = 'E-Menum'
        obj.company_name_en = 'E-Menum'
        obj.company_name_ar = 'E-Menum'
        obj.company_name_ru = 'E-Menum'
        obj.company_name_de = 'E-Menum'
        # tagline
        obj.tagline_tr = 'QR Menunuz, Isletmenizin Dijital Vitrini'
        obj.tagline_en = 'Your QR Menu, Your Business\'s Digital Showcase'
        obj.tagline_ar = '\u0642\u0627\u0626\u0645\u0629 QR \u0627\u0644\u062e\u0627\u0635\u0629 \u0628\u0643\u060c \u0648\u0627\u062c\u0647\u0629 \u0639\u0645\u0644\u0643 \u0627\u0644\u0631\u0642\u0645\u064a\u0629'
        obj.tagline_ru = '\u0412\u0430\u0448\u0435 QR-\u043c\u0435\u043d\u044e \u2014 \u0446\u0438\u0444\u0440\u043e\u0432\u0430 \u0432\u0456\u0442\u0440\u0438\u043d\u0430 \u0432\u0430\u0448\u043e\u0433\u043e \u0431\u0456\u0437\u043d\u0435\u0441\u0443'
        obj.tagline_de = '\u0645\u0646\u0648\u06cc QR \u0634\u0645\u0627\u060c \u0648\u06cc\u062a\u0631\u06cc\u0646 \u062f\u06cc\u062c\u06cc\u062a\u0627\u0644 \u06a9\u0633\u0628\u200c\u0648\u06a9\u0627\u0631\u062a\u0627\u0646'
        # description
        obj.description_tr = (
            'Restoran ve kafeler icin yapay zeka destekli dijital menu platformu. '
            'QR menu, siparis yonetimi, analitik ve daha fazlasi.'
        )
        obj.description_en = (
            'AI-powered digital menu platform for restaurants and cafes. '
            'QR menus, order management, analytics and more.'
        )
        obj.description_ar = (
            '\u0645\u0646\u0635\u0629 \u0642\u0648\u0627\u0626\u0645 \u0631\u0642\u0645\u064a\u0629 \u0645\u062f\u0639\u0648\u0645\u0629 \u0628\u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a \u0644\u0644\u0645\u0637\u0627\u0639\u0645 \u0648\u0627\u0644\u0645\u0642\u0627\u0647\u064a. '
            '\u0642\u0648\u0627\u0626\u0645 QR\u060c \u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0637\u0644\u0628\u0627\u062a\u060c \u0627\u0644\u062a\u062d\u0644\u064a\u0644\u0627\u062a \u0648\u0627\u0644\u0645\u0632\u064a\u062f.'
        )
        obj.description_ru = (
            '\u041f\u043b\u0430\u0442\u0444\u043e\u0440\u043c\u0430 \u0446\u0438\u0444\u0440\u043e\u0432\u043e\u0433\u043e \u043c\u0435\u043d\u044e \u0437 \u043f\u0456\u0434\u0442\u0440\u0438\u043c\u043a\u043e\u044e \u0428\u0406 \u0434\u043b\u044f \u0440\u0435\u0441\u0442\u043e\u0440\u0430\u043d\u0456\u0432 \u0442\u0430 \u043a\u0430\u0444\u0435. '
            'QR-\u043c\u0435\u043d\u044e, \u0443\u043f\u0440\u0430\u0432\u043b\u0456\u043d\u043d\u044f \u0437\u0430\u043c\u043e\u0432\u043b\u0435\u043d\u043d\u044f\u043c\u0438, \u0430\u043d\u0430\u043b\u0456\u0442\u0438\u043a\u0430 \u0442\u0430 \u0431\u0430\u0433\u0430\u0442\u043e \u0456\u043d\u0448\u043e\u0433\u043e.'
        )
        obj.description_de = (
            '\u067e\u0644\u062a\u0641\u0631\u0645 \u0645\u0646\u0648\u06cc \u062f\u06cc\u062c\u06cc\u062a\u0627\u0644 \u0645\u0628\u062a\u0646\u06cc \u0628\u0631 \u0647\u0648\u0634 \u0645\u0635\u0646\u0648\u0639\u06cc \u0628\u0631\u0627\u06cc \u0631\u0633\u062a\u0648\u0631\u0627\u0646\u200c\u0647\u0627 \u0648 \u06a9\u0627\u0641\u0647\u200c\u0647\u0627. '
            '\u0645\u0646\u0648\u06cc QR\u060c \u0645\u062f\u06cc\u0631\u06cc\u062a \u0633\u0641\u0627\u0631\u0634\u060c \u062a\u062d\u0644\u06cc\u0644 \u062f\u0627\u062f\u0647\u200c\u0647\u0627 \u0648 \u0628\u06cc\u0634\u062a\u0631.'
        )
        # Non-translated fields
        obj.phone = '+90 850 123 4567'
        obj.email = 'info@e-menum.com'
        # address
        obj.address_tr = 'Istanbul, Turkiye'
        obj.address_en = 'Istanbul, Turkey'
        obj.address_ar = '\u0625\u0633\u0637\u0646\u0628\u0648\u0644\u060c \u062a\u0631\u0643\u064a\u0627'
        obj.address_ru = '\u0421\u0442\u0430\u043c\u0431\u0443\u043b, \u0422\u0443\u0440\u0435\u0447\u0447\u0438\u043d\u0430'
        obj.address_de = '\u0627\u0633\u062a\u0627\u0646\u0628\u0648\u0644\u060c \u062a\u0631\u06a9\u06cc\u0647'
        # Social media (not translated)
        obj.social_instagram = 'https://instagram.com/emenum'
        obj.social_twitter = 'https://twitter.com/emenum'
        obj.social_linkedin = 'https://linkedin.com/company/emenum'
        obj.social_youtube = 'https://youtube.com/@emenum'
        obj.whatsapp_number = '908501234567'
        # whatsapp_message
        obj.whatsapp_message_tr = 'Merhaba! E-Menum hakkinda bilgi almak istiyorum.'
        obj.whatsapp_message_en = 'Hello! I would like to learn more about E-Menum.'
        obj.whatsapp_message_ar = '\u0645\u0631\u062d\u0628\u0627\u064b! \u0623\u0631\u063a\u0628 \u0641\u064a \u0645\u0639\u0631\u0641\u0629 \u0627\u0644\u0645\u0632\u064a\u062f \u0639\u0646 E-Menum.'
        obj.whatsapp_message_ru = '\u0412\u0456\u0442\u0430\u044e! \u0425\u043e\u0447\u0443 \u0434\u0456\u0437\u043d\u0430\u0442\u0438\u0441\u044f \u0431\u0456\u043b\u044c\u0448\u0435 \u043f\u0440\u043e E-Menum.'
        obj.whatsapp_message_de = '\u0633\u0644\u0627\u0645! \u0645\u06cc\u200c\u062e\u0648\u0627\u0647\u0645 \u062f\u0631\u0628\u0627\u0631\u0647 E-Menum \u0627\u0637\u0644\u0627\u0639\u0627\u062a \u0628\u06cc\u0634\u062a\u0631\u06cc \u06a9\u0633\u0628 \u06a9\u0646\u0645.'
        # cta_primary_text
        obj.cta_primary_text_tr = '14 Gun Ucretsiz Basla'
        obj.cta_primary_text_en = 'Start 14-Day Free Trial'
        obj.cta_primary_text_ar = '\u0627\u0628\u062f\u0623 \u062a\u062c\u0631\u0628\u0629 \u0645\u062c\u0627\u0646\u064a\u0629 \u0644\u0645\u062f\u0629 14 \u064a\u0648\u0645\u0627\u064b'
        obj.cta_primary_text_ru = '\u041f\u043e\u0447\u043d\u0456\u0442\u044c 14-\u0434\u0435\u043d\u043d\u0443 \u0431\u0435\u0437\u043a\u043e\u0448\u0442\u043e\u0432\u043d\u0443 \u0432\u0435\u0440\u0441\u0456\u044e'
        obj.cta_primary_text_de = '\u0634\u0631\u0648\u0639 \u062f\u0648\u0631\u0647 \u0631\u0627\u06cc\u06af\u0627\u0646 \u06f1\u06f4 \u0631\u0648\u0632\u0647'
        # cta_secondary_text
        obj.cta_secondary_text_tr = 'Demo Iste'
        obj.cta_secondary_text_en = 'Request Demo'
        obj.cta_secondary_text_ar = '\u0627\u0637\u0644\u0628 \u0639\u0631\u0636\u0627\u064b \u062a\u0648\u0636\u064a\u062d\u064a\u0627\u064b'
        obj.cta_secondary_text_ru = '\u0417\u0430\u043c\u043e\u0432\u0438\u0442\u0438 \u0434\u0435\u043c\u043e'
        obj.cta_secondary_text_de = '\u062f\u0631\u062e\u0648\u0627\u0633\u062a \u062f\u0645\u043e'
        # cta_trust_text
        obj.cta_trust_text_tr = 'Kredi karti gerekmez \u00b7 2 dakikada kurulum'
        obj.cta_trust_text_en = 'No credit card required \u00b7 Set up in 2 minutes'
        obj.cta_trust_text_ar = '\u0644\u0627 \u062d\u0627\u062c\u0629 \u0644\u0628\u0637\u0627\u0642\u0629 \u0627\u0626\u062a\u0645\u0627\u0646 \u00b7 \u0627\u0644\u0625\u0639\u062f\u0627\u062f \u062e\u0644\u0627\u0644 \u062f\u0642\u064a\u0642\u062a\u064a\u0646'
        obj.cta_trust_text_ru = '\u041a\u0440\u0435\u0434\u0438\u0442\u043d\u0430 \u043a\u0430\u0440\u0442\u043a\u0430 \u043d\u0435 \u043f\u043e\u0442\u0440\u0456\u0431\u043d\u0430 \u00b7 \u041d\u0430\u043b\u0430\u0448\u0442\u0443\u0432\u0430\u043d\u043d\u044f \u0437\u0430 2 \u0445\u0432\u0438\u043b\u0438\u043d\u0438'
        obj.cta_trust_text_de = '\u0628\u062f\u0648\u0646 \u0646\u06cc\u0627\u0632 \u0628\u0647 \u06a9\u0627\u0631\u062a \u0627\u0639\u062a\u0628\u0627\u0631\u06cc \u00b7 \u0631\u0627\u0647\u200c\u0627\u0646\u062f\u0627\u0632\u06cc \u062f\u0631 \u06f2 \u062f\u0642\u06cc\u0642\u0647'
        # Non-translated URL fields
        obj.cta_primary_url = 'website:demo'
        obj.cta_secondary_url = 'website:demo'
        obj.login_url = '/admin/'
        # Announcement bar
        obj.announcement_text_tr = 'Yeni: AI Menu Asistani simdi kullanima hazir!'
        obj.announcement_text_en = 'New: AI Menu Assistant is now available!'
        obj.announcement_url = '/tr/ozellikler/'
        obj.announcement_is_active = True
        # Cookie banner
        obj.cookie_banner_title_tr = 'Cerez Kullanimi'
        obj.cookie_banner_title_en = 'Cookie Usage'
        obj.cookie_banner_text_tr = 'Web sitemizde size daha iyi bir deneyim sunabilmek icin cerezleri kullaniyoruz.'
        obj.cookie_banner_text_en = 'We use cookies on our website to provide you with a better experience.'
        # Company legal details
        obj.vat_no = '1234567890'
        obj.mersis_no = '0123456789012345'
        obj.trade_registry = 'Istanbul Ticaret Sicil Mudurlugu - 123456'
        obj.status_page_url = 'https://status.emenum.com'
        obj.save()
        self.stdout.write('  \u2713 SiteSettings')

    def _seed_page_heroes(self):
        heroes = [
            {
                'page': 'home',
                'title_tr': 'QR Menunuz, Isletmenizin Dijital Vitrini',
                'title_en': 'Your QR Menu, Your Business\'s Digital Showcase',
                'title_ar': '\u0642\u0627\u0626\u0645\u0629 QR \u0627\u0644\u062e\u0627\u0635\u0629 \u0628\u0643\u060c \u0648\u0627\u062c\u0647\u0629 \u0639\u0645\u0644\u0643 \u0627\u0644\u0631\u0642\u0645\u064a\u0629',
                'title_ru': '\u0412\u0430\u0448\u0435 QR-\u043c\u0435\u043d\u044e \u2014 \u0446\u0438\u0444\u0440\u043e\u0432\u0430 \u0432\u0456\u0442\u0440\u0438\u043d\u0430 \u0432\u0430\u0448\u043e\u0433\u043e \u0431\u0456\u0437\u043d\u0435\u0441\u0443',
                'title_de': '\u0645\u0646\u0648\u06cc QR \u0634\u0645\u0627\u060c \u0648\u06cc\u062a\u0631\u06cc\u0646 \u062f\u06cc\u062c\u06cc\u062a\u0627\u0644 \u06a9\u0633\u0628\u200c\u0648\u06a9\u0627\u0631\u062a\u0627\u0646',
                'subtitle_tr': 'Yapay zeka destekli dijital menu platformu. Menu olusturun, siparisleri yonetin, veriye dayali kararlar alin. Bakanlik zorunluluguna uyumlu.',
                'subtitle_en': 'AI-powered digital menu platform. Create menus, manage orders, make data-driven decisions. Ministry regulation compliant.',
                'subtitle_ar': '\u0645\u0646\u0635\u0629 \u0642\u0648\u0627\u0626\u0645 \u0631\u0642\u0645\u064a\u0629 \u0645\u062f\u0639\u0648\u0645\u0629 \u0628\u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a. \u0623\u0646\u0634\u0626 \u0627\u0644\u0642\u0648\u0627\u0626\u0645\u060c \u0623\u062f\u0631 \u0627\u0644\u0637\u0644\u0628\u0627\u062a\u060c \u0627\u062a\u062e\u0630 \u0642\u0631\u0627\u0631\u0627\u062a \u0645\u0628\u0646\u064a\u0629 \u0639\u0644\u0649 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a.',
                'subtitle_ru': '\u041f\u043b\u0430\u0442\u0444\u043e\u0440\u043c\u0430 \u0446\u0438\u0444\u0440\u043e\u0432\u043e\u0433\u043e \u043c\u0435\u043d\u044e \u0437 \u043f\u0456\u0434\u0442\u0440\u0438\u043c\u043a\u043e\u044e \u0428\u0406. \u0421\u0442\u0432\u043e\u0440\u044e\u0439\u0442\u0435 \u043c\u0435\u043d\u044e, \u043a\u0435\u0440\u0443\u0439\u0442\u0435 \u0437\u0430\u043c\u043e\u0432\u043b\u0435\u043d\u043d\u044f\u043c\u0438, \u043f\u0440\u0438\u0439\u043c\u0430\u0439\u0442\u0435 \u0440\u0456\u0448\u0435\u043d\u043d\u044f \u043d\u0430 \u043e\u0441\u043d\u043e\u0432\u0456 \u0434\u0430\u043d\u0438\u0445.',
                'subtitle_de': '\u067e\u0644\u062a\u0641\u0631\u0645 \u0645\u0646\u0648\u06cc \u062f\u06cc\u062c\u06cc\u062a\u0627\u0644 \u0645\u0628\u062a\u0646\u06cc \u0628\u0631 \u0647\u0648\u0634 \u0645\u0635\u0646\u0648\u0639\u06cc. \u0645\u0646\u0648 \u0628\u0633\u0627\u0632\u06cc\u062f\u060c \u0633\u0641\u0627\u0631\u0634\u200c\u0647\u0627 \u0631\u0627 \u0645\u062f\u06cc\u0631\u06cc\u062a \u06a9\u0646\u06cc\u062f\u060c \u062a\u0635\u0645\u06cc\u0645\u200c\u0647\u0627\u06cc \u0645\u0628\u062a\u0646\u06cc \u0628\u0631 \u062f\u0627\u062f\u0647 \u0628\u06af\u06cc\u0631\u06cc\u062f.',
                'badge_text_tr': 'Yapay Zeka Destekli QR Menu Platformu',
                'badge_text_en': 'AI-Powered QR Menu Platform',
                'badge_text_ar': '\u0645\u0646\u0635\u0629 \u0642\u0648\u0627\u0626\u0645 QR \u0645\u062f\u0639\u0648\u0645\u0629 \u0628\u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a',
                'badge_text_ru': 'QR-\u043c\u0435\u043d\u044e \u043f\u043b\u0430\u0442\u0444\u043e\u0440\u043c\u0430 \u0437\u0456 \u0428\u0406',
                'badge_text_de': '\u067e\u0644\u062a\u0641\u0631\u0645 \u0645\u0646\u0648\u06cc QR \u0645\u0628\u062a\u0646\u06cc \u0628\u0631 \u0647\u0648\u0634 \u0645\u0635\u0646\u0648\u0639\u06cc',
                'cta_primary_text_tr': '14 Gun Ucretsiz Basla',
                'cta_primary_text_en': 'Start 14-Day Free Trial',
                'cta_primary_text_ar': '\u0627\u0628\u062f\u0623 \u062a\u062c\u0631\u0628\u0629 \u0645\u062c\u0627\u0646\u064a\u0629 14 \u064a\u0648\u0645\u0627\u064b',
                'cta_primary_text_ru': '14 \u0434\u043d\u0456\u0432 \u0431\u0435\u0437\u043a\u043e\u0448\u0442\u043e\u0432\u043d\u043e',
                'cta_primary_text_de': '\u0634\u0631\u0648\u0639 \u062f\u0648\u0631\u0647 \u0631\u0627\u06cc\u06af\u0627\u0646 \u06f1\u06f4 \u0631\u0648\u0632\u0647',
                'cta_primary_url': 'website:demo',
                'cta_secondary_text_tr': 'Canli Demo Izle',
                'cta_secondary_text_en': 'Watch Live Demo',
                'cta_secondary_text_ar': '\u0634\u0627\u0647\u062f \u0627\u0644\u0639\u0631\u0636 \u0627\u0644\u0645\u0628\u0627\u0634\u0631',
                'cta_secondary_text_ru': '\u041f\u0435\u0440\u0435\u0433\u043b\u044f\u043d\u0443\u0442\u0438 \u0434\u0435\u043c\u043e',
                'cta_secondary_text_de': '\u0645\u0634\u0627\u0647\u062f\u0647 \u062f\u0645\u0648\u06cc \u0632\u0646\u062f\u0647',
                'cta_secondary_url': 'website:demo',
                'trust_text_tr': 'Kredi karti gerekmez \u00b7 2 dakikada kurulum',
                'trust_text_en': 'No credit card required \u00b7 Set up in 2 minutes',
                'trust_text_ar': '\u0644\u0627 \u062d\u0627\u062c\u0629 \u0644\u0628\u0637\u0627\u0642\u0629 \u0627\u0626\u062a\u0645\u0627\u0646 \u00b7 \u0627\u0644\u0625\u0639\u062f\u0627\u062f \u062e\u0644\u0627\u0644 \u062f\u0642\u064a\u0642\u062a\u064a\u0646',
                'trust_text_ru': '\u041a\u0440\u0435\u0434\u0438\u0442\u043d\u0430 \u043a\u0430\u0440\u0442\u043a\u0430 \u043d\u0435 \u043f\u043e\u0442\u0440\u0456\u0431\u043d\u0430 \u00b7 \u041d\u0430\u043b\u0430\u0448\u0442\u0443\u0432\u0430\u043d\u043d\u044f \u0437\u0430 2 \u0445\u0432',
                'trust_text_de': '\u0628\u062f\u0648\u0646 \u0646\u06cc\u0627\u0632 \u0628\u0647 \u06a9\u0627\u0631\u062a \u0627\u0639\u062a\u0628\u0627\u0631\u06cc \u00b7 \u0631\u0627\u0647\u200c\u0627\u0646\u062f\u0627\u0632\u06cc \u062f\u0631 \u06f2 \u062f\u0642\u06cc\u0642\u0647',
                'show_hero_image': True,
            },
            {
                'page': 'features',
                'title_tr': '50\'den Fazla Ozellik, Tek Platform',
                'title_en': '50+ Features, One Platform',
                'title_ar': '\u0623\u0643\u062b\u0631 \u0645\u0646 50 \u0645\u064a\u0632\u0629\u060c \u0645\u0646\u0635\u0629 \u0648\u0627\u062d\u062f\u0629',
                'title_ru': '50+ \u0444\u0443\u043d\u043a\u0446\u0456\u0439, \u043e\u0434\u043d\u0430 \u043f\u043b\u0430\u0442\u0444\u043e\u0440\u043c\u0430',
                'title_de': '\u0628\u06cc\u0634 \u0627\u0632 \u06f5\u06f0 \u0648\u06cc\u0698\u06af\u06cc\u060c \u06cc\u06a9 \u067e\u0644\u062a\u0641\u0631\u0645',
                'subtitle_tr': 'Dijital menuden siparis yonetimine, AI icerik uretiminden analitige \u2014 isletmenizin ihtiyaci olan her sey.',
                'subtitle_en': 'From digital menus to order management, AI content generation to analytics \u2014 everything your business needs.',
                'subtitle_ar': '\u0645\u0646 \u0627\u0644\u0642\u0648\u0627\u0626\u0645 \u0627\u0644\u0631\u0642\u0645\u064a\u0629 \u0625\u0644\u0649 \u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0637\u0644\u0628\u0627\u062a\u060c \u0645\u0646 \u0625\u0646\u0634\u0627\u0621 \u0627\u0644\u0645\u062d\u062a\u0648\u0649 \u0628\u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a \u0625\u0644\u0649 \u0627\u0644\u062a\u062d\u0644\u064a\u0644\u0627\u062a \u2014 \u0643\u0644 \u0645\u0627 \u064a\u062d\u062a\u0627\u062c\u0647 \u0639\u0645\u0644\u0643.',
                'subtitle_ru': '\u0412\u0456\u0434 \u0446\u0438\u0444\u0440\u043e\u0432\u043e\u0433\u043e \u043c\u0435\u043d\u044e \u0434\u043e \u0443\u043f\u0440\u0430\u0432\u043b\u0456\u043d\u043d\u044f \u0437\u0430\u043c\u043e\u0432\u043b\u0435\u043d\u043d\u044f\u043c\u0438, \u0432\u0456\u0434 \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0456\u0457 \u043a\u043e\u043d\u0442\u0435\u043d\u0442\u0443 \u0428\u0406 \u0434\u043e \u0430\u043d\u0430\u043b\u0456\u0442\u0438\u043a\u0438 \u2014 \u0432\u0441\u0435 \u0434\u043b\u044f \u0432\u0430\u0448\u043e\u0433\u043e \u0431\u0456\u0437\u043d\u0435\u0441\u0443.',
                'subtitle_de': '\u0627\u0632 \u0645\u0646\u0648\u06cc \u062f\u06cc\u062c\u06cc\u062a\u0627\u0644 \u062a\u0627 \u0645\u062f\u06cc\u0631\u06cc\u062a \u0633\u0641\u0627\u0631\u0634\u060c \u0627\u0632 \u062a\u0648\u0644\u06cc\u062f \u0645\u062d\u062a\u0648\u0627\u06cc \u0647\u0648\u0634\u0645\u0646\u062f \u062a\u0627 \u062a\u062d\u0644\u06cc\u0644 \u062f\u0627\u062f\u0647\u200c\u0647\u0627 \u2014 \u0647\u0631 \u0622\u0646\u0686\u0647 \u06a9\u0633\u0628\u200c\u0648\u06a9\u0627\u0631 \u0634\u0645\u0627 \u0646\u06cc\u0627\u0632 \u062f\u0627\u0631\u062f.',
                'badge_text_tr': 'Tam Kapsamli Platform',
                'badge_text_en': 'Comprehensive Platform',
                'badge_text_ar': '\u0645\u0646\u0635\u0629 \u0634\u0627\u0645\u0644\u0629',
                'badge_text_ru': '\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0441\u043d\u0430 \u043f\u043b\u0430\u0442\u0444\u043e\u0440\u043c\u0430',
                'badge_text_de': '\u067e\u0644\u062a\u0641\u0631\u0645 \u062c\u0627\u0645\u0639',
                'show_hero_image': False,
            },
            {
                'page': 'pricing',
                'title_tr': 'Isletmenize Uygun Plan Secin',
                'title_en': 'Choose the Right Plan for Your Business',
                'title_ar': '\u0627\u062e\u062a\u0631 \u0627\u0644\u062e\u0637\u0629 \u0627\u0644\u0645\u0646\u0627\u0633\u0628\u0629 \u0644\u0639\u0645\u0644\u0643',
                'title_ru': '\u041e\u0431\u0435\u0440\u0456\u0442\u044c \u043f\u043b\u0430\u043d, \u0449\u043e \u043f\u0456\u0434\u0445\u043e\u0434\u0438\u0442\u044c \u0432\u0430\u0448\u043e\u043c\u0443 \u0431\u0456\u0437\u043d\u0435\u0441\u0443',
                'title_de': '\u067e\u0644\u0646 \u0645\u0646\u0627\u0633\u0628 \u06a9\u0633\u0628\u200c\u0648\u06a9\u0627\u0631 \u062e\u0648\u062f \u0631\u0627 \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646\u06cc\u062f',
                'subtitle_tr': 'Ucretsiz baslayin, buyudukce yukseltin. Tum planlar 14 gun ucretsiz deneme ile baslar.',
                'subtitle_en': 'Start free, upgrade as you grow. All plans come with a 14-day free trial.',
                'subtitle_ar': '\u0627\u0628\u062f\u0623 \u0645\u062c\u0627\u0646\u0627\u064b\u060c \u0642\u0645 \u0628\u0627\u0644\u062a\u0631\u0642\u064a\u0629 \u0645\u0639 \u0646\u0645\u0648\u0651\u0643. \u062c\u0645\u064a\u0639 \u0627\u0644\u062e\u0637\u0637 \u062a\u0628\u062f\u0623 \u0628\u062a\u062c\u0631\u0628\u0629 \u0645\u062c\u0627\u0646\u064a\u0629 14 \u064a\u0648\u0645\u0627\u064b.',
                'subtitle_ru': '\u041f\u043e\u0447\u043d\u0456\u0442\u044c \u0431\u0435\u0437\u043a\u043e\u0448\u0442\u043e\u0432\u043d\u043e, \u043e\u043d\u043e\u0432\u043b\u044e\u0439\u0442\u0435 \u0437 \u0440\u043e\u0441\u0442\u043e\u043c. \u0423\u0441\u0456 \u043f\u043b\u0430\u043d\u0438 \u043c\u0430\u044e\u0442\u044c 14-\u0434\u0435\u043d\u043d\u0438\u0439 \u0431\u0435\u0437\u043a\u043e\u0448\u0442\u043e\u0432\u043d\u0438\u0439 \u043f\u0435\u0440\u0456\u043e\u0434.',
                'subtitle_de': '\u0631\u0627\u06cc\u06af\u0627\u0646 \u0634\u0631\u0648\u0639 \u06a9\u0646\u06cc\u062f\u060c \u0628\u0627 \u0631\u0634\u062f \u06a9\u0633\u0628\u200c\u0648\u06a9\u0627\u0631 \u0627\u0631\u062a\u0642\u0627 \u062f\u0647\u06cc\u062f. \u0647\u0645\u0647 \u067e\u0644\u0646\u200c\u0647\u0627 \u0628\u0627 \u06f1\u06f4 \u0631\u0648\u0632 \u062f\u0648\u0631\u0647 \u0631\u0627\u06cc\u06af\u0627\u0646 \u0622\u063a\u0627\u0632 \u0645\u06cc\u200c\u0634\u0648\u0646\u062f.',
                'badge_text_tr': 'Seffaf Fiyatlandirma',
                'badge_text_en': 'Transparent Pricing',
                'badge_text_ar': '\u062a\u0633\u0639\u064a\u0631 \u0634\u0641\u0627\u0641',
                'badge_text_ru': '\u041f\u0440\u043e\u0437\u043e\u0440\u0435 \u0446\u0456\u043d\u043e\u0443\u0442\u0432\u043e\u0440\u0435\u043d\u043d\u044f',
                'badge_text_de': '\u0642\u06cc\u0645\u062a\u200c\u06af\u0630\u0627\u0631\u06cc \u0634\u0641\u0627\u0641',
                'show_hero_image': False,
            },
            {
                'page': 'about',
                'title_tr': 'E-Menum\'u Yakindan Taniyin',
                'title_en': 'Get to Know E-Menum',
                'title_ar': '\u062a\u0639\u0631\u0641 \u0639\u0644\u0649 E-Menum \u0639\u0646 \u0642\u0631\u0628',
                'title_ru': '\u041f\u0456\u0437\u043d\u0430\u0439\u0442\u0435 E-Menum \u0431\u043b\u0438\u0436\u0447\u0435',
                'title_de': 'E-Menum \u0631\u0627 \u0628\u0647\u062a\u0631 \u0628\u0634\u0646\u0627\u0633\u06cc\u062f',
                'subtitle_tr': 'Turkiye\'nin F&B sektorunu dijitallestirme misyonuyla yola ciktik.',
                'subtitle_en': 'We set out with the mission to digitalize Turkey\'s F&B sector.',
                'subtitle_ar': '\u0627\u0646\u0637\u0644\u0642\u0646\u0627 \u0628\u0645\u0647\u0645\u0629 \u0631\u0642\u0645\u0646\u0629 \u0642\u0637\u0627\u0639 \u0627\u0644\u0623\u063a\u0630\u064a\u0629 \u0648\u0627\u0644\u0645\u0634\u0631\u0648\u0628\u0627\u062a \u0641\u064a \u062a\u0631\u0643\u064a\u0627.',
                'subtitle_ru': '\u041c\u0438 \u0440\u043e\u0437\u043f\u043e\u0447\u0430\u043b\u0438 \u0437 \u043c\u0456\u0441\u0456\u0454\u044e \u0446\u0438\u0444\u0440\u043e\u0432\u0456\u0437\u0430\u0446\u0456\u0457 F&B \u0441\u0435\u043a\u0442\u043e\u0440\u0443 \u0422\u0443\u0440\u0435\u0447\u0447\u0438\u043d\u0438.',
                'subtitle_de': '\u0645\u0627 \u0628\u0627 \u0645\u0627\u0645\u0648\u0631\u06cc\u062a \u062f\u06cc\u062c\u06cc\u062a\u0627\u0644\u06cc \u06a9\u0631\u062f\u0646 \u0635\u0646\u0639\u062a \u063a\u0630\u0627 \u0648 \u0646\u0648\u0634\u06cc\u062f\u0646\u06cc \u062a\u0631\u06a9\u06cc\u0647 \u0622\u063a\u0627\u0632 \u06a9\u0631\u062f\u06cc\u0645.',
                'badge_text_tr': 'Hakkimizda',
                'badge_text_en': 'About Us',
                'badge_text_ar': '\u0645\u0646 \u0646\u062d\u0646',
                'badge_text_ru': '\u041f\u0440\u043e \u043d\u0430\u0441',
                'badge_text_de': '\u062f\u0631\u0628\u0627\u0631\u0647 \u0645\u0627',
                'show_hero_image': False,
            },
            {
                'page': 'contact',
                'title_tr': 'Bizimle Iletisime Gecin',
                'title_en': 'Get in Touch',
                'title_ar': '\u062a\u0648\u0627\u0635\u0644 \u0645\u0639\u0646\u0627',
                'title_ru': '\u0417\u0432\'\u044f\u0436\u0456\u0442\u044c\u0441\u044f \u0437 \u043d\u0430\u043c\u0438',
                'title_de': '\u0628\u0627 \u0645\u0627 \u062f\u0631 \u062a\u0645\u0627\u0633 \u0628\u0627\u0634\u06cc\u062f',
                'subtitle_tr': 'Sorulariniz, onerileriniz veya is birligi teklifleriniz icin bize ulasin.',
                'subtitle_en': 'Reach out for questions, suggestions, or partnership inquiries.',
                'subtitle_ar': '\u062a\u0648\u0627\u0635\u0644 \u0645\u0639\u0646\u0627 \u0644\u0644\u0623\u0633\u0626\u0644\u0629 \u0623\u0648 \u0627\u0644\u0627\u0642\u062a\u0631\u0627\u062d\u0627\u062a \u0623\u0648 \u0639\u0631\u0648\u0636 \u0627\u0644\u0634\u0631\u0627\u0643\u0629.',
                'subtitle_ru': '\u0417\u0432\u0435\u0440\u0442\u0430\u0439\u0442\u0435\u0441\u044f \u0437 \u043f\u0438\u0442\u0430\u043d\u043d\u044f\u043c\u0438, \u043f\u0440\u043e\u043f\u043e\u0437\u0438\u0446\u0456\u044f\u043c\u0438 \u0447\u0438 \u043f\u0430\u0440\u0442\u043d\u0435\u0440\u0441\u0442\u0432\u043e\u043c.',
                'subtitle_de': '\u0628\u0631\u0627\u06cc \u0633\u0648\u0627\u0644\u0627\u062a\u060c \u067e\u06cc\u0634\u0646\u0647\u0627\u062f\u0627\u062a \u06cc\u0627 \u0647\u0645\u06a9\u0627\u0631\u06cc \u0628\u0627 \u0645\u0627 \u062a\u0645\u0627\u0633 \u0628\u06af\u06cc\u0631\u06cc\u062f.',
                'badge_text_tr': 'Iletisim',
                'badge_text_en': 'Contact',
                'badge_text_ar': '\u0627\u062a\u0635\u0644 \u0628\u0646\u0627',
                'badge_text_ru': '\u041a\u043e\u043d\u0442\u0430\u043a\u0442\u0438',
                'badge_text_de': '\u062a\u0645\u0627\u0633',
                'show_hero_image': False,
            },
            {
                'page': 'demo',
                'title_tr': 'Canli Demo Talep Edin',
                'title_en': 'Request a Live Demo',
                'title_ar': '\u0627\u0637\u0644\u0628 \u0639\u0631\u0636\u0627\u064b \u062a\u0648\u0636\u064a\u062d\u064a\u0627\u064b \u0645\u0628\u0627\u0634\u0631\u0627\u064b',
                'title_ru': '\u0417\u0430\u043c\u043e\u0432\u0442\u0435 \u0436\u0438\u0432\u0443 \u0434\u0435\u043c\u043e\u043d\u0441\u0442\u0440\u0430\u0446\u0456\u044e',
                'title_de': '\u062f\u0631\u062e\u0648\u0627\u0633\u062a \u062f\u0645\u0648\u06cc \u0632\u0646\u062f\u0647',
                'subtitle_tr': 'Ekibimiz size ozel bir demo ile platformumuzu tanitssin. Sektorunuze uygun cozumleri kesfedelim.',
                'subtitle_en': 'Let our team showcase the platform with a personalized demo. Discover solutions tailored to your industry.',
                'subtitle_ar': '\u062f\u0639 \u0641\u0631\u064a\u0642\u0646\u0627 \u064a\u0639\u0631\u0636 \u0644\u0643 \u0627\u0644\u0645\u0646\u0635\u0629 \u0628\u0639\u0631\u0636 \u0645\u062e\u0635\u0635. \u0627\u0643\u062a\u0634\u0641 \u0627\u0644\u062d\u0644\u0648\u0644 \u0627\u0644\u0645\u0646\u0627\u0633\u0628\u0629 \u0644\u0642\u0637\u0627\u0639\u0643.',
                'subtitle_ru': '\u041d\u0430\u0448\u0430 \u043a\u043e\u043c\u0430\u043d\u0434\u0430 \u043f\u0440\u043e\u0432\u0435\u0434\u0435 \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u044c\u043d\u0443 \u0434\u0435\u043c\u043e\u043d\u0441\u0442\u0440\u0430\u0446\u0456\u044e. \u0412\u0456\u0434\u043a\u0440\u0438\u0439\u0442\u0435 \u0440\u0456\u0448\u0435\u043d\u043d\u044f \u0434\u043b\u044f \u0432\u0430\u0448\u043e\u0457 \u0433\u0430\u043b\u0443\u0437\u0456.',
                'subtitle_de': '\u062a\u06cc\u0645 \u0645\u0627 \u067e\u0644\u062a\u0641\u0631\u0645 \u0631\u0627 \u0628\u0627 \u062f\u0645\u0648\u06cc \u0627\u062e\u062a\u0635\u0627\u0635\u06cc \u0628\u0647 \u0634\u0645\u0627 \u0645\u0639\u0631\u0641\u06cc \u0645\u06cc\u200c\u06a9\u0646\u062f. \u0631\u0627\u0647\u200c\u062d\u0644\u200c\u0647\u0627\u06cc \u0645\u0646\u0627\u0633\u0628 \u0635\u0646\u0639\u062a \u062e\u0648\u062f \u0631\u0627 \u06a9\u0634\u0641 \u06a9\u0646\u06cc\u062f.',
                'badge_text_tr': 'Ucretsiz Demo',
                'badge_text_en': 'Free Demo',
                'badge_text_ar': '\u0639\u0631\u0636 \u0645\u062c\u0627\u0646\u064a',
                'badge_text_ru': '\u0411\u0435\u0437\u043a\u043e\u0448\u0442\u043e\u0432\u043d\u0435 \u0434\u0435\u043c\u043e',
                'badge_text_de': '\u062f\u0645\u0648\u06cc \u0631\u0627\u06cc\u06af\u0627\u0646',
                'show_hero_image': False,
            },
            {
                'page': 'blog',
                'title_tr': 'Blog & Kaynaklar',
                'title_en': 'Blog & Resources',
                'title_ar': '\u0627\u0644\u0645\u062f\u0648\u0646\u0629 \u0648\u0627\u0644\u0645\u0648\u0627\u0631\u062f',
                'title_ru': '\u0411\u043b\u043e\u0433 \u0442\u0430 \u0440\u0435\u0441\u0443\u0440\u0441\u0438',
                'title_de': '\u0648\u0628\u0644\u0627\u06af \u0648 \u0645\u0646\u0627\u0628\u0639',
                'subtitle_tr': 'Dijital menu, restoran yonetimi ve F&B sektoru hakkinda guncel icerikler.',
                'subtitle_en': 'Latest content on digital menus, restaurant management, and the F&B industry.',
                'subtitle_ar': '\u0623\u062d\u062f\u062b \u0627\u0644\u0645\u062d\u062a\u0648\u064a\u0627\u062a \u062d\u0648\u0644 \u0627\u0644\u0642\u0648\u0627\u0626\u0645 \u0627\u0644\u0631\u0642\u0645\u064a\u0629 \u0648\u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u0637\u0627\u0639\u0645 \u0648\u0642\u0637\u0627\u0639 \u0627\u0644\u0623\u063a\u0630\u064a\u0629.',
                'subtitle_ru': '\u0410\u043a\u0442\u0443\u0430\u043b\u044c\u043d\u0456 \u043c\u0430\u0442\u0435\u0440\u0456\u0430\u043b\u0438 \u043f\u0440\u043e \u0446\u0438\u0444\u0440\u043e\u0432\u0456 \u043c\u0435\u043d\u044e, \u0443\u043f\u0440\u0430\u0432\u043b\u0456\u043d\u043d\u044f \u0440\u0435\u0441\u0442\u043e\u0440\u0430\u043d\u0430\u043c\u0438 \u0442\u0430 F&B \u0441\u0435\u043a\u0442\u043e\u0440.',
                'subtitle_de': '\u062c\u062f\u06cc\u062f\u062a\u0631\u06cc\u0646 \u0645\u0637\u0627\u0644\u0628 \u062f\u0631\u0628\u0627\u0631\u0647 \u0645\u0646\u0648\u06cc \u062f\u06cc\u062c\u06cc\u062a\u0627\u0644\u060c \u0645\u062f\u06cc\u0631\u06cc\u062a \u0631\u0633\u062a\u0648\u0631\u0627\u0646 \u0648 \u0635\u0646\u0639\u062a \u063a\u0630\u0627 \u0648 \u0646\u0648\u0634\u06cc\u062f\u0646\u06cc.',
                'badge_text_tr': 'Blog',
                'badge_text_en': 'Blog',
                'badge_text_ar': '\u0627\u0644\u0645\u062f\u0648\u0646\u0629',
                'badge_text_ru': '\u0411\u043b\u043e\u0433',
                'badge_text_de': '\u0648\u0628\u0644\u0627\u06af',
                'show_hero_image': False,
            },
        ]
        for h in heroes:
            page = h.pop('page')
            PageHero.objects.update_or_create(page=page, defaults=h)
        self.stdout.write(f'  \u2713 PageHero ({len(heroes)})')

    def _seed_home_sections(self):
        # Problem / Solution cards
        ps_cards = [
            {
                'section_type': 'problem_solution',
                'title_tr': 'Basili Menu Sorunu',
                'title_en': 'Printed Menu Problem',
                'title_ar': 'مشكلة القوائم المطبوعة',
                'title_ru': 'Проблема друкованого меню',
                'title_de': 'مشکل منوی چاپی',
                'description_tr': 'Pahali baski, guncelleme zorlugu, hijyen endisesi, analitik eksikligi.',
                'description_en': 'Expensive printing, difficulty updating, hygiene concerns, lack of analytics.',
                'description_ar': 'طباعة مكلفة، صعوبة التحديث، مخاوف النظافة، نقص التحليلات.',
                'description_ru': 'Дорогий друк, складність оновлення, гігієнічні занепокоєння, відсутність аналітики.',
                'description_de': 'چاپ گران، دشواری به‌روزرسانی، نگرانی بهداشتی، نبود تحلیل داده.',
                'icon': 'ph-x-circle',
                'color': 'red',
                'card_variant': 'problem',
                'sort_order': 1,
            },
            {
                'section_type': 'problem_solution',
                'title_tr': 'QR Menu Cozumu',
                'title_en': 'QR Menu Solution',
                'title_ar': 'حل قائمة QR',
                'title_ru': 'Рішення QR-меню',
                'title_de': 'راه‌حل منوی QR',
                'description_tr': 'Aninda guncelleme, sifir maliyet, temassiz deneyim, kolay yonetim.',
                'description_en': 'Instant updates, zero cost, contactless experience, easy management.',
                'description_ar': 'تحديث فوري، تكلفة صفرية، تجربة بدون تلامس، إدارة سهلة.',
                'description_ru': 'Миттєве оновлення, нульова вартість, безконтактний досвід, легке управління.',
                'description_de': 'به‌روزرسانی آنی، هزینه صفر، تجربه بدون تماس، مدیریت آسان.',
                'icon': 'ph-qr-code',
                'color': 'primary',
                'card_variant': 'solution',
                'sort_order': 2,
            },
            {
                'section_type': 'problem_solution',
                'title_tr': 'AI Destekli Fark',
                'title_en': 'AI-Powered Difference',
                'title_ar': 'الفرق المدعوم بالذكاء الاصطناعي',
                'title_ru': 'Різниця завдяки ШІ',
                'title_de': 'تفاوت مبتنی بر هوش مصنوعی',
                'description_tr': 'Otomatik icerik, akilli tahminler, veri odakli optimizasyon.',
                'description_en': 'Automatic content, smart predictions, data-driven optimization.',
                'description_ar': 'محتوى تلقائي، تنبؤات ذكية، تحسين مبني على البيانات.',
                'description_ru': 'Автоматичний контент, розумні прогнози, оптимізація на основі даних.',
                'description_de': 'محتوای خودکار، پیش‌بینی‌های هوشمند، بهینه‌سازی داده‌محور.',
                'icon': 'ph-brain',
                'color': 'green',
                'card_variant': 'differentiator',
                'sort_order': 3,
            },
        ]

        # Feature cards
        feature_cards = [
            {
                'title_tr': 'QR Menu', 'title_en': 'QR Menu', 'title_ar': 'قائمة QR', 'title_ru': 'QR-меню', 'title_de': 'منوی QR',
                'description_tr': 'Saniyeler icinde dijital menu olusturun. QR kod ile musterilerinize sunun.',
                'description_en': 'Create a digital menu in seconds. Serve it to your customers via QR code.',
                'description_ar': 'أنشئ قائمة رقمية في ثوانٍ. قدّمها لعملائك عبر رمز QR.',
                'description_ru': 'Створіть цифрове меню за лічені секунди. Надайте його клієнтам через QR-код.',
                'description_de': 'در چند ثانیه منوی دیجیتال بسازید. با کد QR به مشتریان ارائه دهید.',
                'icon': 'ph-qr-code', 'color': 'primary', 'sort_order': 1,
            },
            {
                'title_tr': 'Siparis Yonetimi', 'title_en': 'Order Management', 'title_ar': 'إدارة الطلبات', 'title_ru': 'Управління замовленнями', 'title_de': 'مدیریت سفارش',
                'description_tr': 'Online siparis alin, masa takibi yapin, mutfaga aninda bildirin.',
                'description_en': 'Take online orders, track tables, instantly notify the kitchen.',
                'description_ar': 'استقبل الطلبات عبر الإنترنت، تتبع الطاولات، أبلغ المطبخ فوراً.',
                'description_ru': 'Приймайте онлайн-замовлення, відстежуйте столики, миттєво повідомляйте кухню.',
                'description_de': 'سفارش آنلاین بگیرید، میزها را پیگیری کنید، فوراً به آشپزخانه اطلاع دهید.',
                'icon': 'ph-shopping-cart', 'color': 'green', 'sort_order': 2,
            },
            {
                'title_tr': 'AI Icerik Uretimi', 'title_en': 'AI Content Generation', 'title_ar': 'إنشاء المحتوى بالذكاء الاصطناعي', 'title_ru': 'Генерація контенту ШІ', 'title_de': 'تولید محتوا با هوش مصنوعی',
                'description_tr': 'Yapay zeka ile urun aciklamalari, etiketler ve icerik otomatik olusturulur.',
                'description_en': 'Product descriptions, tags and content are automatically generated with AI.',
                'description_ar': 'يتم إنشاء أوصاف المنتجات والعلامات والمحتوى تلقائياً بالذكاء الاصطناعي.',
                'description_ru': 'Описи продуктів, теги та контент автоматично створюються за допомогою ШІ.',
                'description_de': 'توضیحات محصول، برچسب‌ها و محتوا به‌صورت خودکار با هوش مصنوعی ساخته می‌شوند.',
                'icon': 'ph-brain', 'color': 'purple', 'sort_order': 3,
            },
            {
                'title_tr': 'Analitik Dashboard', 'title_en': 'Analytics Dashboard', 'title_ar': 'لوحة التحليلات', 'title_ru': 'Аналітична панель', 'title_de': 'داشبورد تحلیلی',
                'description_tr': 'Satis trendleri, populer urunler, musteri davranislari — veriye dayali kararlar.',
                'description_en': 'Sales trends, popular products, customer behavior — data-driven decisions.',
                'description_ar': 'اتجاهات المبيعات، المنتجات الشائعة، سلوك العملاء — قرارات مبنية على البيانات.',
                'description_ru': 'Тренди продажів, популярні продукти, поведінка клієнтів — рішення на основі даних.',
                'description_de': 'روندهای فروش، محصولات محبوب، رفتار مشتری — تصمیم‌های داده‌محور.',
                'icon': 'ph-chart-line-up', 'color': 'amber', 'sort_order': 4,
            },
            {
                'title_tr': 'Coklu Sube', 'title_en': 'Multi-Branch', 'title_ar': 'فروع متعددة', 'title_ru': 'Багато філій', 'title_de': 'چند شعبه‌ای',
                'description_tr': 'Tum subelerinizi tek panelden yonetin. Menu degisiklikleri aninda yansir.',
                'description_en': 'Manage all your branches from a single panel. Menu changes are reflected instantly.',
                'description_ar': 'أدر جميع فروعك من لوحة واحدة. تنعكس تغييرات القائمة فوراً.',
                'description_ru': 'Керуйте всіма філіями з однієї панелі. Зміни меню відображаються миттєво.',
                'description_de': 'همه شعب خود را از یک پنل مدیریت کنید. تغییرات منو فوراً اعمال می‌شوند.',
                'icon': 'ph-buildings', 'color': 'rose', 'sort_order': 5,
            },
            {
                'title_tr': 'Tema Motoru', 'title_en': 'Theme Engine', 'title_ar': 'محرك السمات', 'title_ru': 'Двигун тем', 'title_de': 'موتور قالب',
                'description_tr': 'Markaniza uygun tasarim. Renkler, fontlar, gorunumler tamamen ozellestirilebilir.',
                'description_en': 'Design matching your brand. Colors, fonts, and layouts are fully customizable.',
                'description_ar': 'تصميم يتناسب مع علامتك التجارية. الألوان والخطوط والتخطيطات قابلة للتخصيص بالكامل.',
                'description_ru': 'Дизайн відповідно до вашого бренду. Кольори, шрифти та макети повністю налаштовуються.',
                'description_de': 'طراحی متناسب با برند شما. رنگ‌ها، فونت‌ها و نماها کاملاً قابل سفارشی‌سازی هستند.',
                'icon': 'ph-paint-brush', 'color': 'cyan', 'sort_order': 6,
            },
        ]
        for fc in feature_cards:
            fc['section_type'] = 'feature_card'

        # How it works steps
        steps = [
            {
                'title_tr': 'Kayit Olun', 'title_en': 'Sign Up', 'title_ar': 'سجّل الآن', 'title_ru': 'Зареєструйтесь', 'title_de': 'ثبت‌نام کنید',
                'description_tr': 'Ucretsiz hesap olusturun. Kredi karti gerekmez, 2 dakikada hazir.',
                'description_en': 'Create a free account. No credit card required, ready in 2 minutes.',
                'description_ar': 'أنشئ حساباً مجانياً. لا حاجة لبطاقة ائتمان، جاهز خلال دقيقتين.',
                'description_ru': 'Створіть безкоштовний обліковий запис. Кредитна картка не потрібна, готово за 2 хвилини.',
                'description_de': 'یک حساب رایگان بسازید. بدون نیاز به کارت اعتباری، در ۲ دقیقه آماده.',
                'step_number': 1, 'sort_order': 1,
            },
            {
                'title_tr': 'Menunuzu Olusturun', 'title_en': 'Create Your Menu', 'title_ar': 'أنشئ قائمتك', 'title_ru': 'Створіть своє меню', 'title_de': 'منوی خود را بسازید',
                'description_tr': 'Kategori ve urunlerinizi ekleyin. AI ile aciklamalari otomatik olusturun.',
                'description_en': 'Add your categories and products. Automatically generate descriptions with AI.',
                'description_ar': 'أضف فئاتك ومنتجاتك. أنشئ الأوصاف تلقائياً بالذكاء الاصطناعي.',
                'description_ru': 'Додайте категорії та продукти. Автоматично створюйте описи за допомогою ШІ.',
                'description_de': 'دسته‌بندی‌ها و محصولات خود را اضافه کنید. توضیحات را با هوش مصنوعی خودکار بسازید.',
                'step_number': 2, 'sort_order': 2,
            },
            {
                'title_tr': 'QR Kodu Paylasin', 'title_en': 'Share Your QR Code', 'title_ar': 'شارك رمز QR', 'title_ru': 'Поділіться QR-кодом', 'title_de': 'کد QR را به اشتراک بگذارید',
                'description_tr': 'QR kodunuzu masalara yerlestirin. Musteriler telefonlarinda menuyu goruntulesin.',
                'description_en': 'Place your QR code on tables. Customers can view the menu on their phones.',
                'description_ar': 'ضع رمز QR على الطاولات. يمكن للعملاء عرض القائمة على هواتفهم.',
                'description_ru': 'Розмістіть QR-код на столиках. Клієнти зможуть переглядати меню на своїх телефонах.',
                'description_de': 'کد QR را روی میزها قرار دهید. مشتریان منو را روی گوشی خود مشاهده می‌کنند.',
                'step_number': 3, 'sort_order': 3,
            },
        ]
        for s in steps:
            s['section_type'] = 'how_it_works'

        # Stat counters
        stats = [
            {
                'title_tr': 'Hedef Pazar', 'title_en': 'Target Market', 'title_ar': 'السوق المستهدف', 'title_ru': 'Цільовий ринок', 'title_de': 'بازار هدف',
                'description_tr': '', 'description_en': '', 'description_ar': '', 'description_ru': '', 'description_de': '',
                'stat_value': '350.000+', 'stat_suffix': '', 'icon': 'ph-storefront', 'sort_order': 1,
            },
            {
                'title_tr': 'Ozellik', 'title_en': 'Features', 'title_ar': 'الميزات', 'title_ru': 'Функції', 'title_de': 'ویژگی‌ها',
                'description_tr': '', 'description_en': '', 'description_ar': '', 'description_ru': '', 'description_de': '',
                'stat_value': '50+', 'stat_suffix': '', 'icon': 'ph-star', 'sort_order': 2,
            },
            {
                'title_tr': 'Uptime', 'title_en': 'Uptime', 'title_ar': 'وقت التشغيل', 'title_ru': 'Час роботи', 'title_de': 'آپتایم',
                'description_tr': '', 'description_en': '', 'description_ar': '', 'description_ru': '', 'description_de': '',
                'stat_value': '99.9', 'stat_suffix': '%', 'icon': 'ph-cloud-check', 'sort_order': 3,
            },
            {
                'title_tr': 'Destek', 'title_en': 'Support', 'title_ar': 'الدعم', 'title_ru': 'Підтримка', 'title_de': 'پشتیبانی',
                'description_tr': '', 'description_en': '', 'description_ar': '', 'description_ru': '', 'description_de': '',
                'stat_value': '7/24', 'stat_suffix': '', 'icon': 'ph-headset', 'sort_order': 4,
            },
        ]
        for st in stats:
            st['section_type'] = 'stat_counter'

        all_sections = ps_cards + feature_cards + steps + stats
        for section_data in all_sections:
            section_type = section_data['section_type']
            HomeSection.objects.update_or_create(
                section_type=section_type,
                sort_order=section_data['sort_order'],
                defaults=section_data,
            )
        self.stdout.write(f'  \u2713 HomeSection ({len(all_sections)})')

    def _seed_feature_categories(self):
        categories = [
            {
                'title_tr': 'Menu Yonetimi',
                'title_en': 'Menu Management',
                'title_ar': 'إدارة القائمة',
                'title_ru': 'Управління меню',
                'title_de': 'مدیریت منو',
                'description_tr': 'Dijital menunuzu kolayca olusturun ve yonetin.',
                'description_en': 'Create and manage your digital menu with ease.',
                'description_ar': 'أنشئ قائمتك الرقمية وأدرها بسهولة.',
                'description_ru': 'Легко створюйте та керуйте своїм цифровим меню.',
                'description_de': 'منوی دیجیتال خود را به‌راحتی بسازید و مدیریت کنید.',
                'badge_text_tr': 'Menu',
                'badge_text_en': 'Menu',
                'badge_text_ar': 'القائمة',
                'badge_text_ru': 'Меню',
                'badge_text_de': 'منو',
                'badge_color': 'primary',
                'icon': 'ph-fork-knife',
                'layout_reversed': False,
                'sort_order': 1,
                'bullets': [
                    {
                        'text_tr': 'Surukleme-birakma menu duzenleyici',
                        'text_en': 'Drag-and-drop menu editor',
                        'text_ar': 'محرر قوائم بالسحب والإفلات',
                        'text_ru': 'Редактор меню з перетягуванням',
                        'text_de': 'ویرایشگر منو با کشیدن و رها کردن',
                    },
                    {
                        'text_tr': 'Urun varyantlari ve eklentiler',
                        'text_en': 'Product variants and add-ons',
                        'text_ar': 'متغيرات المنتج والإضافات',
                        'text_ru': 'Варіанти продуктів та додатки',
                        'text_de': 'انواع محصول و افزودنی‌ها',
                    },
                    {
                        'text_tr': 'Alerjen ve besin bilgisi yonetimi',
                        'text_en': 'Allergen and nutrition info management',
                        'text_ar': 'إدارة معلومات المواد المسببة للحساسية والتغذية',
                        'text_ru': 'Управління алергенами та харчовою цінністю',
                        'text_de': 'مدیریت اطلاعات آلرژن‌ها و تغذیه',
                    },
                    {
                        'text_tr': 'QR kod olusturma ve yonetim',
                        'text_en': 'QR code generation and management',
                        'text_ar': 'إنشاء وإدارة رموز QR',
                        'text_ru': 'Створення та управління QR-кодами',
                        'text_de': 'ایجاد و مدیریت کدهای QR',
                    },
                ],
            },
            {
                'title_tr': 'Siparis Yonetimi',
                'title_en': 'Order Management',
                'title_ar': 'إدارة الطلبات',
                'title_ru': 'Управління замовленнями',
                'title_de': 'مدیریت سفارشات',
                'description_tr': 'Siparisleri canli takip edin, masalari yonetin.',
                'description_en': 'Track orders live and manage your tables.',
                'description_ar': 'تتبع الطلبات مباشرة وأدر طاولاتك.',
                'description_ru': 'Відстежуйте замовлення в реальному часі та керуйте столиками.',
                'description_de': 'سفارشات را به‌صورت زنده پیگیری و میزها را مدیریت کنید.',
                'badge_text_tr': 'Siparis',
                'badge_text_en': 'Orders',
                'badge_text_ar': 'الطلبات',
                'badge_text_ru': 'Замовлення',
                'badge_text_de': 'سفارشات',
                'badge_color': 'green',
                'icon': 'ph-shopping-cart',
                'layout_reversed': True,
                'sort_order': 2,
                'bullets': [
                    {
                        'text_tr': 'Canli siparis takibi',
                        'text_en': 'Live order tracking',
                        'text_ar': 'تتبع الطلبات مباشرة',
                        'text_ru': 'Відстеження замовлень у реальному часі',
                        'text_de': 'پیگیری زنده سفارشات',
                    },
                    {
                        'text_tr': 'Masa ve bolge yonetimi',
                        'text_en': 'Table and zone management',
                        'text_ar': 'إدارة الطاولات والمناطق',
                        'text_ru': 'Управління столиками та зонами',
                        'text_de': 'مدیریت میز و بخش‌ها',
                    },
                    {
                        'text_tr': 'Mutfak entegrasyonu',
                        'text_en': 'Kitchen integration',
                        'text_ar': 'تكامل المطبخ',
                        'text_ru': 'Інтеграція з кухнею',
                        'text_de': 'یکپارچه‌سازی با آشپزخانه',
                    },
                    {
                        'text_tr': 'Siparis gecmisi ve raporlar',
                        'text_en': 'Order history and reports',
                        'text_ar': 'سجل الطلبات والتقارير',
                        'text_ru': 'Історія замовлень та звіти',
                        'text_de': 'تاریخچه سفارشات و گزارش‌ها',
                    },
                ],
            },
            {
                'title_tr': 'AI Icerik Uretimi',
                'title_en': 'AI Content Generation',
                'title_ar': 'إنشاء المحتوى بالذكاء الاصطناعي',
                'title_ru': 'Генерація контенту за допомогою ШІ',
                'title_de': 'تولید محتوا با هوش مصنوعی',
                'description_tr': 'Yapay zeka ile icerik olusturma ve optimizasyon.',
                'description_en': 'Create and optimize content with artificial intelligence.',
                'description_ar': 'إنشاء المحتوى وتحسينه باستخدام الذكاء الاصطناعي.',
                'description_ru': 'Створення та оптимізація контенту за допомогою штучного інтелекту.',
                'description_de': 'ایجاد و بهینه‌سازی محتوا با هوش مصنوعی.',
                'badge_text_tr': 'AI',
                'badge_text_en': 'AI',
                'badge_text_ar': 'AI',
                'badge_text_ru': 'AI',
                'badge_text_de': 'AI',
                'badge_color': 'purple',
                'icon': 'ph-brain',
                'layout_reversed': False,
                'sort_order': 3,
                'bullets': [
                    {
                        'text_tr': 'Otomatik urun aciklamalari',
                        'text_en': 'Automatic product descriptions',
                        'text_ar': 'أوصاف المنتجات التلقائية',
                        'text_ru': 'Автоматичні описи продуктів',
                        'text_de': 'توضیحات خودکار محصول',
                    },
                    {
                        'text_tr': 'Akilli etiketleme ve kategorileme',
                        'text_en': 'Smart tagging and categorization',
                        'text_ar': 'التصنيف والوسم الذكي',
                        'text_ru': 'Розумне тегування та категоризація',
                        'text_de': 'برچسب‌گذاری و دسته‌بندی هوشمند',
                    },
                    {
                        'text_tr': 'Coklu dil destegi',
                        'text_en': 'Multi-language support',
                        'text_ar': 'دعم متعدد اللغات',
                        'text_ru': 'Підтримка багатьох мов',
                        'text_de': 'پشتیبانی از چند زبان',
                    },
                    {
                        'text_tr': 'SEO optimizasyonu',
                        'text_en': 'SEO optimization',
                        'text_ar': 'تحسين محركات البحث',
                        'text_ru': 'SEO-оптимізація',
                        'text_de': 'بهینه‌سازی سئو',
                    },
                ],
            },
            {
                'title_tr': 'Analitik & Raporlama',
                'title_en': 'Analytics & Reporting',
                'title_ar': 'التحليلات والتقارير',
                'title_ru': 'Аналітика та звітність',
                'title_de': 'تحلیل و گزارش‌دهی',
                'description_tr': 'Veriye dayali kararlar alin, isletmenizi optimize edin.',
                'description_en': 'Make data-driven decisions and optimize your business.',
                'description_ar': 'اتخذ قرارات مبنية على البيانات وحسّن أعمالك.',
                'description_ru': 'Приймайте рішення на основі даних та оптимізуйте свій бізнес.',
                'description_de': 'تصمیمات مبتنی بر داده بگیرید و کسب‌وکارتان را بهینه کنید.',
                'badge_text_tr': 'Analitik',
                'badge_text_en': 'Analytics',
                'badge_text_ar': 'التحليلات',
                'badge_text_ru': 'Аналітика',
                'badge_text_de': 'تحلیل‌ها',
                'badge_color': 'amber',
                'icon': 'ph-chart-line-up',
                'layout_reversed': True,
                'sort_order': 4,
                'bullets': [
                    {
                        'text_tr': 'Canli satis dashboard\'u',
                        'text_en': 'Live sales dashboard',
                        'text_ar': 'لوحة المبيعات المباشرة',
                        'text_ru': 'Панель продажів у реальному часі',
                        'text_de': 'داشبورد فروش زنده',
                    },
                    {
                        'text_tr': 'Satis raporlari ve trendler',
                        'text_en': 'Sales reports and trends',
                        'text_ar': 'تقارير المبيعات والاتجاهات',
                        'text_ru': 'Звіти про продажі та тренди',
                        'text_de': 'گزارش‌های فروش و روندها',
                    },
                    {
                        'text_tr': 'Musteri davranis analizi',
                        'text_en': 'Customer behavior analysis',
                        'text_ar': 'تحليل سلوك العملاء',
                        'text_ru': 'Аналіз поведінки клієнтів',
                        'text_de': 'تحلیل رفتار مشتریان',
                    },
                    {
                        'text_tr': 'Tahminleme ve oneriler',
                        'text_en': 'Forecasting and recommendations',
                        'text_ar': 'التنبؤات والتوصيات',
                        'text_ru': 'Прогнозування та рекомендації',
                        'text_de': 'پیش‌بینی و پیشنهادات',
                    },
                ],
            },
        ]
        for cat_data in categories:
            bullets_data = cat_data.pop('bullets')
            cat, _ = FeatureCategory.objects.update_or_create(
                title_tr=cat_data['title_tr'],
                defaults=cat_data,
            )
            for i, bullet_data in enumerate(bullets_data):
                FeatureBullet.objects.update_or_create(
                    category=cat,
                    text_tr=bullet_data['text_tr'],
                    defaults={**bullet_data, 'sort_order': i + 1, 'is_active': True},
                )
        self.stdout.write(f'  \u2713 FeatureCategory ({len(categories)}) + FeatureBullet')

    def _seed_testimonials(self):
        testimonials = [
            {
                'author_name_tr': 'Ayse Yilmaz',
                'author_name_en': 'Ayse Yilmaz',
                'author_name_ar': 'عائشة يلماز',
                'author_name_ru': 'Айше Їлмаз',
                'author_name_de': 'عایشه ییلماز',
                'initials': 'AY',
                'author_role_or_business_tr': 'Lezzet Duragi Restoran',
                'author_role_or_business_en': 'Lezzet Duragi Restaurant',
                'author_role_or_business_ar': 'مطعم لذت دوراغي',
                'author_role_or_business_ru': 'Ресторан Lezzet Duragi',
                'author_role_or_business_de': 'رستوران لذت دوراغی',
                'author_location_tr': 'Istanbul',
                'author_location_en': 'Istanbul',
                'author_location_ar': 'إسطنبول',
                'author_location_ru': 'Стамбул',
                'author_location_de': 'استانبول',
                'business_type_label_tr': 'Restoran',
                'business_type_label_en': 'Restaurant',
                'business_type_label_ar': 'مطعم',
                'business_type_label_ru': 'Ресторан',
                'business_type_label_de': 'رستوران',
                'badge_color': 'primary',
                'avatar_color': 'primary',
                'quote_tr': 'E-Menum sayesinde menumuzu aninda guncelleyebiliyoruz. Musterilerimiz QR kodu okutup hemen siparis verebiliyor. Basili menu maliyetimiz sifira indi!',
                'quote_en': 'Thanks to E-Menum, we can update our menu instantly. Our customers scan the QR code and place orders right away. Our printed menu costs dropped to zero!',
                'quote_ar': 'بفضل E-Menum، يمكننا تحديث قائمتنا فوراً. يمسح عملاؤنا رمز QR ويطلبون على الفور. انخفضت تكاليف القوائم المطبوعة لدينا إلى الصفر!',
                'quote_ru': 'Завдяки E-Menum ми можемо миттєво оновлювати наше меню. Клієнти сканують QR-код і одразу замовляють. Витрати на друковане меню впали до нуля!',
                'quote_de': 'به لطف E-Menum، می‌توانیم منوی خود را فوراً به‌روزرسانی کنیم. مشتریان ما کد QR را اسکن می‌کنند و بلافاصله سفارش می‌دهند. هزینه منوی چاپی ما به صفر رسید!',
                'rating': 5,
                'sort_order': 1,
            },
            {
                'author_name_tr': 'Fatih Kaya',
                'author_name_en': 'Fatih Kaya',
                'author_name_ar': 'فاتح كايا',
                'author_name_ru': 'Фатіх Кая',
                'author_name_de': 'فاتح کایا',
                'initials': 'FK',
                'author_role_or_business_tr': 'Kahve Dunyasi',
                'author_role_or_business_en': 'Kahve Dunyasi',
                'author_role_or_business_ar': 'عالم القهوة',
                'author_role_or_business_ru': 'Kahve Dunyasi',
                'author_role_or_business_de': 'دنیای قهوه',
                'author_location_tr': 'Ankara',
                'author_location_en': 'Ankara',
                'author_location_ar': 'أنقرة',
                'author_location_ru': 'Анкара',
                'author_location_de': 'آنکارا',
                'business_type_label_tr': 'Kafe',
                'business_type_label_en': 'Cafe',
                'business_type_label_ar': 'مقهى',
                'business_type_label_ru': 'Кафе',
                'business_type_label_de': 'کافه',
                'badge_color': 'green',
                'avatar_color': 'green',
                'quote_tr': 'AI ile urun aciklamalarini otomatik olusturmak muhtesem. Aylik 50+ urun ekliyoruz, artik dakikalar icinde hazir.',
                'quote_en': 'Automatically generating product descriptions with AI is amazing. We add 50+ products monthly, and they are ready in minutes now.',
                'quote_ar': 'إنشاء أوصاف المنتجات تلقائياً بالذكاء الاصطناعي أمر مذهل. نضيف أكثر من 50 منتجاً شهرياً، وأصبحت جاهزة في دقائق.',
                'quote_ru': 'Автоматичне створення описів продуктів за допомогою ШІ -- це чудово. Ми додаємо 50+ продуктів щомісяця, і тепер вони готові за лічені хвилини.',
                'quote_de': 'تولید خودکار توضیحات محصول با هوش مصنوعی فوق‌العاده است. ماهانه بیش از ۵۰ محصول اضافه می‌کنیم و حالا در عرض چند دقیقه آماده می‌شوند.',
                'rating': 5,
                'sort_order': 2,
            },
            {
                'author_name_tr': 'Mehmet Ozturk',
                'author_name_en': 'Mehmet Ozturk',
                'author_name_ar': 'محمد أوزتورك',
                'author_name_ru': 'Мехмет Озтюрк',
                'author_name_de': 'محمت اوزتورک',
                'initials': 'MO',
                'author_role_or_business_tr': 'Zincir Isletme (12 Sube)',
                'author_role_or_business_en': 'Chain Business (12 Branches)',
                'author_role_or_business_ar': 'سلسلة أعمال (12 فرعاً)',
                'author_role_or_business_ru': 'Мережевий бізнес (12 філій)',
                'author_role_or_business_de': 'کسب‌وکار زنجیره‌ای (۱۲ شعبه)',
                'author_location_tr': 'Izmir',
                'author_location_en': 'Izmir',
                'author_location_ar': 'إزمير',
                'author_location_ru': 'Ізмір',
                'author_location_de': 'ازمیر',
                'business_type_label_tr': 'Zincir Isletme',
                'business_type_label_en': 'Chain Business',
                'business_type_label_ar': 'سلسلة أعمال',
                'business_type_label_ru': 'Мережевий бізнес',
                'business_type_label_de': 'کسب‌وکار زنجیره‌ای',
                'badge_color': 'purple',
                'avatar_color': 'purple',
                'quote_tr': 'Coklu sube yonetimi harika calisiyor. Tek panelden 12 subenin menusunu yonetebiliyorum. Analitik raporlar da cok faydali.',
                'quote_en': 'Multi-branch management works wonderfully. I can manage menus for 12 branches from a single panel. The analytics reports are also very useful.',
                'quote_ar': 'إدارة الفروع المتعددة تعمل بشكل رائع. يمكنني إدارة قوائم 12 فرعاً من لوحة واحدة. التقارير التحليلية مفيدة جداً أيضاً.',
                'quote_ru': 'Управління кількома філіями працює чудово. Я можу керувати меню 12 філій з однієї панелі. Аналітичні звіти також дуже корисні.',
                'quote_de': 'مدیریت چند شعبه‌ای عالی کار می‌کند. می‌توانم منوی ۱۲ شعبه را از یک پنل مدیریت کنم. گزارش‌های تحلیلی هم بسیار مفید هستند.',
                'rating': 5,
                'sort_order': 3,
            },
        ]
        for t in testimonials:
            Testimonial.objects.update_or_create(
                author_name_tr=t['author_name_tr'],
                defaults=t,
            )
        self.stdout.write(f'  \u2713 Testimonial ({len(testimonials)})')

    def _seed_trust_badges(self):
        badges = [
            {
                'label_tr': 'KVKK Uyumlu',
                'label_en': 'KVKK Compliant',
                'label_ar': 'متوافق مع KVKK',
                'label_ru': 'Відповідає KVKK',
                'label_de': 'سازگار با KVKK',
                'icon': 'ph-shield-check',
                'sort_order': 1,
            },
            {
                'label_tr': 'SSL Sifreleme',
                'label_en': 'SSL Encryption',
                'label_ar': 'تشفير SSL',
                'label_ru': 'SSL шифрування',
                'label_de': 'رمزنگاری SSL',
                'icon': 'ph-lock',
                'sort_order': 2,
            },
            {
                'label_tr': '99.9% Uptime',
                'label_en': '99.9% Uptime',
                'label_ar': '99.9% وقت التشغيل',
                'label_ru': '99.9% Час роботи',
                'label_de': '99.9% آپتایم',
                'icon': 'ph-cloud-check',
                'sort_order': 3,
            },
            {
                'label_tr': '7/24 Destek',
                'label_en': '24/7 Support',
                'label_ar': 'دعم 24/7',
                'label_ru': 'Підтримка 24/7',
                'label_de': 'پشتیبانی ۲۴/۷',
                'icon': 'ph-headset',
                'sort_order': 4,
            },
        ]
        for b in badges:
            TrustBadge.objects.update_or_create(label_tr=b['label_tr'], defaults=b)
        self.stdout.write(f'  \u2713 TrustBadge ({len(badges)})')

    def _seed_trust_locations(self):
        locations = [
            {
                'text_tr': "Istanbul'dan 47 isletme",
                'text_en': '47 businesses from Istanbul',
                'text_ar': '47 منشأة من إسطنبول',
                'text_ru': '47 закладів зі Стамбула',
                'text_de': '47 کسب‌وکار از استانبول',
                'sort_order': 1,
            },
            {
                'text_tr': "Ankara'dan 23 isletme",
                'text_en': '23 businesses from Ankara',
                'text_ar': '23 منشأة من أنقرة',
                'text_ru': '23 заклади з Анкари',
                'text_de': '23 کسب‌وکار از آنکارا',
                'sort_order': 2,
            },
            {
                'text_tr': "Izmir'den 18 isletme",
                'text_en': '18 businesses from Izmir',
                'text_ar': '18 منشأة من إزمير',
                'text_ru': '18 закладів з Ізміра',
                'text_de': '18 کسب‌وکار از ازمیر',
                'sort_order': 3,
            },
            {
                'text_tr': 've daha fazlasi...',
                'text_en': 'and more...',
                'text_ar': 'والمزيد...',
                'text_ru': 'та багато інших...',
                'text_de': 'و بیشتر...',
                'sort_order': 4,
            },
        ]
        for loc in locations:
            TrustLocation.objects.update_or_create(text_tr=loc['text_tr'], defaults=loc)
        self.stdout.write(f'  \u2713 TrustLocation ({len(locations)})')

    def _seed_faqs(self):
        faqs = [
            {
                'question_tr': 'E-Menum nedir?',
                'question_en': 'What is E-Menum?',
                'question_ar': 'ما هو E-Menum؟',
                'question_ru': 'Що таке E-Menum?',
                'question_de': 'E-Menum چیست؟',
                'answer_tr': 'E-Menum, restoran ve kafeler icin yapay zeka destekli dijital menu platformudur. QR menu olusturma, siparis yonetimi, analitik ve AI icerik uretimi gibi 50+ ozellik sunar.',
                'answer_en': 'E-Menum is an AI-powered digital menu platform for restaurants and cafes. It offers 50+ features including QR menu creation, order management, analytics and AI content generation.',
                'answer_ar': 'E-Menum هي منصة قوائم رقمية مدعومة بالذكاء الاصطناعي للمطاعم والمقاهي. تقدم أكثر من 50 ميزة تشمل إنشاء قوائم QR، وإدارة الطلبات، والتحليلات، وإنشاء المحتوى بالذكاء الاصطناعي.',
                'answer_ru': 'E-Menum -- це платформа цифрового меню на основі ШІ для ресторанів та кафе. Вона пропонує 50+ функцій, включаючи створення QR-меню, управління замовленнями, аналітику та генерацію контенту за допомогою ШІ.',
                'answer_de': 'E-Menum یک پلتفرم منوی دیجیتال مبتنی بر هوش مصنوعی برای رستوران‌ها و کافه‌ها است. بیش از ۵۰ ویژگی از جمله ساخت منوی QR، مدیریت سفارشات، تحلیل داده‌ها و تولید محتوا با هوش مصنوعی ارائه می‌دهد.',
                'page': 'both',
                'sort_order': 1,
            },
            {
                'question_tr': 'Ucretsiz deneme suresi ne kadar?',
                'question_en': 'How long is the free trial?',
                'question_ar': 'ما مدة الفترة التجريبية المجانية؟',
                'question_ru': 'Яка тривалість безкоштовного пробного періоду?',
                'question_de': 'مدت دوره آزمایشی رایگان چقدر است؟',
                'answer_tr': 'Tum ucretli planlarimiz 14 gun ucretsiz deneme ile baslar. Deneme suresi boyunca tum ozelliklere erisebilirsiniz. Kredi karti bilgisi gerekmez.',
                'answer_en': 'All our paid plans start with a 14-day free trial. You can access all features during the trial period. No credit card required.',
                'answer_ar': 'تبدأ جميع خططنا المدفوعة بفترة تجريبية مجانية لمدة 14 يوماً. يمكنك الوصول إلى جميع الميزات خلال الفترة التجريبية. لا حاجة لبطاقة ائتمان.',
                'answer_ru': 'Усі наші платні плани починаються з 14-денного безкоштовного пробного періоду. Ви маєте доступ до всіх функцій протягом пробного періоду. Кредитна картка не потрібна.',
                'answer_de': 'تمام پلن‌های پولی ما با ۱۴ روز دوره آزمایشی رایگان شروع می‌شوند. در طول دوره آزمایشی به تمام امکانات دسترسی خواهید داشت. نیازی به کارت اعتباری نیست.',
                'page': 'pricing',
                'sort_order': 2,
            },
            {
                'question_tr': 'Plan degisikligi yapabilir miyim?',
                'question_en': 'Can I change my plan?',
                'question_ar': 'هل يمكنني تغيير خطتي؟',
                'question_ru': 'Чи можу я змінити свій план?',
                'question_de': 'آیا می‌توانم پلن خود را تغییر دهم؟',
                'answer_tr': 'Evet, istediginiz zaman planinizi yukseltebilir veya dusurabilirsiniz. Yukseltme aninda gecerli olur, dusurme ise mevcut fatura donemin sonunda uygulanir.',
                'answer_en': 'Yes, you can upgrade or downgrade your plan at any time. Upgrades take effect immediately, while downgrades are applied at the end of the current billing period.',
                'answer_ar': 'نعم، يمكنك ترقية أو تخفيض خطتك في أي وقت. تسري الترقيات فوراً، بينما يتم تطبيق التخفيضات في نهاية فترة الفوترة الحالية.',
                'answer_ru': 'Так, ви можете підвищити або знизити свій план у будь-який час. Підвищення набуває чинності негайно, а зниження застосовується в кінці поточного розрахункового періоду.',
                'answer_de': 'بله، می‌توانید هر زمان پلن خود را ارتقا یا کاهش دهید. ارتقا فوراً اعمال می‌شود، در حالی که کاهش در پایان دوره صورت‌حساب فعلی اجرا می‌شود.',
                'page': 'pricing',
                'sort_order': 3,
            },
            {
                'question_tr': 'Verilerim guvenli mi?',
                'question_en': 'Is my data safe?',
                'question_ar': 'هل بياناتي آمنة؟',
                'question_ru': 'Чи мої дані у безпеці?',
                'question_de': 'آیا داده‌های من امن هستند؟',
                'answer_tr': 'Evet, tum verileriniz SSL/TLS sifreleme ile korunmaktadir. KVKK uyumlu altyapimiz ve %99.9 uptime garantimiz ile verileriniz her zaman guvendedir.',
                'answer_en': 'Yes, all your data is protected with SSL/TLS encryption. With our KVKK-compliant infrastructure and 99.9% uptime guarantee, your data is always safe.',
                'answer_ar': 'نعم، جميع بياناتك محمية بتشفير SSL/TLS. مع بنيتنا التحتية المتوافقة مع KVKK وضمان وقت التشغيل بنسبة 99.9%، بياناتك آمنة دائماً.',
                'answer_ru': 'Так, усі ваші дані захищені шифруванням SSL/TLS. Завдяки нашій інфраструктурі, що відповідає вимогам KVKK, та гарантії безвідмовної роботи 99,9%, ваші дані завжди в безпеці.',
                'answer_de': 'بله، تمام داده‌های شما با رمزگذاری SSL/TLS محافظت می‌شوند. با زیرساخت سازگار با KVKK و تضمین آپتایم ۹۹.۹ درصد، داده‌های شما همیشه امن هستند.',
                'page': 'both',
                'sort_order': 4,
            },
            {
                'question_tr': 'Teknik destek nasil alabilirim?',
                'question_en': 'How can I get technical support?',
                'question_ar': 'كيف يمكنني الحصول على الدعم الفني؟',
                'question_ru': 'Як я можу отримати технічну підтримку?',
                'question_de': 'چگونه می‌توانم پشتیبانی فنی دریافت کنم؟',
                'answer_tr': '7/24 canli destek hattimiz, e-posta destegi ve kapsamli yardim merkezi ile her zaman yaninizda. Professional ve ustu planlarda oncelikli destek sunuyoruz.',
                'answer_en': 'We are always here for you with our 24/7 live support line, email support, and comprehensive help center. We offer priority support on Professional and higher plans.',
                'answer_ar': 'نحن دائماً بجانبك مع خط الدعم المباشر 24/7، ودعم البريد الإلكتروني، ومركز المساعدة الشامل. نقدم دعماً ذا أولوية في خطط Professional وما فوقها.',
                'answer_ru': 'Ми завжди поруч із нашою лінією підтримки 24/7, підтримкою електронною поштою та обширним центром допомоги. Ми пропонуємо пріоритетну підтримку для планів Professional та вище.',
                'answer_de': 'ما همیشه با خط پشتیبانی زنده ۲۴/۷، پشتیبانی ایمیلی و مرکز راهنمای جامع در کنار شما هستیم. در پلن‌های Professional و بالاتر پشتیبانی اولویت‌دار ارائه می‌دهیم.',
                'page': 'both',
                'sort_order': 5,
            },
        ]
        for faq in faqs:
            FAQ.objects.update_or_create(question_tr=faq['question_tr'], defaults=faq)
        self.stdout.write(f'  \u2713 FAQ ({len(faqs)})')

    def _seed_team_members(self):
        members = [
            {
                'name_tr': 'Ismail K.', 'name_en': 'Ismail K.', 'name_ar': 'إسماعيل ك.', 'name_ru': 'Ісмаїл К.', 'name_de': 'اسماعیل ک.',
                'initials': 'IK',
                'title_tr': 'Founder & CEO', 'title_en': 'Founder & CEO', 'title_ar': 'المؤسس والرئيس التنفيذي', 'title_ru': 'Засновник і CEO', 'title_de': 'بنیان‌گذار و مدیرعامل',
                'avatar_color': 'primary', 'sort_order': 1,
            },
            {
                'name_tr': 'Ali T.', 'name_en': 'Ali T.', 'name_ar': 'علي ت.', 'name_ru': 'Алі Т.', 'name_de': 'علی ت.',
                'initials': 'AT',
                'title_tr': 'Frontend Lead', 'title_en': 'Frontend Lead', 'title_ar': 'قائد الواجهة الأمامية', 'title_ru': 'Керівник фронтенду', 'title_de': 'سرپرست فرانت‌اند',
                'avatar_color': 'green', 'sort_order': 2,
            },
            {
                'name_tr': 'Bora S.', 'name_en': 'Bora S.', 'name_ar': 'بورا س.', 'name_ru': 'Бора С.', 'name_de': 'بورا س.',
                'initials': 'BS',
                'title_tr': 'Backend Lead', 'title_en': 'Backend Lead', 'title_ar': 'قائد الخلفية', 'title_ru': 'Керівник бекенду', 'title_de': 'سرپرست بک‌اند',
                'avatar_color': 'purple', 'sort_order': 3,
            },
            {
                'name_tr': 'Ahmet D.', 'name_en': 'Ahmet D.', 'name_ar': 'أحمد د.', 'name_ru': 'Ахмет Д.', 'name_de': 'احمد د.',
                'initials': 'AD',
                'title_tr': 'DevOps & Infrastructure', 'title_en': 'DevOps & Infrastructure', 'title_ar': 'DevOps والبنية التحتية', 'title_ru': 'DevOps та інфраструктура', 'title_de': 'DevOps و زیرساخت',
                'avatar_color': 'amber', 'sort_order': 4,
            },
            {
                'name_tr': 'Pinar Y.', 'name_en': 'Pinar Y.', 'name_ar': 'بينار ي.', 'name_ru': 'Пинар Й.', 'name_de': 'پینار ی.',
                'initials': 'PY',
                'title_tr': 'Sales & Customer Success', 'title_en': 'Sales & Customer Success', 'title_ar': 'المبيعات ونجاح العملاء', 'title_ru': 'Продажі та успіх клієнтів', 'title_de': 'فروش و موفقیت مشتری',
                'avatar_color': 'rose', 'sort_order': 5,
            },
        ]
        for m in members:
            TeamMember.objects.update_or_create(name_tr=m['name_tr'], defaults=m)
        self.stdout.write(f'  \u2713 TeamMember ({len(members)})')

    def _seed_company_values(self):
        values = [
            {
                'title_tr': 'Musteri Odaklilik',
                'title_en': 'Customer Focus',
                'title_ar': 'التركيز على العملاء',
                'title_ru': 'Орієнтація на клієнта',
                'title_de': 'مشتری‌مداری',
                'description_tr': 'Her kararda musterilerimizin ihtiyaclarini on planda tutuyoruz.',
                'description_en': 'We prioritize our customers\' needs in every decision.',
                'description_ar': 'نضع احتياجات عملائنا في المقام الأول في كل قرار.',
                'description_ru': 'Ми ставимо потреби наших клієнтів на перше місце в кожному рішенні.',
                'description_de': 'در هر تصمیمی نیازهای مشتریان را در اولویت قرار می‌دهیم.',
                'icon': 'ph-users',
                'color': 'primary',
                'sort_order': 1,
            },
            {
                'title_tr': 'Inovasyon',
                'title_en': 'Innovation',
                'title_ar': 'الابتكار',
                'title_ru': 'Інновації',
                'title_de': 'نوآوری',
                'description_tr': 'Yapay zeka ve modern teknolojilerle sektoru donusturuyoruz.',
                'description_en': 'We are transforming the industry with AI and modern technologies.',
                'description_ar': 'نحوّل القطاع بالذكاء الاصطناعي والتقنيات الحديثة.',
                'description_ru': 'Ми трансформуємо галузь за допомогою ШІ та сучасних технологій.',
                'description_de': 'با هوش مصنوعی و فناوری‌های مدرن صنعت را متحول می‌کنیم.',
                'icon': 'ph-lightbulb',
                'color': 'amber',
                'sort_order': 2,
            },
            {
                'title_tr': 'Guvenilirlik',
                'title_en': 'Reliability',
                'title_ar': 'الموثوقية',
                'title_ru': 'Надійність',
                'title_de': 'قابلیت اطمینان',
                'description_tr': '%99.9 uptime garantisi ve KVKK uyumlu altyapi ile guven sunuyoruz.',
                'description_en': 'We provide trust with 99.9% uptime guarantee and KVKK-compliant infrastructure.',
                'description_ar': 'نوفر الثقة بضمان وقت تشغيل 99.9% وبنية تحتية متوافقة مع KVKK.',
                'description_ru': 'Ми забезпечуємо довіру з гарантією 99.9% часу роботи та інфраструктурою, що відповідає KVKK.',
                'description_de': 'با تضمین آپتایم 99.9% و زیرساخت سازگار با KVKK اعتماد ارائه می‌دهیم.',
                'icon': 'ph-shield-check',
                'color': 'green',
                'sort_order': 3,
            },
            {
                'title_tr': 'Erisilebilirlik',
                'title_en': 'Accessibility',
                'title_ar': 'إمكانية الوصول',
                'title_ru': 'Доступність',
                'title_de': 'دسترسی‌پذیری',
                'description_tr': 'Her olcekteki isletme icin uygun fiyatli ve kolay kullanilabilir cozumler.',
                'description_en': 'Affordable and easy-to-use solutions for businesses of all sizes.',
                'description_ar': 'حلول ميسورة التكلفة وسهلة الاستخدام للمنشآت بجميع أحجامها.',
                'description_ru': 'Доступні та зручні рішення для бізнесу будь-якого масштабу.',
                'description_de': 'راه‌حل‌های مقرون‌به‌صرفه و آسان برای کسب‌وکارهای هر اندازه.',
                'icon': 'ph-hand-heart',
                'color': 'purple',
                'sort_order': 4,
            },
        ]
        for v in values:
            CompanyValue.objects.update_or_create(title_tr=v['title_tr'], defaults=v)
        self.stdout.write(f'  \u2713 CompanyValue ({len(values)})')

    def _seed_company_stats(self):
        stats = [
            {
                'value_tr': '2024', 'value_en': '2024', 'value_ar': '2024', 'value_ru': '2024', 'value_de': '2024',
                'label_tr': 'Kurulus', 'label_en': 'Founded', 'label_ar': 'التأسيس', 'label_ru': 'Заснування', 'label_de': 'تاسیس',
                'sort_order': 1,
            },
            {
                'value_tr': '5+', 'value_en': '5+', 'value_ar': '5+', 'value_ru': '5+', 'value_de': '5+',
                'label_tr': 'Ekip', 'label_en': 'Team', 'label_ar': 'الفريق', 'label_ru': 'Команда', 'label_de': 'تیم',
                'sort_order': 2,
            },
            {
                'value_tr': '50+', 'value_en': '50+', 'value_ar': '50+', 'value_ru': '50+', 'value_de': '50+',
                'label_tr': 'Ozellik', 'label_en': 'Features', 'label_ar': 'الميزات', 'label_ru': 'Функції', 'label_de': 'ویژگی',
                'sort_order': 3,
            },
            {
                'value_tr': '\u221e', 'value_en': '\u221e', 'value_ar': '\u221e', 'value_ru': '\u221e', 'value_de': '\u221e',
                'label_tr': 'Tutku', 'label_en': 'Passion', 'label_ar': 'الشغف', 'label_ru': 'Пристрасть', 'label_de': 'اشتیاق',
                'sort_order': 4,
            },
        ]
        for s in stats:
            CompanyStat.objects.update_or_create(label_tr=s['label_tr'], defaults=s)
        self.stdout.write(f'  \u2713 CompanyStat ({len(stats)})')

    def _seed_legal_pages(self):
        pages = [
            {
                'slug': 'privacy',
                'title_tr': 'Gizlilik Politikasi',
                'title_en': 'Privacy Policy',
                'title_ar': 'سياسة الخصوصية',
                'title_ru': 'Політика конфіденційності',
                'title_de': 'سیاست حریم خصوصی',
                'last_updated_display_tr': '22 Subat 2026',
                'last_updated_display_en': 'February 22, 2026',
                'last_updated_display_ar': '22 فبراير 2026',
                'last_updated_display_ru': '22 лютого 2026',
                'last_updated_display_de': '22 فوریه 2026',
                'meta_description_tr': 'E-Menum gizlilik politikasi — kisisel verilerin korunmasi ve kullanimi hakkinda bilgilendirme.',
                'meta_description_en': 'E-Menum privacy policy — information about personal data protection and usage.',
                'meta_description_ar': 'سياسة خصوصية E-Menum — معلومات حول حماية البيانات الشخصية واستخدامها.',
                'meta_description_ru': 'Політика конфіденційності E-Menum — інформація про захист та використання персональних даних.',
                'meta_description_de': 'سیاست حریم خصوصی E-Menum — اطلاعات درباره حفاظت و استفاده از داده‌های شخصی.',
                'content_tr': self._get_privacy_content_tr(),
                'content_en': self._get_privacy_content_en(),
                'content_ar': self._get_privacy_content_ar(),
                'content_ru': self._get_privacy_content_ru(),
                'content_de': self._get_privacy_content_de(),
            },
            {
                'slug': 'terms',
                'title_tr': 'Kullanim Sartlari',
                'title_en': 'Terms of Use',
                'title_ar': 'شروط الاستخدام',
                'title_ru': 'Умови використання',
                'title_de': 'شرایط استفاده',
                'last_updated_display_tr': '22 Subat 2026',
                'last_updated_display_en': 'February 22, 2026',
                'last_updated_display_ar': '22 فبراير 2026',
                'last_updated_display_ru': '22 лютого 2026',
                'last_updated_display_de': '22 فوریه 2026',
                'meta_description_tr': 'E-Menum kullanim sartlari — platform kullanim kosullari ve kurallar.',
                'meta_description_en': 'E-Menum terms of use — platform usage conditions and rules.',
                'meta_description_ar': 'شروط استخدام E-Menum — شروط وقواعد استخدام المنصة.',
                'meta_description_ru': 'Умови використання E-Menum — умови та правила користування платформою.',
                'meta_description_de': 'شرایط استفاده E-Menum — شرایط و قوانین استفاده از پلتفرم.',
                'content_tr': self._get_terms_content_tr(),
                'content_en': self._get_terms_content_en(),
                'content_ar': self._get_terms_content_ar(),
                'content_ru': self._get_terms_content_ru(),
                'content_de': self._get_terms_content_de(),
            },
            {
                'slug': 'kvkk',
                'title_tr': 'KVKK Aydinlatma Metni',
                'title_en': 'KVKK Disclosure Notice',
                'title_ar': 'إشعار الإفصاح KVKK',
                'title_ru': 'Повідомлення KVKK',
                'title_de': 'اطلاعیه افشای KVKK',
                'last_updated_display_tr': '22 Subat 2026',
                'last_updated_display_en': 'February 22, 2026',
                'last_updated_display_ar': '22 فبراير 2026',
                'last_updated_display_ru': '22 лютого 2026',
                'last_updated_display_de': '22 فوریه 2026',
                'meta_description_tr': 'E-Menum KVKK aydinlatma metni — 6698 sayili kanun kapsaminda bilgilendirme.',
                'meta_description_en': 'E-Menum KVKK disclosure notice — information under Law No. 6698 on Personal Data Protection.',
                'meta_description_ar': 'إشعار الإفصاح KVKK من E-Menum — معلومات بموجب قانون حماية البيانات الشخصية رقم 6698.',
                'meta_description_ru': 'Повідомлення KVKK від E-Menum — інформація відповідно до Закону № 6698 про захист персональних даних.',
                'meta_description_de': 'اطلاعیه افشای KVKK از E-Menum — اطلاعات طبق قانون شماره 6698 حفاظت از داده‌های شخصی.',
                'content_tr': self._get_kvkk_content_tr(),
                'content_en': self._get_kvkk_content_en(),
                'content_ar': self._get_kvkk_content_ar(),
                'content_ru': self._get_kvkk_content_ru(),
                'content_de': self._get_kvkk_content_de(),
            },
            {
                'slug': 'cookie',
                'title_tr': 'Cerez Politikasi',
                'title_en': 'Cookie Policy',
                'title_ar': 'سياسة ملفات تعريف الارتباط',
                'title_ru': 'Политика в отношении файлов cookie',
                'title_de': 'Cookie-Richtlinie',
                'last_updated_display_tr': '22 Subat 2026',
                'last_updated_display_en': 'February 22, 2026',
                'last_updated_display_ar': '22 فبراير 2026',
                'last_updated_display_ru': '22 февраля 2026',
                'last_updated_display_de': '22. Februar 2026',
                'meta_description_tr': 'E-Menum cerez politikasi — cerez kullanimi, turleri ve tercihleri hakkinda bilgi.',
                'meta_description_en': 'E-Menum cookie policy — information about cookie usage, types and preferences.',
                'content_tr': '<h2>Cerez Politikasi</h2><p>Bu Cerez Politikasi, E-Menum web sitesini ziyaret ettiginizde cerezlerin nasil kullanildigini aciklar.</p><h3>1. Cerez Nedir?</h3><p>Cerezler, web sitemizi ziyaret ettiginizde tarayiciniza yerlestirilen kucuk metin dosyalaridir. Cerezler, web sitemizin duzgun calismasi, guvenligin saglanmasi, daha iyi bir kullanici deneyimi sunulmasi ve web sitemizin nasil kullanildiginin anlasilmasi icin kullanilir.</p><h3>2. Hangi Cerezleri Kullaniyoruz?</h3><p><strong>Zorunlu Cerezler:</strong> Web sitemizin temel islevlerinin calismasi icin gereklidir. Bu cerezler olmadan web sitemiz duzgun calisamaz.</p><p><strong>Analitik Cerezler:</strong> Ziyaretcilerin web sitemizi nasil kullandigini anlamamiza yardimci olur.</p><p><strong>Islevsel Cerezler:</strong> Dil tercihleri gibi secimlerinizi hatirlamamizi saglar.</p><h3>3. Cerez Tercihleriniz</h3><p>Tarayici ayarlarindan cerezleri kontrol edebilir veya silebilirsiniz. Ancak cerezleri devre disi birakmaniz, web sitemizin bazi ozelliklerinin calismamasi ile sonuclanabilir.</p><h3>4. Iletisim</h3><p>Cerez politikamiz hakkinda sorulariniz icin <a href="mailto:info@e-menum.com">info@e-menum.com</a> adresinden bizimle iletisime gecebilirsiniz.</p>',
                'content_en': '<h2>Cookie Policy</h2><p>This Cookie Policy explains how cookies are used when you visit the E-Menum website.</p><h3>1. What are Cookies?</h3><p>Cookies are small text files placed in your browser when you visit our website. They are used to ensure proper functioning, maintain security, provide a better user experience, and understand how our website is used.</p><h3>2. What Cookies Do We Use?</h3><p><strong>Essential Cookies:</strong> Required for basic website functionality. Without these cookies, our website cannot function properly.</p><p><strong>Analytics Cookies:</strong> Help us understand how visitors use our website.</p><p><strong>Functional Cookies:</strong> Remember your preferences such as language selection.</p><h3>3. Your Cookie Preferences</h3><p>You can control or delete cookies through your browser settings. However, disabling cookies may result in some features of our website not functioning.</p><h3>4. Contact</h3><p>For questions about our cookie policy, contact us at <a href="mailto:info@e-menum.com">info@e-menum.com</a>.</p>',
            },
        ]
        for p in pages:
            LegalPage.objects.update_or_create(slug=p['slug'], defaults=p)
        self.stdout.write(f'  \u2713 LegalPage ({len(pages)})')

    def _seed_blog_posts(self):
        posts = [
            {
                'slug': 'dijital-menu-nedir',
                'title_tr': 'Dijital Menu Nedir? Isletmenize Neler Katar?',
                'title_en': 'What is a Digital Menu? What Does It Bring to Your Business?',
                'title_ar': 'ما هي القائمة الرقمية؟ وما الذي تضيفه لعملك؟',
                'title_ru': 'Що таке цифрове меню? Що воно дає вашому бізнесу?',
                'title_de': 'منوی دیجیتال چیست؟ چه مزایایی برای کسب‌وکار شما دارد؟',
                'excerpt_tr': 'Dijital menu kavrami, avantajlari ve isletmenize katacagi deger hakkinda kapsamli rehber.',
                'excerpt_en': 'A comprehensive guide about the digital menu concept, its advantages and the value it adds to your business.',
                'excerpt_ar': 'دليل شامل حول مفهوم القائمة الرقمية ومزاياها والقيمة التي تضيفها لعملك.',
                'excerpt_ru': 'Вичерпний посібник про концепцію цифрового меню, його переваги та цінність для вашого бізнесу.',
                'excerpt_de': 'راهنمای جامع درباره مفهوم منوی دیجیتال، مزایا و ارزشی که به کسب‌وکار شما اضافه می‌کند.',
                'content_tr': '<p>Dijital menu, geleneksel basili menulerin yerini alan modern bir cozumdur. Bu yazida dijital menunun avantajlarini detayli olarak inceliyoruz.</p>',
                'content_en': '<p>A digital menu is a modern solution replacing traditional printed menus. In this article, we examine the advantages of digital menus in detail.</p>',
                'content_ar': '<p>القائمة الرقمية هي حل عصري يحل محل القوائم المطبوعة التقليدية. في هذا المقال نستعرض مزايا القوائم الرقمية بالتفصيل.</p>',
                'content_ru': '<p>Цифрове меню — це сучасне рішення, що замінює традиційні друковані меню. У цій статті ми детально розглядаємо переваги цифрових меню.</p>',
                'content_de': '<p>منوی دیجیتال یک راه‌حل مدرن است که جایگزین منوهای چاپی سنتی می‌شود. در این مقاله مزایای منوی دیجیتال را به تفصیل بررسی می‌کنیم.</p>',
                'category_tr': 'Rehber',
                'category_en': 'Guide',
                'category_ar': 'دليل',
                'category_ru': 'Посібник',
                'category_de': 'راهنما',
                'meta_description_tr': 'Dijital menu kavrami, avantajlari ve isletmenize katacagi deger hakkinda kapsamli rehber.',
                'meta_description_en': 'A comprehensive guide about the digital menu concept, its advantages and the value it adds to your business.',
                'meta_description_ar': 'دليل شامل حول مفهوم القائمة الرقمية ومزاياها والقيمة التي تضيفها لعملك.',
                'meta_description_ru': 'Вичерпний посібник про концепцію цифрового меню, його переваги та цінність для вашого бізнесу.',
                'meta_description_de': 'راهنمای جامع درباره مفهوم منوی دیجیتال، مزایا و ارزشی که به کسب‌وکار شما اضافه می‌کند.',
                'author_name': 'E-Menum Ekibi',
                'status': 'draft',
            },
            {
                'slug': 'qr-menu-musteri-deneyimi',
                'title_tr': 'QR Menu ile Musteri Deneyimini Nasil Iyilestirirsiniz?',
                'title_en': 'How to Improve Customer Experience with QR Menus?',
                'title_ar': 'كيف تحسن تجربة العملاء باستخدام قائمة QR؟',
                'title_ru': 'Як покращити клієнтський досвід за допомогою QR-меню?',
                'title_de': 'چگونه با منوی QR تجربه مشتری را بهبود دهید؟',
                'excerpt_tr': 'QR menu teknolojisi ile musteri memnuniyetini artirmanin yollari.',
                'excerpt_en': 'Ways to increase customer satisfaction with QR menu technology.',
                'excerpt_ar': 'طرق زيادة رضا العملاء باستخدام تقنية قائمة QR.',
                'excerpt_ru': 'Способи підвищення задоволеності клієнтів за допомогою технології QR-меню.',
                'excerpt_de': 'روش‌های افزایش رضایت مشتری با فناوری منوی QR.',
                'content_tr': '<p>QR menu, musterilerinizin telefonlarindan kolayca menunuzu goruntulemesini saglar. Bu yazida QR menunun musteri deneyimine etkilerini inceliyoruz.</p>',
                'content_en': '<p>QR menus allow your customers to easily view your menu from their phones. In this article, we examine the effects of QR menus on customer experience.</p>',
                'content_ar': '<p>تتيح قوائم QR لعملائك عرض قائمتك بسهولة من هواتفهم. في هذا المقال نستعرض تأثير قوائم QR على تجربة العملاء.</p>',
                'content_ru': '<p>QR-меню дозволяє вашим клієнтам легко переглядати меню зі своїх телефонів. У цій статті ми розглядаємо вплив QR-меню на клієнтський досвід.</p>',
                'content_de': '<p>منوی QR به مشتریان شما امکان می‌دهد به راحتی از گوشی خود منو را مشاهده کنند. در این مقاله تأثیر منوی QR بر تجربه مشتری را بررسی می‌کنیم.</p>',
                'category_tr': 'Ipuclari',
                'category_en': 'Tips',
                'category_ar': 'نصائح',
                'category_ru': 'Поради',
                'category_de': 'نکات',
                'meta_description_tr': 'QR menu teknolojisi ile musteri memnuniyetini artirmanin yollari.',
                'meta_description_en': 'Ways to increase customer satisfaction with QR menu technology.',
                'meta_description_ar': 'طرق زيادة رضا العملاء باستخدام تقنية قائمة QR.',
                'meta_description_ru': 'Способи підвищення задоволеності клієнтів за допомогою технології QR-меню.',
                'meta_description_de': 'روش‌های افزایش رضایت مشتری با فناوری منوی QR.',
                'author_name': 'E-Menum Ekibi',
                'status': 'draft',
            },
            {
                'slug': 'restoran-yonetimi-yapay-zeka',
                'title_tr': 'Restoran Yonetiminde Yapay Zekanin Rolu',
                'title_en': 'The Role of Artificial Intelligence in Restaurant Management',
                'title_ar': 'دور الذكاء الاصطناعي في إدارة المطاعم',
                'title_ru': 'Роль штучного інтелекту в управлінні ресторанами',
                'title_de': 'نقش هوش مصنوعی در مدیریت رستوران',
                'excerpt_tr': 'AI teknolojisinin restoran isletmeciligi uzerindeki donusturucu etkisi.',
                'excerpt_en': 'The transformative impact of AI technology on restaurant management.',
                'excerpt_ar': 'التأثير التحويلي لتقنية الذكاء الاصطناعي على إدارة المطاعم.',
                'excerpt_ru': 'Трансформаційний вплив технології ШІ на управління ресторанами.',
                'excerpt_de': 'تأثیر تحول‌آفرین فناوری هوش مصنوعی بر مدیریت رستوران.',
                'content_tr': '<p>Yapay zeka, restoran sektorunde icerik uretiminden musteri analizine kadar pek cok alanda devrim yaratiyor.</p>',
                'content_en': '<p>Artificial intelligence is revolutionizing the restaurant industry in many areas, from content generation to customer analysis.</p>',
                'content_ar': '<p>يُحدث الذكاء الاصطناعي ثورة في قطاع المطاعم في مجالات عديدة، من إنتاج المحتوى إلى تحليل العملاء.</p>',
                'content_ru': '<p>Штучний інтелект здійснює революцію в ресторанній галузі в багатьох сферах — від створення контенту до аналізу клієнтів.</p>',
                'content_de': '<p>هوش مصنوعی در حوزه‌های متعددی از صنعت رستوران، از تولید محتوا تا تحلیل مشتری، تحول ایجاد می‌کند.</p>',
                'category_tr': 'Teknoloji',
                'category_en': 'Technology',
                'category_ar': 'تكنولوجيا',
                'category_ru': 'Технології',
                'category_de': 'فناوری',
                'meta_description_tr': 'AI teknolojisinin restoran isletmeciligi uzerindeki donusturucu etkisi.',
                'meta_description_en': 'The transformative impact of AI technology on restaurant management.',
                'meta_description_ar': 'التأثير التحويلي لتقنية الذكاء الاصطناعي على إدارة المطاعم.',
                'meta_description_ru': 'Трансформаційний вплив технології ШІ на управління ресторанами.',
                'meta_description_de': 'تأثیر تحول‌آفرین فناوری هوش مصنوعی بر مدیریت رستوران.',
                'author_name': 'E-Menum Ekibi',
                'status': 'draft',
            },
        ]
        for p in posts:
            BlogPost.objects.update_or_create(slug=p['slug'], defaults=p)
        self.stdout.write(f'  \u2713 BlogPost ({len(posts)})')

    def _seed_plan_display_features(self):
        """Seed pricing card display features linked to subscription Plans."""
        from apps.subscriptions.models import Plan

        plan_features = {
            'free': [
                {'text_tr': '1 menu, 20 urun', 'text_en': '1 menu, 20 products', 'text_ar': '1 قائمة، 20 منتج', 'text_ru': '1 меню, 20 продуктів', 'text_de': '1 منو، 20 محصول', 'is_highlighted': False},
                {'text_tr': 'QR kod olusturma', 'text_en': 'QR code generation', 'text_ar': 'إنشاء رمز QR', 'text_ru': 'Генерація QR-коду', 'text_de': 'ایجاد کد QR', 'is_highlighted': False},
                {'text_tr': 'Temel tema', 'text_en': 'Basic theme', 'text_ar': 'قالب أساسي', 'text_ru': 'Базова тема', 'text_de': 'قالب پایه', 'is_highlighted': False},
            ],
            'starter': [
                {'text_tr': '3 menu, 100 urun', 'text_en': '3 menus, 100 products', 'text_ar': '3 قوائم، 100 منتج', 'text_ru': '3 меню, 100 продуктів', 'text_de': '3 منو، 100 محصول', 'is_highlighted': False},
                {'text_tr': 'QR kod olusturma', 'text_en': 'QR code generation', 'text_ar': 'إنشاء رمز QR', 'text_ru': 'Генерація QR-коду', 'text_de': 'ایجاد کد QR', 'is_highlighted': False},
                {'text_tr': 'Tum temalar', 'text_en': 'All themes', 'text_ar': 'جميع القوالب', 'text_ru': 'Усі теми', 'text_de': 'تمام قالب‌ها', 'is_highlighted': False},
                {'text_tr': 'E-posta destek', 'text_en': 'Email support', 'text_ar': 'دعم البريد الإلكتروني', 'text_ru': 'Підтримка електронною поштою', 'text_de': 'پشتیبانی ایمیلی', 'is_highlighted': False},
            ],
            'professional': [
                {'text_tr': 'Sinirsiz menu ve urun', 'text_en': 'Unlimited menus and products', 'text_ar': 'قوائم ومنتجات غير محدودة', 'text_ru': 'Необмежені меню та продукти', 'text_de': 'منو و محصولات نامحدود', 'is_highlighted': True},
                {'text_tr': 'AI icerik uretimi', 'text_en': 'AI content generation', 'text_ar': 'إنشاء محتوى بالذكاء الاصطناعي', 'text_ru': 'Генерація контенту ШІ', 'text_de': 'تولید محتوا با هوش مصنوعی', 'is_highlighted': True},
                {'text_tr': 'Analitik dashboard', 'text_en': 'Analytics dashboard', 'text_ar': 'لوحة التحليلات', 'text_ru': 'Аналітична панель', 'text_de': 'داشبورد تحلیلی', 'is_highlighted': False},
                {'text_tr': 'Oncelikli destek', 'text_en': 'Priority support', 'text_ar': 'دعم ذو أولوية', 'text_ru': 'Пріоритетна підтримка', 'text_de': 'پشتیبانی اولویت‌دار', 'is_highlighted': False},
                {'text_tr': 'Coklu sube (3)', 'text_en': 'Multiple branches (3)', 'text_ar': 'فروع متعددة (3)', 'text_ru': 'Кілька філій (3)', 'text_de': 'چند شعبه (3)', 'is_highlighted': False},
            ],
            'business': [
                {'text_tr': 'Professional ozellikleri +', 'text_en': 'Professional features +', 'text_ar': 'ميزات Professional +', 'text_ru': 'Функції Professional +', 'text_de': 'ویژگی‌های Professional +', 'is_highlighted': True},
                {'text_tr': '10 sube destegi', 'text_en': '10 branch support', 'text_ar': 'دعم 10 فروع', 'text_ru': 'Підтримка 10 філій', 'text_de': 'پشتیبانی 10 شعبه', 'is_highlighted': False},
                {'text_tr': 'API erisimi', 'text_en': 'API access', 'text_ar': 'وصول API', 'text_ru': 'Доступ до API', 'text_de': 'دسترسی API', 'is_highlighted': False},
                {'text_tr': 'Ozel tema tasarimi', 'text_en': 'Custom theme design', 'text_ar': 'تصميم قالب مخصص', 'text_ru': 'Індивідуальний дизайн теми', 'text_de': 'طراحی قالب سفارشی', 'is_highlighted': False},
                {'text_tr': 'SLA garantisi', 'text_en': 'SLA guarantee', 'text_ar': 'ضمان SLA', 'text_ru': 'Гарантія SLA', 'text_de': 'تضمین SLA', 'is_highlighted': False},
            ],
            'enterprise': [
                {'text_tr': 'Sinirsiz her sey', 'text_en': 'Unlimited everything', 'text_ar': 'كل شيء غير محدود', 'text_ru': 'Все необмежено', 'text_de': 'همه چیز نامحدود', 'is_highlighted': True},
                {'text_tr': 'Sinirsiz sube', 'text_en': 'Unlimited branches', 'text_ar': 'فروع غير محدودة', 'text_ru': 'Необмежені філії', 'text_de': 'شعب نامحدود', 'is_highlighted': False},
                {'text_tr': 'Ozel entegrasyon', 'text_en': 'Custom integration', 'text_ar': 'تكامل مخصص', 'text_ru': 'Індивідуальна інтеграція', 'text_de': 'یکپارچه‌سازی سفارشی', 'is_highlighted': False},
                {'text_tr': 'VIP destek', 'text_en': 'VIP support', 'text_ar': 'دعم VIP', 'text_ru': 'VIP-підтримка', 'text_de': 'پشتیبانی VIP', 'is_highlighted': False},
                {'text_tr': 'SLA + Ozel mudur', 'text_en': 'SLA + Dedicated manager', 'text_ar': 'SLA + مدير مخصص', 'text_ru': 'SLA + Персональний менеджер', 'text_de': 'SLA + مدیر اختصاصی', 'is_highlighted': False},
            ],
        }

        total = 0
        for plan_slug, features in plan_features.items():
            try:
                plan = Plan.objects.get(slug=plan_slug)
            except Plan.DoesNotExist:
                self.stdout.write(f'    ! Plan "{plan_slug}" bulunamadi, atlaniyor')
                continue

            for i, feat in enumerate(features):
                is_highlighted = feat.pop('is_highlighted')
                PlanDisplayFeature.objects.update_or_create(
                    plan=plan,
                    text_tr=feat['text_tr'],
                    defaults={
                        **feat,
                        'is_highlighted': is_highlighted,
                        'sort_order': i + 1,
                        'is_active': True,
                    },
                )
                total += 1

        self.stdout.write(f'  \u2713 PlanDisplayFeature ({total})')

    def _seed_navigation_links(self):
        # Clear existing navigation links
        NavigationLink.objects.all().delete()

        # Header navigation
        # Parent: Urun (dropdown)
        urun = NavigationLink.objects.create(
            location='header',
            label_tr='Urun', label_en='Product', label_ar='المنتج', label_ru='Продукт', label_de='محصول',
            url='', sort_order=1,
        )
        NavigationLink.objects.create(
            location='header',
            label_tr='Tum Ozellikler', label_en='All Features', label_ar='جميع الميزات', label_ru='Усі функції', label_de='تمام ویژگی‌ها',
            url='website:features',
            icon='ph-list-checks',
            description_tr='50+ ozellik, tek platform', description_en='50+ features, one platform', description_ar='أكثر من 50 ميزة، منصة واحدة', description_ru='50+ функцій, одна платформа', description_de='بیش از 50 ویژگی، یک پلتفرم',
            parent=urun, sort_order=1,
        )
        NavigationLink.objects.create(
            location='header',
            label_tr='Fiyatlandirma', label_en='Pricing', label_ar='التسعير', label_ru='Ціни', label_de='قیمت‌گذاری',
            url='website:pricing',
            icon='ph-currency-circle-dollar',
            description_tr='Isletmenize uygun plan', description_en='The right plan for your business', description_ar='الخطة المناسبة لعملك', description_ru='Відповідний план для вашого бізнесу', description_de='پلن مناسب برای کسب‌وکار شما',
            parent=urun, sort_order=2,
        )
        NavigationLink.objects.create(
            location='header',
            label_tr='Canli Demo', label_en='Live Demo', label_ar='عرض حي', label_ru='Демо', label_de='دموی زنده',
            url='website:demo',
            icon='ph-play-circle',
            description_tr='Platformu canli kesfet', description_en='Explore the platform live', description_ar='استكشف المنصة مباشرة', description_ru='Ознайомтеся з платформою наживо', description_de='پلتفرم را زنده کشف کنید',
            parent=urun, sort_order=3,
        )

        # Parent: Cozumler (dropdown)
        cozumler = NavigationLink.objects.create(
            location='header',
            label_tr='Cozumler', label_en='Solutions', label_ar='الحلول', label_ru='Рішення', label_de='راه‌حل‌ها',
            url='', sort_order=2,
        )
        NavigationLink.objects.create(
            location='header',
            label_tr='Restoran', label_en='Restaurant', label_ar='مطعم', label_ru='Ресторан', label_de='رستوران',
            url='website:features',
            icon='ph-fork-knife',
            description_tr="A'la carte ve fine dining", description_en='A la carte and fine dining', description_ar='انتقاء الأطباق والمطاعم الراقية', description_ru='A la carte та вишукана кухня', description_de='آلاکارت و غذاخوری لوکس',
            parent=cozumler, sort_order=1,
        )
        NavigationLink.objects.create(
            location='header',
            label_tr='Kafe', label_en='Cafe', label_ar='مقهى', label_ru='Кафе', label_de='کافه',
            url='website:features',
            icon='ph-coffee',
            description_tr='Kahve ve icecek odakli', description_en='Coffee and beverage focused', description_ar='متخصص في القهوة والمشروبات', description_ru='Орієнтовано на каву та напої', description_de='متمرکز بر قهوه و نوشیدنی',
            parent=cozumler, sort_order=2,
        )
        NavigationLink.objects.create(
            location='header',
            label_tr='Fast Food', label_en='Fast Food', label_ar='وجبات سريعة', label_ru='Фаст-фуд', label_de='فست‌فود',
            url='website:features',
            icon='ph-hamburger',
            description_tr='Hizli servis isletmeler', description_en='Quick service businesses', description_ar='مطاعم الخدمة السريعة', description_ru='Заклади швидкого обслуговування', description_de='کسب‌وکارهای سرویس سریع',
            parent=cozumler, sort_order=3,
        )
        NavigationLink.objects.create(
            location='header',
            label_tr='Zincir Isletme', label_en='Chain Business', label_ar='سلسلة أعمال', label_ru='Мережевий бізнес', label_de='زنجیره‌ای',
            url='website:features',
            icon='ph-buildings',
            description_tr='Coklu sube yonetimi', description_en='Multi-branch management', description_ar='إدارة الفروع المتعددة', description_ru='Управління кількома філіями', description_de='مدیریت چند شعبه',
            parent=cozumler, sort_order=4,
        )

        # Direct header links
        NavigationLink.objects.create(
            location='header',
            label_tr='Hakkimizda', label_en='About Us', label_ar='من نحن', label_ru='Про нас', label_de='درباره ما',
            url='website:about', sort_order=3,
        )
        NavigationLink.objects.create(
            location='header',
            label_tr='Blog', label_en='Blog', label_ar='المدونة', label_ru='Блог', label_de='بلاگ',
            url='website:blog', sort_order=4,
        )
        NavigationLink.objects.create(
            location='header',
            label_tr='Iletisim', label_en='Contact', label_ar='اتصل بنا', label_ru='Контакти', label_de='تماس با ما',
            url='website:contact', sort_order=5,
        )

        # Footer: Product links
        NavigationLink.objects.create(
            location='footer_product',
            label_tr='Ozellikler', label_en='Features', label_ar='الميزات', label_ru='Функції', label_de='ویژگی‌ها',
            url='website:features', sort_order=1,
        )
        NavigationLink.objects.create(
            location='footer_product',
            label_tr='Fiyatlandirma', label_en='Pricing', label_ar='التسعير', label_ru='Ціни', label_de='قیمت‌گذاری',
            url='website:pricing', sort_order=2,
        )
        NavigationLink.objects.create(
            location='footer_product',
            label_tr='Canli Demo', label_en='Live Demo', label_ar='عرض حي', label_ru='Демо', label_de='دموی زنده',
            url='website:demo', sort_order=3,
        )

        # Footer: Solutions links
        NavigationLink.objects.create(
            location='footer_solutions',
            label_tr='Restoran', label_en='Restaurant', label_ar='مطعم', label_ru='Ресторан', label_de='رستوران',
            url='website:features', sort_order=1,
        )
        NavigationLink.objects.create(
            location='footer_solutions',
            label_tr='Kafe', label_en='Cafe', label_ar='مقهى', label_ru='Кафе', label_de='کافه',
            url='website:features', sort_order=2,
        )
        NavigationLink.objects.create(
            location='footer_solutions',
            label_tr='Fast Food', label_en='Fast Food', label_ar='وجبات سريعة', label_ru='Фаст-фуд', label_de='فست‌فود',
            url='website:features', sort_order=3,
        )
        NavigationLink.objects.create(
            location='footer_solutions',
            label_tr='Zincir Isletme', label_en='Chain Business', label_ar='سلسلة أعمال', label_ru='Мережевий бізнес', label_de='زنجیره‌ای',
            url='website:features', sort_order=4,
        )

        # Footer: Company links
        NavigationLink.objects.create(
            location='footer_company',
            label_tr='Hakkimizda', label_en='About Us', label_ar='من نحن', label_ru='Про нас', label_de='درباره ما',
            url='website:about', sort_order=1,
        )
        NavigationLink.objects.create(
            location='footer_company',
            label_tr='Blog', label_en='Blog', label_ar='المدونة', label_ru='Блог', label_de='بلاگ',
            url='website:blog', sort_order=2,
        )

        # Footer: Support links
        NavigationLink.objects.create(
            location='footer_support',
            label_tr='Iletisim', label_en='Contact', label_ar='اتصل بنا', label_ru='Контакти', label_de='تماس با ما',
            url='website:contact', sort_order=1,
        )

        # Footer: Legal links
        NavigationLink.objects.create(
            location='footer_legal',
            label_tr='Gizlilik Politikasi', label_en='Privacy Policy', label_ar='سياسة الخصوصية', label_ru='Політика конфіденційності', label_de='سیاست حریم خصوصی',
            url='website:privacy', sort_order=1,
        )
        NavigationLink.objects.create(
            location='footer_legal',
            label_tr='Kullanim Sartlari', label_en='Terms of Use', label_ar='شروط الاستخدام', label_ru='Умови використання', label_de='شرایط استفاده',
            url='website:terms', sort_order=2,
        )
        NavigationLink.objects.create(
            location='footer_legal',
            label_tr='KVKK', label_en='KVKK', label_ar='KVKK', label_ru='KVKK', label_de='KVKK',
            url='website:kvkk', sort_order=3,
        )

        total = NavigationLink.objects.count()
        self.stdout.write(f'  \u2713 NavigationLink ({total})')

    # =========================================================================
    # Legal page content helpers
    # =========================================================================

    def _get_privacy_content_tr(self):
        return """
<h3>1. Toplanan Veriler</h3>
<p>E-Menum platformunu kullandiginizda asagidaki verileriniz toplanabilir:</p>
<ul>
<li>Ad, soyad, e-posta adresi, telefon numarasi</li>
<li>Isletme adi ve isletme bilgileri</li>
<li>Odeme bilgileri (guvenli odeme altyapisi uzerinden)</li>
<li>Platform kullanim verileri ve analitik bilgiler</li>
<li>Cerez verileri ve tarayici bilgileri</li>
</ul>

<h3>2. Verilerin Kullanim Amaci</h3>
<p>Toplanan veriler asagidaki amaclarla kullanilir:</p>
<ul>
<li>Hizmet sunumu ve iyilestirme</li>
<li>Musteri iletisimi ve destek</li>
<li>Fatura ve odeme islemleri</li>
<li>Yasal yukumluluklerin yerine getirilmesi</li>
<li>Platform guvenligi ve dolandiricilik onleme</li>
</ul>

<h3>3. Veri Paylasimi</h3>
<p>Kisisel verileriniz ucuncu taraflarla yalnizca asagidaki durumlarda paylasilir:</p>
<ul>
<li>Yasal zorunluluk halinde (mahkeme karari, resmi talep)</li>
<li>Odeme islemleri icin guvenli odeme saglaycilari ile</li>
<li>Acik rizaniz dahilinde</li>
</ul>

<h3>4. Veri Guvenligi</h3>
<p>Verileriniz SSL/TLS sifreleme ile korunmaktadir. Sunucularimiz Turkiye'de barindirilmakta ve uluslararasi guvenlik standartlarina uygun olarak isletilmektedir.</p>

<h3>5. Cerezler</h3>
<p>Platformumuz, kullanici deneyimini iyilestirmek icin cerezler kullanmaktadir. Tarayici ayarlarinizdan cerez tercihlerinizi yonetebilirsiniz.</p>

<h3>6. Haklariniz</h3>
<p>KVKK kapsaminda asagidaki haklara sahipsiniz:</p>
<ul>
<li>Kisisel verilerinizin islenip islenmedigini ogrenme</li>
<li>Islenmisse buna iliskin bilgi talep etme</li>
<li>Islenme amacini ve buna uygun kullanilip kullanilmadigini ogrenme</li>
<li>Eksik veya yanlis islenmisse duzeltilmesini isteme</li>
<li>Silinmesini veya yok edilmesini isteme</li>
</ul>

<h3>7. Iletisim</h3>
<p>Gizlilik politikamiz hakkinda sorulariniz icin <strong>info@e-menum.com</strong> adresinden bize ulasabilirsiniz.</p>
"""

    def _get_privacy_content_en(self):
        return """
<h3>1. Data We Collect</h3>
<p>When you use the E-Menum platform, the following data may be collected:</p>
<ul>
<li>First name, last name, email address, phone number</li>
<li>Business name and business information</li>
<li>Payment information (through secure payment infrastructure)</li>
<li>Platform usage data and analytics</li>
<li>Cookie data and browser information</li>
</ul>

<h3>2. Purpose of Data Usage</h3>
<p>The collected data is used for the following purposes:</p>
<ul>
<li>Service delivery and improvement</li>
<li>Customer communication and support</li>
<li>Billing and payment transactions</li>
<li>Fulfillment of legal obligations</li>
<li>Platform security and fraud prevention</li>
</ul>

<h3>3. Data Sharing</h3>
<p>Your personal data is shared with third parties only in the following cases:</p>
<ul>
<li>When required by law (court order, official request)</li>
<li>With secure payment providers for payment transactions</li>
<li>With your explicit consent</li>
</ul>

<h3>4. Data Security</h3>
<p>Your data is protected with SSL/TLS encryption. Our servers are hosted in Turkey and operated in compliance with international security standards.</p>

<h3>5. Cookies</h3>
<p>Our platform uses cookies to improve user experience. You can manage your cookie preferences through your browser settings.</p>

<h3>6. Your Rights</h3>
<p>Under KVKK (Turkish Data Protection Law), you have the following rights:</p>
<ul>
<li>To learn whether your personal data is being processed</li>
<li>To request information if it has been processed</li>
<li>To learn the purpose of processing and whether it is used accordingly</li>
<li>To request correction if it is incomplete or incorrect</li>
<li>To request deletion or destruction</li>
</ul>

<h3>7. Contact</h3>
<p>For questions about our privacy policy, you can reach us at <strong>info@e-menum.com</strong>.</p>
"""

    def _get_privacy_content_ar(self):
        return """
<h3>1. البيانات التي نجمعها</h3>
<p>عند استخدام منصة E-Menum، قد يتم جمع البيانات التالية: الاسم، البريد الإلكتروني، رقم الهاتف، معلومات العمل، بيانات الدفع، وبيانات استخدام المنصة.</p>

<h3>2. استخدام البيانات</h3>
<p>تُستخدم البيانات المجمعة لتقديم الخدمات وتحسينها، والتواصل مع العملاء، ومعالجة المدفوعات، والامتثال للالتزامات القانونية، وضمان أمن المنصة.</p>

<h3>3. حقوقك</h3>
<p>يحق لك معرفة ما إذا كانت بياناتك الشخصية تتم معالجتها، وطلب تصحيحها أو حذفها. للاستفسارات، تواصل معنا عبر <strong>info@e-menum.com</strong>.</p>
"""

    def _get_privacy_content_ru(self):
        return """
<h3>1. Дані, які ми збираємо</h3>
<p>При використанні платформи E-Menum можуть збиратися такі дані: ім'я, електронна пошта, номер телефону, інформація про бізнес, платіжні дані та дані використання платформи.</p>

<h3>2. Використання даних</h3>
<p>Зібрані дані використовуються для надання та покращення послуг, комунікації з клієнтами, обробки платежів, виконання юридичних зобов'язань та забезпечення безпеки платформи.</p>

<h3>3. Ваші права</h3>
<p>Ви маєте право дізнатися, чи обробляються ваші персональні дані, вимагати їх виправлення або видалення. Для запитань зв'яжіться з нами за адресою <strong>info@e-menum.com</strong>.</p>
"""

    def _get_privacy_content_de(self):
        return """
<h3>1. داده‌هایی که جمع‌آوری می‌کنیم</h3>
<p>هنگام استفاده از پلتفرم E-Menum، داده‌های زیر ممکن است جمع‌آوری شوند: نام، ایمیل، شماره تلفن، اطلاعات کسب‌وکار، اطلاعات پرداخت و داده‌های استفاده از پلتفرم.</p>

<h3>2. استفاده از داده‌ها</h3>
<p>داده‌های جمع‌آوری شده برای ارائه و بهبود خدمات، ارتباط با مشتریان، پردازش پرداخت‌ها، انجام تعهدات قانونی و تأمین امنیت پلتفرم استفاده می‌شوند.</p>

<h3>3. حقوق شما</h3>
<p>شما حق دارید بدانید آیا داده‌های شخصی شما پردازش می‌شوند و درخواست اصلاح یا حذف آن‌ها را داشته باشید. برای سوالات با ما از طریق <strong>info@e-menum.com</strong> تماس بگیرید.</p>
"""

    def _get_terms_content_tr(self):
        return """
<h3>1. Hizmet Tanimi</h3>
<p>E-Menum, restoran ve kafeler icin dijital menu yonetimi, siparis takibi ve analitik hizmetleri sunan bir SaaS platformudur.</p>

<h3>2. Hesap Olusturma</h3>
<p>Platformu kullanmak icin gecerli bir e-posta adresi ile hesap olusturmaniz gerekmektedir. Hesap bilgilerinizin guvenligi sizin sorumlulugunuzdadir.</p>

<h3>3. Kullanim Kosullari</h3>
<ul>
<li>Platformu yasal amaclarla kullanmayi kabul edersiniz</li>
<li>Diger kullanicilarin haklarini ihlal etmemeyi taahhut edersiniz</li>
<li>Platformun guvenligini tehlikeye atacak eylemlerde bulunmamalisiniz</li>
<li>Icerik yuklemelerinde telif haklarina dikkat etmelisiniz</li>
</ul>

<h3>4. Odeme ve Faturalama</h3>
<p>Ucretli planlar aylik veya yillik olarak faturalandirilir. Yillik planlarda %20 indirim uygulanir. Planlar arasinda gecis istediginiz zaman yapilabilir.</p>

<h3>5. Iptal ve Iade</h3>
<p>Aboneliginizi istediginiz zaman iptal edebilirsiniz. Iptal sonrasi mevcut fatura donemin sonuna kadar hizmetten yararlanmaya devam edersiniz.</p>

<h3>6. Sorumluluk Sinirlamasi</h3>
<p>E-Menum, platform uzerinden saglanan hizmetlerin kesintisiz veya hatasiz olacagini garanti etmez. Ancak %99.9 uptime hedefi ile calisir.</p>

<h3>7. Degisiklikler</h3>
<p>Bu kullanim sartlari onceden bildirimde bulunarak guncellenebilir. Guncellemeler web sitemizde yayinlandigindan itibaren gecerli olur.</p>
"""

    def _get_terms_content_en(self):
        return """
<h3>1. Service Definition</h3>
<p>E-Menum is a SaaS platform providing digital menu management, order tracking, and analytics services for restaurants and cafes.</p>

<h3>2. Account Creation</h3>
<p>To use the platform, you need to create an account with a valid email address. You are responsible for the security of your account credentials.</p>

<h3>3. Terms of Use</h3>
<ul>
<li>You agree to use the platform for lawful purposes</li>
<li>You commit not to violate other users' rights</li>
<li>You must not engage in actions that jeopardize the platform's security</li>
<li>You must respect copyright when uploading content</li>
</ul>

<h3>4. Payment and Billing</h3>
<p>Paid plans are billed monthly or annually. A 20% discount applies to annual plans. You can switch between plans at any time.</p>

<h3>5. Cancellation and Refund</h3>
<p>You can cancel your subscription at any time. After cancellation, you continue to use the service until the end of the current billing period.</p>

<h3>6. Limitation of Liability</h3>
<p>E-Menum does not guarantee that services provided through the platform will be uninterrupted or error-free. However, it operates with a 99.9% uptime target.</p>

<h3>7. Changes</h3>
<p>These terms of use may be updated with prior notice. Updates become effective once published on our website.</p>
"""

    def _get_terms_content_ar(self):
        return """
<h3>1. تعريف الخدمة</h3>
<p>E-Menum هي منصة SaaS تقدم خدمات إدارة القوائم الرقمية وتتبع الطلبات والتحليلات للمطاعم والمقاهي.</p>

<h3>2. شروط الاستخدام</h3>
<p>توافق على استخدام المنصة لأغراض قانونية وعدم انتهاك حقوق المستخدمين الآخرين. يتم إصدار فواتير الخطط المدفوعة شهرياً أو سنوياً مع خصم 20% على الخطط السنوية.</p>

<h3>3. الإلغاء</h3>
<p>يمكنك إلغاء اشتراكك في أي وقت. بعد الإلغاء، تستمر في استخدام الخدمة حتى نهاية فترة الفوترة الحالية. للاستفسارات، تواصل معنا عبر <strong>info@e-menum.com</strong>.</p>
"""

    def _get_terms_content_ru(self):
        return """
<h3>1. Визначення послуги</h3>
<p>E-Menum — це SaaS-платформа, що надає послуги управління цифровим меню, відстеження замовлень та аналітики для ресторанів і кафе.</p>

<h3>2. Умови використання</h3>
<p>Ви погоджуєтесь використовувати платформу в законних цілях і не порушувати права інших користувачів. Оплата платних планів здійснюється щомісячно або щорічно зі знижкою 20% на річні плани.</p>

<h3>3. Скасування</h3>
<p>Ви можете скасувати підписку в будь-який час. Після скасування ви продовжуєте користуватися послугою до кінця поточного розрахункового періоду. Для запитань зв'яжіться з нами за адресою <strong>info@e-menum.com</strong>.</p>
"""

    def _get_terms_content_de(self):
        return """
<h3>1. تعریف خدمات</h3>
<p>E-Menum یک پلتفرم SaaS است که خدمات مدیریت منوی دیجیتال، پیگیری سفارشات و تحلیل داده‌ها را برای رستوران‌ها و کافه‌ها ارائه می‌دهد.</p>

<h3>2. شرایط استفاده</h3>
<p>شما موافقت می‌کنید که از پلتفرم برای اهداف قانونی استفاده کنید و حقوق سایر کاربران را نقض نکنید. پلن‌های پولی به صورت ماهانه یا سالانه صورتحساب می‌شوند و 20% تخفیف برای پلن‌های سالانه اعمال می‌شود.</p>

<h3>3. لغو اشتراک</h3>
<p>شما می‌توانید اشتراک خود را در هر زمانی لغو کنید. پس از لغو، تا پایان دوره صورتحساب جاری به استفاده از خدمات ادامه خواهید داد. برای سوالات با ما از طریق <strong>info@e-menum.com</strong> تماس بگیرید.</p>
"""

    def _get_kvkk_content_tr(self):
        return """
<h3>Veri Sorumlusu</h3>
<p><strong>E-Menum Teknoloji A.S.</strong><br>
Adres: Istanbul, Turkiye<br>
E-posta: kvkk@e-menum.com</p>

<h3>Kisisel Verilerin Islenmesi</h3>
<p>6698 sayili Kisisel Verilerin Korunmasi Kanunu ("KVKK") kapsaminda, kisisel verileriniz asagida belirtilen amaclarla islenmektedir:</p>

<h3>Islenen Veri Kategorileri</h3>
<ul>
<li><strong>Kimlik Bilgileri:</strong> Ad, soyad</li>
<li><strong>Iletisim Bilgileri:</strong> E-posta, telefon, adres</li>
<li><strong>Isletme Bilgileri:</strong> Isletme adi, tipi, sube sayisi</li>
<li><strong>Finansal Bilgiler:</strong> Fatura ve odeme bilgileri</li>
<li><strong>Islem Guvenligi:</strong> IP adresi, log kayitlari</li>
</ul>

<h3>Isleme Amacalari</h3>
<ul>
<li>Hizmet sunumu ve sozlesme yukumlulukleri</li>
<li>Musteri iliskiler yonetimi</li>
<li>Fatura ve muhasebe islemleri</li>
<li>Yasal yukumlulukler</li>
<li>Bilgi guvenligi sureclerinin yurutulmesi</li>
</ul>

<h3>Veri Aktarimi</h3>
<p>Kisisel verileriniz, yasal zorunluluklar ve hizmet gereksinimleri cercevesinde yetkili kamu kurumlari ve is ortaklarimiz ile paylasilabilir.</p>

<h3>Haklariniz (KVKK Madde 11)</h3>
<ul>
<li>Kisisel verilerinizin islenip islenmedigini ogrenme</li>
<li>Islenmisse bilgi talep etme</li>
<li>Islenme amacini ve uygun kullanilip kullanilmadigini ogrenme</li>
<li>Yurt icinde/disinda aktarildigini ogrenme</li>
<li>Eksik/yanlis islenmisse duzeltilmesini isteme</li>
<li>KVKK Madde 7 kapsaminda silinmesini/yok edilmesini isteme</li>
<li>Duzeltme/silme islemlerinin aktarim yapilanlara bildirilmesini isteme</li>
<li>Munhasiran otomatik sistemler ile analiz edilmesi sonucu aleyhinize sonuc cikmasi halinde itiraz etme</li>
<li>Kanuna aykiri islenmesi nedeniyle zarara ugramaniz halinde tazminat talep etme</li>
</ul>

<h3>Basvuru Yontemi</h3>
<p>KVKK kapsamindaki haklarinizi kullanmak icin <strong>kvkk@e-menum.com</strong> adresine yazili basvuruda bulunabilirsiniz.</p>
"""

    def _get_kvkk_content_en(self):
        return """
<h3>Data Controller</h3>
<p><strong>E-Menum Teknoloji A.S.</strong><br>
Address: Istanbul, Turkey<br>
Email: kvkk@e-menum.com</p>

<h3>Processing of Personal Data</h3>
<p>Under Law No. 6698 on the Protection of Personal Data ("KVKK"), your personal data is processed for the purposes stated below:</p>

<h3>Categories of Data Processed</h3>
<ul>
<li><strong>Identity Information:</strong> First name, last name</li>
<li><strong>Contact Information:</strong> Email, phone, address</li>
<li><strong>Business Information:</strong> Business name, type, number of branches</li>
<li><strong>Financial Information:</strong> Billing and payment details</li>
<li><strong>Transaction Security:</strong> IP address, log records</li>
</ul>

<h3>Processing Purposes</h3>
<ul>
<li>Service delivery and contractual obligations</li>
<li>Customer relationship management</li>
<li>Billing and accounting</li>
<li>Legal obligations</li>
<li>Execution of information security processes</li>
</ul>

<h3>Data Transfers</h3>
<p>Your personal data may be shared with authorized public institutions and business partners within the framework of legal obligations and service requirements.</p>

<h3>Your Rights (KVKK Article 11)</h3>
<ul>
<li>To learn whether your personal data is being processed</li>
<li>To request information if it has been processed</li>
<li>To learn the purpose of processing and whether it is used accordingly</li>
<li>To learn whether it has been transferred domestically or abroad</li>
<li>To request correction if it is incomplete or incorrect</li>
<li>To request deletion or destruction under KVKK Article 7</li>
<li>To request notification of corrections or deletions to third parties</li>
<li>To object to results arising from analysis solely by automated systems</li>
<li>To claim compensation for damages caused by unlawful processing</li>
</ul>

<h3>Application Method</h3>
<p>To exercise your rights under KVKK, you may submit a written application to <strong>kvkk@e-menum.com</strong>.</p>
"""

    def _get_kvkk_content_ar(self):
        return """
<h3>المسؤول عن البيانات</h3>
<p><strong>E-Menum Teknoloji A.S.</strong><br>
العنوان: إسطنبول، تركيا<br>
البريد الإلكتروني: kvkk@e-menum.com</p>

<h3>معالجة البيانات الشخصية</h3>
<p>بموجب قانون حماية البيانات الشخصية رقم 6698 (KVKK)، تتم معالجة بياناتك الشخصية للأغراض التالية: تقديم الخدمات، إدارة علاقات العملاء، الفوترة والمحاسبة، والالتزامات القانونية.</p>

<h3>حقوقك</h3>
<p>يحق لك معرفة ما إذا كانت بياناتك تتم معالجتها، وطلب تصحيحها أو حذفها، والاعتراض على النتائج الناشئة عن التحليل الآلي. للتقديم، راسلنا على <strong>kvkk@e-menum.com</strong>.</p>
"""

    def _get_kvkk_content_ru(self):
        return """
<h3>Контролер даних</h3>
<p><strong>E-Menum Teknoloji A.S.</strong><br>
Адреса: Стамбул, Туреччина<br>
Електронна пошта: kvkk@e-menum.com</p>

<h3>Обробка персональних даних</h3>
<p>Відповідно до Закону № 6698 про захист персональних даних (KVKK), ваші персональні дані обробляються для таких цілей: надання послуг, управління відносинами з клієнтами, виставлення рахунків та бухгалтерія, юридичні зобов'язання.</p>

<h3>Ваші права</h3>
<p>Ви маєте право дізнатися, чи обробляються ваші дані, вимагати їх виправлення або видалення, та оскаржувати результати автоматизованого аналізу. Для подання заявки пишіть на <strong>kvkk@e-menum.com</strong>.</p>
"""

    def _get_kvkk_content_de(self):
        return """
<h3>مسئول داده‌ها</h3>
<p><strong>E-Menum Teknoloji A.S.</strong><br>
آدرس: استانبول، ترکیه<br>
ایمیل: kvkk@e-menum.com</p>

<h3>پردازش داده‌های شخصی</h3>
<p>بر اساس قانون شماره 6698 حفاظت از داده‌های شخصی (KVKK)، داده‌های شخصی شما برای اهداف زیر پردازش می‌شوند: ارائه خدمات، مدیریت روابط مشتری، صدور صورتحساب و حسابداری، و تعهدات قانونی.</p>

<h3>حقوق شما</h3>
<p>شما حق دارید بدانید آیا داده‌های شما پردازش می‌شوند، درخواست اصلاح یا حذف آن‌ها را داشته باشید و به نتایج تحلیل خودکار اعتراض کنید. برای ارسال درخواست به <strong>kvkk@e-menum.com</strong> ایمیل بزنید.</p>
"""

    def _seed_sectors(self):
        self.stdout.write('  Seeding sectors...')
        sectors = [
            {'name_tr': 'Restoran', 'name_en': 'Restaurant', 'name_ar': 'مطعم', 'name_ru': 'Ресторан', 'name_de': 'Restaurant', 'slug': 'restoran', 'icon': 'ph-fork-knife', 'color': '#1A6B5A'},
            {'name_tr': 'Kafe', 'name_en': 'Cafe', 'name_ar': 'مقهى', 'name_ru': 'Кафе', 'name_de': 'Café', 'slug': 'kafe', 'icon': 'ph-coffee', 'color': '#8B5E3C'},
            {'name_tr': 'Otel', 'name_en': 'Hotel', 'name_ar': 'فندق', 'name_ru': 'Отель', 'name_de': 'Hotel', 'slug': 'otel', 'icon': 'ph-buildings', 'color': '#2563EB'},
            {'name_tr': 'Zincir Isletme', 'name_en': 'Chain Business', 'name_ar': 'سلسلة أعمال', 'name_ru': 'Сеть', 'name_de': 'Kette', 'slug': 'zincir', 'icon': 'ph-git-branch', 'color': '#7C3AED'},
            {'name_tr': 'Fast Food', 'name_en': 'Fast Food', 'name_ar': 'وجبات سريعة', 'name_ru': 'Фастфуд', 'name_de': 'Fast Food', 'slug': 'fast-food', 'icon': 'ph-hamburger', 'color': '#DC2626'},
            {'name_tr': 'Catering', 'name_en': 'Catering', 'name_ar': 'تموين', 'name_ru': 'Кейтеринг', 'name_de': 'Catering', 'slug': 'catering', 'icon': 'ph-truck', 'color': '#EA580C'},
            {'name_tr': 'Bar & Pub', 'name_en': 'Bar & Pub', 'name_ar': 'بار', 'name_ru': 'Бар', 'name_de': 'Bar & Pub', 'slug': 'bar', 'icon': 'ph-wine', 'color': '#BE123C'},
            {'name_tr': 'Pastane', 'name_en': 'Bakery', 'name_ar': 'مخبز', 'name_ru': 'Кондитерская', 'name_de': 'Bäckerei', 'slug': 'pastane', 'icon': 'ph-cake', 'color': '#DB2777'},
        ]
        for i, data in enumerate(sectors):
            Sector.objects.update_or_create(slug=data['slug'], defaults={**data, 'sort_order': i * 10, 'is_active': True})

    def _seed_solutions(self):
        self.stdout.write('  Seeding solutions...')
        sector_map = {s.slug: s for s in Sector.objects.all()}
        solutions = [
            {'slug': 'restoran-dijital-menu', 'sector_slug': 'restoran', 'title_tr': 'Restoran Dijital Menu Cozumu', 'title_en': 'Restaurant Digital Menu Solution', 'title_ar': 'حل القائمة الرقمية للمطاعم', 'title_ru': 'Решение цифрового меню для ресторанов', 'title_de': 'Digitale Menülösung für Restaurants', 'subtitle_tr': 'Restoraninizi dijitale tasiyin, musterilerinizi etkilenin.', 'subtitle_en': 'Digitize your restaurant, impress your customers.'},
            {'slug': 'kafe-menu-yonetimi', 'sector_slug': 'kafe', 'title_tr': 'Kafe Menu Yonetimi', 'title_en': 'Cafe Menu Management', 'title_ar': 'إدارة قائمة المقهى', 'title_ru': 'Управление меню кафе', 'title_de': 'Café-Menüverwaltung', 'subtitle_tr': 'Kafenize modern bir dokunusa hazir misiniz?', 'subtitle_en': 'Ready to give your cafe a modern touch?'},
            {'slug': 'otel-oda-servisi', 'sector_slug': 'otel', 'title_tr': 'Otel Oda Servisi', 'title_en': 'Hotel Room Service', 'title_ar': 'خدمة الغرف الفندقية', 'title_ru': 'Обслуживание номеров', 'title_de': 'Hotel-Zimmerservice', 'subtitle_tr': 'Misafir deneyimini dijitallestirin.', 'subtitle_en': 'Digitize the guest experience.'},
        ]
        for i, data in enumerate(solutions):
            sector = sector_map.get(data.pop('sector_slug'))
            data['sector'] = sector
            data['sort_order'] = i * 10
            data['is_active'] = True
            data['solution_type'] = 'sector'
            SolutionPage.objects.update_or_create(slug=data['slug'], defaults=data)

    def _seed_case_studies(self):
        self.stdout.write('  Seeding case studies...')
        CaseStudy.objects.update_or_create(slug='lezzet-corner', defaults={
            'title_tr': 'Lezzet Corner: %40 Siparis Artisi', 'title_en': 'Lezzet Corner: 40% Order Increase',
            'company_name': 'Lezzet Corner', 'is_featured': True, 'is_active': True, 'sort_order': 0,
            'excerpt_tr': 'E-Menum ile dijital menuye gecen Lezzet Corner, 3 ayda siparislerini %40 artirdi.',
            'excerpt_en': 'Lezzet Corner increased orders by 40% in 3 months after switching to E-Menum digital menu.',
            'stat_1_value': '%40', 'stat_1_label_tr': 'Siparis Artisi', 'stat_1_label_en': 'Order Increase',
            'stat_2_value': '%25', 'stat_2_label_tr': 'Maliyet Dususu', 'stat_2_label_en': 'Cost Reduction',
            'stat_3_value': '3 Ay', 'stat_3_label_tr': 'Geri Odeme', 'stat_3_label_en': 'Payback Period',
            'challenge_tr': '<p>Lezzet Corner, 5 subeli bir restoran zinciriydi ve basili menulerin guncellenmesi buyuk zaman ve maliyet kaybina neden oluyordu.</p>',
            'challenge_en': '<p>Lezzet Corner was a 5-branch restaurant chain where updating printed menus caused significant time and cost waste.</p>',
            'solution_tr': '<p>E-Menum dijital menu platformuna gecis yaparak tum subelerde anlik menu guncellemesi saglanildi.</p>',
            'solution_en': '<p>By switching to E-Menum digital menu platform, instant menu updates were enabled across all branches.</p>',
            'results_tr': '<p>3 ay icerisinde siparis basina harcanan sure %30 azaldi, musteri memnuniyeti %95 seviyesine yukseldi.</p>',
            'results_en': '<p>Within 3 months, time per order decreased by 30%, and customer satisfaction rose to 95%.</p>',
            'quote_tr': 'E-Menum ile musterilerimiz artik menuyuu telefonlarindan gorup direkt siparis verebiliyor.',
            'quote_en': 'With E-Menum, our customers can now browse the menu on their phones and order directly.',
            'quote_author': 'Ahmet Yilmaz', 'quote_author_title_tr': 'Kurucu Ortak', 'quote_author_title_en': 'Co-Founder',
        })

    def _seed_roi_config(self):
        self.stdout.write('  Seeding ROI config...')
        if ROICalculatorConfig.objects.exists():
            ROICalculatorConfig.objects.update(
                avg_order_increase_pct=15.00, avg_cost_reduction_pct=30.00,
                avg_time_saved_hours=10.00, avg_menu_print_cost=2500.00,
            )
        else:
            ROICalculatorConfig.objects.create(
                avg_order_increase_pct=15.00, avg_cost_reduction_pct=30.00,
                avg_time_saved_hours=10.00, avg_menu_print_cost=2500.00,
            )

    def _seed_resource_categories(self):
        self.stdout.write('  Seeding resource categories...')
        cats = [
            {'slug': 'sektor-analizleri', 'name_tr': 'Sektor Analizleri', 'name_en': 'Industry Analysis', 'name_ar': 'تحليلات القطاع', 'name_ru': 'Анализ отрасли', 'name_de': 'Branchenanalyse'},
            {'slug': 'dijital-donusum', 'name_tr': 'Dijital Donusum', 'name_en': 'Digital Transformation', 'name_ar': 'التحول الرقمي', 'name_ru': 'Цифровая трансформация', 'name_de': 'Digitale Transformation'},
        ]
        for i, data in enumerate(cats):
            ResourceCategory.objects.update_or_create(slug=data['slug'], defaults={**data, 'sort_order': i * 10, 'is_active': True})

    def _seed_help_categories(self):
        self.stdout.write('  Seeding help categories...')
        cats = [
            {'slug': 'baslangic', 'name_tr': 'Baslangic', 'name_en': 'Getting Started', 'name_ar': 'البداية', 'name_ru': 'Начало работы', 'name_de': 'Erste Schritte', 'icon': 'ph-rocket-launch', 'description_tr': 'Platform kullanmaya baslamak icin temel rehber.', 'description_en': 'Basic guide to get started with the platform.'},
            {'slug': 'menu-yonetimi', 'name_tr': 'Menu Yonetimi', 'name_en': 'Menu Management', 'name_ar': 'إدارة القائمة', 'name_ru': 'Управление меню', 'name_de': 'Menüverwaltung', 'icon': 'ph-list-dashes', 'description_tr': 'Menu olusturma, duzenleme ve yayin.', 'description_en': 'Creating, editing, and publishing menus.'},
            {'slug': 'qr-kod', 'name_tr': 'QR Kod', 'name_en': 'QR Code', 'name_ar': 'رمز QR', 'name_ru': 'QR-код', 'name_de': 'QR-Code', 'icon': 'ph-qr-code', 'description_tr': 'QR kod olusturma ve yerlestirme.', 'description_en': 'Creating and placing QR codes.'},
            {'slug': 'siparis-takibi', 'name_tr': 'Siparis Takibi', 'name_en': 'Order Tracking', 'name_ar': 'تتبع الطلبات', 'name_ru': 'Отслеживание заказов', 'name_de': 'Bestellverfolgung', 'icon': 'ph-receipt', 'description_tr': 'Siparis yonetimi ve takip islemleri.', 'description_en': 'Order management and tracking operations.'},
            {'slug': 'faturalama', 'name_tr': 'Faturalama', 'name_en': 'Billing', 'name_ar': 'الفوترة', 'name_ru': 'Выставление счетов', 'name_de': 'Abrechnung', 'icon': 'ph-credit-card', 'description_tr': 'Plan degisiklikleri, odeme ve fatura islemleri.', 'description_en': 'Plan changes, payment, and billing operations.'},
        ]
        for i, data in enumerate(cats):
            HelpCategory.objects.update_or_create(slug=data['slug'], defaults={**data, 'sort_order': i * 10, 'is_active': True})

    def _seed_help_articles(self):
        self.stdout.write('  Seeding help articles...')
        cat_map = {c.slug: c for c in HelpCategory.objects.all()}
        articles = [
            {'slug': 'hesap-olusturma', 'cat': 'baslangic', 'title_tr': 'Hesap Nasil Olusturulur?', 'title_en': 'How to Create an Account?', 'content_tr': '<p>E-Menum platformunda hesap olusturmak icin web sitemize gidin ve "Ucretsiz Basla" butonuna tiklayin.</p>', 'content_en': '<p>To create an account on E-Menum, visit our website and click the "Start Free" button.</p>'},
            {'slug': 'menu-olusturma', 'cat': 'menu-yonetimi', 'title_tr': 'Ilk Menunuzu Olusturun', 'title_en': 'Create Your First Menu', 'content_tr': '<p>Dashboard\'a giris yaptiktan sonra sol menuden "Menuler" secenegine tiklayin ve "Yeni Menu" butonuna basin.</p>', 'content_en': '<p>After logging in, click "Menus" from the left sidebar, then click "New Menu".</p>'},
            {'slug': 'qr-kod-indirme', 'cat': 'qr-kod', 'title_tr': 'QR Kod Indirme ve Yazdirma', 'title_en': 'QR Code Download and Printing', 'content_tr': '<p>QR kodlarinizi PNG veya SVG formatinda indirip baskiya gondereblirsiniz.</p>', 'content_en': '<p>You can download your QR codes in PNG or SVG format and send them to print.</p>'},
            {'slug': 'siparis-durumu', 'cat': 'siparis-takibi', 'title_tr': 'Siparis Durumu Takibi', 'title_en': 'Order Status Tracking', 'content_tr': '<p>Gelen siparisleri gercek zamanli olarak dashboard uzerinden takip edebilirsiniz.</p>', 'content_en': '<p>You can track incoming orders in real-time through your dashboard.</p>'},
            {'slug': 'plan-degistirme', 'cat': 'faturalama', 'title_tr': 'Plan Degistirme', 'title_en': 'Changing Your Plan', 'content_tr': '<p>Mevcut planinizi istediginiz zaman yukseltebilir veya dusureblirsiniz.</p>', 'content_en': '<p>You can upgrade or downgrade your plan at any time.</p>'},
        ]
        for i, data in enumerate(articles):
            cat = cat_map.get(data.pop('cat'))
            HelpArticle.objects.update_or_create(slug=data['slug'], defaults={**data, 'category': cat, 'sort_order': i * 10, 'is_active': True})

    def _seed_career_positions(self):
        self.stdout.write('  Seeding career positions...')
        positions = [
            {'slug': 'senior-backend-developer', 'title_tr': 'Senior Backend Developer', 'title_en': 'Senior Backend Developer', 'department_tr': 'Muhendislik', 'department_en': 'Engineering', 'location_tr': 'Istanbul (Uzaktan)', 'location_en': 'Istanbul (Remote)', 'employment_type': 'full_time', 'description_tr': '<p>Node.js ve TypeScript ile yuksek olceklenebilir backend servisleri gelistirecek deneyimli bir gelistirici ariyoruz.</p>', 'description_en': '<p>We are looking for an experienced developer to build highly scalable backend services with Node.js and TypeScript.</p>'},
            {'slug': 'urun-tasarimcisi', 'title_tr': 'Urun Tasarimcisi (UI/UX)', 'title_en': 'Product Designer (UI/UX)', 'department_tr': 'Tasarim', 'department_en': 'Design', 'location_tr': 'Istanbul', 'location_en': 'Istanbul', 'employment_type': 'full_time', 'description_tr': '<p>Kullanici deneyimini sekillendirecek ve urun tasarimini yonetecek bir tasarimci ariyoruz.</p>', 'description_en': '<p>We are looking for a designer to shape user experiences and lead product design.</p>'},
            {'slug': 'satis-temsilcisi', 'title_tr': 'Satis Temsilcisi', 'title_en': 'Sales Representative', 'department_tr': 'Satis', 'department_en': 'Sales', 'location_tr': 'Istanbul', 'location_en': 'Istanbul', 'employment_type': 'full_time', 'description_tr': '<p>F&B sektorundeki isletmelere E-Menum cozumlerini tanitacak bir satis temsilcisi ariyoruz.</p>', 'description_en': '<p>We are looking for a sales representative to introduce E-Menum solutions to F&B businesses.</p>'},
        ]
        for i, data in enumerate(positions):
            CareerPosition.objects.update_or_create(slug=data['slug'], defaults={**data, 'sort_order': i * 10, 'is_active': True})

    def _seed_milestones(self):
        self.stdout.write('  Seeding milestones...')
        milestones = [
            {'year': 2023, 'quarter': 'Q1', 'title_tr': 'E-Menum Kuruldu', 'title_en': 'E-Menum Founded', 'description_tr': 'Fikir asamasindan ilk MVP\'ye.', 'description_en': 'From idea stage to first MVP.'},
            {'year': 2023, 'quarter': 'Q3', 'title_tr': 'Ilk 100 Musteri', 'title_en': 'First 100 Customers', 'description_tr': 'Beta surumunden itibaren 100 isletme platformu kullaniyor.', 'description_en': '100 businesses using the platform since beta.'},
            {'year': 2024, 'quarter': 'Q1', 'title_tr': 'AI Ozellikleri Lansman', 'title_en': 'AI Features Launch', 'description_tr': 'Yapay zeka destekli icerik uretimi ve tahminleme.', 'description_en': 'AI-powered content generation and forecasting.'},
            {'year': 2024, 'quarter': 'Q3', 'title_tr': '1000+ Isletme', 'title_en': '1000+ Businesses', 'description_tr': 'Aktif musteri sayisi 1000 i gecti.', 'description_en': 'Active customer count surpassed 1000.'},
            {'year': 2025, 'quarter': 'Q1', 'title_tr': 'Uluslararasi Acilim', 'title_en': 'International Expansion', 'description_tr': 'Arapca ve Rusca dil destegi ile bolgesel buyume.', 'description_en': 'Regional growth with Arabic and Russian language support.'},
        ]
        for data in milestones:
            Milestone.objects.update_or_create(year=data['year'], quarter=data['quarter'], defaults={**data, 'is_active': True})

    def _seed_investor_page(self):
        self.stdout.write('  Seeding investor page...')
        defaults = {
            'title_tr': 'Yatirimci Iliskileri', 'title_en': 'Investor Relations',
            'subtitle_tr': 'E-Menum in finansal performansi ve buyume stratejisi.',
            'subtitle_en': 'E-Menum financial performance and growth strategy.',
            'overview_content_tr': '<p>E-Menum, Turkiye F&B sektorundeki 350.000+ isletmeyi hedefleyen bir SaaS platformudur. Yapay zeka destekli dijital menu cozumleri ile sektorde farklilasiyoruz.</p>',
            'overview_content_en': '<p>E-Menum is a SaaS platform targeting 350,000+ businesses in Turkey\'s F&B sector. We differentiate with AI-powered digital menu solutions.</p>',
        }
        if InvestorPage.objects.exists():
            InvestorPage.objects.update(**defaults)
        else:
            InvestorPage.objects.create(**defaults)

    def _seed_partner_programs(self):
        self.stdout.write('  Seeding partner programs...')
        programs = [
            {'slug': 'referans-programi', 'title_tr': 'Referans Programi', 'title_en': 'Referral Program', 'description_tr': 'Musteri yonlendirerek gelir elde edin. Her basarili yonlendirme icin komisyon kazanin.', 'description_en': 'Earn revenue by referring customers. Earn commission for each successful referral.', 'program_type': 'referral', 'icon': 'ph-megaphone'},
            {'slug': 'entegrasyon-partnerligi', 'title_tr': 'Entegrasyon Partnerligi', 'title_en': 'Integration Partnership', 'description_tr': 'POS ve odeme sistemlerinizi E-Menum ile entegre edin.', 'description_en': 'Integrate your POS and payment systems with E-Menum.', 'program_type': 'integration', 'icon': 'ph-plugs-connected'},
            {'slug': 'bayi-programi', 'title_tr': 'Bayi Programi', 'title_en': 'Reseller Program', 'description_tr': 'E-Menum u kendi markaniz altinda satin ve teknik destek alin.', 'description_en': 'Sell E-Menum under your own brand and get technical support.', 'program_type': 'reseller', 'icon': 'ph-storefront'},
        ]
        for i, data in enumerate(programs):
            program, _ = PartnerProgram.objects.update_or_create(slug=data['slug'], defaults={**data, 'sort_order': i * 10, 'is_active': True})
            # Add tiers
            if data['slug'] == 'referans-programi':
                silver, _ = PartnerTier.objects.update_or_create(program=program, name='Silver', defaults={'description_tr': 'Baslangic seviyesi', 'description_en': 'Entry level', 'commission_pct': 10, 'sort_order': 0})
                gold, _ = PartnerTier.objects.update_or_create(program=program, name='Gold', defaults={'description_tr': 'Orta seviye', 'description_en': 'Mid level', 'commission_pct': 15, 'sort_order': 10})
                platinum, _ = PartnerTier.objects.update_or_create(program=program, name='Platinum', defaults={'description_tr': 'En ust seviye', 'description_en': 'Top level', 'commission_pct': 20, 'sort_order': 20})
                for tier in [silver, gold, platinum]:
                    PartnerBenefit.objects.get_or_create(tier=tier, text_tr='Ozel partner portali', defaults={'text_en': 'Dedicated partner portal', 'sort_order': 0})
                    PartnerBenefit.objects.get_or_create(tier=tier, text_tr='Oncelikli destek', defaults={'text_en': 'Priority support', 'sort_order': 10})

    def _seed_new_page_heroes(self):
        self.stdout.write('  Seeding new page heroes...')
        heroes = [
            {'page': 'solutions', 'title_tr': 'Isletmenize Ozel Cozumler', 'title_en': 'Solutions Tailored for Your Business', 'subtitle_tr': 'Her sektorun kendine ozgu ihtiyaclari vardir.', 'subtitle_en': 'Every sector has its unique needs.'},
            {'page': 'customers', 'title_tr': 'Musterilerimizin Basarisi, Bizim Basarimiz', 'title_en': 'Our Customers Success is Our Success', 'subtitle_tr': 'Binlerce isletme E-Menum ile dijital donusumunu tamamladi.', 'subtitle_en': 'Thousands of businesses completed their digital transformation with E-Menum.'},
            {'page': 'resources', 'title_tr': 'Bilgi Merkezi', 'title_en': 'Knowledge Center', 'subtitle_tr': 'Sektor raporlari, ucretsiz araclar ve webinarlarla isletmenizi buyutun.', 'subtitle_en': 'Grow your business with industry reports, free tools, and webinars.'},
            {'page': 'investor', 'title_tr': 'Yatirimci Iliskileri', 'title_en': 'Investor Relations', 'subtitle_tr': 'Finansal performans ve buyume stratejimiz.', 'subtitle_en': 'Our financial performance and growth strategy.'},
            {'page': 'partners', 'title_tr': 'Birlikte Buyuyelim', 'title_en': 'Grow Together', 'subtitle_tr': 'Partner programimiza katilarak gelir elde edin.', 'subtitle_en': 'Earn revenue by joining our partner program.'},
            {'page': 'support', 'title_tr': 'Size Nasil Yardimci Olabiliriz?', 'title_en': 'How Can We Help You?', 'subtitle_tr': 'Destek merkezimizde aradaginizi bulun.', 'subtitle_en': 'Find what you need in our support center.'},
            {'page': 'careers', 'title_tr': 'Gelecegi Birlikte Insa Edelim', 'title_en': 'Let Us Build the Future Together', 'subtitle_tr': 'E-Menum ekibine katilin.', 'subtitle_en': 'Join the E-Menum team.'},
            {'page': 'press', 'title_tr': 'Basin ve Medya', 'title_en': 'Press and Media', 'subtitle_tr': 'Basin bultenleri ve marka kaynaklari.', 'subtitle_en': 'Press releases and brand resources.'},
        ]
        for data in heroes:
            PageHero.objects.update_or_create(page=data['page'], defaults={**data, 'is_active': True})

    def _seed_storefront_nav_links(self):
        self.stdout.write('  Seeding storefront navigation links...')
        # Mega menu header links
        mega_items = [
            {'label_tr': 'Urun', 'label_en': 'Product', 'location': 'header', 'sort_order': 10, 'icon': 'ph-cube', 'children': [
                {'label_tr': 'Ozellikler', 'label_en': 'Features', 'url': 'website:features', 'icon': 'ph-star', 'description_tr': 'Tum platform ozellikleri', 'description_en': 'All platform features'},
                {'label_tr': 'Fiyatlandirma', 'label_en': 'Pricing', 'url': 'website:pricing', 'icon': 'ph-credit-card', 'description_tr': 'Planlar ve fiyatlar', 'description_en': 'Plans and pricing'},
            ]},
            {'label_tr': 'Cozumler', 'label_en': 'Solutions', 'location': 'header', 'sort_order': 20, 'icon': 'ph-lightbulb', 'children': [
                {'label_tr': 'Sektorel Cozumler', 'label_en': 'Industry Solutions', 'url': 'website:solutions', 'icon': 'ph-buildings', 'description_tr': 'Sektorunuze ozel cozumler', 'description_en': 'Solutions for your industry'},
                {'label_tr': 'Basari Hikayeleri', 'label_en': 'Success Stories', 'url': 'website:customers', 'icon': 'ph-trophy', 'description_tr': 'Musteri basari hikayeleri', 'description_en': 'Customer success stories'},
                {'label_tr': 'ROI Hesaplayici', 'label_en': 'ROI Calculator', 'url': 'website:roi_calculator', 'icon': 'ph-calculator', 'description_tr': 'Yatirim getirisi hesaplayin', 'description_en': 'Calculate your return on investment'},
            ]},
            {'label_tr': 'Kaynaklar', 'label_en': 'Resources', 'location': 'header', 'sort_order': 30, 'icon': 'ph-books', 'children': [
                {'label_tr': 'Kaynak Merkezi', 'label_en': 'Resource Center', 'url': 'website:resources', 'icon': 'ph-book-open', 'description_tr': 'Raporlar, araclar, webinarlar', 'description_en': 'Reports, tools, webinars'},
                {'label_tr': 'Blog', 'label_en': 'Blog', 'url': 'website:blog', 'icon': 'ph-newspaper', 'description_tr': 'Sektor haberleri ve ipuclari', 'description_en': 'Industry news and tips'},
                {'label_tr': 'Destek Merkezi', 'label_en': 'Help Center', 'url': 'website:support', 'icon': 'ph-lifebuoy', 'description_tr': 'SSS ve rehberler', 'description_en': 'FAQ and guides'},
            ]},
            {'label_tr': 'Sirket', 'label_en': 'Company', 'location': 'header', 'sort_order': 40, 'icon': 'ph-building-office', 'children': [
                {'label_tr': 'Hakkimizda', 'label_en': 'About Us', 'url': 'website:about', 'icon': 'ph-info', 'description_tr': 'Hikayemiz ve degerlerimiz', 'description_en': 'Our story and values'},
                {'label_tr': 'Kariyer', 'label_en': 'Careers', 'url': 'website:careers', 'icon': 'ph-briefcase', 'description_tr': 'Acik pozisyonlar', 'description_en': 'Open positions'},
                {'label_tr': 'Basin', 'label_en': 'Press', 'url': 'website:press', 'icon': 'ph-newspaper-clipping', 'description_tr': 'Basin bultenleri', 'description_en': 'Press releases'},
                {'label_tr': 'Partnerler', 'label_en': 'Partners', 'url': 'website:partners', 'icon': 'ph-handshake', 'description_tr': 'Partner programi', 'description_en': 'Partner program'},
            ]},
        ]

        for item in mega_items:
            children = item.pop('children', [])
            parent, _ = NavigationLink.objects.update_or_create(
                label_tr=item['label_tr'], location='header', parent__isnull=True,
                defaults={**item, 'is_active': True}
            )
            for j, child in enumerate(children):
                child['parent'] = parent
                child['location'] = 'header'
                child['sort_order'] = j * 10
                NavigationLink.objects.update_or_create(
                    url=child['url'], parent=parent,
                    defaults={**child, 'is_active': True}
                )

        # Footer Resources links
        resource_links = [
            {'label_tr': 'Kaynaklar', 'label_en': 'Resources', 'url': 'website:resources'},
            {'label_tr': 'Blog', 'label_en': 'Blog', 'url': 'website:blog'},
            {'label_tr': 'Destek', 'label_en': 'Support', 'url': 'website:support'},
        ]
        for i, link in enumerate(resource_links):
            NavigationLink.objects.update_or_create(
                url=link['url'], location='footer_resources',
                defaults={**link, 'location': 'footer_resources', 'sort_order': i * 10, 'is_active': True}
            )

        # Footer Investors links
        investor_links = [
            {'label_tr': 'Yatirimci Iliskileri', 'label_en': 'Investor Relations', 'url': 'website:investor'},
            {'label_tr': 'Partnerler', 'label_en': 'Partners', 'url': 'website:partners'},
        ]
        for i, link in enumerate(investor_links):
            NavigationLink.objects.update_or_create(
                url=link['url'], location='footer_investors',
                defaults={**link, 'location': 'footer_investors', 'sort_order': i * 10, 'is_active': True}
            )
