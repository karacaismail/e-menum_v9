"""
Management command to seed CMS content for the E-Menum storefront.

Usage:
    python manage.py seed_cms_content

Idempotent: uses update_or_create so it can be run multiple times safely.
Seeds all 34 website CMS models with rich TR+EN content.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.website.models import (
    BlogPost,
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
    help = 'Seed CMS content with rich marketing page data (idempotent)'

    def handle(self, *args, **options):
        self.stdout.write('Seeding CMS content...\n')

        self._seed_site_settings()
        self._seed_page_heroes()
        self._seed_home_sections()
        self._seed_feature_categories()
        self._seed_testimonials()
        self._seed_trust_badges()
        self._seed_trust_locations()
        self._seed_company_stats()
        self._seed_faqs()
        self._seed_team_members()
        self._seed_company_values()
        self._seed_legal_pages()
        self._seed_blog_posts()
        self._seed_plan_display_features()
        self._seed_navigation_links()
        self._seed_sectors()
        self._seed_solutions()
        self._seed_case_studies()
        self._seed_roi_config()
        self._seed_resource_categories()
        self._seed_industry_reports()
        self._seed_free_tools()
        self._seed_webinars()
        self._seed_career_positions()
        self._seed_press_releases()
        self._seed_milestones()
        self._seed_investor_page()
        self._seed_investor_financials()
        self._seed_partner_programs()
        self._seed_help_categories()
        self._seed_help_articles()
        self._seed_storefront_nav_links()

        self.stdout.write(self.style.SUCCESS('\nAll CMS content seeded successfully!'))

    # =========================================================================
    # 1. SITE SETTINGS (singleton)
    # =========================================================================
    def _seed_site_settings(self):
        obj = SiteSettings.load()
        obj.company_name_tr = 'E-Menum'
        obj.company_name_en = 'E-Menum'
        obj.tagline_tr = 'Akilli Menuler, Veri Odakli Kararlar'
        obj.tagline_en = 'Smart Menus, Data-Driven Decisions'
        obj.description_tr = (
            'Turkiye\'nin lider yapay zeka destekli dijital menu platformu. '
            '1.200+ isletme tarafindan tercih edilen E-Menum ile QR menu olusturun, '
            'siparis yonetimi yapin, gercek zamanli analitik ile isletmenizi buyutun. '
            'KVKK uyumlu, 7/24 teknik destek.'
        )
        obj.description_en = (
            'Turkey\'s leading AI-powered digital menu platform. Create QR menus, '
            'manage orders, grow your business with real-time analytics. '
            'Trusted by 1,200+ businesses. GDPR compliant, 24/7 support.'
        )
        obj.phone = '+90 850 123 4567'
        obj.email = 'info@e-menum.net'
        obj.address_tr = 'Maslak Mah. Buyukdere Cad. No:255, Nurol Plaza Kat:12, Sariyer/Istanbul'
        obj.address_en = 'Maslak Mah. Buyukdere Cad. No:255, Nurol Plaza Floor:12, Sariyer/Istanbul'
        obj.social_instagram = 'https://instagram.com/emenum'
        obj.social_twitter = 'https://twitter.com/emenum'
        obj.social_linkedin = 'https://linkedin.com/company/emenum'
        obj.social_youtube = 'https://youtube.com/@emenum'
        obj.whatsapp_number = '908501234567'
        obj.whatsapp_message_tr = 'Merhaba! E-Menum hakkinda bilgi almak ve ucretsiz demo talep etmek istiyorum.'
        obj.whatsapp_message_en = 'Hello! I would like to learn about E-Menum and request a free demo.'
        obj.cta_primary_text_tr = '14 Gun Ucretsiz Basla'
        obj.cta_primary_text_en = 'Start Free for 14 Days'
        obj.cta_primary_url = 'website:demo'
        obj.cta_secondary_text_tr = 'Canli Demo Izle'
        obj.cta_secondary_text_en = 'Watch Live Demo'
        obj.cta_secondary_url = 'website:demo'
        obj.cta_trust_text_tr = 'Kredi karti gerekmez · 2 dakikada kurulum · 1.200+ isletme tarafindan tercih ediliyor'
        obj.cta_trust_text_en = 'No credit card required · Setup in 2 minutes · Trusted by 1,200+ businesses'
        obj.login_url = '/admin/'
        obj.announcement_text_tr = 'Yeni: AI Icerik Motoru v2.0 yayinda! Urun aciklamalarinizi yapay zeka ile olusturun.'
        obj.announcement_text_en = 'New: AI Content Engine v2.0 is live! Generate product descriptions with AI.'
        obj.announcement_url = '/blog/ai-icerik-motoru-v2/'
        obj.announcement_is_active = True
        obj.cookie_banner_title_tr = 'Cerez Kullanimi'
        obj.cookie_banner_title_en = 'Cookie Usage'
        obj.cookie_banner_text_tr = 'Web sitemizde size en iyi deneyimi sunabilmek icin cerezleri kullaniyoruz. Devam ederek cerez politikamizi kabul etmis olursunuz.'
        obj.cookie_banner_text_en = 'We use cookies to provide you with the best experience on our website. By continuing, you accept our cookie policy.'
        obj.vat_no = '1234567890'
        obj.mersis_no = '0123456789012345'
        obj.trade_registry = 'Istanbul Ticaret Sicili - 123456'
        obj.status_page_url = 'https://status.e-menum.net'
        obj.save()
        self.stdout.write('  ✓ SiteSettings')

    # =========================================================================
    # 2. PAGE HEROES (15 pages)
    # =========================================================================
    def _seed_page_heroes(self):
        heroes = [
            {
                'page': 'home',
                'defaults': {
                    'title_tr': 'Dijital Menunuz ile Isletmenizi Donusturun',
                    'title_en': 'Transform Your Business with Digital Menus',
                    'subtitle_tr': 'Yapay zeka destekli dijital menu platformu ile basili menulere elveda deyin. QR menu olusturun, siparisleri yonetin, gercek zamanli analitigle isletmenizi buyutun. 1.200+ isletme tarafindan tercih ediliyor.',
                    'subtitle_en': 'Say goodbye to printed menus with our AI-powered digital menu platform. Create QR menus, manage orders, grow your business with real-time analytics. Trusted by 1,200+ businesses.',
                    'badge_text_tr': '#1 Dijital Menu Platformu',
                    'badge_text_en': '#1 Digital Menu Platform',
                    'cta_primary_text_tr': '14 Gun Ucretsiz Basla',
                    'cta_primary_text_en': 'Start Free for 14 Days',
                    'cta_primary_url': 'website:demo',
                    'cta_secondary_text_tr': 'Canli Demo Izle',
                    'cta_secondary_text_en': 'Watch Live Demo',
                    'cta_secondary_url': 'website:features',
                    'trust_text_tr': 'Kredi karti gerekmez · 2 dakikada kurulum',
                    'trust_text_en': 'No credit card required · Setup in 2 minutes',
                    'show_hero_image': True,
                    'gradient_class': 'hero-gradient-primary',
                    'is_active': True,
                },
            },
            {
                'page': 'features',
                'defaults': {
                    'title_tr': '50+ Ozellik ile Isletmenizin Her Ihtiyacina Cevap',
                    'title_en': '50+ Features for Every Need of Your Business',
                    'subtitle_tr': 'Dijital menu olusturmadan AI icerik uretimine, siparis yonetiminden gelismis analitige kadar tum ihtiyaclariniz tek platformda. Isletmenizi gelecegin teknolojisi ile yonetin.',
                    'subtitle_en': 'From digital menu creation to AI content generation, order management to advanced analytics — all your needs in one platform. Manage your business with future technology.',
                    'badge_text_tr': 'Tam Ozellik Seti',
                    'badge_text_en': 'Full Feature Set',
                    'gradient_class': 'hero-gradient-blue',
                    'is_active': True,
                },
            },
            {
                'page': 'pricing',
                'defaults': {
                    'title_tr': 'Her Butceye Uygun, Seffaf Fiyatlandirma',
                    'title_en': 'Transparent Pricing for Every Budget',
                    'subtitle_tr': 'Gizli ucret yok, sozlesme yok. Ucretsiz planla baslayin, isletmeniz buyudukce yukselin. Yillik planlarda %20 indirim. Tum planlarda 14 gun ucretsiz deneme.',
                    'subtitle_en': 'No hidden fees, no contracts. Start free and scale as you grow. 20% discount on annual plans. 14-day free trial on all plans.',
                    'badge_text_tr': '14 Gun Ucretsiz',
                    'badge_text_en': '14 Days Free',
                    'gradient_class': 'hero-gradient-green',
                    'is_active': True,
                },
            },
            {
                'page': 'about',
                'defaults': {
                    'title_tr': 'Turkiye\'nin F&B Dijitallesme Lideri',
                    'title_en': 'Turkey\'s F&B Digitalization Leader',
                    'subtitle_tr': 'E-Menum, 2024 yilinda kurulan ve Turkiye\'nin 350.000+ isletmelik F&B sektorune dijital donusum cozumleri sunan teknoloji sirketidir. Misyonumuz: her isletmeye akilli menu teknolojisi ulastirmak.',
                    'subtitle_en': 'E-Menum is a technology company founded in 2024, providing digital transformation solutions to Turkey\'s 350,000+ F&B sector. Our mission: delivering smart menu technology to every business.',
                    'badge_text_tr': 'Hakkimizda',
                    'badge_text_en': 'About Us',
                    'gradient_class': 'hero-gradient-purple',
                    'is_active': True,
                },
            },
            {
                'page': 'contact',
                'defaults': {
                    'title_tr': 'Bize Ulasin, Isletmenizi Birlikte Buyutelim',
                    'title_en': 'Contact Us, Let\'s Grow Your Business Together',
                    'subtitle_tr': '7/24 destek ekibimiz sorularinizi yanitlamak ve isletmenize ozel cozumler sunmak icin hazir. Satis, teknik destek veya is birligi icin bize hemen ulasin.',
                    'subtitle_en': 'Our 24/7 support team is ready to answer your questions and offer solutions tailored to your business. Contact us now for sales, technical support, or partnerships.',
                    'badge_text_tr': 'Iletisim',
                    'badge_text_en': 'Contact',
                    'gradient_class': 'hero-gradient-teal',
                    'is_active': True,
                },
            },
            {
                'page': 'demo',
                'defaults': {
                    'title_tr': 'Ucretsiz Demo Talep Edin, Farki Gorun',
                    'title_en': 'Request a Free Demo, See the Difference',
                    'subtitle_tr': 'Uzman ekibimiz size ozel bir demo ile E-Menum platformunu tanitstin. Isletmenize ozel cozum onerileri ve fiyatlandirma bilgisi alin. 15 dakikalik demo, sinirsiz deger.',
                    'subtitle_en': 'Our expert team will introduce the E-Menum platform with a personalized demo. Get solution recommendations and pricing info tailored to your business.',
                    'badge_text_tr': 'Ucretsiz Demo',
                    'badge_text_en': 'Free Demo',
                    'gradient_class': 'hero-gradient-orange',
                    'is_active': True,
                },
            },
            {
                'page': 'blog',
                'defaults': {
                    'title_tr': 'E-Menum Blog: F&B Sektorunde Dijital Donusum',
                    'title_en': 'E-Menum Blog: Digital Transformation in F&B',
                    'subtitle_tr': 'Restoran yonetimi, dijital menu stratejileri, AI teknolojileri ve sektor trendleri hakkinda uzman icerikleri. Isletmenizi bir adim one tasiyacak bilgiler.',
                    'subtitle_en': 'Expert content on restaurant management, digital menu strategies, AI technologies, and industry trends. Insights to take your business one step ahead.',
                    'badge_text_tr': 'Blog',
                    'badge_text_en': 'Blog',
                    'gradient_class': 'hero-gradient-indigo',
                    'is_active': True,
                },
            },
            {
                'page': 'solutions',
                'defaults': {
                    'title_tr': 'Her Sektore Ozel Dijital Menu Cozumleri',
                    'title_en': 'Digital Menu Solutions for Every Industry',
                    'subtitle_tr': 'Restorandan kafeye, otel F&B\'den catering\'e kadar her isletme tipine ozel cozumler. Sektorunuzun ihtiyaclarina uygun yapilandirma ve entegrasyon secenekleri.',
                    'subtitle_en': 'Custom solutions for every business type, from restaurants to cafes, hotel F&B to catering. Configuration and integration options suited to your industry needs.',
                    'badge_text_tr': 'Sektore Ozel',
                    'badge_text_en': 'Industry-Specific',
                    'gradient_class': 'hero-gradient-rose',
                    'is_active': True,
                },
            },
            {
                'page': 'customers',
                'defaults': {
                    'title_tr': '1.200+ Isletme E-Menum ile Buyuyor',
                    'title_en': '1,200+ Businesses Growing with E-Menum',
                    'subtitle_tr': 'Turkiye\'nin dort bir yanindaki basari hikayelerini kesfedin. Gercek isletmeler, gercek sonuclar: ortalama %40 gelir artisi, %30 maliyet dususu, %45 daha hizli servis.',
                    'subtitle_en': 'Discover success stories from all across Turkey. Real businesses, real results: average 40% revenue increase, 30% cost reduction, 45% faster service.',
                    'badge_text_tr': 'Basari Hikayeleri',
                    'badge_text_en': 'Success Stories',
                    'gradient_class': 'hero-gradient-amber',
                    'is_active': True,
                },
            },
            {
                'page': 'resources',
                'defaults': {
                    'title_tr': 'Kaynak Merkezi: Bilgi, Arac ve Rehberler',
                    'title_en': 'Resource Center: Knowledge, Tools & Guides',
                    'subtitle_tr': 'Sektor raporlari, ucretsiz araclar, webinarlar ve rehberler ile isletmenizi gelistirin. Uzman ekibimizin hazirladigi iceriklere ucretsiz erisin.',
                    'subtitle_en': 'Grow your business with industry reports, free tools, webinars, and guides. Access expert content prepared by our team for free.',
                    'badge_text_tr': 'Ucretsiz Kaynaklar',
                    'badge_text_en': 'Free Resources',
                    'gradient_class': 'hero-gradient-cyan',
                    'is_active': True,
                },
            },
            {
                'page': 'investor',
                'defaults': {
                    'title_tr': 'Yatirimci Iliskileri',
                    'title_en': 'Investor Relations',
                    'subtitle_tr': 'E-Menum Teknoloji A.S. yatirimci bilgileri, finansal raporlar, sunumlar ve sirket haberleri. Seffaf yonetim, surdurulebilir buyume.',
                    'subtitle_en': 'E-Menum Teknoloji A.S. investor information, financial reports, presentations, and company news. Transparent governance, sustainable growth.',
                    'badge_text_tr': 'Yatirimci',
                    'badge_text_en': 'Investor',
                    'gradient_class': 'hero-gradient-slate',
                    'is_active': True,
                },
            },
            {
                'page': 'partners',
                'defaults': {
                    'title_tr': 'Partner Programi: Birlikte Buyuyelim',
                    'title_en': 'Partner Program: Let\'s Grow Together',
                    'subtitle_tr': 'E-Menum partner agina katilin, komisyon kazanin ve musterilerinize katma deger sunun. Reseller, entegrasyon ve referans ortakligi secenekleri.',
                    'subtitle_en': 'Join the E-Menum partner network, earn commissions, and add value to your customers. Reseller, integration, and referral partnership options.',
                    'badge_text_tr': 'Ortaklik',
                    'badge_text_en': 'Partnership',
                    'gradient_class': 'hero-gradient-emerald',
                    'is_active': True,
                },
            },
            {
                'page': 'support',
                'defaults': {
                    'title_tr': 'Yardim Merkezi: 7/24 Teknik Destek',
                    'title_en': 'Help Center: 24/7 Technical Support',
                    'subtitle_tr': 'Detayli rehberler, adim adim kilavuzlar ve SSS ile aradiginiz cevaplari hizla bulun. Bulamadiysiniz? 7/24 destek ekibimiz bir tik uzaginizda.',
                    'subtitle_en': 'Find answers quickly with detailed guides, step-by-step manuals, and FAQ. Can\'t find it? Our 24/7 support team is just a click away.',
                    'badge_text_tr': 'Yardim',
                    'badge_text_en': 'Help',
                    'gradient_class': 'hero-gradient-sky',
                    'is_active': True,
                },
            },
            {
                'page': 'careers',
                'defaults': {
                    'title_tr': 'Kariyerinizi E-Menum\'da Sekillendirin',
                    'title_en': 'Shape Your Career at E-Menum',
                    'subtitle_tr': 'F&B teknolojisinin gelecegini birlikte insa edelim. Yenilikci, hizli buyuyen ve odullu bir ekibe katilin. Esnek calisma, rekabetci maas ve sinirsiz gelisim firsati.',
                    'subtitle_en': 'Let\'s build the future of F&B technology together. Join an innovative, fast-growing, and award-winning team. Flexible work, competitive salary, and unlimited growth.',
                    'badge_text_tr': 'Kariyer',
                    'badge_text_en': 'Careers',
                    'gradient_class': 'hero-gradient-violet',
                    'is_active': True,
                },
            },
            {
                'page': 'press',
                'defaults': {
                    'title_tr': 'Basin Odasi: Haberler ve Medya',
                    'title_en': 'Press Room: News & Media',
                    'subtitle_tr': 'E-Menum basin bultenleri, medya kiti, logo ve marka varliklari. Medya talepleri icin basin@e-menum.net adresine yazin.',
                    'subtitle_en': 'E-Menum press releases, media kit, logos, and brand assets. For media inquiries, write to press@e-menum.net.',
                    'badge_text_tr': 'Basin',
                    'badge_text_en': 'Press',
                    'gradient_class': 'hero-gradient-zinc',
                    'is_active': True,
                },
            },
        ]
        for h in heroes:
            PageHero.objects.update_or_create(page=h['page'], defaults=h['defaults'])
        self.stdout.write(f'  ✓ PageHero ({len(heroes)})')

    # =========================================================================
    # 3. HOME SECTIONS (22 sections)
    # =========================================================================
    def _seed_home_sections(self):
        # Problem-Solution cards (3)
        ps_cards = [
            {
                'section_type': 'problem_solution',
                'title_tr': 'Sorun: Basili Menuler Isletmenizi Yavaslatıyor',
                'title_en': 'Problem: Printed Menus Are Slowing Your Business',
                'description_tr': 'Her fiyat degisikliginde yeni baski maliyeti, guncelleme gecikmeleri, alerjen bilgi eksikligi ve musteri memnuniyetsizligi. Basili menuler cagdisi kaldi.',
                'description_en': 'New printing costs for every price change, update delays, missing allergen info, and customer dissatisfaction. Printed menus are outdated.',
                'icon': 'ph-warning-circle',
                'color': 'red',
                'card_variant': 'problem',
                'sort_order': 1,
                'is_active': True,
            },
            {
                'section_type': 'problem_solution',
                'title_tr': 'Cozum: E-Menum Dijital Menu Platformu',
                'title_en': 'Solution: E-Menum Digital Menu Platform',
                'description_tr': 'Aninda guncellenen dijital menu, QR kod ile kolay erisim, AI destekli icerik uretimi ve gercek zamanli analitik. Tek platform, sinirsiz imkan.',
                'description_en': 'Instantly updating digital menu, easy QR code access, AI-powered content generation, and real-time analytics. One platform, unlimited possibilities.',
                'icon': 'ph-check-circle',
                'color': 'green',
                'card_variant': 'solution',
                'sort_order': 2,
                'is_active': True,
            },
            {
                'section_type': 'problem_solution',
                'title_tr': 'Fark: Yapay Zeka Destekli Akilli Sistem',
                'title_en': 'Difference: AI-Powered Smart System',
                'description_tr': 'Sadece bir menu degil, isletmenizin dijital beyni. AI ile icerik uretimi, tahminleme motoru, otomatik raporlama ve veri odakli karar destek sistemi.',
                'description_en': 'Not just a menu, but the digital brain of your business. AI content generation, forecasting engine, automated reporting, and data-driven decision support.',
                'icon': 'ph-brain',
                'color': 'purple',
                'card_variant': 'differentiator',
                'sort_order': 3,
                'is_active': True,
            },
        ]
        for card in ps_cards:
            HomeSection.objects.update_or_create(
                section_type=card['section_type'], sort_order=card['sort_order'], defaults=card,
            )

        # Feature cards (9)
        feature_cards = [
            {'section_type': 'feature_card', 'title_tr': 'QR Menu Olusturma', 'title_en': 'QR Menu Creation', 'description_tr': 'Surukle-birak arayuzu ile profesyonel dijital menunuzu dakikalar icinde olusturun. Sinirsiz kategori ve urun destegi.', 'description_en': 'Create your professional digital menu in minutes with drag-and-drop. Unlimited categories and products.', 'icon': 'ph-qr-code', 'color': 'primary', 'sort_order': 10, 'is_active': True},
            {'section_type': 'feature_card', 'title_tr': 'AI Icerik Uretimi', 'title_en': 'AI Content Generation', 'description_tr': 'GPT destekli motor ile urun aciklamalarini otomatik uretin. Marka sesinize uygun, SEO dostu icerikler.', 'description_en': 'Auto-generate product descriptions with GPT-powered engine. Brand-consistent, SEO-friendly content.', 'icon': 'ph-magic-wand', 'color': 'purple', 'sort_order': 11, 'is_active': True},
            {'section_type': 'feature_card', 'title_tr': 'Gercek Zamanli Analitik', 'title_en': 'Real-Time Analytics', 'description_tr': 'Menu goruntuleme, QR tarama istatistikleri ve satis trendlerini canli takip edin. Ozellestirilmis dashboard.', 'description_en': 'Track menu views, QR scan statistics, and sales trends live. Customizable dashboard.', 'icon': 'ph-chart-line-up', 'color': 'blue', 'sort_order': 12, 'is_active': True},
            {'section_type': 'feature_card', 'title_tr': 'Siparis Yonetimi', 'title_en': 'Order Management', 'description_tr': 'QR menu uzerinden gelen siparisleri aninda alin. Masa bazli takip ve mutfak ekrani entegrasyonu.', 'description_en': 'Receive orders instantly via QR menu. Table-based tracking and kitchen display integration.', 'icon': 'ph-receipt', 'color': 'orange', 'sort_order': 13, 'is_active': True},
            {'section_type': 'feature_card', 'title_tr': 'Coklu Sube Yonetimi', 'title_en': 'Multi-Branch Management', 'description_tr': 'Tek panelden tum subelerinizi yonetin. Merkezi menu, sube bazli fiyatlandirma ve performans karsilastirmasi.', 'description_en': 'Manage all branches from one panel. Centralized menu, branch pricing, and performance comparison.', 'icon': 'ph-buildings', 'color': 'teal', 'sort_order': 14, 'is_active': True},
            {'section_type': 'feature_card', 'title_tr': 'Alerjen Yonetimi', 'title_en': 'Allergen Management', 'description_tr': '14 temel alerjen otomatik isaretleme, beslenme bilgisi ve ozel diyet filtreleri. Bakanlik mevzuatina tam uyumlu.', 'description_en': '14 core allergens auto-labeling, nutritional info, and special diet filters. Fully compliant with regulations.', 'icon': 'ph-warning-diamond', 'color': 'yellow', 'sort_order': 15, 'is_active': True},
            {'section_type': 'feature_card', 'title_tr': 'Musteri Analitigi', 'title_en': 'Customer Analytics', 'description_tr': 'Musteri davranis analizi, segmentasyon ve kisisellestirilmis kampanya onerileri ile satis artisi.', 'description_en': 'Customer behavior analysis, segmentation, and personalized campaign recommendations for sales growth.', 'icon': 'ph-users-three', 'color': 'rose', 'sort_order': 16, 'is_active': True},
            {'section_type': 'feature_card', 'title_tr': 'Entegrasyon Platformu', 'title_en': 'Integration Platform', 'description_tr': 'POS, muhasebe, paket servis ve odeme altyapilari ile sorunsuz entegrasyon. RESTful API ve webhook destegi.', 'description_en': 'Seamless integration with POS, accounting, delivery, and payment systems. RESTful API and webhook support.', 'icon': 'ph-plugs-connected', 'color': 'indigo', 'sort_order': 17, 'is_active': True},
            {'section_type': 'feature_card', 'title_tr': 'Raporlama ve Tahminleme', 'title_en': 'Reporting & Forecasting', 'description_tr': 'AI destekli satis tahmini, stok optimizasyonu ve otomatik rapor ciktilari ile veriye dayali yonetim.', 'description_en': 'AI-powered sales forecasting, inventory optimization, and automatic report exports for data-driven management.', 'icon': 'ph-chart-bar', 'color': 'emerald', 'sort_order': 18, 'is_active': True},
        ]
        for card in feature_cards:
            HomeSection.objects.update_or_create(
                section_type=card['section_type'], sort_order=card['sort_order'], defaults=card,
            )

        # How It Works (4 steps)
        steps = [
            {'section_type': 'how_it_works', 'title_tr': 'Ucretsiz Kaydolun', 'title_en': 'Sign Up Free', 'description_tr': 'E-posta adresiniz ve isletme bilgilerinizle 2 dakikada kayit olun. Kredi karti gerekmez, 14 gun ucretsiz deneyin.', 'description_en': 'Register in 2 minutes with your email. No credit card required, try free for 14 days.', 'icon': 'ph-user-plus', 'color': 'primary', 'step_number': 1, 'sort_order': 20, 'is_active': True},
            {'section_type': 'how_it_works', 'title_tr': 'Menunuzu Olusturun', 'title_en': 'Create Your Menu', 'description_tr': 'Surukle-birak arayuzu ile kategoriler ve urunler ekleyin. AI ile aciklamalari otomatik uretin.', 'description_en': 'Add categories and products with drag-and-drop. Auto-generate descriptions with AI.', 'icon': 'ph-pencil-line', 'color': 'blue', 'step_number': 2, 'sort_order': 21, 'is_active': True},
            {'section_type': 'how_it_works', 'title_tr': 'QR Kodunuzu Yerlestirin', 'title_en': 'Place Your QR Codes', 'description_tr': 'Markaniza ozel QR kodlar olusturun ve masalariniza yerlestirin. Musterileriniz aninda menuye ulassin.', 'description_en': 'Create branded QR codes and place on tables. Your customers access the menu instantly.', 'icon': 'ph-qr-code', 'color': 'green', 'step_number': 3, 'sort_order': 22, 'is_active': True},
            {'section_type': 'how_it_works', 'title_tr': 'Analiz Edin ve Buyuyun', 'title_en': 'Analyze and Grow', 'description_tr': 'Gercek zamanli analitigle verileri inceleyin. AI onerileriyle menunuzu optimize edin ve gelirinizi artirin.', 'description_en': 'Review data with real-time analytics. Optimize your menu with AI recommendations and increase revenue.', 'icon': 'ph-rocket-launch', 'color': 'purple', 'step_number': 4, 'sort_order': 23, 'is_active': True},
        ]
        for step in steps:
            HomeSection.objects.update_or_create(
                section_type=step['section_type'], sort_order=step['sort_order'], defaults=step,
            )

        # Stat Counters (6)
        stats = [
            {'section_type': 'stat_counter', 'title_tr': 'Hedef Isletme', 'title_en': 'Target Businesses', 'description_tr': 'Turkiye genelinde hedefledigimiz F&B isletme sayisi', 'description_en': 'F&B businesses we target across Turkey', 'stat_value': '350.000', 'stat_suffix': '+', 'icon': 'ph-storefront', 'color': 'primary', 'sort_order': 30, 'is_active': True},
            {'section_type': 'stat_counter', 'title_tr': 'Aktif Musteri', 'title_en': 'Active Customers', 'description_tr': 'E-Menum\'u aktif kullanan isletme', 'description_en': 'Businesses actively using E-Menum', 'stat_value': '1.200', 'stat_suffix': '+', 'icon': 'ph-handshake', 'color': 'green', 'sort_order': 31, 'is_active': True},
            {'section_type': 'stat_counter', 'title_tr': 'Aylik QR Tarama', 'title_en': 'Monthly QR Scans', 'description_tr': 'Platformumuz uzerinden aylik QR tarama', 'description_en': 'Monthly QR scans through our platform', 'stat_value': '15M', 'stat_suffix': '+', 'icon': 'ph-scan', 'color': 'blue', 'sort_order': 32, 'is_active': True},
            {'section_type': 'stat_counter', 'title_tr': 'Calisma Suresi', 'title_en': 'Uptime', 'description_tr': 'Platformun kesintisiz calisma orani', 'description_en': 'Platform uninterrupted uptime rate', 'stat_value': '99.9', 'stat_suffix': '%', 'icon': 'ph-shield-check', 'color': 'emerald', 'sort_order': 33, 'is_active': True},
            {'section_type': 'stat_counter', 'title_tr': 'Teknik Destek', 'title_en': 'Technical Support', 'description_tr': 'Yil boyunca 7/24 kesintisiz destek', 'description_en': 'Year-round 24/7 uninterrupted support', 'stat_value': '7/24', 'stat_suffix': '', 'icon': 'ph-headset', 'color': 'orange', 'sort_order': 34, 'is_active': True},
            {'section_type': 'stat_counter', 'title_tr': 'Platform Ozelligi', 'title_en': 'Platform Features', 'description_tr': 'Isletmenizin her ihtiyacina cevap veren ozellik', 'description_en': 'Features addressing every business need', 'stat_value': '50', 'stat_suffix': '+', 'icon': 'ph-puzzle-piece', 'color': 'purple', 'sort_order': 35, 'is_active': True},
        ]
        for stat in stats:
            HomeSection.objects.update_or_create(
                section_type=stat['section_type'], sort_order=stat['sort_order'], defaults=stat,
            )

        total = len(ps_cards) + len(feature_cards) + len(steps) + len(stats)
        self.stdout.write(f'  ✓ HomeSection ({total})')

    # =========================================================================
    # 4. FEATURE CATEGORIES (8 categories + bullets)
    # =========================================================================
    def _seed_feature_categories(self):
        cats = [
            {'sort_order': 1, 'defaults': {'title_tr': 'Dijital Menu Olusturma ve Yonetimi', 'title_en': 'Digital Menu Creation & Management', 'description_tr': 'Sinirsiz kategori ve urun ile profesyonel dijital menunuzu saniyeler icinde olusturun. Surukle-birak arayuzu, canli onizleme ve aninda yayinlama ile menu yonetimini kolaylastirin.', 'description_en': 'Create your professional digital menu in seconds with unlimited categories and products. Simplify menu management with drag-and-drop, live preview, and instant publishing.', 'badge_text_tr': 'Temel Ozellik', 'badge_text_en': 'Core Feature', 'badge_color': 'primary', 'icon': 'ph-qr-code', 'image_alt_tr': 'E-Menum dijital menu ekrani', 'image_alt_en': 'E-Menum digital menu screen', 'layout_reversed': False, 'is_active': True}, 'bullets': [('Sinirsiz kategori, urun ve varyant olusturma', 'Unlimited categories, products, and variants'), ('Surukle-birak ile kolay siralama', 'Easy sorting with drag-and-drop'), ('Canli onizleme ve tek tikla yayinlama', 'Live preview and one-click publishing'), ('Coklu dil destegi (TR, EN ve 5+ dil)', 'Multi-language support (TR, EN and 5+ languages)'), ('Ozel tema tasarimi ve marka renkleri', 'Custom theme design and brand colors'), ('Toplu urun yukleme ve Excel/CSV aktarimi', 'Bulk upload and Excel/CSV import')]},
            {'sort_order': 2, 'defaults': {'title_tr': 'Yapay Zeka Icerik Uretimi', 'title_en': 'AI Content Generation', 'description_tr': 'GPT destekli icerik motoru ile urun aciklamalari, kampanya metinleri ve sosyal medya paylasimlari otomatik uretilir. Markaniza ozel dil ayarlari ile tutarli marka sesi.', 'description_en': 'Auto-generate product descriptions, campaign texts, and social media posts with GPT-powered engine. Consistent brand voice with custom language settings.', 'badge_text_tr': 'AI Destekli', 'badge_text_en': 'AI-Powered', 'badge_color': 'purple', 'icon': 'ph-magic-wand', 'image_alt_tr': 'E-Menum AI icerik uretimi', 'image_alt_en': 'E-Menum AI content generation', 'layout_reversed': True, 'is_active': True}, 'bullets': [('Tek tikla profesyonel urun aciklamalari', 'Professional product descriptions with one click'), ('Sektor ve mutfak tipine ozel sablonlar', 'Templates specific to industry and cuisine type'), ('Kampanya ve promosyon metinleri otomatik', 'Automatic campaign and promotion texts'), ('Sosyal medya metinleri ve hashtag onerileri', 'Social media texts and hashtag suggestions'), ('Marka sesi ve ton ayarlari', 'Brand voice and tone settings')]},
            {'sort_order': 3, 'defaults': {'title_tr': 'Gercek Zamanli Analitik', 'title_en': 'Real-Time Analytics', 'description_tr': 'Menu goruntuleme, QR tarama istatistikleri, en cok tercih edilen urunler ve satis trendlerini canli takip edin. Ozellestirilmis dashboard ile isletmenizin nabzini tutun.', 'description_en': 'Track menu views, QR scans, most popular products, and sales trends live. Keep your pulse on business with customizable dashboards.', 'badge_text_tr': 'Canli Veri', 'badge_text_en': 'Live Data', 'badge_color': 'blue', 'icon': 'ph-chart-line-up', 'image_alt_tr': 'E-Menum analitik dashboard', 'image_alt_en': 'E-Menum analytics dashboard', 'layout_reversed': False, 'is_active': True}, 'bullets': [('Gercek zamanli menu ve QR tarama istatistikleri', 'Real-time menu and QR scan statistics'), ('En cok goruntulenen urun analizi', 'Most viewed product analysis'), ('Gunluk, haftalik ve aylik trend raporlari', 'Daily, weekly, and monthly trend reports'), ('Ozellestirilmis widget ve dashboard', 'Customizable widgets and dashboard'), ('Otomatik haftalik ozet rapor', 'Automatic weekly summary reports'), ('Sube bazli performans karsilastirma', 'Branch-level performance comparison')]},
            {'sort_order': 4, 'defaults': {'title_tr': 'Siparis Yonetimi ve Masa Takibi', 'title_en': 'Order Management & Table Tracking', 'description_tr': 'QR menu uzerinden gelen siparisleri aninda alin. Masa bazli siparis takibi, mutfak ekrani entegrasyonu ve otomatik bildirimler ile servis suresi %45 kisaliyor.', 'description_en': 'Receive orders instantly via QR menu. Table-based order tracking, kitchen display integration, and automatic notifications reduce service time by 45%.', 'badge_text_tr': 'Hizli Servis', 'badge_text_en': 'Fast Service', 'badge_color': 'orange', 'icon': 'ph-receipt', 'image_alt_tr': 'E-Menum siparis yonetimi', 'image_alt_en': 'E-Menum order management', 'layout_reversed': True, 'is_active': True}, 'bullets': [('QR kod ile masadan aninda siparis', 'Instant ordering from table via QR'), ('Masa bazli siparis takibi ve durum guncelleme', 'Table-based order tracking and status'), ('Mutfak ekrani (KDS) entegrasyonu', 'Kitchen display system (KDS) integration'), ('Garson cagirma ve hesap isteme', 'Waiter call and bill request'), ('Siparis gecmisi ve tekrar siparis kolayligi', 'Order history and easy reorder')]},
            {'sort_order': 5, 'defaults': {'title_tr': 'Coklu Sube ve Zincir Yonetimi', 'title_en': 'Multi-Branch & Chain Management', 'description_tr': 'Tek merkezi panelden tum subelerinizi yonetin. Sube bazli fiyatlandirma, merkezi menu yonetimi ve karsilastirmali performans raporlari.', 'description_en': 'Manage all branches from a single panel. Branch-specific pricing, centralized menu management, and comparative performance reports.', 'badge_text_tr': 'Kurumsal', 'badge_text_en': 'Enterprise', 'badge_color': 'teal', 'icon': 'ph-buildings', 'image_alt_tr': 'E-Menum coklu sube yonetimi', 'image_alt_en': 'E-Menum multi-branch management', 'layout_reversed': False, 'is_active': True}, 'bullets': [('Tek panelden sinirsiz sube yonetimi', 'Unlimited branches from one panel'), ('Merkezi menu ile tum subelere dagitim', 'Centralized menu distribution to all branches'), ('Sube bazli fiyatlandirma ve kampanya', 'Branch-specific pricing and campaigns'), ('Subeler arasi performans karsilastirmasi', 'Inter-branch performance comparison'), ('Yetkilendirilmis kullanici rolleri', 'Authorized user roles and access control'), ('Merkez ofis ve sube bazli raporlama', 'HQ and branch-level reporting')]},
            {'sort_order': 6, 'defaults': {'title_tr': 'Alerjen Yonetimi ve Yasal Uyumluluk', 'title_en': 'Allergen Management & Legal Compliance', 'description_tr': 'KVKK ve bakanlik zorunluluguna tam uyumluluk. 14 temel alerjen otomatik isaretleme, beslenme bilgisi ve ozel diyet filtreleme.', 'description_en': 'Full compliance with regulations. 14 core allergen auto-labeling, nutritional info, and special diet filtering.', 'badge_text_tr': 'Yasal Uyumlu', 'badge_text_en': 'Compliant', 'badge_color': 'yellow', 'icon': 'ph-warning-diamond', 'image_alt_tr': 'E-Menum alerjen yonetimi', 'image_alt_en': 'E-Menum allergen management', 'layout_reversed': True, 'is_active': True}, 'bullets': [('14 temel alerjenin otomatik isaretlenmesi', 'Automatic labeling of 14 core allergens'), ('Bakanlik mevzuatina tam uyumlu bilgilendirme', 'Fully compliant allergen information'), ('Beslenme bilgisi ve kalori gosterimi', 'Nutritional info and calorie display'), ('Vegan, glutensiz, laktozsuz diyet filtreleri', 'Vegan, gluten-free, lactose-free filters'), ('Alerjen bazli uyari sistemi', 'Allergen-based alert system')]},
            {'sort_order': 7, 'defaults': {'title_tr': 'Entegrasyon ve Acik API', 'title_en': 'Integration & Open API', 'description_tr': 'POS, muhasebe, paket servis ve odeme altyapilari ile sorunsuz entegrasyon. RESTful API, webhook destegi ve hazir entegrasyon kutuphanesi.', 'description_en': 'Seamless integration with POS, accounting, delivery, and payment systems. RESTful API, webhook support, and ready integration library.', 'badge_text_tr': 'Acik Ekosistem', 'badge_text_en': 'Open Ecosystem', 'badge_color': 'indigo', 'icon': 'ph-plugs-connected', 'image_alt_tr': 'E-Menum entegrasyon haritasi', 'image_alt_en': 'E-Menum integration map', 'layout_reversed': False, 'is_active': True}, 'bullets': [('POS sistemi entegrasyonlari', 'POS system integrations'), ('Paket servis platformu entegrasyonu', 'Delivery platform integration'), ('Muhasebe yazilimi baglantisi', 'Accounting software connection'), ('RESTful API ve sandbox ortami', 'RESTful API and sandbox environment'), ('Webhook ile gercek zamanli senkronizasyon', 'Real-time sync with webhooks'), ('OAuth 2.0 guvenli yetkilendirme', 'Secure OAuth 2.0 authorization')]},
            {'sort_order': 8, 'defaults': {'title_tr': 'Raporlama ve Tahminleme Motoru', 'title_en': 'Reporting & Forecasting Engine', 'description_tr': 'Gelismis raporlama ve AI destekli tahminleme ile gelir, maliyet, kar marji ve satis trendlerini analiz edin. Stok optimizasyonu ve otomatik rapor ciktilari.', 'description_en': 'Analyze revenue, cost, margin, and trends with advanced reporting and AI forecasting. Inventory optimization and automatic report exports.', 'badge_text_tr': 'Akilli Raporlama', 'badge_text_en': 'Smart Reporting', 'badge_color': 'emerald', 'icon': 'ph-chart-bar', 'image_alt_tr': 'E-Menum raporlama paneli', 'image_alt_en': 'E-Menum reporting panel', 'layout_reversed': True, 'is_active': True}, 'bullets': [('Gelir, maliyet ve kar marji analizleri', 'Revenue, cost, and margin analysis'), ('AI destekli satis tahmini', 'AI-powered sales forecasting'), ('Stok optimizasyonu ve israf azaltma', 'Inventory optimization and waste reduction'), ('Otomatik Excel, PDF ve CSV rapor', 'Automatic Excel, PDF, and CSV reports'), ('Donem bazli performans karsilastirmasi', 'Period-based performance comparison')]},
        ]
        count = 0
        for cat_data in cats:
            bullets = cat_data.pop('bullets')
            cat, _ = FeatureCategory.objects.update_or_create(sort_order=cat_data['sort_order'], defaults=cat_data['defaults'])
            for idx, (tr, en) in enumerate(bullets, start=1):
                FeatureBullet.objects.update_or_create(category=cat, sort_order=idx, defaults={'text_tr': tr, 'text_en': en, 'is_active': True})
            count += 1
        self.stdout.write(f'  ✓ FeatureCategory ({count}) + bullets')

    # =========================================================================
    # 5. TESTIMONIALS (12)
    # =========================================================================
    def _seed_testimonials(self):
        items = [
            {'author_name_tr': 'Mehmet Yilmaz', 'author_name_en': 'Mehmet Yilmaz', 'author_role_or_business_tr': 'Sahip, Lezzet Duragi Restoran', 'author_role_or_business_en': 'Owner, Lezzet Duragi Restaurant', 'author_location_tr': 'Istanbul, Kadikoy', 'author_location_en': 'Istanbul, Kadikoy', 'business_type_label_tr': 'Restoran', 'business_type_label_en': 'Restaurant', 'quote_tr': 'E-Menum ile basili menu maliyetlerimiz sifira indi. Ustelik musterilerimiz QR menuden siparis vermeye bayiliyor. Ilk ayda ciromuz %25 artti.', 'quote_en': 'Our printed menu costs dropped to zero with E-Menum. Plus, our customers love ordering via QR menu. Revenue increased 25% in the first month.', 'rating': 5, 'avatar_color': 'primary', 'sort_order': 1, 'is_active': True},
            {'author_name_tr': 'Ayse Demir', 'author_name_en': 'Ayse Demir', 'author_role_or_business_tr': 'Genel Mudur, Cafe Mola Zinciri', 'author_role_or_business_en': 'GM, Cafe Mola Chain', 'author_location_tr': 'Ankara, Cankaya', 'author_location_en': 'Ankara, Cankaya', 'business_type_label_tr': 'Kafe Zinciri', 'business_type_label_en': 'Cafe Chain', 'quote_tr': '5 subemizi tek panelden yonetiyoruz. Merkezi menu degisiklikleri aninda tum subelere yansıyor. Operasyonel verimliligimiz inanilmaz artti.', 'quote_en': 'We manage 5 branches from one panel. Central menu changes reflect instantly across all branches. Our operational efficiency increased incredibly.', 'rating': 5, 'avatar_color': 'emerald', 'sort_order': 2, 'is_active': True},
            {'author_name_tr': 'Ali Kaya', 'author_name_en': 'Ali Kaya', 'author_role_or_business_tr': 'Kurucu, The Burger House', 'author_role_or_business_en': 'Founder, The Burger House', 'author_location_tr': 'Izmir, Alsancak', 'author_location_en': 'Izmir, Alsancak', 'business_type_label_tr': 'Fast Food', 'business_type_label_en': 'Fast Food', 'quote_tr': 'AI icerik motoru ile tum urunlerimizin aciklamalarini yeniledik. Profesyonel ve tutarli bir menu dili olusturduk. Harika bir ozellik!', 'quote_en': 'We refreshed all product descriptions with the AI content engine. Created a professional and consistent menu language. Amazing feature!', 'rating': 5, 'avatar_color': 'amber', 'sort_order': 3, 'is_active': True},
            {'author_name_tr': 'Fatma Ozturk', 'author_name_en': 'Fatma Ozturk', 'author_role_or_business_tr': 'Isletme Muduru, Deniz Restaurant', 'author_role_or_business_en': 'Operations Manager, Deniz Restaurant', 'author_location_tr': 'Antalya, Konyaalti', 'author_location_en': 'Antalya, Konyaalti', 'business_type_label_tr': 'Balik Restoran', 'business_type_label_en': 'Seafood Restaurant', 'quote_tr': 'Turistik bolgede oldugumuz icin coklu dil destegi hayat kurtarici oldu. Ingilizce, Almanca ve Rusca menumuz var. Musterilerimiz cok memnun.', 'quote_en': 'Multi-language support was a lifesaver since we are in a tourist area. We have English, German, and Russian menus. Customers are very happy.', 'rating': 5, 'avatar_color': 'blue', 'sort_order': 4, 'is_active': True},
            {'author_name_tr': 'Hakan Arslan', 'author_name_en': 'Hakan Arslan', 'author_role_or_business_tr': 'Sahip, Anadolu Sofrasi', 'author_role_or_business_en': 'Owner, Anadolu Sofrasi', 'author_location_tr': 'Bursa, Osmangazi', 'author_location_en': 'Bursa, Osmangazi', 'business_type_label_tr': 'Geleneksel Restoran', 'business_type_label_en': 'Traditional Restaurant', 'quote_tr': 'Alerjen yonetimi ozelliği mevzuat uyumlulugumuz icin mukemmel oldu. 14 alerjen otomatik isaretleniyor. Artik yasal sorunlardan endiselenmiyoruz.', 'quote_en': 'Allergen management feature was perfect for our regulatory compliance. 14 allergens are auto-labeled. No more worrying about legal issues.', 'rating': 5, 'avatar_color': 'rose', 'sort_order': 5, 'is_active': True},
            {'author_name_tr': 'Zeynep Sahin', 'author_name_en': 'Zeynep Sahin', 'author_role_or_business_tr': 'Pazarlama Muduru, Green Bowl', 'author_role_or_business_en': 'Marketing Manager, Green Bowl', 'author_location_tr': 'Istanbul, Besiktas', 'author_location_en': 'Istanbul, Besiktas', 'business_type_label_tr': 'Saglikli Beslenme', 'business_type_label_en': 'Healthy Food', 'quote_tr': 'Analitik dashboard ile en cok satan urunlerimizi ve musteri trendlerini takip ediyoruz. Veri odakli kararlar almaya basladik. Gelir %35 artti.', 'quote_en': 'We track bestsellers and customer trends with the analytics dashboard. Started making data-driven decisions. Revenue increased 35%.', 'rating': 5, 'avatar_color': 'violet', 'sort_order': 6, 'is_active': True},
            {'author_name_tr': 'Emre Can', 'author_name_en': 'Emre Can', 'author_role_or_business_tr': 'IT Muduru, Grand Hotel Istanbul', 'author_role_or_business_en': 'IT Manager, Grand Hotel Istanbul', 'author_location_tr': 'Istanbul, Sisli', 'author_location_en': 'Istanbul, Sisli', 'business_type_label_tr': 'Otel F&B', 'business_type_label_en': 'Hotel F&B', 'quote_tr': 'Otelimizin 3 restorani ve bar menulerini tek panelden yonetiyoruz. POS entegrasyonu sayesinde siparisler otomatik adisyona dususyor. Mukemmel!', 'quote_en': 'We manage menus for our hotel\'s 3 restaurants and bar from one panel. Orders auto-sync to POS thanks to integration. Excellent!', 'rating': 5, 'avatar_color': 'indigo', 'sort_order': 7, 'is_active': True},
            {'author_name_tr': 'Selin Yildiz', 'author_name_en': 'Selin Yildiz', 'author_role_or_business_tr': 'Sahip, Tatli Dukkan', 'author_role_or_business_en': 'Owner, Tatli Dukkan', 'author_location_tr': 'Eskisehir', 'author_location_en': 'Eskisehir', 'business_type_label_tr': 'Pastane', 'business_type_label_en': 'Pastry Shop', 'quote_tr': 'Her gun degisen taze urunlerimizi aninda menuye ekliyoruz. Baski derdi bitti, musteriler vitrin disindaki urunleri de gorebiliyor.', 'quote_en': 'We instantly add our daily fresh products to the menu. No more printing hassle, customers can see products beyond the display.', 'rating': 4, 'avatar_color': 'pink', 'sort_order': 8, 'is_active': True},
            {'author_name_tr': 'Burak Celik', 'author_name_en': 'Burak Celik', 'author_role_or_business_tr': 'Kurucu, Pizza Lab', 'author_role_or_business_en': 'Founder, Pizza Lab', 'author_location_tr': 'Gaziantep', 'author_location_en': 'Gaziantep', 'business_type_label_tr': 'Pizzaci', 'business_type_label_en': 'Pizzeria', 'quote_tr': 'Siparis yonetimi modulu ile garson hatalari minimuma indi. Musteriler masadan direkt siparis veriyor, mutfak ekraninda aninda goruyoruz.', 'quote_en': 'Waiter errors minimized with order management module. Customers order directly from table, we see it instantly on kitchen display.', 'rating': 5, 'avatar_color': 'orange', 'sort_order': 9, 'is_active': True},
            {'author_name_tr': 'Deniz Korkmaz', 'author_name_en': 'Deniz Korkmaz', 'author_role_or_business_tr': 'Genel Koordinator, Catering Plus', 'author_role_or_business_en': 'General Coordinator, Catering Plus', 'author_location_tr': 'Istanbul, Maslak', 'author_location_en': 'Istanbul, Maslak', 'business_type_label_tr': 'Catering', 'business_type_label_en': 'Catering', 'quote_tr': 'Her etkinlik icin ozel dijital menu olusturuyoruz. Menu hazirlama suremiz 3 gunden saatlere dustu. Musterilerimiz profesyonelligimize hayran kaliyor.', 'quote_en': 'We create custom digital menus for each event. Menu prep time dropped from 3 days to hours. Clients are amazed by our professionalism.', 'rating': 5, 'avatar_color': 'teal', 'sort_order': 10, 'is_active': True},
            {'author_name_tr': 'Oguz Yildirim', 'author_name_en': 'Oguz Yildirim', 'author_role_or_business_tr': 'Isletme Sahibi, Kebapci Oguz', 'author_role_or_business_en': 'Owner, Kebapci Oguz', 'author_location_tr': 'Adana', 'author_location_en': 'Adana', 'business_type_label_tr': 'Kebapci', 'business_type_label_en': 'Kebab Restaurant', 'quote_tr': 'Teknolojiyle aram iyi degildi ama E-Menum o kadar kolay ki, kendi basima tum menuyu olusturdum. Destek ekibi de harika, 5 dakikada cozum buluyorlar.', 'quote_en': 'I wasn\'t good with technology but E-Menum is so easy that I created the entire menu myself. Support team is great too, they solve issues in 5 minutes.', 'rating': 4, 'avatar_color': 'red', 'sort_order': 11, 'is_active': True},
            {'author_name_tr': 'Elif Aksoy', 'author_name_en': 'Elif Aksoy', 'author_role_or_business_tr': 'Kurucu Ortak, Acai Corner', 'author_role_or_business_en': 'Co-Founder, Acai Corner', 'author_location_tr': 'Istanbul, Bebek', 'author_location_en': 'Istanbul, Bebek', 'business_type_label_tr': 'Saglikli Kafe', 'business_type_label_en': 'Healthy Cafe', 'quote_tr': 'Haftalik rapor otomatik e-postamiza geliyor. Hangi urunlerin trend oldugunu, hangi saatlerde yogunluk oldugunu net goruyoruz. Stratejimizi buna gore kuruyoruz.', 'quote_en': 'Weekly report comes to our email automatically. We clearly see trending products and peak hours. We build our strategy accordingly.', 'rating': 5, 'avatar_color': 'green', 'sort_order': 12, 'is_active': True},
        ]
        for t in items:
            Testimonial.objects.update_or_create(author_name_tr=t['author_name_tr'], defaults=t)
        self.stdout.write(f'  ✓ Testimonial ({len(items)})')

    # =========================================================================
    # 6. TRUST BADGES (5)
    # =========================================================================
    def _seed_trust_badges(self):
        badges = [
            {'sort_order': 1, 'label_tr': 'KVKK Uyumlu', 'label_en': 'GDPR Compliant', 'icon': 'ph-shield-check', 'is_active': True},
            {'sort_order': 2, 'label_tr': 'SSL Guvenlik', 'label_en': 'SSL Secured', 'icon': 'ph-lock-key', 'is_active': True},
            {'sort_order': 3, 'label_tr': '%99.9 Uptime', 'label_en': '99.9% Uptime', 'icon': 'ph-cloud-check', 'is_active': True},
            {'sort_order': 4, 'label_tr': '7/24 Destek', 'label_en': '24/7 Support', 'icon': 'ph-headset', 'is_active': True},
            {'sort_order': 5, 'label_tr': 'ISO 27001', 'label_en': 'ISO 27001', 'icon': 'ph-certificate', 'is_active': True},
        ]
        for b in badges:
            TrustBadge.objects.update_or_create(sort_order=b['sort_order'], defaults=b)
        self.stdout.write(f'  ✓ TrustBadge ({len(badges)})')

    # =========================================================================
    # 7. TRUST LOCATIONS (12)
    # =========================================================================
    def _seed_trust_locations(self):
        locs = [
            (1, 'Istanbul — 450+ isletme', 'Istanbul — 450+ businesses'),
            (2, 'Ankara — 120+ isletme', 'Ankara — 120+ businesses'),
            (3, 'Izmir — 95+ isletme', 'Izmir — 95+ businesses'),
            (4, 'Antalya — 80+ isletme', 'Antalya — 80+ businesses'),
            (5, 'Bursa — 65+ isletme', 'Bursa — 65+ businesses'),
            (6, 'Mugla — 55+ isletme', 'Mugla — 55+ businesses'),
            (7, 'Adana — 45+ isletme', 'Adana — 45+ businesses'),
            (8, 'Gaziantep — 40+ isletme', 'Gaziantep — 40+ businesses'),
            (9, 'Konya — 35+ isletme', 'Konya — 35+ businesses'),
            (10, 'Trabzon — 30+ isletme', 'Trabzon — 30+ businesses'),
            (11, 'Eskisehir — 25+ isletme', 'Eskisehir — 25+ businesses'),
            (12, 'Diger Iller — 160+ isletme', 'Other Cities — 160+ businesses'),
        ]
        for so, tr, en in locs:
            TrustLocation.objects.update_or_create(sort_order=so, defaults={'text_tr': tr, 'text_en': en, 'sort_order': so, 'is_active': True})
        self.stdout.write(f'  ✓ TrustLocation ({len(locs)})')

    # =========================================================================
    # 8. COMPANY STATS (6)
    # =========================================================================
    def _seed_company_stats(self):
        stats = [
            {'sort_order': 1, 'value_tr': '350.000+', 'value_en': '350,000+', 'label_tr': 'Hedef Isletme', 'label_en': 'Target Businesses', 'is_active': True},
            {'sort_order': 2, 'value_tr': '1.200+', 'value_en': '1,200+', 'label_tr': 'Aktif Musteri', 'label_en': 'Active Customers', 'is_active': True},
            {'sort_order': 3, 'value_tr': '15M+', 'value_en': '15M+', 'label_tr': 'Aylik QR Tarama', 'label_en': 'Monthly QR Scans', 'is_active': True},
            {'sort_order': 4, 'value_tr': '%99.9', 'value_en': '99.9%', 'label_tr': 'Uptime Orani', 'label_en': 'Uptime Rate', 'is_active': True},
            {'sort_order': 5, 'value_tr': '7/24', 'value_en': '24/7', 'label_tr': 'Teknik Destek', 'label_en': 'Technical Support', 'is_active': True},
            {'sort_order': 6, 'value_tr': '50+', 'value_en': '50+', 'label_tr': 'Platform Ozelligi', 'label_en': 'Platform Features', 'is_active': True},
        ]
        for s in stats:
            CompanyStat.objects.update_or_create(sort_order=s['sort_order'], defaults=s)
        self.stdout.write(f'  ✓ CompanyStat ({len(stats)})')

    # =========================================================================
    # 9. FAQS (30)
    # =========================================================================
    def _seed_faqs(self):
        faqs = [
            # PRICING (8)
            {'question_tr': 'E-Menum\'un fiyatlandirmasi nasil?', 'question_en': 'How is E-Menum priced?', 'answer_tr': 'Ucretsiz planimiz ile hemen baslayabilirsiniz. Ucretli planlarimiz aylik 2.000 TL\'den baslar ve isletme buyuklugune gore olceklenir. Tum planlarda 14 gun ucretsiz deneme sunuyoruz.', 'answer_en': 'You can start immediately with our free plan. Paid plans start from 2,000 TL/month and scale by business size. We offer a 14-day free trial on all plans.', 'page': 'pricing', 'sort_order': 1, 'is_active': True},
            {'question_tr': 'Yillik planlarda indirim var mi?', 'question_en': 'Is there a discount on annual plans?', 'answer_tr': 'Evet! Yillik planlarda %20 indirim uyguluyoruz. Ayrica 6 aylik odemede %10 indirim secenegi de mevcuttur.', 'answer_en': 'Yes! We offer 20% discount on annual plans. A 10% discount option is also available for 6-month payments.', 'page': 'pricing', 'sort_order': 2, 'is_active': True},
            {'question_tr': 'Ucretsiz plan ne icerir?', 'question_en': 'What does the free plan include?', 'answer_tr': 'Ucretsiz planda 1 menu, 50 urun, temel QR kod olusturma ve sinirli analitik ozellikleri sunulmaktadir. Kredi karti gerektirmez.', 'answer_en': 'The free plan includes 1 menu, 50 products, basic QR code creation, and limited analytics. No credit card required.', 'page': 'pricing', 'sort_order': 3, 'is_active': True},
            {'question_tr': 'Plan degisikligi yapabilir miyim?', 'question_en': 'Can I change my plan?', 'answer_tr': 'Evet, istediginiz zaman plan yukseltme veya dusurme yapabilirsiniz. Yukseltmelerde fark oranli hesaplanir, dusurmeler bir sonraki donemde gecerli olur.', 'answer_en': 'Yes, you can upgrade or downgrade anytime. Upgrades are prorated, downgrades take effect in the next billing period.', 'page': 'pricing', 'sort_order': 4, 'is_active': True},
            {'question_tr': 'Gizli ucret var mi?', 'question_en': 'Are there any hidden fees?', 'answer_tr': 'Kesinlikle hayir. Tum fiyatlar seffaf sekilde web sitemizde yayinlanmaktadir. Kurulum ucreti, iptal ucreti veya gizli komisyon yoktur.', 'answer_en': 'Absolutely not. All prices are transparently published on our website. No setup fees, cancellation fees, or hidden commissions.', 'page': 'pricing', 'sort_order': 5, 'is_active': True},
            {'question_tr': 'Odeme yontemleri nelerdir?', 'question_en': 'What payment methods are accepted?', 'answer_tr': 'Kredi karti, banka karti, havale/EFT ve online odeme (iyzico) ile odeme yapabilirsiniz. Kurumsal musteriler icin fatura ile odeme de mevcuttur.', 'answer_en': 'We accept credit card, debit card, bank transfer, and online payment (iyzico). Invoice payment is also available for corporate customers.', 'page': 'pricing', 'sort_order': 6, 'is_active': True},
            {'question_tr': 'Coklu sube indirimi var mi?', 'question_en': 'Is there a multi-branch discount?', 'answer_tr': '3 ve uzeri sube icin hacim indirimi uyguluyoruz. Detayli fiyatlandirma icin satis ekibimizle iletisime gecebilirsiniz.', 'answer_en': 'We offer volume discounts for 3+ branches. Contact our sales team for detailed pricing.', 'page': 'pricing', 'sort_order': 7, 'is_active': True},
            {'question_tr': 'Iptal politikaniz nedir?', 'question_en': 'What is your cancellation policy?', 'answer_tr': 'Sozlesme zorunlulugu yoktur. Istediginiz zaman iptal edebilirsiniz. Iptal durumunda mevcut donem sonuna kadar hizmet devam eder ve verileriniz 30 gun boyunca saklanir.', 'answer_en': 'No contract obligation. You can cancel anytime. Service continues until the end of the current period and your data is kept for 30 days.', 'page': 'pricing', 'sort_order': 8, 'is_active': True},
            # SUPPORT (8)
            {'question_tr': 'Teknik destek saatleri nedir?', 'question_en': 'What are the support hours?', 'answer_tr': '7/24 teknik destek sunuyoruz. Canli sohbet, e-posta ve telefon ile bize ulasabilirsiniz. Oncelikli destek Enterprise plan dahilindedir.', 'answer_en': 'We provide 24/7 technical support. Reach us via live chat, email, and phone. Priority support is included in Enterprise plan.', 'page': 'support', 'sort_order': 9, 'is_active': True},
            {'question_tr': 'Kurulum icin teknik bilgi gerekiyor mu?', 'question_en': 'Do I need technical knowledge for setup?', 'answer_tr': 'Hayir, E-Menum sifir teknik bilgi ile kullanilabilir. Surukle-birak arayuzumuz ile menunuzu dakikalar icinde olusturabilirsiniz. Ayrica ucretsiz kurulum destegi sunuyoruz.', 'answer_en': 'No, E-Menum can be used with zero technical knowledge. Create your menu in minutes with our drag-and-drop interface. We also offer free setup support.', 'page': 'support', 'sort_order': 10, 'is_active': True},
            {'question_tr': 'Verilerim guvenli mi?', 'question_en': 'Is my data secure?', 'answer_tr': 'Evet. AES-256 sifreleme, SSL sertifikasi, gunluk yedekleme ve KVKK tam uyumluluguyla verileriniz en yuksek guvenlik standartlarinda korunmaktadir.', 'answer_en': 'Yes. Your data is protected with the highest security standards: AES-256 encryption, SSL certificate, daily backups, and full GDPR compliance.', 'page': 'support', 'sort_order': 11, 'is_active': True},
            {'question_tr': 'Mevcut POS sistemimle entegre olur mu?', 'question_en': 'Does it integrate with my current POS?', 'answer_tr': 'E-Menum, Adisyo, IdeaSoft, Mikro, Logo ve diger populer POS sistemleriyle entegre olur. Ozel entegrasyon icin API dokumantasyonumuz mevcuttur.', 'answer_en': 'E-Menum integrates with popular POS systems. Custom integration is available through our API documentation.', 'page': 'support', 'sort_order': 12, 'is_active': True},
            {'question_tr': 'Menu degisiklikleri ne kadar surede yansir?', 'question_en': 'How fast are menu changes reflected?', 'answer_tr': 'Aninda! Menunuzde yaptiginiz her degisiklik kaydet tusuna bastiginiz anda canli menuye yansir. Herhangi bir bekleme suresi veya onay süreci yoktur.', 'answer_en': 'Instantly! Every change you make is reflected on the live menu the moment you save. No waiting time or approval process.', 'page': 'support', 'sort_order': 13, 'is_active': True},
            {'question_tr': 'Birden fazla dilde menu olusturabilir miyim?', 'question_en': 'Can I create menus in multiple languages?', 'answer_tr': 'Evet, Turkce, Ingilizce, Arapca, Rusca, Almanca ve Farsca dahil 6 dilde menu olusturabilirsiniz. AI ceviri destegi de mevcuttur.', 'answer_en': 'Yes, you can create menus in 6 languages including Turkish, English, Arabic, Russian, German, and Persian. AI translation support is also available.', 'page': 'support', 'sort_order': 14, 'is_active': True},
            {'question_tr': 'Egitim ve onboarding sureci nasil?', 'question_en': 'What is the training and onboarding process?', 'answer_tr': 'Ucretsiz online egitim, video rehberler ve 1-1 onboarding gorusmesi sunuyoruz. Enterprise musteriler icin yerinde egitim de mevcuttur.', 'answer_en': 'We offer free online training, video guides, and 1-on-1 onboarding sessions. On-site training is available for Enterprise customers.', 'page': 'support', 'sort_order': 15, 'is_active': True},
            {'question_tr': 'Veri goc hizmeti sunuyor musunuz?', 'question_en': 'Do you offer data migration service?', 'answer_tr': 'Evet, mevcut menu verilerinizi ucretsiz olarak E-Menum platformuna aktariyoruz. Excel, PDF veya baska formatlardaki menulerinizi bize gondermeniz yeterli.', 'answer_en': 'Yes, we migrate your existing menu data to E-Menum platform for free. Just send us your menus in Excel, PDF, or other formats.', 'page': 'support', 'sort_order': 16, 'is_active': True},
            # CONTACT (4)
            {'question_tr': 'Satis ekibine nasil ulasabilirim?', 'question_en': 'How can I reach the sales team?', 'answer_tr': 'Satis ekibimize sales@e-menum.net adresi, +90 850 123 4567 telefon veya web sitemizden demo formu doldurarak ulasabilirsiniz.', 'answer_en': 'Reach our sales team at sales@e-menum.net, +90 850 123 4567, or by filling the demo form on our website.', 'page': 'contact', 'sort_order': 17, 'is_active': True},
            {'question_tr': 'Ofisiniz nerede?', 'question_en': 'Where is your office located?', 'answer_tr': 'Merkez ofisimiz Istanbul, Maslak\'ta Nurol Plaza\'da yer almaktadir. Randevu ile ziyaret edebilirsiniz.', 'answer_en': 'Our headquarters is located at Nurol Plaza, Maslak, Istanbul. You can visit by appointment.', 'page': 'contact', 'sort_order': 18, 'is_active': True},
            {'question_tr': 'Canli demo alabilir miyim?', 'question_en': 'Can I get a live demo?', 'answer_tr': 'Elbette! Demo talep formunu doldurun, uzman ekibimiz 24 saat icinde sizinle iletisime gecer ve size ozel canli demo sunar.', 'answer_en': 'Of course! Fill the demo request form and our expert team will contact you within 24 hours for a personalized live demo.', 'page': 'contact', 'sort_order': 19, 'is_active': True},
            {'question_tr': 'Is birligi ve ortaklik icin kimle gorusmeliyim?', 'question_en': 'Who should I contact for partnership?', 'answer_tr': 'Is birligi ve ortaklik teklifleri icin partners@e-menum.net adresine yazabilir veya Partner Programi sayfamizdaki formu doldurabilirsiniz.', 'answer_en': 'For partnership inquiries, write to partners@e-menum.net or fill the form on our Partner Program page.', 'page': 'contact', 'sort_order': 20, 'is_active': True},
            # GENERAL (5)
            {'question_tr': 'E-Menum nedir?', 'question_en': 'What is E-Menum?', 'answer_tr': 'E-Menum, restoran ve kafelere yonelik yapay zeka destekli dijital menu ve isletme yonetim platformudur. QR menu, siparis yonetimi, analitik ve AI icerik uretimi tek platformda sunulmaktadir.', 'answer_en': 'E-Menum is an AI-powered digital menu and business management platform for restaurants and cafes. QR menus, order management, analytics, and AI content generation in one platform.', 'page': 'general', 'sort_order': 21, 'is_active': True},
            {'question_tr': 'Hangi sektorlere hizmet veriyorsunuz?', 'question_en': 'Which industries do you serve?', 'answer_tr': 'Restoran, kafe, otel F&B, fast food, pastane, bar, catering ve zincir isletmeler dahil tum yiyecek-icecek sektorune hizmet veriyoruz.', 'answer_en': 'We serve the entire F&B industry including restaurants, cafes, hotel F&B, fast food, bakeries, bars, catering, and chain businesses.', 'page': 'general', 'sort_order': 22, 'is_active': True},
            {'question_tr': 'QR menu nasil calisir?', 'question_en': 'How does the QR menu work?', 'answer_tr': 'Musteriler masadaki QR kodu telefonlariyla tarar ve aninda dijital menuye ulasir. Siparis verebilir, fiyatlari gorebilir ve alerjen bilgilerini inceleyebilir.', 'answer_en': 'Customers scan the QR code on the table with their phone and instantly access the digital menu. They can order, view prices, and check allergen information.', 'page': 'general', 'sort_order': 23, 'is_active': True},
            {'question_tr': 'Mobil uygulama gerekli mi?', 'question_en': 'Is a mobile app required?', 'answer_tr': 'Musterileriniz icin uygulama gerekmez, QR menu web tarayicida acilir. Isletme yonetim paneliniz de responsive tasarimlidir ve mobilde sorunsuz calisir.', 'answer_en': 'No app needed for your customers, the QR menu opens in a web browser. Your business management panel is also responsive and works seamlessly on mobile.', 'page': 'general', 'sort_order': 24, 'is_active': True},
            {'question_tr': 'E-Menum KVKK uyumlu mu?', 'question_en': 'Is E-Menum GDPR compliant?', 'answer_tr': 'Evet, E-Menum KVKK (Kisisel Verilerin Korunmasi Kanunu) ve uluslararasi veri koruma standartlarina tam uyumludur. Verileriniz Turkiye\'deki sunucularda saklanir.', 'answer_en': 'Yes, E-Menum is fully compliant with GDPR and international data protection standards. Your data is stored on servers in Turkey.', 'page': 'general', 'sort_order': 25, 'is_active': True},
            # BOTH (5)
            {'question_tr': 'Deneme suresi bittikten sonra ne olur?', 'question_en': 'What happens after the trial ends?', 'answer_tr': 'Deneme suresi bittiginde ucretsiz plana otomatik gecersiniz. Verileriniz kaybolmaz. Istediginiz zaman ucretli plana gecis yapabilirsiniz.', 'answer_en': 'When the trial ends, you automatically switch to the free plan. Your data is preserved. You can upgrade to a paid plan anytime.', 'page': 'both', 'sort_order': 26, 'is_active': True},
            {'question_tr': 'Sozlesme zorunlulugu var mi?', 'question_en': 'Is there a contract obligation?', 'answer_tr': 'Hayir, hicbir planimizda zorunlu sozlesme yoktur. Aylik olarak kullanabilir, istediginiz zaman iptal edebilirsiniz.', 'answer_en': 'No, none of our plans have a mandatory contract. You can use it monthly and cancel anytime.', 'page': 'both', 'sort_order': 27, 'is_active': True},
            {'question_tr': 'Basili menuyu tamamen kaldirmam gerekiyor mu?', 'question_en': 'Do I need to completely remove printed menus?', 'answer_tr': 'Hayir, dijital menu basili menunun alternatifi olarak calisabilir. Ancak tamamen dijitale gecen isletmeler ortalama %30 maliyet tasarrufu saglamaktadir.', 'answer_en': 'No, the digital menu can work alongside printed menus. However, businesses that go fully digital save an average of 30% on costs.', 'page': 'both', 'sort_order': 28, 'is_active': True},
            {'question_tr': 'Musteri desteginiz ne kadar hizli?', 'question_en': 'How fast is your customer support?', 'answer_tr': 'Canli sohbette ortalama 2 dakika, e-postada 2 saat, telefonda aninda yanit alirsiniz. Oncelikli destek Enterprise plana dahildir.', 'answer_en': 'Average 2-minute response on live chat, 2 hours on email, instant on phone. Priority support is included in Enterprise plan.', 'page': 'both', 'sort_order': 29, 'is_active': True},
            {'question_tr': 'Referans programiniz var mi?', 'question_en': 'Do you have a referral program?', 'answer_tr': 'Evet! Her basarili referans icin hem siz hem yeni musteri 1 ay ucretsiz kullanim kazanir. Detaylar icin Partner Programi sayfamizi ziyaret edin.', 'answer_en': 'Yes! Both you and the new customer earn 1 month free for every successful referral. Visit our Partner Program page for details.', 'page': 'both', 'sort_order': 30, 'is_active': True},
        ]
        for f in faqs:
            FAQ.objects.update_or_create(sort_order=f['sort_order'], defaults=f)
        self.stdout.write(f'  ✓ FAQ ({len(faqs)})')

    # =========================================================================
    # 10. TEAM MEMBERS (7)
    # =========================================================================
    def _seed_team_members(self):
        members = [
            {'sort_order': 1, 'name_tr': 'Ismail Karaca', 'name_en': 'Ismail Karaca', 'title_tr': 'CEO & Kurucu', 'title_en': 'CEO & Founder', 'initials': 'IK', 'avatar_color': 'primary', 'is_active': True},
            {'sort_order': 2, 'name_tr': 'Bora Aydin', 'name_en': 'Bora Aydin', 'title_tr': 'CTO', 'title_en': 'CTO', 'initials': 'BA', 'avatar_color': 'blue', 'is_active': True},
            {'sort_order': 3, 'name_tr': 'Ali Veli', 'name_en': 'Ali Veli', 'title_tr': 'Frontend Gelistirici', 'title_en': 'Frontend Developer', 'initials': 'AV', 'avatar_color': 'emerald', 'is_active': True},
            {'sort_order': 4, 'name_tr': 'Ahmet Yilmaz', 'name_en': 'Ahmet Yilmaz', 'title_tr': 'DevOps Muhendisi', 'title_en': 'DevOps Engineer', 'initials': 'AY', 'avatar_color': 'orange', 'is_active': True},
            {'sort_order': 5, 'name_tr': 'Pinar Demir', 'name_en': 'Pinar Demir', 'title_tr': 'Satis ve Pazarlama Muduru', 'title_en': 'Sales & Marketing Manager', 'initials': 'PD', 'avatar_color': 'rose', 'is_active': True},
            {'sort_order': 6, 'name_tr': 'Cem Ozkan', 'name_en': 'Cem Ozkan', 'title_tr': 'Urun Yoneticisi', 'title_en': 'Product Manager', 'initials': 'CO', 'avatar_color': 'purple', 'is_active': True},
            {'sort_order': 7, 'name_tr': 'Elif Koc', 'name_en': 'Elif Koc', 'title_tr': 'Musteri Basari Uzmanı', 'title_en': 'Customer Success Specialist', 'initials': 'EK', 'avatar_color': 'teal', 'is_active': True},
        ]
        for m in members:
            TeamMember.objects.update_or_create(sort_order=m['sort_order'], defaults=m)
        self.stdout.write(f'  ✓ TeamMember ({len(members)})')

    # =========================================================================
    # 11. COMPANY VALUES (6)
    # =========================================================================
    def _seed_company_values(self):
        values = [
            {'sort_order': 1, 'title_tr': 'Inovasyon', 'title_en': 'Innovation', 'description_tr': 'Yapay zeka ve veri bilimi ile F&B sektorune yenilikci cozumler getiriyoruz. Surekli arastirma ve gelistirme ile sektorun gelecegini sekillendiriyoruz.', 'description_en': 'We bring innovative solutions to the F&B sector with AI and data science. We shape the future of the industry through continuous R&D.', 'icon': 'ph-lightbulb', 'color': 'purple', 'is_active': True},
            {'sort_order': 2, 'title_tr': 'Musteri Odaklilik', 'title_en': 'Customer Focus', 'description_tr': 'Her kararda musterimizin basarisi onceliğimizdir. 7/24 destek, kisisellestirilmis cozumler ve surdurulebilir is ortakligi.', 'description_en': 'Customer success is our priority in every decision. 24/7 support, personalized solutions, and sustainable partnership.', 'icon': 'ph-heart', 'color': 'rose', 'is_active': True},
            {'sort_order': 3, 'title_tr': 'Seffaflik', 'title_en': 'Transparency', 'description_tr': 'Gizli ucret yok, surpriz yok. Seffaf fiyatlandirma, acik iletisim ve guvenilir is ortakligi. Soylediklerimizi yapariz.', 'description_en': 'No hidden fees, no surprises. Transparent pricing, open communication, and reliable partnership.', 'icon': 'ph-eye', 'color': 'blue', 'is_active': True},
            {'sort_order': 4, 'title_tr': 'Veri Guvenligi', 'title_en': 'Data Security', 'description_tr': 'KVKK ve uluslararasi standartlara tam uyumluluk. AES-256 sifreleme, yillik bagimsiz denetimler ve surekli guvenlik izleme.', 'description_en': 'Full compliance with GDPR and international standards. AES-256 encryption, annual independent audits, and continuous security monitoring.', 'icon': 'ph-shield-check', 'color': 'emerald', 'is_active': True},
            {'sort_order': 5, 'title_tr': 'Surdurulebilirlik', 'title_en': 'Sustainability', 'description_tr': 'Basili menu israfina son. Dijital donusum ile cevreci cozumler sunuyoruz. Her dijital menu bir agac kurtariyor.', 'description_en': 'End to printed menu waste. We offer eco-friendly solutions through digital transformation. Every digital menu saves a tree.', 'icon': 'ph-leaf', 'color': 'green', 'is_active': True},
            {'sort_order': 6, 'title_tr': 'Takim Ruhu', 'title_en': 'Team Spirit', 'description_tr': 'Farkli disiplinlerden gelen yetenekleri bir araya getiriyoruz. Esnek calisma, acik iletisim ve ortak hedeflerle buyuyoruz.', 'description_en': 'We bring together talents from diverse disciplines. We grow with flexible work, open communication, and shared goals.', 'icon': 'ph-users-three', 'color': 'orange', 'is_active': True},
        ]
        for v in values:
            CompanyValue.objects.update_or_create(sort_order=v['sort_order'], defaults=v)
        self.stdout.write(f'  ✓ CompanyValue ({len(values)})')

    # =========================================================================
    # 12. LEGAL PAGES (8)
    # =========================================================================
    def _seed_legal_pages(self):
        pages = [
            {'slug': 'privacy', 'title_tr': 'Gizlilik Politikasi', 'title_en': 'Privacy Policy', 'content_tr': '<h2>1. Genel Bakis</h2><p>E-Menum Teknoloji A.S. olarak kisisel verilerinizin korunmasina buyuk onem veriyoruz. Bu gizlilik politikasi, hizmetlerimizi kullanirken hangi verilerin toplandigini, nasil islendigi ve korundugunuza dair bilgileri icerir.</p><h2>2. Toplanan Veriler</h2><p>Hizmetlerimizi kullandiginizda asagidaki verileri toplayabiliriz: ad-soyad, e-posta adresi, telefon numarasi, isletme bilgileri, kullanim verileri ve cerez bilgileri.</p><h2>3. Verilerin Kullanimi</h2><p>Toplanan veriler hizmet sunumu, musteri destegi, urun gelistirme ve yasal yukumluluklerin yerine getirilmesi amaciyla kullanilir.</p><h2>4. Veri Guvenligi</h2><p>AES-256 sifreleme, SSL sertifikasi, gunluk yedekleme ve erisim kontrolleri ile verilerinizi en yuksek standartlarda koruyoruz.</p><h2>5. Ucuncu Taraf Paylasimi</h2><p>Kisisel verileriniz acik rizaniz olmadan ucuncu taraflarla paylasilmaz. Yasal zorunluluklar haric hicbir durumda verileriniz satilmaz veya kiralanmaz.</p><h2>6. Iletisim</h2><p>Gizlilik politikamiz hakkinda sorulariniz icin privacy@e-menum.net adresine yazabilirsiniz.</p>', 'content_en': '<h2>1. Overview</h2><p>At E-Menum Teknoloji A.S., we greatly value the protection of your personal data. This privacy policy explains what data is collected, how it is processed, and how it is protected when you use our services.</p><h2>2. Data Collected</h2><p>When using our services, we may collect: name, email, phone number, business information, usage data, and cookie information.</p><h2>3. Use of Data</h2><p>Collected data is used for service delivery, customer support, product development, and fulfilling legal obligations.</p><h2>4. Data Security</h2><p>We protect your data with the highest standards: AES-256 encryption, SSL certificates, daily backups, and access controls.</p><h2>5. Third-Party Sharing</h2><p>Your personal data is not shared with third parties without your explicit consent. Your data is never sold or rented.</p><h2>6. Contact</h2><p>For questions about our privacy policy, write to privacy@e-menum.net.</p>', 'last_updated_display': '15 Subat 2026', 'meta_description_tr': 'E-Menum gizlilik politikasi - kisisel verilerinizin korunmasi', 'meta_description_en': 'E-Menum privacy policy - protection of your personal data', 'is_active': True},
            {'slug': 'terms', 'title_tr': 'Kullanim Sartlari', 'title_en': 'Terms of Service', 'content_tr': '<h2>1. Taraflar</h2><p>Bu sozlesme E-Menum Teknoloji A.S. ile hizmetten yararlanan kullanici arasinda duzenlenmistir.</p><h2>2. Hizmet Tanimi</h2><p>E-Menum dijital menu olusturma, siparis yonetimi, analitik ve AI icerik uretimi hizmetleri sunmaktadir.</p><h2>3. Kullanim Kosullari</h2><p>Platform yasal amaclar disinda kullanilamaz. Kullanici, icerik dogrulugu ve yasal uyumdan sorumludur.</p><h2>4. Odeme ve Fatura</h2><p>Ucretli planlar icin odemeler aylik veya yillik olarak tahsil edilir. Faturalar elektronik ortamda duzenlenir.</p><h2>5. Iptal</h2><p>Kullanici istediği zaman aboneligini iptal edebilir. Iptal durumunda mevcut donem sonuna kadar hizmet devam eder.</p><h2>6. Sorumluluk Siniri</h2><p>E-Menum, platform kaynakli olmayan zararlardan sorumlu degildir. Maksimum sorumluluk son 12 aylik abonelik tutari ile sinirlidir.</p>', 'content_en': '<h2>1. Parties</h2><p>This agreement is between E-Menum Teknoloji A.S. and the user benefiting from the service.</p><h2>2. Service Definition</h2><p>E-Menum provides digital menu creation, order management, analytics, and AI content generation services.</p><h2>3. Usage Conditions</h2><p>The platform cannot be used for illegal purposes. The user is responsible for content accuracy and legal compliance.</p><h2>4. Payment and Billing</h2><p>Payments for paid plans are collected monthly or annually. Invoices are issued electronically.</p><h2>5. Cancellation</h2><p>Users can cancel their subscription at any time. Service continues until the end of the current period.</p><h2>6. Liability Limit</h2><p>E-Menum is not liable for damages not caused by the platform. Maximum liability is limited to the last 12 months of subscription fees.</p>', 'last_updated_display': '15 Subat 2026', 'meta_description_tr': 'E-Menum kullanim sartlari ve hizmet sozlesmesi', 'meta_description_en': 'E-Menum terms of service and service agreement', 'is_active': True},
            {'slug': 'kvkk', 'title_tr': 'KVKK Aydinlatma Metni', 'title_en': 'Data Protection Notice', 'content_tr': '<h2>Veri Sorumlusu</h2><p>E-Menum Teknoloji A.S., 6698 sayili Kisisel Verilerin Korunmasi Kanunu kapsaminda veri sorumlusu sifatiyla hareket etmektedir.</p><h2>Islenen Veriler</h2><p>Kimlik bilgileri, iletisim bilgileri, isletme bilgileri, kullanim verileri ve finansal bilgiler islenmektedir.</p><h2>Isleme Amaci</h2><p>Hizmet sunumu, sozlesme ifasi, musteri iliskileri yonetimi, yasal yukumlulukler ve guvenlik amaciyla veriler islenmektedir.</p><h2>Haklariniz</h2><p>KVKK md. 11 kapsaminda kisisel verilerinizin islenmesine iliskin bilgi talep etme, duzeltme, silme ve itiraz etme haklariniz bulunmaktadir.</p><h2>Basvuru</h2><p>Haklarinizi kullanmak icin kvkk@e-menum.net adresine basvurabilirsiniz.</p>', 'content_en': '<h2>Data Controller</h2><p>E-Menum Teknoloji A.S. acts as the data controller under the Personal Data Protection Law No. 6698.</p><h2>Processed Data</h2><p>Identity information, contact details, business information, usage data, and financial information are processed.</p><h2>Processing Purpose</h2><p>Data is processed for service delivery, contract fulfillment, customer relationship management, legal obligations, and security.</p><h2>Your Rights</h2><p>Under Article 11 of KVKK, you have the right to request information, correction, deletion, and objection regarding the processing of your personal data.</p><h2>Application</h2><p>To exercise your rights, contact kvkk@e-menum.net.</p>', 'last_updated_display': '1 Ocak 2026', 'meta_description_tr': 'E-Menum KVKK aydinlatma metni ve kisisel verilerin korunmasi', 'meta_description_en': 'E-Menum data protection notice and personal data protection', 'is_active': True},
            {'slug': 'cookie', 'title_tr': 'Cerez Politikasi', 'title_en': 'Cookie Policy', 'content_tr': '<h2>Cerez Nedir?</h2><p>Cerezler web sitemizi ziyaret ettiginizde cihaziniza kaydedilen kucuk metin dosyalaridir.</p><h2>Kullandigimiz Cerez Turleri</h2><p><strong>Zorunlu Cerezler:</strong> Sitenin calisması icin gereklidir. <strong>Analitik Cerezler:</strong> Ziyaretci davranislarini anlamak icin kullanilir. <strong>Pazarlama Cerezleri:</strong> Kisisellestirilmis icerik sunmak icin kullanilir.</p><h2>Cerez Yonetimi</h2><p>Tarayici ayarlarindan cerezleri kontrol edebilir veya reddedebilirsiniz. Zorunlu cerezlerin devre disi birakilmasi site islevselligini etkileyebilir.</p>', 'content_en': '<h2>What Are Cookies?</h2><p>Cookies are small text files stored on your device when you visit our website.</p><h2>Types of Cookies We Use</h2><p><strong>Essential Cookies:</strong> Required for site functionality. <strong>Analytics Cookies:</strong> Used to understand visitor behavior. <strong>Marketing Cookies:</strong> Used to deliver personalized content.</p><h2>Cookie Management</h2><p>You can control or reject cookies from your browser settings. Disabling essential cookies may affect site functionality.</p>', 'last_updated_display': '1 Ocak 2026', 'meta_description_tr': 'E-Menum cerez politikasi', 'meta_description_en': 'E-Menum cookie policy', 'is_active': True},
            {'slug': 'sla', 'title_tr': 'Hizmet Seviye Anlasmasi (SLA)', 'title_en': 'Service Level Agreement (SLA)', 'content_tr': '<h2>Uptime Garantisi</h2><p>E-Menum %99.9 uptime garantisi sunmaktadir. Planli bakim calismalari en az 48 saat onceden bildirilir.</p><h2>Destek Seviyeleri</h2><p><strong>Starter:</strong> E-posta destegi (24 saat). <strong>Professional:</strong> Canli sohbet ve e-posta (4 saat). <strong>Enterprise:</strong> 7/24 oncelikli destek, ozel hesap yoneticisi (1 saat).</p><h2>Tazminat</h2><p>SLA ihlali durumunda aylik ucretin %10\'u oraninda hizmet kredisi saglanir.</p>', 'content_en': '<h2>Uptime Guarantee</h2><p>E-Menum provides a 99.9% uptime guarantee. Scheduled maintenance is announced at least 48 hours in advance.</p><h2>Support Levels</h2><p><strong>Starter:</strong> Email support (24 hours). <strong>Professional:</strong> Live chat and email (4 hours). <strong>Enterprise:</strong> 24/7 priority support, dedicated account manager (1 hour).</p><h2>Compensation</h2><p>In case of SLA breach, a service credit of 10% of the monthly fee is provided.</p>', 'last_updated_display': '1 Ocak 2026', 'meta_description_tr': 'E-Menum hizmet seviye anlasmasi ve uptime garantisi', 'meta_description_en': 'E-Menum service level agreement and uptime guarantee', 'is_active': True},
            {'slug': 'dpa', 'title_tr': 'Veri Isleme Anlasmasi (DPA)', 'title_en': 'Data Processing Agreement (DPA)', 'content_tr': '<h2>Amac</h2><p>Bu anlasma E-Menum\'un musterileri adina islenen kisisel verilerin korunmasina iliskin yukumlulukleri belirler.</p><h2>Veri Isleme Kosullari</h2><p>Veriler yalnizca hizmet sunumu icin islenir. Ucuncu taraf alt isleyiciler KVKK uyumlu sekilde secilir ve denetlenir.</p><h2>Guvenlik Onlemleri</h2><p>AES-256 sifreleme, erisim kontrolleri, loglar ve yillik bagimsiz guvenlik denetimi uygulanir.</p><h2>Veri Ihlali Bildirimi</h2><p>Olasi bir veri ihlali durumunda veri sorumlusu 24 saat icinde bilgilendirilir.</p>', 'content_en': '<h2>Purpose</h2><p>This agreement defines E-Menum\'s obligations regarding the protection of personal data processed on behalf of customers.</p><h2>Data Processing Conditions</h2><p>Data is processed only for service delivery. Third-party sub-processors are selected and audited in GDPR compliance.</p><h2>Security Measures</h2><p>AES-256 encryption, access controls, logging, and annual independent security audits are applied.</p><h2>Data Breach Notification</h2><p>In case of a data breach, the data controller is notified within 24 hours.</p>', 'last_updated_display': '1 Ocak 2026', 'meta_description_tr': 'E-Menum veri isleme anlasmasi', 'meta_description_en': 'E-Menum data processing agreement', 'is_active': True},
            {'slug': 'security', 'title_tr': 'Guvenlik Politikasi', 'title_en': 'Security Policy', 'content_tr': '<h2>Altyapi Guvenligi</h2><p>Sunucularimiz ISO 27001 sertifikali veri merkezlerinde barindirilmaktadir. DDoS korumasi, firewall ve IDS/IPS sistemleri aktiftir.</p><h2>Uygulama Guvenligi</h2><p>Duzenlii guvenlik taramalari, kod incelemesi, penetrasyon testleri ve OWASP standartlarina uyumluluk saglanmaktadir.</p><h2>Veri Sifreleme</h2><p>Tum veriler AES-256 ile sifrelenir. Aktarimda TLS 1.3, saklamada at-rest encryption kullanilir.</p><h2>Erisim Kontrolu</h2><p>Rol bazli yetkilendirme (RBAC), iki faktorlu kimlik dogrulama (2FA) ve minimum yetki ilkesi uygulanir.</p>', 'content_en': '<h2>Infrastructure Security</h2><p>Our servers are hosted in ISO 27001 certified data centers. DDoS protection, firewall, and IDS/IPS systems are active.</p><h2>Application Security</h2><p>Regular security scans, code reviews, penetration tests, and OWASP compliance are ensured.</p><h2>Data Encryption</h2><p>All data is encrypted with AES-256. TLS 1.3 in transit and at-rest encryption for storage.</p><h2>Access Control</h2><p>Role-based authorization (RBAC), two-factor authentication (2FA), and least privilege principle are applied.</p>', 'last_updated_display': '1 Ocak 2026', 'meta_description_tr': 'E-Menum guvenlik politikasi ve veri koruma', 'meta_description_en': 'E-Menum security policy and data protection', 'is_active': True},
            {'slug': 'disclaimer', 'title_tr': 'Sorumluluk Reddi', 'title_en': 'Disclaimer', 'content_tr': '<h2>Genel</h2><p>Bu web sitesindeki bilgiler genel bilgilendirme amaclidir ve profesyonel danismanlik yerine gecmez.</p><h2>Icerik Dogrulugu</h2><p>Iceriklerimizin dogrulugunu saglamak icin ozen gosteriyoruz ancak hatalarin olabilecegini kabul ederiz. E-Menum icerik hatalarindan kaynaklanan zararlardan sorumlu tutulamaz.</p><h2>Dis Linkler</h2><p>Web sitemizde ucuncu taraf sitelere linkler bulunabilir. Bu sitelerin icerikleri ve gizlilik uygulamalari bizim kontrolumuz disindadir.</p>', 'content_en': '<h2>General</h2><p>Information on this website is for general informational purposes and does not replace professional advice.</p><h2>Content Accuracy</h2><p>We take care to ensure accuracy but acknowledge errors may occur. E-Menum cannot be held responsible for damages resulting from content errors.</p><h2>External Links</h2><p>Our website may contain links to third-party sites. Their content and privacy practices are beyond our control.</p>', 'last_updated_display': '1 Ocak 2026', 'meta_description_tr': 'E-Menum yasal sorumluluk reddi beyani', 'meta_description_en': 'E-Menum legal disclaimer statement', 'is_active': True},
        ]
        for p in pages:
            LegalPage.objects.update_or_create(slug=p['slug'], defaults=p)
        self.stdout.write(f'  ✓ LegalPage ({len(pages)})')

    # =========================================================================
    # 13. BLOG POSTS (12)
    # =========================================================================
    def _seed_blog_posts(self):
        now = timezone.now()
        posts = [
            {'slug': 'dijital-menu-nedir-neden-gecmeli', 'title_tr': 'Dijital Menu Nedir? Neden Gecmelisiniz?', 'title_en': 'What Is a Digital Menu? Why Should You Switch?', 'excerpt_tr': 'Basili menulerin maliyetleri ve sinirliliklari karsisinda dijital menulerin avantajlarini kesfet.', 'excerpt_en': 'Discover the advantages of digital menus versus the costs and limitations of printed menus.', 'content_tr': '<p>Dijital menu, isletmenizin urunlerini QR kod veya web baglantisi araciligiyla musterilere sunan interaktif bir platformdur.</p><h2>Basili Menulerin Sorunlari</h2><ul><li>Her fiyat degisikliginde yeni baski maliyeti</li><li>Hijyen endiseleri</li><li>Guncelleme gecikmeleri</li></ul><h2>Dijital Menulerin Avantajlari</h2><ul><li>Aninda guncelleme</li><li>Sifir baski maliyeti</li><li>Coklu dil destegi</li><li>Analitik ve veri toplama</li></ul><p>E-Menum ile dijital menuye gecis sadece 2 dakika suruyor.</p>', 'content_en': '<p>A digital menu is an interactive platform that presents your business products to customers via QR code or web link.</p><h2>Problems with Printed Menus</h2><ul><li>New printing costs for every price change</li><li>Hygiene concerns</li><li>Update delays</li></ul><h2>Advantages of Digital Menus</h2><ul><li>Instant updates</li><li>Zero printing costs</li><li>Multi-language support</li><li>Analytics and data collection</li></ul><p>Switching to a digital menu with E-Menum takes just 2 minutes.</p>', 'category_tr': 'Dijital Donusum', 'category_en': 'Digital Transformation', 'author_name': 'E-Menum Blog', 'status': 'published', 'published_at': now - timedelta(days=60), 'is_featured': True, 'meta_description_tr': 'Dijital menu nedir, avantajlari nelerdir?', 'meta_description_en': 'What is a digital menu and its advantages?'},
            {'slug': 'qr-menu-ile-satis-artirma-stratejileri', 'title_tr': 'QR Menu ile Satis Artirma: 7 Kanıtlanmis Strateji', 'title_en': '7 Proven Strategies to Increase Sales with QR Menu', 'excerpt_tr': 'QR menunuzu satisa donusturecek 7 strateji. Ortalama %40 gelir artisi nasil saglanir?', 'excerpt_en': '7 strategies to turn your QR menu into a sales engine. How to achieve 40% revenue increase?', 'content_tr': '<p>QR menuler sadece basili menunun dijital hali degil, ayni zamanda guclu bir satis aracidir.</p><h2>1. Gorsel Zenginlik</h2><p>Profesyonel urun fotograflari siparis oranini %30 artirir.</p><h2>2. Upselling ve Cross-selling</h2><p>Akilli oneriler ile ortalama sepet tutarini yukseltebilirsiniz.</p><h2>3. Mevsimsel Kampanyalar</h2><p>Aninda degisen kampanya banner\'lari ile musteri dikkatini cekin.</p><h2>4. Sosyal Kanit</h2><p>Populer urunleri ve musteri yorumlarini gosterin.</p><h2>5. Kisisellestirilmis Oneriler</h2><p>AI destekli oneri motoru ile her musteriye ozel teklifler.</p><h2>6. Kolay Tekrar Siparis</h2><p>Onceki siparisleri tek tikla tekrarlama ozelligi.</p><h2>7. Anlık Bildirimler</h2><p>Happy hour ve flash kampanya bildirimleri ile acil satis.</p>', 'content_en': '<p>QR menus are not just digital versions of printed menus — they are powerful sales tools.</p><h2>1. Visual Richness</h2><p>Professional product photos increase order rates by 30%.</p><h2>2. Upselling & Cross-selling</h2><p>Increase average basket value with smart recommendations.</p><h2>3. Seasonal Campaigns</h2><p>Catch customer attention with instantly changing campaign banners.</p><h2>4. Social Proof</h2><p>Show popular products and customer reviews.</p><h2>5. Personalized Recommendations</h2><p>Custom offers for each customer with AI-powered recommendation engine.</p><h2>6. Easy Reorder</h2><p>One-click reorder from previous orders.</p><h2>7. Instant Notifications</h2><p>Urgent sales with happy hour and flash campaign notifications.</p>', 'category_tr': 'Satis Stratejisi', 'category_en': 'Sales Strategy', 'author_name': 'Pinar Demir', 'status': 'published', 'published_at': now - timedelta(days=45), 'is_featured': True, 'meta_description_tr': 'QR menu ile satis artirma stratejileri', 'meta_description_en': 'Sales strategies with QR menu'},
            {'slug': 'restoran-dijitallesme-rehberi-2026', 'title_tr': 'Restoran Dijitallesme Rehberi 2026', 'title_en': 'Restaurant Digitalization Guide 2026', 'excerpt_tr': '2026 yilinda restoraninizi dijitallestirecek adim adim rehber.', 'excerpt_en': 'Step-by-step guide to digitalize your restaurant in 2026.', 'content_tr': '<p>F&B sektorunde dijital donusum artik bir tercih degil, zorunluluktur. Bu rehberde restoraninizi dijitallestirecek temel adimlari bulacaksiniz.</p><h2>Adim 1: Dijital Menu</h2><p>Baslangic noktasi olarak QR menu ile baslayın.</p><h2>Adim 2: Online Siparis</h2><p>Masa uzerinden ve paket servis siparisi alin.</p><h2>Adim 3: Analitik</h2><p>Veri toplama ve raporlama ile kararlari destekleyin.</p><h2>Adim 4: AI Entegrasyonu</h2><p>AI ile icerik uretimi ve tahminleme yapin.</p><h2>Adim 5: Tam Entegrasyon</h2><p>POS, muhasebe ve CRM sistemiyle butunlesik calisin.</p>', 'content_en': '<p>Digital transformation in F&B is no longer a choice but a necessity. This guide covers the key steps to digitalize your restaurant.</p><h2>Step 1: Digital Menu</h2><p>Start with QR menu as your starting point.</p><h2>Step 2: Online Ordering</h2><p>Accept table and delivery orders.</p><h2>Step 3: Analytics</h2><p>Support decisions with data collection and reporting.</p><h2>Step 4: AI Integration</h2><p>Generate content and forecast with AI.</p><h2>Step 5: Full Integration</h2><p>Work integrated with POS, accounting, and CRM.</p>', 'category_tr': 'Dijital Donusum', 'category_en': 'Digital Transformation', 'author_name': 'Ismail Karaca', 'status': 'published', 'published_at': now - timedelta(days=30), 'is_featured': False, 'meta_description_tr': 'Restoran dijitallesme rehberi 2026', 'meta_description_en': 'Restaurant digitalization guide 2026'},
            {'slug': 'ai-ile-menu-yonetimi', 'title_tr': 'Yapay Zeka ile Menu Yonetimi: Gelecek Bugun Basladi', 'title_en': 'Menu Management with AI: The Future Starts Today', 'excerpt_tr': 'AI destekli menu yonetiminin isletmelere sagladigi avantajlar.', 'excerpt_en': 'Benefits of AI-powered menu management for businesses.', 'content_tr': '<p>Yapay zeka, menu yonetiminde devrim yaratıyor. Otomatik icerik uretiminden satis tahminine, maliyet optimizasyonundan musteri segmentasyonuna kadar AI her noktada isletmelere deger katiyor.</p><h2>AI Icerik Uretimi</h2><p>GPT destekli motor, urun aciklamalarini saniyeler icinde profesyonelce yazar.</p><h2>Tahminleme Motoru</h2><p>Gecmis verilerden ogrenip gelecek satis trendlerini tahmin eder.</p><h2>Maliyet Optimizasyonu</h2><p>Food cost analizi ve menu muhendisligi ile kar marjini optimize edin.</p>', 'content_en': '<p>AI is revolutionizing menu management. From auto-content generation to sales forecasting, cost optimization to customer segmentation, AI adds value at every point.</p><h2>AI Content Generation</h2><p>GPT-powered engine writes product descriptions professionally in seconds.</p><h2>Forecasting Engine</h2><p>Learns from past data and predicts future sales trends.</p><h2>Cost Optimization</h2><p>Optimize profit margins with food cost analysis and menu engineering.</p>', 'category_tr': 'Yapay Zeka', 'category_en': 'Artificial Intelligence', 'author_name': 'Bora Aydin', 'status': 'published', 'published_at': now - timedelta(days=20), 'is_featured': False, 'meta_description_tr': 'AI ile menu yonetimi ve otomasyon', 'meta_description_en': 'Menu management and automation with AI'},
            {'slug': 'alerjen-yonetimi-mevzuat-rehberi', 'title_tr': 'Alerjen Yonetimi: Restoran Isletmecileri icin Mevzuat Rehberi', 'title_en': 'Allergen Management: Regulatory Guide for Restaurant Operators', 'excerpt_tr': 'Turkiye\'de alerjen bilgilendirme zorunluluklari ve uyumluluk rehberi.', 'excerpt_en': 'Allergen information obligations and compliance guide in Turkey.', 'content_tr': '<p>Turkiye\'de yiyecek-icecek isletmeleri 14 temel alerjeni menude belirtmekle yukumludur.</p><h2>Zorunlu 14 Alerjen</h2><p>Gluten, kabuklu deniz urunleri, yumurta, balik, yer fistigi, soya, sut, kabuklu meyveler, kereviz, hardal, susam, kukulrt dioksit, acik bicimli ve yumusakcalar.</p><h2>E-Menum Cozumu</h2><p>E-Menum ile alerjenler otomatik olarak isaretlenir ve musterilere gorsel olarak sunulur.</p>', 'content_en': '<p>F&B businesses in Turkey are required to indicate 14 core allergens on their menus.</p><h2>Mandatory 14 Allergens</h2><p>Gluten, crustaceans, eggs, fish, peanuts, soy, milk, tree nuts, celery, mustard, sesame, sulphur dioxide, lupin, and molluscs.</p><h2>E-Menum Solution</h2><p>With E-Menum, allergens are automatically labeled and visually presented to customers.</p>', 'category_tr': 'Mevzuat', 'category_en': 'Regulations', 'author_name': 'E-Menum Blog', 'status': 'published', 'published_at': now - timedelta(days=15), 'is_featured': False, 'meta_description_tr': 'Alerjen yonetimi mevzuat rehberi', 'meta_description_en': 'Allergen management regulatory guide'},
            {'slug': 'ai-icerik-motoru-v2', 'title_tr': 'AI Icerik Motoru v2.0: Yenilikler ve Ozellikler', 'title_en': 'AI Content Engine v2.0: New Features and Capabilities', 'excerpt_tr': 'E-Menum AI Icerik Motoru v2.0 ile gelen yeni ozellikler.', 'excerpt_en': 'New features with E-Menum AI Content Engine v2.0.', 'content_tr': '<p>AI Icerik Motoru v2.0 ile urun aciklamalari, kampanya metinleri ve sosyal medya icerikleri artik daha akilli ve tutarli.</p><h2>Yenilikler</h2><ul><li>Marka sesi ayarlama</li><li>Coklu dil ceviri destegi</li><li>Toplu icerik uretimi</li><li>SEO optimizasyonlu metinler</li></ul>', 'content_en': '<p>With AI Content Engine v2.0, product descriptions, campaign texts, and social media content are now smarter and more consistent.</p><h2>New Features</h2><ul><li>Brand voice customization</li><li>Multi-language translation support</li><li>Bulk content generation</li><li>SEO-optimized texts</li></ul>', 'category_tr': 'Urun Guncellemesi', 'category_en': 'Product Update', 'author_name': 'Cem Ozkan', 'status': 'published', 'published_at': now - timedelta(days=5), 'is_featured': True, 'meta_description_tr': 'AI Icerik Motoru v2.0 yenilikleri', 'meta_description_en': 'AI Content Engine v2.0 new features'},
            {'slug': 'food-cost-kontrolu-rehberi', 'title_tr': 'Food Cost Kontrolu: Kar Marjinizi Artiracak 5 Yontem', 'title_en': 'Food Cost Control: 5 Methods to Increase Your Profit Margin', 'excerpt_tr': 'Food cost kontrolu ile kar marjinizi nasil artirirsiniz?', 'excerpt_en': 'How to increase profit margins with food cost control?', 'content_tr': '<p>F&B sektorunde food cost, gelirinizin %28-35\'ini olusturur. Bu orani optimize etmek kar marjinizi dogrudan etkiler.</p><h2>1. Porsiyon Standartlari</h2><p>Net gramaj ve olcu tanimlayarak fire oranini dusurun.</p><h2>2. Menu Muhendisligi</h2><p>Menu matris analizi ile yildiz urunleri one cikarin.</p><h2>3. Tedarik Optimizasyonu</h2><p>Toplu alisveris ve mevsimsel malzeme kullanimi.</p><h2>4. Dijital Stok Takibi</h2><p>Gercek zamanli stok izleme ile israfi onleyin.</p><h2>5. AI Tahminleme</h2><p>Satis tahmini ile gereksiz stok maliyetini azaltin.</p>', 'content_en': '<p>In F&B, food cost accounts for 28-35% of your revenue. Optimizing this ratio directly impacts your profit margin.</p><h2>1. Portion Standards</h2><p>Reduce waste by defining net weights and measures.</p><h2>2. Menu Engineering</h2><p>Highlight star products with menu matrix analysis.</p><h2>3. Supply Optimization</h2><p>Bulk purchasing and seasonal ingredients.</p><h2>4. Digital Inventory Tracking</h2><p>Prevent waste with real-time stock monitoring.</p><h2>5. AI Forecasting</h2><p>Reduce unnecessary stock costs with sales forecasting.</p>', 'category_tr': 'Isletme Yonetimi', 'category_en': 'Business Management', 'author_name': 'Pinar Demir', 'status': 'published', 'published_at': now - timedelta(days=40), 'is_featured': False, 'meta_description_tr': 'Food cost kontrolu rehberi', 'meta_description_en': 'Food cost control guide'},
            {'slug': 'coklu-sube-yonetimi-ipuclari', 'title_tr': 'Coklu Sube Yonetimi: Zincir Isletmeler icin Ipuclari', 'title_en': 'Multi-Branch Management: Tips for Chain Businesses', 'excerpt_tr': 'Zincir isletme yonetiminde merkezi kontrol ve sube otonomisi dengesi.', 'excerpt_en': 'Balance between central control and branch autonomy in chain management.', 'content_tr': '<p>Coklu sube yonetimi, operasyonel tutarlilik ve verimlilik icin kritik oneme sahiptir.</p><h2>Merkezi Menu Yonetimi</h2><p>Tek noktadan tum subelere menu dagitimi.</p><h2>Sube Bazli Esneklik</h2><p>Bolgesel tercihler icin sube bazli fiyat ve urun farklilastirma.</p><h2>Performans Karsilastirmasi</h2><p>Subeler arasi satis, memnuniyet ve operasyon metrikleri.</p>', 'content_en': '<p>Multi-branch management is critical for operational consistency and efficiency.</p><h2>Centralized Menu Management</h2><p>Menu distribution to all branches from a single point.</p><h2>Branch-Level Flexibility</h2><p>Branch-specific pricing and product differentiation for regional preferences.</p><h2>Performance Comparison</h2><p>Inter-branch sales, satisfaction, and operation metrics.</p>', 'category_tr': 'Isletme Yonetimi', 'category_en': 'Business Management', 'author_name': 'Ismail Karaca', 'status': 'published', 'published_at': now - timedelta(days=35), 'is_featured': False, 'meta_description_tr': 'Coklu sube yonetimi ipuclari', 'meta_description_en': 'Multi-branch management tips'},
            {'slug': 'musteri-deneyimi-dijital-menu', 'title_tr': 'Dijital Menu ile Musteri Deneyimini Nasil Iyilestirirsiniz?', 'title_en': 'How to Improve Customer Experience with Digital Menu?', 'excerpt_tr': 'Dijital menulerin musteri memnuniyetine etkisi ve iyilestirme yontemleri.', 'excerpt_en': 'Impact of digital menus on customer satisfaction and improvement methods.', 'content_tr': '<p>Musteri deneyimi, F&B sektorunde basarinin anahtaridir. Dijital menuler, bu deneyimi onemli olcude iyilestirebilir.</p><h2>Hizli Erisim</h2><p>QR kod taramasi ile saniyeler icinde menuye ulasim.</p><h2>Gorsel Zenginlik</h2><p>Yuksek kaliteli urun fotograflari ile cazip sunum.</p><h2>Kisisellestirilmis Deneyim</h2><p>Alerjen filtreleme, dil secimi ve onceki siparis gecmisi.</p><h2>Hizli Servis</h2><p>Masadan siparis ile bekleme suresini minimize edin.</p>', 'content_en': '<p>Customer experience is the key to success in F&B. Digital menus can significantly improve this experience.</p><h2>Quick Access</h2><p>Access menu in seconds with QR code scan.</p><h2>Visual Richness</h2><p>Attractive presentation with high-quality product photos.</p><h2>Personalized Experience</h2><p>Allergen filtering, language selection, and order history.</p><h2>Fast Service</h2><p>Minimize waiting time with table ordering.</p>', 'category_tr': 'Musteri Deneyimi', 'category_en': 'Customer Experience', 'author_name': 'Elif Koc', 'status': 'published', 'published_at': now - timedelta(days=25), 'is_featured': False, 'meta_description_tr': 'Dijital menu ile musteri deneyimi iyilestirme', 'meta_description_en': 'Improving customer experience with digital menu'},
            {'slug': 'pos-entegrasyonu-rehberi', 'title_tr': 'POS Entegrasyonu: E-Menum ile Sorunsuz Baglanti', 'title_en': 'POS Integration: Seamless Connection with E-Menum', 'excerpt_tr': 'POS sisteminizi E-Menum ile nasil entegre edebilirsiniz?', 'excerpt_en': 'How to integrate your POS system with E-Menum?', 'content_tr': '<p>POS entegrasyonu, dijital menuden gelen siparislerin otomatik olarak adisyon sistemine aktarilmasini saglar.</p><h2>Desteklenen Sistemler</h2><p>Adisyo, IdeaSoft, Mikro, Logo ve diger populer POS sistemleri.</p><h2>Entegrasyon Sureci</h2><p>API anahtari olusturun, E-Menum panelinden baglanti kurun, test siparisleri verin. Ortalama kurulum suresi 30 dakikadir.</p><h2>Avantajlar</h2><ul><li>Manuel veri girisi ortadan kalkar</li><li>Hata orani minimuma iner</li><li>Gercek zamanli stok senkronizasyonu</li></ul>', 'content_en': '<p>POS integration allows orders from the digital menu to automatically transfer to the billing system.</p><h2>Supported Systems</h2><p>Major POS systems including popular Turkish and international solutions.</p><h2>Integration Process</h2><p>Create an API key, connect from E-Menum panel, place test orders. Average setup time is 30 minutes.</p><h2>Benefits</h2><ul><li>Eliminates manual data entry</li><li>Minimizes error rate</li><li>Real-time stock synchronization</li></ul>', 'category_tr': 'Entegrasyon', 'category_en': 'Integration', 'author_name': 'Bora Aydin', 'status': 'published', 'published_at': now - timedelta(days=10), 'is_featured': False, 'meta_description_tr': 'POS entegrasyonu rehberi', 'meta_description_en': 'POS integration guide'},
            {'slug': 'sektor-trendleri-2026', 'title_tr': '2026 F&B Sektor Trendleri: Dijital Donusum Hiz Kazaniyor', 'title_en': '2026 F&B Industry Trends: Digital Transformation Accelerates', 'excerpt_tr': '2026 yilinda F&B sektorunu sekillendiren teknoloji trendleri.', 'excerpt_en': 'Technology trends shaping the F&B industry in 2026.', 'content_tr': '<p>2026 yilinda F&B sektoru hizla dijitallesiyor. AI, otomasyon ve veri analitigi sektoru donusturuyor.</p><h2>Temel Trendler</h2><ul><li>AI destekli menu optimizasyonu</li><li>Temassiz siparis ve odeme</li><li>Surdurulebilirlik ve dijital menuler</li><li>Kisisellestirilmis musteri deneyimi</li><li>Bulut mutfak (ghost kitchen) yukselmesi</li></ul>', 'content_en': '<p>The F&B sector is rapidly digitalizing in 2026. AI, automation, and data analytics are transforming the industry.</p><h2>Key Trends</h2><ul><li>AI-powered menu optimization</li><li>Contactless ordering and payment</li><li>Sustainability and digital menus</li><li>Personalized customer experience</li><li>Rise of cloud kitchens (ghost kitchens)</li></ul>', 'category_tr': 'Sektor Analizi', 'category_en': 'Industry Analysis', 'author_name': 'E-Menum Blog', 'status': 'published', 'published_at': now - timedelta(days=7), 'is_featured': False, 'meta_description_tr': '2026 F&B sektor trendleri', 'meta_description_en': '2026 F&B industry trends'},
            {'slug': 'e-menum-basari-hikayesi-cafe-mola', 'title_tr': 'Basari Hikayesi: Cafe Mola Zinciri E-Menum ile Nasil %40 Buyudu?', 'title_en': 'Success Story: How Cafe Mola Chain Grew 40% with E-Menum?', 'excerpt_tr': '5 subeli Cafe Mola zincirinin E-Menum ile dijital donusum hikayesi.', 'excerpt_en': 'Digital transformation story of 5-branch Cafe Mola chain with E-Menum.', 'content_tr': '<p>Ankara merkezli Cafe Mola zinciri, 5 subesiyle E-Menum platformuna gecis yaparak 6 ay icinde %40 gelir artisi sagladi.</p><h2>Zorluklar</h2><p>Her subenin farkli menu ve fiyat yonetimi, basili menu maliyetleri ve veri eksikligi.</p><h2>Cozum</h2><p>E-Menum merkezi menu yonetimi, sube bazli fiyatlandirma ve gercek zamanli analitik.</p><h2>Sonuclar</h2><ul><li>%40 gelir artisi</li><li>%30 maliyet dususu</li><li>%95 musteri memnuniyeti</li></ul>', 'content_en': '<p>Ankara-based Cafe Mola chain achieved 40% revenue increase within 6 months by switching to E-Menum platform with 5 branches.</p><h2>Challenges</h2><p>Different menu and price management per branch, printing costs, and lack of data.</p><h2>Solution</h2><p>E-Menum centralized menu management, branch-specific pricing, and real-time analytics.</p><h2>Results</h2><ul><li>40% revenue increase</li><li>30% cost reduction</li><li>95% customer satisfaction</li></ul>', 'category_tr': 'Basari Hikayesi', 'category_en': 'Success Story', 'author_name': 'Pinar Demir', 'status': 'published', 'published_at': now - timedelta(days=3), 'is_featured': False, 'meta_description_tr': 'Cafe Mola basari hikayesi', 'meta_description_en': 'Cafe Mola success story'},
        ]
        for p in posts:
            BlogPost.objects.update_or_create(slug=p['slug'], defaults=p)
        self.stdout.write(f'  ✓ BlogPost ({len(posts)})')

    # =========================================================================
    # 14. PLAN DISPLAY FEATURES
    # =========================================================================
    def _seed_plan_display_features(self):
        from apps.subscriptions.models import Plan
        # Create plans if not exist
        plans_data = [
            {'slug': 'free', 'name': 'Ucretsiz', 'tier': 'free', 'price_monthly': 0, 'price_yearly': 0, 'is_active': True, 'is_public': True, 'is_default': True, 'sort_order': 1,
             'features': [('1 menu, 50 urun', '1 menu, 50 products'), ('Temel QR kod', 'Basic QR code'), ('Sinirli analitik', 'Limited analytics'), ('E-posta destegi', 'Email support')]},
            {'slug': 'starter', 'name': 'Starter', 'tier': 'starter', 'price_monthly': 2000, 'price_yearly': 19200, 'is_active': True, 'is_public': True, 'is_default': False, 'sort_order': 2,
             'features': [('3 menu, 200 urun', '3 menus, 200 products'), ('Ozel QR kod tasarimi', 'Custom QR code design'), ('Temel analitik dashboard', 'Basic analytics dashboard'), ('AI icerik uretimi (50/ay)', 'AI content generation (50/mo)'), ('Canli sohbet destegi', 'Live chat support'), ('Alerjen yonetimi', 'Allergen management')]},
            {'slug': 'professional', 'name': 'Professional', 'tier': 'professional', 'price_monthly': 4500, 'price_yearly': 43200, 'is_active': True, 'is_public': True, 'is_default': False, 'sort_order': 3, 'highlight_text': 'En Populer',
             'features': [('Sinirsiz menu ve urun', 'Unlimited menus and products', True), ('Gelismis analitik ve raporlama', 'Advanced analytics and reporting', True), ('AI icerik uretimi (sinirsiz)', 'AI content generation (unlimited)', True), ('QR siparis modulu', 'QR ordering module'), ('POS entegrasyonu', 'POS integration'), ('Coklu dil destegi (6 dil)', 'Multi-language (6 languages)'), ('Oncelikli destek', 'Priority support'), ('API erisimi', 'API access')]},
            {'slug': 'enterprise', 'name': 'Enterprise', 'tier': 'enterprise', 'price_monthly': 8000, 'price_yearly': 76800, 'is_active': True, 'is_public': True, 'is_default': False, 'sort_order': 4,
             'features': [('Her sey Professional dahil', 'Everything in Professional', True), ('Sinirsiz sube yonetimi', 'Unlimited branch management', True), ('Ozel hesap yoneticisi', 'Dedicated account manager', True), ('Beyaz etiket secenegi', 'White-label option'), ('SLA garantisi (%99.9)', 'SLA guarantee (99.9%)'), ('7/24 telefon destegi', '24/7 phone support'), ('Ozel entegrasyon destegi', 'Custom integration support'), ('Yillik is planlama', 'Annual business planning'), ('Yerinde egitim', 'On-site training')]},
        ]
        count = 0
        for plan_data in plans_data:
            features = plan_data.pop('features')
            plan, _ = Plan.objects.update_or_create(slug=plan_data['slug'], defaults=plan_data)
            for idx, feat in enumerate(features, start=1):
                if len(feat) == 3:
                    tr, en, highlighted = feat
                else:
                    tr, en = feat
                    highlighted = False
                PlanDisplayFeature.objects.update_or_create(
                    plan=plan, sort_order=idx,
                    defaults={'text_tr': tr, 'text_en': en, 'is_highlighted': highlighted, 'is_active': True})
                count += 1
        self.stdout.write(f'  ✓ Plan ({len(plans_data)}) + PlanDisplayFeature ({count})')

    # =========================================================================
    # 15. NAVIGATION LINKS
    # =========================================================================
    def _seed_navigation_links(self):
        links = [
            # FOOTER — Urun
            {'location': 'footer_product', 'label_tr': 'Ozellikler', 'label_en': 'Features', 'url': 'website:features', 'sort_order': 1, 'is_active': True},
            {'location': 'footer_product', 'label_tr': 'Fiyatlandirma', 'label_en': 'Pricing', 'url': 'website:pricing', 'sort_order': 2, 'is_active': True},
            {'location': 'footer_product', 'label_tr': 'Entegrasyonlar', 'label_en': 'Integrations', 'url': 'website:features', 'sort_order': 3, 'is_active': True},
            {'location': 'footer_product', 'label_tr': 'Neler Yeni', 'label_en': 'What\'s New', 'url': 'website:blog', 'sort_order': 4, 'is_active': True},
            # FOOTER — Cozumler
            {'location': 'footer_solutions', 'label_tr': 'Restoran', 'label_en': 'Restaurant', 'url': 'website:solutions', 'sort_order': 1, 'is_active': True},
            {'location': 'footer_solutions', 'label_tr': 'Kafe', 'label_en': 'Cafe', 'url': 'website:solutions', 'sort_order': 2, 'is_active': True},
            {'location': 'footer_solutions', 'label_tr': 'Otel F&B', 'label_en': 'Hotel F&B', 'url': 'website:solutions', 'sort_order': 3, 'is_active': True},
            {'location': 'footer_solutions', 'label_tr': 'Zincir Isletme', 'label_en': 'Chain Business', 'url': 'website:solutions', 'sort_order': 4, 'is_active': True},
            # FOOTER — Sirket
            {'location': 'footer_company', 'label_tr': 'Hakkimizda', 'label_en': 'About Us', 'url': 'website:about', 'sort_order': 1, 'is_active': True},
            {'location': 'footer_company', 'label_tr': 'Kariyer', 'label_en': 'Careers', 'url': 'website:careers', 'sort_order': 2, 'is_active': True},
            {'location': 'footer_company', 'label_tr': 'Basin', 'label_en': 'Press', 'url': 'website:press', 'sort_order': 3, 'is_active': True},
            {'location': 'footer_company', 'label_tr': 'Iletisim', 'label_en': 'Contact', 'url': 'website:contact', 'sort_order': 4, 'is_active': True},
            # FOOTER — Destek
            {'location': 'footer_support', 'label_tr': 'Yardim Merkezi', 'label_en': 'Help Center', 'url': 'website:support', 'sort_order': 1, 'is_active': True},
            {'location': 'footer_support', 'label_tr': 'SSS', 'label_en': 'FAQ', 'url': 'website:pricing', 'sort_order': 2, 'is_active': True},
            {'location': 'footer_support', 'label_tr': 'API Dokumantasyonu', 'label_en': 'API Documentation', 'url': 'website:support', 'sort_order': 3, 'is_active': True},
            {'location': 'footer_support', 'label_tr': 'Sistem Durumu', 'label_en': 'System Status', 'url': 'https://status.e-menum.net', 'sort_order': 4, 'is_active': True},
            # FOOTER — Yasal
            {'location': 'footer_legal', 'label_tr': 'Gizlilik Politikasi', 'label_en': 'Privacy Policy', 'url': 'website:privacy', 'sort_order': 1, 'is_active': True},
            {'location': 'footer_legal', 'label_tr': 'Kullanim Sartlari', 'label_en': 'Terms of Service', 'url': 'website:terms', 'sort_order': 2, 'is_active': True},
            {'location': 'footer_legal', 'label_tr': 'KVKK', 'label_en': 'Data Protection', 'url': 'website:kvkk', 'sort_order': 3, 'is_active': True},
            {'location': 'footer_legal', 'label_tr': 'Cerez Politikasi', 'label_en': 'Cookie Policy', 'url': 'website:cookie_policy', 'sort_order': 4, 'is_active': True},
            # FOOTER — Kaynaklar
            {'location': 'footer_resources', 'label_tr': 'Blog', 'label_en': 'Blog', 'url': 'website:blog', 'sort_order': 1, 'is_active': True},
            {'location': 'footer_resources', 'label_tr': 'Sektor Raporlari', 'label_en': 'Industry Reports', 'url': 'website:resources', 'sort_order': 2, 'is_active': True},
            {'location': 'footer_resources', 'label_tr': 'Ucretsiz Araclar', 'label_en': 'Free Tools', 'url': 'website:resources', 'sort_order': 3, 'is_active': True},
            {'location': 'footer_resources', 'label_tr': 'Webinarlar', 'label_en': 'Webinars', 'url': 'website:resources', 'sort_order': 4, 'is_active': True},
            # FOOTER — Yatirimci
            {'location': 'footer_investors', 'label_tr': 'Yatirimci Iliskileri', 'label_en': 'Investor Relations', 'url': 'website:investor', 'sort_order': 1, 'is_active': True},
            {'location': 'footer_investors', 'label_tr': 'Partner Programi', 'label_en': 'Partner Program', 'url': 'website:partners', 'sort_order': 2, 'is_active': True},
        ]
        for link in links:
            NavigationLink.objects.update_or_create(
                location=link['location'], sort_order=link['sort_order'],
                defaults=link)
        self.stdout.write(f'  ✓ NavigationLink ({len(links)})')

    # =========================================================================
    # 16. SECTORS (8)
    # =========================================================================
    def _seed_sectors(self):
        sectors = [
            {'slug': 'restoran', 'name_tr': 'Restoran', 'name_en': 'Restaurant', 'description_tr': 'Fine dining\'dan casual yemekhaneye her turdeki restoran isletmesine ozel dijital menu cozumleri. Siparis yonetimi ve analitik dahil.', 'description_en': 'Custom digital menu solutions for all types of restaurant businesses from fine dining to casual dining. Including order management and analytics.', 'icon': 'ph-fork-knife', 'color': 'primary', 'sort_order': 1, 'is_active': True},
            {'slug': 'kafe', 'name_tr': 'Kafe ve Kahveci', 'name_en': 'Cafe & Coffee Shop', 'description_tr': 'Kafeler, kahveciler ve cay bahceleri icin ozellestirilmis menu ve siparis cozumleri. Mevsimsel menu degisikliklerini aninda yansitma.', 'description_en': 'Customized menu and order solutions for cafes, coffee shops, and tea gardens. Instant seasonal menu updates.', 'icon': 'ph-coffee', 'color': 'amber', 'sort_order': 2, 'is_active': True},
            {'slug': 'otel-fb', 'name_tr': 'Otel F&B', 'name_en': 'Hotel F&B', 'description_tr': 'Otellerin restoran, bar, oda servisi ve banket hizmetleri icin merkezi dijital menu yonetimi. Coklu dil destegi.', 'description_en': 'Centralized digital menu management for hotel restaurants, bars, room service, and banquets. Multi-language support.', 'icon': 'ph-building', 'color': 'blue', 'sort_order': 3, 'is_active': True},
            {'slug': 'fast-food', 'name_tr': 'Fast Food ve QSR', 'name_en': 'Fast Food & QSR', 'description_tr': 'Hizli servis restoranlari icin optimize edilmis dijital menu ve siparis sistemi. Hizli siparis akisi ve KDS entegrasyonu.', 'description_en': 'Optimized digital menu and ordering system for quick service restaurants. Fast order flow and KDS integration.', 'icon': 'ph-hamburger', 'color': 'orange', 'sort_order': 4, 'is_active': True},
            {'slug': 'pastane-firin', 'name_tr': 'Pastane ve Firin', 'name_en': 'Pastry & Bakery', 'description_tr': 'Pastane, firin ve tatli dukkanları icin gorsel agirlikli dijital menu. Gunluk taze urun guncellemeleri ve alerjen yonetimi.', 'description_en': 'Visual-rich digital menus for pastry shops, bakeries, and sweet shops. Daily fresh product updates and allergen management.', 'icon': 'ph-cake', 'color': 'rose', 'sort_order': 5, 'is_active': True},
            {'slug': 'bar-pub', 'name_tr': 'Bar ve Pub', 'name_en': 'Bar & Pub', 'description_tr': 'Bar, pub ve gece kulupleri icin dijital icecek menusu ve happy hour yonetimi. Gorsel ve atmosfere uygun tema tasarimi.', 'description_en': 'Digital drink menu and happy hour management for bars, pubs, and nightclubs. Visual and atmosphere-matching theme design.', 'icon': 'ph-wine', 'color': 'purple', 'sort_order': 6, 'is_active': True},
            {'slug': 'catering', 'name_tr': 'Catering ve Etkinlik', 'name_en': 'Catering & Events', 'description_tr': 'Catering sirketleri ve etkinlik organizatorleri icin ozel menu olusturma, musteri onay akisi ve coklu dil destegi.', 'description_en': 'Custom menu creation, client approval workflow, and multi-language support for catering companies and event organizers.', 'icon': 'ph-champagne', 'color': 'teal', 'sort_order': 7, 'is_active': True},
            {'slug': 'zincir-isletme', 'name_tr': 'Zincir Isletmeler', 'name_en': 'Chain Businesses', 'description_tr': 'Coklu subeli zincir isletmeler icin merkezi yonetim, sube bazli fiyatlandirma ve performans karsilastirmasi.', 'description_en': 'Centralized management, branch-specific pricing, and performance comparison for multi-location chain businesses.', 'icon': 'ph-buildings', 'color': 'indigo', 'sort_order': 8, 'is_active': True},
        ]
        for s in sectors:
            Sector.objects.update_or_create(slug=s['slug'], defaults=s)
        self.stdout.write(f'  ✓ Sector ({len(sectors)})')

    # =========================================================================
    # 17. SOLUTIONS (8)
    # =========================================================================
    def _seed_solutions(self):
        sector_map = {s.slug: s for s in Sector.objects.all()}
        items = [
            {'slug': 'restoran-dijital-menu', 'title_tr': 'Restoran icin Dijital Menu Cozumu', 'title_en': 'Digital Menu Solution for Restaurants', 'subtitle_tr': 'Fine dining\'dan casual yemekhaneye, her turlu restoran isletmeniz icin ozel dijital menu ve siparis yonetimi.', 'subtitle_en': 'Custom digital menu and order management for all types of restaurants from fine dining to casual dining.', 'sector': sector_map.get('restoran'), 'solution_type': 'sector', 'content_tr': '<p>E-Menum restoran cozumu, menudan siparise, analitigden entegrasyona kadar tum isletme sureclerinizi dijitallestirir.</p><h3>Neden E-Menum?</h3><p>Restoran isletmeleri icin ozel tasarlanmis ozellikler: masa bazli siparis, garson cagirma, hesap isteme, split bill ve KDS entegrasyonu.</p>', 'content_en': '<p>E-Menum restaurant solution digitalizes all your business processes from menu to orders, analytics to integrations.</p><h3>Why E-Menum?</h3><p>Features specially designed for restaurants: table-based ordering, waiter call, bill request, split bill, and KDS integration.</p>', 'key_benefits_tr': '<ul><li>Masa bazli QR siparis sistemi</li><li>KDS (mutfak ekrani) entegrasyonu</li><li>POS sistemi ile otomatik senkronizasyon</li><li>AI destekli urun aciklamasi uretimi</li><li>Gercek zamanli satis ve performans analitigi</li></ul>', 'key_benefits_en': '<ul><li>Table-based QR ordering system</li><li>KDS (kitchen display) integration</li><li>Automatic POS synchronization</li><li>AI-powered product description generation</li><li>Real-time sales and performance analytics</li></ul>', 'pain_points_tr': '<ul><li>Her fiyat degisikliginde baski maliyeti</li><li>Garson hatalari ve siparis gecikmeleri</li><li>Veri eksikligi nedeniyle yanlis kararlar</li><li>Alerjen bilgilendirme zorunlulugu</li></ul>', 'pain_points_en': '<ul><li>Printing costs for every price change</li><li>Waiter errors and order delays</li><li>Wrong decisions due to lack of data</li><li>Allergen information requirements</li></ul>', 'target_audience_tr': 'Restoran sahipleri ve yoneticileri', 'target_audience_en': 'Restaurant owners and managers', 'is_featured': True, 'sort_order': 1, 'is_active': True},
            {'slug': 'kafe-dijital-menu', 'title_tr': 'Kafe ve Kahveci icin Dijital Menu', 'title_en': 'Digital Menu for Cafes & Coffee Shops', 'subtitle_tr': 'Kafeler, kahveciler ve cay bahceleri icin ozel dijital menu cozumu.', 'subtitle_en': 'Custom digital menu solution for cafes, coffee shops, and tea gardens.', 'sector': sector_map.get('kafe'), 'solution_type': 'sector', 'content_tr': '<p>Kafelerin hizli tempolu ortami icin optimize edilmis dijital menu. Mevsimsel degisiklikleri aninda yansitma, kampanya yonetimi ve musteri sadakati.</p>', 'content_en': '<p>Digital menu optimized for the fast-paced cafe environment. Instant seasonal updates, campaign management, and customer loyalty.</p>', 'key_benefits_tr': '<ul><li>Mevsimsel menu degisikliklerini aninda yayinlama</li><li>Gorsel menu ile siparis oranini artirma</li><li>Kampanya ve happy hour yonetimi</li><li>Musteri sadakat programi entegrasyonu</li></ul>', 'key_benefits_en': '<ul><li>Instant seasonal menu updates</li><li>Increase order rates with visual menus</li><li>Campaign and happy hour management</li><li>Customer loyalty program integration</li></ul>', 'pain_points_tr': '<ul><li>Sik degisen mevsimsel menuler</li><li>Basili menu guncelleme maliyetleri</li><li>Musteri tercih verisi eksikligi</li></ul>', 'pain_points_en': '<ul><li>Frequently changing seasonal menus</li><li>Printed menu update costs</li><li>Lack of customer preference data</li></ul>', 'target_audience_tr': 'Kafe ve kahveci isletme sahipleri', 'target_audience_en': 'Cafe and coffee shop owners', 'is_featured': True, 'sort_order': 2, 'is_active': True},
            {'slug': 'otel-fb-cozumu', 'title_tr': 'Otel F&B icin Dijital Menu Platformu', 'title_en': 'Digital Menu Platform for Hotel F&B', 'subtitle_tr': 'Otellerin restoran, bar, oda servisi ve banket hizmetleri icin merkezi dijital menu.', 'subtitle_en': 'Centralized digital menu for hotel restaurants, bars, room service, and banquets.', 'sector': sector_map.get('otel-fb'), 'solution_type': 'sector', 'content_tr': '<p>Otellerin F&B operasyonlari icin tasarlanmis kapsamli dijital menu cozumu. Coklu dil, oda servisi entegrasyonu ve merkezi yonetim.</p>', 'content_en': '<p>Comprehensive digital menu solution designed for hotel F&B operations. Multi-language, room service integration, and centralized management.</p>', 'key_benefits_tr': '<ul><li>Coklu dil destegi (6+ dil)</li><li>Oda servisi entegrasyonu</li><li>Merkezi menu yonetimi</li><li>QR kod ile temassiz siparis</li></ul>', 'key_benefits_en': '<ul><li>Multi-language support (6+ languages)</li><li>Room service integration</li><li>Centralized menu management</li><li>Contactless ordering via QR</li></ul>', 'pain_points_tr': '<ul><li>Farkli dillerde menu yonetimi zorluklari</li><li>Birden fazla restoran ve bar koordinasyonu</li><li>Oda servisi siparis takibi</li></ul>', 'pain_points_en': '<ul><li>Multi-language menu management challenges</li><li>Multiple restaurant and bar coordination</li><li>Room service order tracking</li></ul>', 'target_audience_tr': 'Otel F&B yoneticileri', 'target_audience_en': 'Hotel F&B managers', 'is_featured': False, 'sort_order': 3, 'is_active': True},
            {'slug': 'fast-food-qsr-cozumu', 'title_tr': 'Fast Food ve QSR icin Hizli Siparis Sistemi', 'title_en': 'Quick Order System for Fast Food & QSR', 'subtitle_tr': 'Hizli servis restoranlari icin optimize edilmis dijital siparis akisi.', 'subtitle_en': 'Optimized digital ordering flow for quick service restaurants.', 'sector': sector_map.get('fast-food'), 'solution_type': 'sector', 'content_tr': '<p>Fast food ve QSR isletmeleri icin hiz odakli dijital siparis sistemi. Self-servis kiosk, hizli siparis akisi ve KDS entegrasyonu.</p>', 'content_en': '<p>Speed-focused digital ordering for fast food and QSR. Self-service kiosk, quick order flow, and KDS integration.</p>', 'key_benefits_tr': '<ul><li>Hizli siparis akisi (ortalama 30 saniye)</li><li>Self-servis kiosk modu</li><li>KDS entegrasyonu</li><li>Drive-through siparis destegi</li></ul>', 'key_benefits_en': '<ul><li>Quick order flow (avg 30 seconds)</li><li>Self-service kiosk mode</li><li>KDS integration</li><li>Drive-through order support</li></ul>', 'pain_points_tr': '<ul><li>Uzun kuyruklar ve bekleme sureleri</li><li>Siparis hatalari</li><li>Yuksek personel maliyetleri</li></ul>', 'pain_points_en': '<ul><li>Long queues and wait times</li><li>Order errors</li><li>High staff costs</li></ul>', 'target_audience_tr': 'Fast food ve QSR isletme sahipleri', 'target_audience_en': 'Fast food and QSR owners', 'is_featured': False, 'sort_order': 4, 'is_active': True},
            {'slug': 'pastane-firin-cozumu', 'title_tr': 'Pastane ve Firin icin Gorsel Menu', 'title_en': 'Visual Menu for Pastry & Bakery', 'subtitle_tr': 'Gorsel agirlikli dijital menu ile urunlerinizi en cazip sekilde sunun.', 'subtitle_en': 'Present your products attractively with visual-rich digital menus.', 'sector': sector_map.get('pastane-firin'), 'solution_type': 'sector', 'content_tr': '<p>Pastane ve firinlar icin gorsel odakli dijital menu. Gunluk taze urun guncellemesi, alerjen yonetimi ve ozel siparis formu.</p>', 'content_en': '<p>Visual-focused digital menu for pastry shops and bakeries. Daily fresh product updates, allergen management, and custom order form.</p>', 'key_benefits_tr': '<ul><li>Gorsel galeri ile urun sunumu</li><li>Gunluk taze urun guncelleme</li><li>Ozel siparis ve pasta formu</li><li>Alerjen bilgi yonetimi</li></ul>', 'key_benefits_en': '<ul><li>Product presentation with visual gallery</li><li>Daily fresh product updates</li><li>Custom order and cake forms</li><li>Allergen info management</li></ul>', 'pain_points_tr': '<ul><li>Her gun degisen urun yelpazesi</li><li>Vitrin disindaki urunlerin gorulememesi</li><li>Alerjen bilgi zorunlulugu</li></ul>', 'pain_points_en': '<ul><li>Daily changing product range</li><li>Products beyond display not visible</li><li>Allergen info requirements</li></ul>', 'target_audience_tr': 'Pastane ve firin isletmecileri', 'target_audience_en': 'Pastry and bakery operators', 'is_featured': False, 'sort_order': 5, 'is_active': True},
            {'slug': 'bar-pub-cozumu', 'title_tr': 'Bar ve Pub icin Dijital Icecek Menusu', 'title_en': 'Digital Drink Menu for Bars & Pubs', 'subtitle_tr': 'Atmosfere uygun tema tasarimi ve happy hour yonetimi.', 'subtitle_en': 'Atmosphere-matching theme design and happy hour management.', 'sector': sector_map.get('bar-pub'), 'solution_type': 'sector', 'content_tr': '<p>Bar ve pub\'lar icin karanlik tema, gorsel kokteyl galeri ve otomatik happy hour kampanya yonetimi.</p>', 'content_en': '<p>Dark theme, visual cocktail gallery, and automatic happy hour campaign management for bars and pubs.</p>', 'key_benefits_tr': '<ul><li>Karanlik tema ve atmosfer tasarimi</li><li>Happy hour otomasyonu</li><li>Kokteyl galeri ve recete gosterimi</li><li>Yas dogrulama uyarisi</li></ul>', 'key_benefits_en': '<ul><li>Dark theme and atmosphere design</li><li>Happy hour automation</li><li>Cocktail gallery and recipe display</li><li>Age verification warning</li></ul>', 'pain_points_tr': '<ul><li>Karanlik ortamda basili menu okuma zorluğu</li><li>Happy hour fiyat degisiklikleri</li><li>Mevsimsel kokteyl menusu guncellemeleri</li></ul>', 'pain_points_en': '<ul><li>Difficulty reading printed menus in dark environments</li><li>Happy hour price changes</li><li>Seasonal cocktail menu updates</li></ul>', 'target_audience_tr': 'Bar ve pub isletmecileri', 'target_audience_en': 'Bar and pub operators', 'is_featured': False, 'sort_order': 6, 'is_active': True},
            {'slug': 'catering-etkinlik-cozumu', 'title_tr': 'Catering ve Etkinlik icin Ozel Menu Platformu', 'title_en': 'Custom Menu Platform for Catering & Events', 'subtitle_tr': 'Her etkinlige ozel dijital menu, musteri onay akisi ve coklu dil destegi.', 'subtitle_en': 'Custom digital menu for each event, client approval workflow, and multi-language support.', 'sector': sector_map.get('catering'), 'solution_type': 'sector', 'content_tr': '<p>Catering ve etkinlik organizatorleri icin etkinlige ozel menu olusturma, musteri onay sureci ve profesyonel sunum.</p>', 'content_en': '<p>Event-specific menu creation, client approval process, and professional presentation for catering and event organizers.</p>', 'key_benefits_tr': '<ul><li>Etkinlige ozel menu sablon sistemi</li><li>Musteri onay ve revizyon akisi</li><li>Coklu dil destegi</li><li>PDF ve dijital menu cikti secenekleri</li></ul>', 'key_benefits_en': '<ul><li>Event-specific menu template system</li><li>Client approval and revision workflow</li><li>Multi-language support</li><li>PDF and digital menu output options</li></ul>', 'pain_points_tr': '<ul><li>Her etkinlik icin sifirdan menu hazirlama</li><li>Musteri onay sureci gecikmeleri</li><li>Coklu dil gereksinimleri</li></ul>', 'pain_points_en': '<ul><li>Creating menus from scratch for each event</li><li>Client approval process delays</li><li>Multi-language requirements</li></ul>', 'target_audience_tr': 'Catering sirketleri ve etkinlik organizatorleri', 'target_audience_en': 'Catering companies and event organizers', 'is_featured': False, 'sort_order': 7, 'is_active': True},
            {'slug': 'zincir-isletme-cozumu', 'title_tr': 'Zincir Isletmeler icin Merkezi Yonetim Platformu', 'title_en': 'Central Management Platform for Chain Businesses', 'subtitle_tr': 'Tek panelden tum subelerinizi yonetin, karsilastirin ve optimize edin.', 'subtitle_en': 'Manage, compare, and optimize all your branches from a single panel.', 'sector': sector_map.get('zincir-isletme'), 'solution_type': 'sector', 'content_tr': '<p>Zincir isletmeler icin merkezi menu yonetimi, sube bazli fiyatlandirma, performans karsilastirmasi ve kurumsal raporlama.</p>', 'content_en': '<p>Centralized menu management, branch-specific pricing, performance comparison, and corporate reporting for chain businesses.</p>', 'key_benefits_tr': '<ul><li>Tek panelden sinirsiz sube yonetimi</li><li>Merkezi menu ile dagitim</li><li>Sube bazli fiyat ve kampanya farklilastirma</li><li>Karsilastirmali performans raporlari</li><li>Yetkilendirilmis kullanici rolleri</li></ul>', 'key_benefits_en': '<ul><li>Unlimited branch management from one panel</li><li>Distribution with centralized menu</li><li>Branch-specific pricing and campaigns</li><li>Comparative performance reports</li><li>Authorized user roles</li></ul>', 'pain_points_tr': '<ul><li>Subelerin farkli menu ve fiyat yonetimi</li><li>Operasyonel tutarsizlik</li><li>Sube performansini karsilastiramama</li></ul>', 'pain_points_en': '<ul><li>Different menu and price management per branch</li><li>Operational inconsistency</li><li>Unable to compare branch performance</li></ul>', 'target_audience_tr': 'Zincir isletme sahipleri ve operasyon yoneticileri', 'target_audience_en': 'Chain business owners and operations managers', 'is_featured': True, 'sort_order': 8, 'is_active': True},
        ]
        for s in items:
            SolutionPage.objects.update_or_create(slug=s['slug'], defaults=s)
        self.stdout.write(f'  ✓ SolutionPage ({len(items)})')

    # =========================================================================
    # 18. CASE STUDIES (6)
    # =========================================================================
    def _seed_case_studies(self):
        now = timezone.now()
        sector_map = {s.slug: s for s in Sector.objects.all()}
        items = [
            {'slug': 'lezzet-duragi-dijital-donusum', 'title_tr': 'Lezzet Duragi: Tek Subeden Dijital Donusum Hikayesi', 'title_en': 'Lezzet Duragi: Digital Transformation Story', 'company_name': 'Lezzet Duragi Restoran', 'sector': sector_map.get('restoran'), 'company_size': '1 sube, 15 personel', 'location': 'Istanbul, Kadikoy', 'excerpt_tr': 'Tek subeli restoran E-Menum ile 3 ayda %25 gelir artisi sagladi.', 'excerpt_en': 'Single-branch restaurant achieved 25% revenue increase in 3 months with E-Menum.', 'challenge_tr': '<p>Basili menu maliyetleri, fiyat guncelleme gecikmeleri ve musteri geri bildirim eksikligi en buyuk sorunlardi.</p>', 'challenge_en': '<p>Printed menu costs, price update delays, and lack of customer feedback were the biggest challenges.</p>', 'solution_tr': '<p>E-Menum dijital menu, QR siparis ve analitik dashboard uygulamaya alindi. 2 gunluk kurulum ile tum masalara QR kodlar yerlestirildi.</p>', 'solution_en': '<p>E-Menum digital menu, QR ordering, and analytics dashboard were implemented. QR codes placed on all tables with 2-day setup.</p>', 'results_tr': '<p>3 ayda %25 gelir artisi, %30 baski maliyeti tasarrufu ve %90 musteri memnuniyeti orani elde edildi.</p>', 'results_en': '<p>25% revenue increase, 30% printing cost savings, and 90% customer satisfaction rate achieved in 3 months.</p>', 'stat_1_value': '%25', 'stat_1_label_tr': 'Gelir Artisi', 'stat_1_label_en': 'Revenue Increase', 'stat_2_value': '%30', 'stat_2_label_tr': 'Maliyet Tasarrufu', 'stat_2_label_en': 'Cost Savings', 'stat_3_value': '%90', 'stat_3_label_tr': 'Musteri Memnuniyeti', 'stat_3_label_en': 'Customer Satisfaction', 'quote_tr': 'E-Menum ile basili menu maliyetlerimiz sifira indi. Ilk ayda ciromuz %25 artti.', 'quote_en': 'Our printed menu costs dropped to zero. Revenue increased 25% in the first month.', 'quote_author_tr': 'Mehmet Yilmaz', 'quote_author_en': 'Mehmet Yilmaz', 'quote_author_title_tr': 'Sahip, Lezzet Duragi', 'quote_author_title_en': 'Owner, Lezzet Duragi', 'is_featured': True, 'published_at': now - timedelta(days=60), 'sort_order': 1, 'is_active': True},
            {'slug': 'cafe-mola-zincir-basarisi', 'title_tr': 'Cafe Mola: 5 Subeli Zincirin Dijital Basarisi', 'title_en': 'Cafe Mola: Digital Success of 5-Branch Chain', 'company_name': 'Cafe Mola Zinciri', 'sector': sector_map.get('kafe'), 'company_size': '5 sube, 45 personel', 'location': 'Ankara', 'excerpt_tr': '5 subeli kafe zinciri E-Menum ile %40 gelir artisi ve %95 musteri memnuniyeti.', 'excerpt_en': '5-branch cafe chain achieved 40% revenue growth and 95% customer satisfaction with E-Menum.', 'challenge_tr': '<p>Her subenin farkli menu yonetimi, tutarsiz fiyatlandirma ve sube performansini karsilastirma zorlugu.</p>', 'challenge_en': '<p>Different menu management per branch, inconsistent pricing, and difficulty comparing branch performance.</p>', 'solution_tr': '<p>E-Menum merkezi menu yonetimi, sube bazli fiyatlandirma ve karsilastirmali analitik dashboard. Tum subeler 1 haftada gecis yapti.</p>', 'solution_en': '<p>E-Menum centralized menu management, branch-specific pricing, and comparative analytics. All branches transitioned in 1 week.</p>', 'results_tr': '<p>6 ayda %40 gelir artisi, %30 maliyet dususu ve %95 musteri memnuniyeti elde edildi.</p>', 'results_en': '<p>40% revenue increase, 30% cost reduction, and 95% customer satisfaction achieved in 6 months.</p>', 'stat_1_value': '%40', 'stat_1_label_tr': 'Gelir Artisi', 'stat_1_label_en': 'Revenue Growth', 'stat_2_value': '%30', 'stat_2_label_tr': 'Maliyet Dususu', 'stat_2_label_en': 'Cost Reduction', 'stat_3_value': '%95', 'stat_3_label_tr': 'Musteri Memnuniyeti', 'stat_3_label_en': 'Customer Satisfaction', 'quote_tr': '5 subemizi tek panelden yonetiyoruz. Operasyonel verimliligimiz inanilmaz artti.', 'quote_en': 'We manage 5 branches from one panel. Our operational efficiency increased incredibly.', 'quote_author_tr': 'Ayse Demir', 'quote_author_en': 'Ayse Demir', 'quote_author_title_tr': 'Genel Mudur', 'quote_author_title_en': 'General Manager', 'is_featured': True, 'published_at': now - timedelta(days=45), 'sort_order': 2, 'is_active': True},
            {'slug': 'grand-hotel-fb-dijitallesme', 'title_tr': 'Grand Hotel Istanbul: F&B Dijitallesme', 'title_en': 'Grand Hotel Istanbul: F&B Digitalization', 'company_name': 'Grand Hotel Istanbul', 'sector': sector_map.get('otel-fb'), 'company_size': '3 restoran + bar, 80 F&B personel', 'location': 'Istanbul, Sisli', 'excerpt_tr': '5 yildizli otelin 3 restorani ve bari E-Menum ile dijitallestirildi.', 'excerpt_en': '5-star hotel\'s 3 restaurants and bar digitalized with E-Menum.', 'challenge_tr': '<p>Coklu dil gereksinimleri, oda servisi koordinasyonu ve POS sistemi entegrasyonu ihtiyaci.</p>', 'challenge_en': '<p>Multi-language requirements, room service coordination, and POS system integration needs.</p>', 'solution_tr': '<p>6 dilde dijital menu, POS entegrasyonu, oda servisi modulu ve merkezi yonetim paneli.</p>', 'solution_en': '<p>Digital menu in 6 languages, POS integration, room service module, and centralized management panel.</p>', 'results_tr': '<p>Oda servisi siparisleri %50 artti. Turist memnuniyeti coklu dil destegi ile yuzde 20 puan yukseldi.</p>', 'results_en': '<p>Room service orders increased 50%. Tourist satisfaction rose 20 points with multi-language support.</p>', 'stat_1_value': '%50', 'stat_1_label_tr': 'Siparis Artisi', 'stat_1_label_en': 'Order Increase', 'stat_2_value': '6', 'stat_2_label_tr': 'Desteklenen Dil', 'stat_2_label_en': 'Languages Supported', 'stat_3_value': '%20', 'stat_3_label_tr': 'Memnuniyet Artisi', 'stat_3_label_en': 'Satisfaction Increase', 'quote_tr': 'Otelimizin 3 restoranini tek panelden yonetiyoruz. POS entegrasyonu mukemmel!', 'quote_en': 'We manage our hotel\'s 3 restaurants from one panel. POS integration is excellent!', 'quote_author_tr': 'Emre Can', 'quote_author_en': 'Emre Can', 'quote_author_title_tr': 'IT Muduru', 'quote_author_title_en': 'IT Manager', 'is_featured': False, 'published_at': now - timedelta(days=30), 'sort_order': 3, 'is_active': True},
            {'slug': 'pizza-lab-siparis-devrimi', 'title_tr': 'Pizza Lab: QR Siparis ile Servis Devrimi', 'title_en': 'Pizza Lab: Service Revolution with QR Ordering', 'company_name': 'Pizza Lab', 'sector': sector_map.get('fast-food'), 'company_size': '1 sube, 10 personel', 'location': 'Gaziantep', 'excerpt_tr': 'QR siparis sistemi ile garson hatalari %90 azaldi, servis suresi %45 kisaldi.', 'excerpt_en': 'Waiter errors reduced 90%, service time shortened 45% with QR ordering.', 'challenge_tr': '<p>Yogun saatlerde siparis hatalari, uzun bekleme sureleri ve musteri sikayetleri.</p>', 'challenge_en': '<p>Order errors during peak hours, long wait times, and customer complaints.</p>', 'solution_tr': '<p>E-Menum QR siparis, KDS entegrasyonu ve otomatik bildirimler. Musteriler masadan direkt siparis veriyor.</p>', 'solution_en': '<p>E-Menum QR ordering, KDS integration, and auto notifications. Customers order directly from the table.</p>', 'results_tr': '<p>Garson hatalari %90 azaldi, servis suresi %45 kisaldi, musteri memnuniyeti %40 artti.</p>', 'results_en': '<p>Waiter errors reduced 90%, service time shortened 45%, customer satisfaction increased 40%.</p>', 'stat_1_value': '%90', 'stat_1_label_tr': 'Hata Azalma', 'stat_1_label_en': 'Error Reduction', 'stat_2_value': '%45', 'stat_2_label_tr': 'Hizli Servis', 'stat_2_label_en': 'Faster Service', 'stat_3_value': '%40', 'stat_3_label_tr': 'Memnuniyet Artisi', 'stat_3_label_en': 'Satisfaction Increase', 'quote_tr': 'Siparis yonetimi modulu ile garson hatalari minimuma indi. Harika!', 'quote_en': 'Waiter errors minimized with order management module. Amazing!', 'quote_author_tr': 'Burak Celik', 'quote_author_en': 'Burak Celik', 'quote_author_title_tr': 'Kurucu, Pizza Lab', 'quote_author_title_en': 'Founder, Pizza Lab', 'is_featured': False, 'published_at': now - timedelta(days=20), 'sort_order': 4, 'is_active': True},
            {'slug': 'catering-plus-profesyonel-cozum', 'title_tr': 'Catering Plus: Etkinlik Menusu Profesyonelligi', 'title_en': 'Catering Plus: Event Menu Professionalism', 'company_name': 'Catering Plus', 'sector': sector_map.get('catering'), 'company_size': '25 personel', 'location': 'Istanbul, Maslak', 'excerpt_tr': 'Menu hazirlama suresi 3 gunden saatlere dustu. Musteriler profesyonellige hayran.', 'excerpt_en': 'Menu prep time dropped from 3 days to hours. Clients amazed by professionalism.', 'challenge_tr': '<p>Her etkinlik icin sifirdan menu hazirlama, musteri onay surecinin uzamasi ve coklu dil gereksinimleri.</p>', 'challenge_en': '<p>Creating menus from scratch for each event, long client approval process, and multi-language needs.</p>', 'solution_tr': '<p>E-Menum sablon sistemi, musteri onay akisi ve otomatik coklu dil ceviri.</p>', 'solution_en': '<p>E-Menum template system, client approval workflow, and automatic multi-language translation.</p>', 'results_tr': '<p>Menu hazirlama suresi %80 kisaldi. Musteri onay sureci 3 gunden 3 saate indi.</p>', 'results_en': '<p>Menu preparation time reduced 80%. Client approval process dropped from 3 days to 3 hours.</p>', 'stat_1_value': '%80', 'stat_1_label_tr': 'Sure Tasarrufu', 'stat_1_label_en': 'Time Savings', 'stat_2_value': '3 saat', 'stat_2_label_tr': 'Onay Suresi', 'stat_2_label_en': 'Approval Time', 'stat_3_value': '%100', 'stat_3_label_tr': 'Musteri Memnuniyeti', 'stat_3_label_en': 'Client Satisfaction', 'quote_tr': 'Her etkinlik icin ozel dijital menu olusturuyoruz. Hazirlama suremiz saatlere dustu.', 'quote_en': 'We create custom digital menus for each event. Prep time dropped to hours.', 'quote_author_tr': 'Deniz Korkmaz', 'quote_author_en': 'Deniz Korkmaz', 'quote_author_title_tr': 'Genel Koordinator', 'quote_author_title_en': 'General Coordinator', 'is_featured': False, 'published_at': now - timedelta(days=10), 'sort_order': 5, 'is_active': True},
            {'slug': 'green-bowl-veri-odakli-buyume', 'title_tr': 'Green Bowl: Veri Odakli Buyume Hikayesi', 'title_en': 'Green Bowl: Data-Driven Growth Story', 'company_name': 'Green Bowl', 'sector': sector_map.get('kafe'), 'company_size': '2 sube, 20 personel', 'location': 'Istanbul, Besiktas', 'excerpt_tr': 'Analitik dashboard ile veri odakli kararlar almaya basladilar. 6 ayda %35 gelir artisi.', 'excerpt_en': 'Started making data-driven decisions with analytics dashboard. 35% revenue increase in 6 months.', 'challenge_tr': '<p>Hangi urunlerin trend oldugu, musteri tercihleri ve yogun saatler hakkinda veri eksikligi.</p>', 'challenge_en': '<p>Lack of data about trending products, customer preferences, and peak hours.</p>', 'solution_tr': '<p>E-Menum analitik dashboard, otomatik haftalik raporlar ve AI oneri motoru. Veri odakli stratejik kararlar.</p>', 'solution_en': '<p>E-Menum analytics dashboard, automatic weekly reports, and AI recommendation engine. Data-driven strategic decisions.</p>', 'results_tr': '<p>6 ayda %35 gelir artisi. Menu optimizasyonu ile kar marji %12 puan artti.</p>', 'results_en': '<p>35% revenue increase in 6 months. Profit margin increased 12 points with menu optimization.</p>', 'stat_1_value': '%35', 'stat_1_label_tr': 'Gelir Artisi', 'stat_1_label_en': 'Revenue Increase', 'stat_2_value': '%12', 'stat_2_label_tr': 'Kar Marji Artisi', 'stat_2_label_en': 'Margin Increase', 'stat_3_value': '6 ay', 'stat_3_label_tr': 'Geri Odeme Suresi', 'stat_3_label_en': 'Payback Period', 'quote_tr': 'Analitik dashboard ile verileri canli takip ediyoruz. Gelir %35 artti.', 'quote_en': 'We track data live with the analytics dashboard. Revenue increased 35%.', 'quote_author_tr': 'Zeynep Sahin', 'quote_author_en': 'Zeynep Sahin', 'quote_author_title_tr': 'Pazarlama Muduru', 'quote_author_title_en': 'Marketing Manager', 'is_featured': False, 'published_at': now - timedelta(days=5), 'sort_order': 6, 'is_active': True},
        ]
        for c in items:
            CaseStudy.objects.update_or_create(slug=c['slug'], defaults=c)
        self.stdout.write(f'  ✓ CaseStudy ({len(items)})')

    # =========================================================================
    # 19. ROI CONFIG (singleton)
    # =========================================================================
    def _seed_roi_config(self):
        defaults = {
            'title_tr': 'ROI Hesaplayici', 'title_en': 'ROI Calculator',
            'description_tr': 'Isletmenizin dijital menuye gecis yaparak ne kadar tasarruf edecegini ve gelirinizi ne olcude arttirabileceginizi hesaplayin.',
            'description_en': 'Calculate how much your business will save and increase revenue by switching to a digital menu.',
            'avg_order_increase_pct': 15.00, 'avg_cost_reduction_pct': 30.00,
            'avg_time_saved_hours': 10.00, 'avg_menu_print_cost': 2500.00, 'is_active': True,
        }
        if ROICalculatorConfig.objects.exists():
            obj = ROICalculatorConfig.objects.first()
            for key, val in defaults.items():
                setattr(obj, key, val)
            obj.save()
        else:
            ROICalculatorConfig.objects.create(**defaults)
        self.stdout.write('  ✓ ROICalculatorConfig')

    # =========================================================================
    # 20. RESOURCE CATEGORIES (5)
    # =========================================================================
    def _seed_resource_categories(self):
        cats = [
            {'slug': 'sektor-raporlari', 'name_tr': 'Sektor Raporlari', 'name_en': 'Industry Reports', 'sort_order': 10, 'is_active': True},
            {'slug': 'rehberler-kilavuzlar', 'name_tr': 'Rehberler ve Kilavuzlar', 'name_en': 'Guides & Handbooks', 'sort_order': 20, 'is_active': True},
            {'slug': 'araclar-sablonlar', 'name_tr': 'Araclar ve Sablonlar', 'name_en': 'Tools & Templates', 'sort_order': 30, 'is_active': True},
            {'slug': 'webinar-etkinlikler', 'name_tr': 'Webinar ve Etkinlikler', 'name_en': 'Webinars & Events', 'sort_order': 40, 'is_active': True},
            {'slug': 'basari-hikayeleri', 'name_tr': 'Basari Hikayeleri', 'name_en': 'Success Stories', 'sort_order': 50, 'is_active': True},
        ]
        for c in cats:
            ResourceCategory.objects.update_or_create(slug=c['slug'], defaults=c)
        self.stdout.write(f'  ✓ ResourceCategory ({len(cats)})')

    # =========================================================================
    # 21. INDUSTRY REPORTS (4)
    # =========================================================================
    def _seed_industry_reports(self):
        now = timezone.now()
        cat = ResourceCategory.objects.filter(slug='sektor-raporlari').first()
        items = [
            {'slug': 'turkiye-fb-dijitallesme-raporu-2025', 'title_tr': 'Turkiye F&B Dijitallesme Raporu 2025', 'title_en': 'Turkey F&B Digitalization Report 2025', 'excerpt_tr': 'Turkiye F&B sektorunde dijitallesme orani, trendler ve firsatlar.', 'excerpt_en': 'Digitalization rate, trends, and opportunities in Turkey F&B sector.', 'content_tr': '<p>Bu rapor Turkiye\'deki 350.000+ F&B isletmesinin dijitallesme durumunu, QR menu kullanimini ve gelecek projeksiyonlarini icerir.</p>', 'content_en': '<p>This report covers the digitalization status, QR menu usage, and future projections of 350,000+ F&B businesses in Turkey.</p>', 'category': cat, 'requires_email': True, 'download_count': 1250, 'published_at': now - timedelta(days=90), 'is_active': True},
            {'slug': 'qr-menu-pazari-analizi-2026', 'title_tr': 'QR Menu Pazari Analizi 2026', 'title_en': 'QR Menu Market Analysis 2026', 'excerpt_tr': 'Global ve yerel QR menu pazarinin buyuklugu ve buyume projeksiyonlari.', 'excerpt_en': 'Global and local QR menu market size and growth projections.', 'content_tr': '<p>QR menu pazari 2026\'da global olarak $5.2B buyukluge ulasti. Turkiye pazari $150M ile hizla buyuyor.</p>', 'content_en': '<p>The QR menu market reached $5.2B globally in 2026. Turkey market is growing rapidly at $150M.</p>', 'category': cat, 'requires_email': True, 'download_count': 890, 'published_at': now - timedelta(days=45), 'is_active': True},
            {'slug': 'ai-fb-sektorunde-kullanim-raporu', 'title_tr': 'Yapay Zeka F&B Sektorunde Kullanim Raporu', 'title_en': 'AI Usage in F&B Sector Report', 'excerpt_tr': 'F&B sektorunde AI kullanim alanlari ve ROI analizi.', 'excerpt_en': 'AI use cases and ROI analysis in F&B sector.', 'content_tr': '<p>F&B sektorunde AI uygulamalari: icerik uretimi, satis tahmini, stok optimizasyonu ve musteri analitigi.</p>', 'content_en': '<p>AI applications in F&B: content generation, sales forecasting, inventory optimization, and customer analytics.</p>', 'category': cat, 'requires_email': True, 'download_count': 670, 'published_at': now - timedelta(days=30), 'is_active': True},
            {'slug': 'musteri-deneyimi-benchmark-raporu', 'title_tr': 'F&B Musteri Deneyimi Benchmark Raporu', 'title_en': 'F&B Customer Experience Benchmark Report', 'excerpt_tr': 'Dijital menu kullanan isletmelerde musteri memnuniyeti karsilastirmasi.', 'excerpt_en': 'Customer satisfaction comparison in businesses using digital menus.', 'content_tr': '<p>Dijital menu kullanan isletmeler, kullanmayanlara kiyasla %35 daha yuksek musteri memnuniyeti skoru elde ediyor.</p>', 'content_en': '<p>Businesses using digital menus achieve 35% higher customer satisfaction scores compared to non-users.</p>', 'category': cat, 'requires_email': True, 'download_count': 520, 'published_at': now - timedelta(days=15), 'is_active': True},
        ]
        for r in items:
            IndustryReport.objects.update_or_create(slug=r['slug'], defaults=r)
        self.stdout.write(f'  ✓ IndustryReport ({len(items)})')

    # =========================================================================
    # 22. FREE TOOLS (4)
    # =========================================================================
    def _seed_free_tools(self):
        items = [
            {'slug': 'menu-maliyet-hesaplayici', 'title_tr': 'Menu Maliyet Hesaplayici', 'title_en': 'Menu Cost Calculator', 'description_tr': 'Basili menu maliyetinizi hesaplayin ve dijital menuye geciste ne kadar tasarruf edeceksinizi gorun.', 'description_en': 'Calculate your printed menu costs and see how much you\'ll save by switching to digital.', 'icon': 'ph-calculator', 'tool_type': 'menu_cost', 'template_name': 'website/tools/menu_cost.html', 'sort_order': 1, 'is_active': True},
            {'slug': 'qr-kod-onizleme', 'title_tr': 'QR Kod Onizleme Araci', 'title_en': 'QR Code Preview Tool', 'description_tr': 'QR kodunuzu farkli tasarimlarla onizleyin. Renk, logo ve stil seceneklerini deneyin.', 'description_en': 'Preview your QR code with different designs. Try color, logo, and style options.', 'icon': 'ph-qr-code', 'tool_type': 'qr_preview', 'template_name': 'website/tools/qr_preview.html', 'sort_order': 2, 'is_active': True},
            {'slug': 'roi-hesaplayici', 'title_tr': 'ROI Hesaplayici', 'title_en': 'ROI Calculator', 'description_tr': 'Dijital menuye geciste yatirim getirinizi hesaplayin. Gelir artisi, maliyet dususu ve geri odeme suresini gorun.', 'description_en': 'Calculate your ROI for switching to digital menu. See revenue increase, cost reduction, and payback period.', 'icon': 'ph-chart-pie', 'tool_type': 'roi_calc', 'template_name': 'website/tools/roi_calc.html', 'sort_order': 3, 'is_active': True},
            {'slug': 'qr-kod-tasarlayici', 'title_tr': 'QR Kod Tasarlayici', 'title_en': 'QR Code Designer', 'description_tr': 'Markaniza ozel QR kod tasarlayin. Renk, sekil, logo ve cerceve secenekleriyle benzersiz QR kodlar olusturun.', 'description_en': 'Design custom QR codes for your brand. Create unique QR codes with color, shape, logo, and frame options.', 'icon': 'ph-paint-brush', 'tool_type': 'qr_designer', 'template_name': 'website/tools/qr_designer.html', 'sort_order': 4, 'is_active': True},
        ]
        for t in items:
            FreeTool.objects.update_or_create(slug=t['slug'], defaults=t)
        self.stdout.write(f'  ✓ FreeTool ({len(items)})')

    # =========================================================================
    # 23. WEBINARS (3)
    # =========================================================================
    def _seed_webinars(self):
        now = timezone.now()
        items = [
            {'slug': 'dijital-menu-101-baslangic-rehberi', 'title_tr': 'Dijital Menu 101: Baslangic Rehberi', 'title_en': 'Digital Menu 101: Getting Started Guide', 'description_tr': 'Dijital menuye gecis surecini adim adim anlatan baslangic webinari. QR menu olusturma, tema secimi ve ilk yayinlama.', 'description_en': 'Beginner webinar explaining the digital menu transition process step by step. QR menu creation, theme selection, and first publishing.', 'speaker_name': 'Cem Ozkan', 'speaker_title': 'Urun Yoneticisi, E-Menum', 'event_date': now - timedelta(days=60), 'duration_minutes': 45, 'video_url': 'https://youtube.com/@emenum/webinar-101', 'status': 'recorded', 'sort_order': 1, 'is_active': True},
            {'slug': 'ai-ile-menu-optimizasyonu', 'title_tr': 'AI ile Menu Optimizasyonu Masterclass', 'title_en': 'Menu Optimization with AI Masterclass', 'description_tr': 'Yapay zeka destekli icerik uretimi, menu muhendisligi ve satis tahmini tekniklerini ogrenin.', 'description_en': 'Learn AI-powered content generation, menu engineering, and sales forecasting techniques.', 'speaker_name': 'Bora Aydin', 'speaker_title': 'CTO, E-Menum', 'event_date': now - timedelta(days=30), 'duration_minutes': 60, 'video_url': 'https://youtube.com/@emenum/ai-masterclass', 'status': 'recorded', 'sort_order': 2, 'is_active': True},
            {'slug': 'zincir-isletme-yonetimi-webinar', 'title_tr': 'Zincir Isletme Yonetimi: Merkezi Kontrol Stratejileri', 'title_en': 'Chain Business Management: Central Control Strategies', 'description_tr': 'Coklu sube yonetimi, merkezi menu dagitimi ve performans takibi stratejilerini uzmanlarimizdan ogrenin.', 'description_en': 'Learn multi-branch management, centralized menu distribution, and performance tracking strategies from our experts.', 'speaker_name': 'Ismail Karaca', 'speaker_title': 'CEO & Kurucu, E-Menum', 'event_date': now + timedelta(days=14), 'duration_minutes': 60, 'registration_url': 'https://e-menum.net/webinar/zincir-yonetimi', 'status': 'upcoming', 'sort_order': 3, 'is_active': True},
        ]
        for w in items:
            Webinar.objects.update_or_create(slug=w['slug'], defaults=w)
        self.stdout.write(f'  ✓ Webinar ({len(items)})')

    # =========================================================================
    # 24. CAREER POSITIONS (5)
    # =========================================================================
    def _seed_career_positions(self):
        now = timezone.now()
        items = [
            {'slug': 'senior-backend-developer', 'title_tr': 'Senior Backend Gelistirici', 'title_en': 'Senior Backend Developer', 'department_tr': 'Muhendislik', 'department_en': 'Engineering', 'location_tr': 'Istanbul / Uzaktan', 'location_en': 'Istanbul / Remote', 'employment_type': 'full_time', 'description_tr': '<p>E-Menum muhendislik ekibine katilarak Node.js/TypeScript tabanli backend sistemlerimizi gelistirin.</p><h3>Sorumluluklar</h3><ul><li>RESTful API gelistirme ve bakimi</li><li>Veritabani tasarimi ve optimizasyonu</li><li>Mikroservis mimarisi ve entegrasyonlar</li><li>Kod incelemesi ve mentor</li></ul>', 'description_en': '<p>Join E-Menum engineering team to develop our Node.js/TypeScript-based backend systems.</p><h3>Responsibilities</h3><ul><li>RESTful API development and maintenance</li><li>Database design and optimization</li><li>Microservice architecture and integrations</li><li>Code review and mentoring</li></ul>', 'requirements_tr': '<ul><li>5+ yil backend gelistirme deneyimi</li><li>Node.js, TypeScript, PostgreSQL uzmanlik</li><li>REST API tasarimi ve dokumanlamasi</li><li>Docker ve CI/CD deneyimi</li></ul>', 'requirements_en': '<ul><li>5+ years backend development experience</li><li>Node.js, TypeScript, PostgreSQL expertise</li><li>REST API design and documentation</li><li>Docker and CI/CD experience</li></ul>', 'benefits_tr': '<ul><li>Rekabetci maas ve RSU</li><li>Uzaktan calisma esnekligi</li><li>Ozel saglik sigortasi</li><li>Egitim butcesi (yillik $2.000)</li><li>Yemek ve ulasim destegi</li></ul>', 'benefits_en': '<ul><li>Competitive salary and RSU</li><li>Remote work flexibility</li><li>Private health insurance</li><li>Education budget ($2,000/year)</li><li>Meal and transportation support</li></ul>', 'is_featured': True, 'published_at': now - timedelta(days=10), 'sort_order': 1, 'is_active': True},
            {'slug': 'frontend-developer', 'title_tr': 'Frontend Gelistirici', 'title_en': 'Frontend Developer', 'department_tr': 'Muhendislik', 'department_en': 'Engineering', 'location_tr': 'Istanbul', 'location_en': 'Istanbul', 'employment_type': 'full_time', 'description_tr': '<p>Kullanici arayuzu gelistirme ekibinde EJS, Tailwind CSS ve Alpine.js ile calismak uzere frontend gelistirici ariyoruz.</p>', 'description_en': '<p>We are looking for a frontend developer to work with EJS, Tailwind CSS, and Alpine.js in our UI development team.</p>', 'requirements_tr': '<ul><li>3+ yil frontend deneyimi</li><li>HTML5, CSS3, JavaScript uzmanlik</li><li>Tailwind CSS ve responsive tasarim</li><li>Git ve versiyon kontrolu</li></ul>', 'requirements_en': '<ul><li>3+ years frontend experience</li><li>HTML5, CSS3, JavaScript expertise</li><li>Tailwind CSS and responsive design</li><li>Git and version control</li></ul>', 'benefits_tr': '<ul><li>Rekabetci maas</li><li>Ozel saglik sigortasi</li><li>Yemek ve ulasim destegi</li><li>Esnek calisma saatleri</li></ul>', 'benefits_en': '<ul><li>Competitive salary</li><li>Private health insurance</li><li>Meal and transportation support</li><li>Flexible working hours</li></ul>', 'is_featured': False, 'published_at': now - timedelta(days=7), 'sort_order': 2, 'is_active': True},
            {'slug': 'urun-yoneticisi', 'title_tr': 'Urun Yoneticisi', 'title_en': 'Product Manager', 'department_tr': 'Urun', 'department_en': 'Product', 'location_tr': 'Istanbul / Hibrit', 'location_en': 'Istanbul / Hybrid', 'employment_type': 'full_time', 'description_tr': '<p>E-Menum urun yol haritasini yonlendirecek deneyimli bir urun yoneticisi ariyoruz.</p>', 'description_en': '<p>We are looking for an experienced product manager to drive E-Menum product roadmap.</p>', 'requirements_tr': '<ul><li>3+ yil SaaS urun yonetimi deneyimi</li><li>Kullanici arastirmasi ve veri analizi</li><li>Agile/Scrum metodolojileri</li></ul>', 'requirements_en': '<ul><li>3+ years SaaS product management experience</li><li>User research and data analysis</li><li>Agile/Scrum methodologies</li></ul>', 'benefits_tr': '<ul><li>Rekabetci maas ve RSU</li><li>Hibrit calisma modeli</li><li>Ozel saglik sigortasi</li></ul>', 'benefits_en': '<ul><li>Competitive salary and RSU</li><li>Hybrid work model</li><li>Private health insurance</li></ul>', 'is_featured': True, 'published_at': now - timedelta(days=5), 'sort_order': 3, 'is_active': True},
            {'slug': 'musteri-basari-uzmani', 'title_tr': 'Musteri Basari Uzmani', 'title_en': 'Customer Success Specialist', 'department_tr': 'Musteri Basarisi', 'department_en': 'Customer Success', 'location_tr': 'Istanbul', 'location_en': 'Istanbul', 'employment_type': 'full_time', 'description_tr': '<p>Musterilerimizin E-Menum\'dan maksimum deger almasini saglayacak musteri basari uzmani ariyoruz.</p>', 'description_en': '<p>We are looking for a customer success specialist to ensure our customers get maximum value from E-Menum.</p>', 'requirements_tr': '<ul><li>2+ yil musteri basarisi veya hesap yonetimi</li><li>SaaS sektorunde deneyim</li><li>Mukemmel iletisim becerileri</li></ul>', 'requirements_en': '<ul><li>2+ years customer success or account management</li><li>SaaS industry experience</li><li>Excellent communication skills</li></ul>', 'benefits_tr': '<ul><li>Rekabetci maas + performans bonusu</li><li>Ozel saglik sigortasi</li><li>Kariyer gelisim firsatlari</li></ul>', 'benefits_en': '<ul><li>Competitive salary + performance bonus</li><li>Private health insurance</li><li>Career growth opportunities</li></ul>', 'is_featured': False, 'published_at': now - timedelta(days=3), 'sort_order': 4, 'is_active': True},
            {'slug': 'dijital-pazarlama-uzmani', 'title_tr': 'Dijital Pazarlama Uzmani', 'title_en': 'Digital Marketing Specialist', 'department_tr': 'Pazarlama', 'department_en': 'Marketing', 'location_tr': 'Istanbul / Uzaktan', 'location_en': 'Istanbul / Remote', 'employment_type': 'full_time', 'description_tr': '<p>E-Menum\'un dijital pazarlama stratejilerini yonetecek deneyimli bir uzman ariyoruz.</p>', 'description_en': '<p>We are looking for an experienced specialist to manage E-Menum digital marketing strategies.</p>', 'requirements_tr': '<ul><li>3+ yil dijital pazarlama deneyimi</li><li>Google Ads, Meta Ads ve SEO uzmanlik</li><li>Icerik pazarlamasi ve sosyal medya</li></ul>', 'requirements_en': '<ul><li>3+ years digital marketing experience</li><li>Google Ads, Meta Ads, and SEO expertise</li><li>Content marketing and social media</li></ul>', 'benefits_tr': '<ul><li>Rekabetci maas</li><li>Uzaktan calisma imkani</li><li>Ozel saglik sigortasi</li></ul>', 'benefits_en': '<ul><li>Competitive salary</li><li>Remote work option</li><li>Private health insurance</li></ul>', 'is_featured': False, 'published_at': now - timedelta(days=1), 'sort_order': 5, 'is_active': True},
        ]
        for c in items:
            CareerPosition.objects.update_or_create(slug=c['slug'], defaults=c)
        self.stdout.write(f'  ✓ CareerPosition ({len(items)})')

    # =========================================================================
    # 25. PRESS RELEASES (4)
    # =========================================================================
    def _seed_press_releases(self):
        now = timezone.now()
        items = [
            {'slug': 'e-menum-1000-musteri-hedefine-ulasti', 'title_tr': 'E-Menum 1.000 Aktif Musteri Hedefine Ulasti', 'title_en': 'E-Menum Reaches 1,000 Active Customer Milestone', 'excerpt_tr': 'Turkiye\'nin lider dijital menu platformu E-Menum, kuruldugundan bu yana 1.000 aktif isletme musterisine ulasti.', 'excerpt_en': 'Turkey\'s leading digital menu platform E-Menum has reached 1,000 active business customers since its founding.', 'content_tr': '<p>Istanbul, 15 Aralik 2025 — E-Menum Teknoloji A.S., dijital menu platformunun 1.000 aktif musteri miline ulastigini duyurdu. Turkiye\'nin 81 ilinden isletmeler platforma kayit olarak dijital donusum yolculuguna basladi.</p><p>CEO Ismail Karaca, "Bu basari ekibimizin ozverili calismasi ve musterilerimizin guveninin sonucudur. Hedefimiz 2026 sonuna kadar 3.000 aktif musteri" dedi.</p>', 'content_en': '<p>Istanbul, December 15, 2025 — E-Menum Teknoloji A.S. announced that its digital menu platform has reached the 1,000 active customer milestone. Businesses from all 81 provinces of Turkey have registered on the platform.</p><p>CEO Ismail Karaca said, "This achievement is the result of our team\'s dedication and our customers\' trust. Our target is 3,000 active customers by end of 2026."</p>', 'source': 'E-Menum Basin Bulteni', 'published_at': now - timedelta(days=90), 'is_featured': True, 'sort_order': 1, 'is_active': True},
            {'slug': 'ai-icerik-motoru-v2-lansmansi', 'title_tr': 'E-Menum AI Icerik Motoru v2.0 Lansmansi', 'title_en': 'E-Menum AI Content Engine v2.0 Launch', 'excerpt_tr': 'E-Menum, yapay zeka destekli icerik uretim motorunun yeni versiyonunu duyurdu.', 'excerpt_en': 'E-Menum announced the new version of its AI-powered content generation engine.', 'content_tr': '<p>Istanbul, 1 Subat 2026 — E-Menum, AI Icerik Motoru v2.0\'yi piyasaya surdu. Yeni versiyon marka sesi ayarlama, toplu icerik uretimi ve SEO optimizasyonlu metin olusturma ozellikleri sunuyor.</p>', 'content_en': '<p>Istanbul, February 1, 2026 — E-Menum launched AI Content Engine v2.0. The new version offers brand voice customization, bulk content generation, and SEO-optimized text creation features.</p>', 'source': 'E-Menum Basin Bulteni', 'published_at': now - timedelta(days=25), 'is_featured': True, 'sort_order': 2, 'is_active': True},
            {'slug': 'pos-entegrasyon-platformu-acildi', 'title_tr': 'E-Menum Acik API ve POS Entegrasyon Platformu Yayinda', 'title_en': 'E-Menum Open API and POS Integration Platform Live', 'excerpt_tr': 'E-Menum, POS sistemleri ve ucuncu taraf uygulamalarla entegrasyon icin acik API platformunu kullanima sundu.', 'excerpt_en': 'E-Menum released its open API platform for integration with POS systems and third-party applications.', 'content_tr': '<p>Istanbul, 10 Subat 2026 — E-Menum, restoran POS sistemleri, muhasebe yazilimlari ve paket servis platformlariyla sorunsuz entegrasyon saglayan acik API platformunu duyurdu. Gelistiriciler icin sandbox ortami ve kapsamli API dokumantasyonu hazir.</p>', 'content_en': '<p>Istanbul, February 10, 2026 — E-Menum announced its open API platform enabling seamless integration with restaurant POS systems, accounting software, and delivery platforms. Sandbox environment and comprehensive API documentation ready for developers.</p>', 'source': 'E-Menum Basin Bulteni', 'published_at': now - timedelta(days=15), 'is_featured': False, 'sort_order': 3, 'is_active': True},
            {'slug': 'partner-programi-lansmansi', 'title_tr': 'E-Menum Partner Programi Lansmansi', 'title_en': 'E-Menum Partner Program Launch', 'excerpt_tr': 'E-Menum, bayi, referans ve teknoloji ortakligi olmak uzere uc farkli partner programini duyurdu.', 'excerpt_en': 'E-Menum announced three different partner programs: reseller, referral, and technology partnership.', 'content_tr': '<p>Istanbul, 20 Subat 2026 — E-Menum, buyuyen ekosistemini guclendirmek icin kapsamli partner programini duyurdu. Bayi, referans ve teknoloji ortakligi programlariyla is ortaklarina %30\'a varan komisyon firsati sunuluyor.</p>', 'content_en': '<p>Istanbul, February 20, 2026 — E-Menum announced its comprehensive partner program to strengthen its growing ecosystem. Reseller, referral, and technology partnership programs offer up to 30% commission to business partners.</p>', 'source': 'E-Menum Basin Bulteni', 'published_at': now - timedelta(days=5), 'is_featured': False, 'sort_order': 4, 'is_active': True},
        ]
        for p in items:
            PressRelease.objects.update_or_create(slug=p['slug'], defaults=p)
        self.stdout.write(f'  ✓ PressRelease ({len(items)})')

    # =========================================================================
    # 26. MILESTONES (6)
    # =========================================================================
    def _seed_milestones(self):
        items = [
            {'year': 2024, 'quarter': 'Q1', 'title_tr': 'E-Menum Kurulusu', 'title_en': 'E-Menum Founded', 'description_tr': 'E-Menum Teknoloji A.S. Istanbul\'da kuruldu. Kurucu ekip ilk MVP uzerinde calismaya basladi.', 'description_en': 'E-Menum Teknoloji A.S. founded in Istanbul. Founding team started working on the first MVP.', 'icon': 'ph-flag', 'sort_order': 1, 'is_active': True},
            {'year': 2024, 'quarter': 'Q3', 'title_tr': 'Beta Lansman', 'title_en': 'Beta Launch', 'description_tr': 'Platform beta olarak 50 pilot isletmeyle kullanima acildi. Ilk musteri geri bildirimleri toplandi.', 'description_en': 'Platform launched in beta with 50 pilot businesses. First customer feedback collected.', 'icon': 'ph-rocket-launch', 'sort_order': 2, 'is_active': True},
            {'year': 2025, 'quarter': 'Q1', 'title_tr': 'Resmi Lansman ve 500 Musteri', 'title_en': 'Official Launch & 500 Customers', 'description_tr': 'E-Menum resmi olarak piyasaya suruldu ve ilk 500 aktif musteri sayisina ulasildi.', 'description_en': 'E-Menum officially launched and reached the first 500 active customers milestone.', 'icon': 'ph-confetti', 'sort_order': 3, 'is_active': True},
            {'year': 2025, 'quarter': 'Q3', 'title_tr': 'AI Icerik Motoru v1.0', 'title_en': 'AI Content Engine v1.0', 'description_tr': 'GPT destekli AI icerik uretim motoru kullanima sunuldu. Otomatik urun aciklamasi ve ceviri ozellikleri eklendi.', 'description_en': 'GPT-powered AI content generation engine launched. Automatic product descriptions and translation features added.', 'icon': 'ph-brain', 'sort_order': 4, 'is_active': True},
            {'year': 2025, 'quarter': 'Q4', 'title_tr': '1.000 Musteri ve Siparis Modulu', 'title_en': '1,000 Customers & Order Module', 'description_tr': '1.000 aktif musteri sayisina ulasildi. QR uzerinden siparis yonetimi modulu basariyla lansmansi yapildi.', 'description_en': 'Reached 1,000 active customers. QR-based order management module successfully launched.', 'icon': 'ph-trophy', 'sort_order': 5, 'is_active': True},
            {'year': 2026, 'quarter': 'Q1', 'title_tr': 'AI Icerik Motoru v2.0 ve Entegrasyonlar', 'title_en': 'AI Content Engine v2.0 & Integrations', 'description_tr': 'AI Icerik Motoru v2.0 yayinda. POS entegrasyonlari ve acik API platformu kullanima sunuldu.', 'description_en': 'AI Content Engine v2.0 live. POS integrations and open API platform released.', 'icon': 'ph-magic-wand', 'sort_order': 6, 'is_active': True},
            {'year': 2026, 'quarter': 'Q2', 'title_tr': 'Hedef: 2.000 Musteri', 'title_en': 'Target: 2,000 Customers', 'description_tr': 'Yeni pazarlama stratejisi ve partner programi ile 2.000 aktif musteri hedefi.', 'description_en': 'Target of 2,000 active customers with new marketing strategy and partner program.', 'icon': 'ph-chart-line-up', 'sort_order': 7, 'is_active': True},
            {'year': 2026, 'quarter': 'Q4', 'title_tr': 'Hedef: Uluslararasi Acilim', 'title_en': 'Target: International Expansion', 'description_tr': 'Turkiye disinda ilk pazarlara acilma hedefi. Balkanlar ve Ortadogu oncelikli bolgeler.', 'description_en': 'Target to enter first international markets. Balkans and Middle East as priority regions.', 'icon': 'ph-globe', 'sort_order': 8, 'is_active': True},
        ]
        for m in items:
            Milestone.objects.update_or_create(year=m['year'], quarter=m['quarter'], defaults=m)
        self.stdout.write(f'  ✓ Milestone ({len(items)})')

    # =========================================================================
    # 27. INVESTOR PAGE (singleton)
    # =========================================================================
    def _seed_investor_page(self):
        defaults = {
            'title_tr': 'Yatirimci Iliskileri',
            'title_en': 'Investor Relations',
            'subtitle_tr': 'E-Menum, Turkiye\'nin 350.000+ isletmelik F&B sektorunu dijitallestirecek bir platform insa ediyor. Buyuyen pazarda lider konumda.',
            'subtitle_en': 'E-Menum is building a platform to digitize Turkey\'s 350,000+ F&B sector. Leading position in a growing market.',
            'overview_content_tr': '<h3>Sirket Hakkinda</h3><p>E-Menum Teknoloji A.S., 2024 yilinda kurulan ve F&B sektorune yapay zeka destekli dijital menu cozumleri sunan bir SaaS platformudur. Temel urunumuz: QR menu, siparis yonetimi, AI icerik uretimi ve gelismis analitik.</p><h3>Pazar Firsati</h3><p>Turkiye F&B sektoru 350.000+ isletmeden olusmaktadir ve dijitallesme orani henuz %5 seviyesindedir. Bu devasa pazar firsati E-Menum icin onemli bir buyume potansiyeli olusturmaktadir.</p><h3>Rekabet Avantajlari</h3><ul><li>AI destekli icerik uretimi ve tahminleme</li><li>Tam entegre siparis ve analitik platformu</li><li>KVKK uyumlu yerli cozum</li><li>Olceklenebilir SaaS modeli</li></ul>',
            'overview_content_en': '<h3>About the Company</h3><p>E-Menum Teknoloji A.S. is a SaaS platform founded in 2024, offering AI-powered digital menu solutions to the F&B sector. Core products: QR menu, order management, AI content generation, and advanced analytics.</p><h3>Market Opportunity</h3><p>Turkey\'s F&B sector consists of 350,000+ businesses with only 5% digitalization rate. This massive market opportunity creates significant growth potential for E-Menum.</p><h3>Competitive Advantages</h3><ul><li>AI-powered content generation and forecasting</li><li>Fully integrated ordering and analytics platform</li><li>GDPR-compliant local solution</li><li>Scalable SaaS model</li></ul>',
            'market_size_tam': '$2.5B',
            'market_size_sam': '$500M',
            'market_size_som': '$50M',
            'investment_thesis_tr': '<h3>Yatirim Tezi</h3><p>Turkiye F&B sektoru dijital donusumun basindadir. E-Menum, AI teknolojisi ve kullanici dostu platformu ile bu donusumun lideri olma potansiyeline sahiptir.</p><ul><li><strong>Buyuk Pazar:</strong> 350.000+ adreslenebilir isletme</li><li><strong>Dusuk Dijitallesme:</strong> Sadece %5 penetrasyon orani</li><li><strong>Yuksek Buyume:</strong> MoM %15+ musteri buyumesi</li><li><strong>Olceklenebilir Model:</strong> SaaS recurring revenue</li><li><strong>AI Farki:</strong> Rakiplerden ayrisan teknoloji</li></ul>',
            'investment_thesis_en': '<h3>Investment Thesis</h3><p>Turkey\'s F&B sector is at the beginning of digital transformation. E-Menum has the potential to lead this transformation with AI technology and user-friendly platform.</p><ul><li><strong>Large Market:</strong> 350,000+ addressable businesses</li><li><strong>Low Digitalization:</strong> Only 5% penetration rate</li><li><strong>High Growth:</strong> MoM 15%+ customer growth</li><li><strong>Scalable Model:</strong> SaaS recurring revenue</li><li><strong>AI Differentiator:</strong> Technology that sets us apart</li></ul>',
            'contact_email': 'investor@e-menum.net',
            'is_active': True,
        }
        if InvestorPage.objects.exists():
            obj = InvestorPage.objects.first()
            for key, val in defaults.items():
                setattr(obj, key, val)
            obj.save()
        else:
            InvestorPage.objects.create(**defaults)
        self.stdout.write('  ✓ InvestorPage')

    # =========================================================================
    # 28. INVESTOR FINANCIALS (4)
    # =========================================================================
    def _seed_investor_financials(self):
        items = [
            {'period': 'Q4 2025', 'metric_name_tr': 'Aylik Tekrarlayan Gelir (MRR)', 'metric_name_en': 'Monthly Recurring Revenue (MRR)', 'metric_value': '₺2.4M', 'change_pct': 18.5, 'sort_order': 1, 'is_active': True},
            {'period': 'Q4 2025', 'metric_name_tr': 'Aktif Musteri Sayisi', 'metric_name_en': 'Active Customer Count', 'metric_value': '1.200+', 'change_pct': 25.0, 'sort_order': 2, 'is_active': True},
            {'period': 'Q4 2025', 'metric_name_tr': 'Net Gelir Tutma Orani (NRR)', 'metric_name_en': 'Net Revenue Retention (NRR)', 'metric_value': '%115', 'change_pct': 5.2, 'sort_order': 3, 'is_active': True},
            {'period': 'Q4 2025', 'metric_name_tr': 'Aylik Kayip Orani (Churn)', 'metric_name_en': 'Monthly Churn Rate', 'metric_value': '%2.1', 'change_pct': -0.8, 'sort_order': 4, 'is_active': True},
        ]
        for f in items:
            InvestorFinancial.objects.update_or_create(period=f['period'], sort_order=f['sort_order'], defaults=f)
        self.stdout.write(f'  ✓ InvestorFinancial ({len(items)})')

    # =========================================================================
    # 29. PARTNER PROGRAMS (3 tiers)
    # =========================================================================
    def _seed_partner_programs(self):
        programs_data = [
            {'slug': 'bayi-programi', 'title_tr': 'Bayi Programi', 'title_en': 'Reseller Program', 'program_type': 'reseller', 'icon': 'ph-storefront', 'description_tr': '<p>E-Menum bayi programi ile kendi bolgenizde dijital menu cozumleri satin ve %30\'a varan komisyon kazanin. Satis egitimi, pazarlama materyalleri ve ozel bayi paneli dahil.</p>', 'description_en': '<p>Sell digital menu solutions in your region with E-Menum reseller program and earn up to 30% commission. Sales training, marketing materials, and dedicated reseller panel included.</p>', 'commission_info_tr': 'Gümüs: %15, Altin: %20, Platin: %30 komisyon', 'commission_info_en': 'Silver: 15%, Gold: 20%, Platinum: 30% commission', 'requirements_tr': '<ul><li>F&B sektorunde deneyim</li><li>Minimum 10 musteri/yil hedefi</li><li>Satis ve destek ekibi</li></ul>', 'requirements_en': '<ul><li>F&B industry experience</li><li>Minimum 10 customers/year target</li><li>Sales and support team</li></ul>', 'contact_email': 'partners@e-menum.net', 'sort_order': 1, 'is_active': True,
             'tiers': [
                 {'name_tr': 'Gumus Bayi', 'name_en': 'Silver Reseller', 'description_tr': 'Baslangic seviyesi', 'description_en': 'Entry level', 'commission_pct': 15.00, 'color': 'gray', 'sort_order': 1, 'benefits': [('Temel satis egitimi', 'Basic sales training'), ('Pazarlama materyalleri', 'Marketing materials'), ('E-posta destegi', 'Email support'), ('Bayi paneli erisimi', 'Reseller panel access')]},
                 {'name_tr': 'Altin Bayi', 'name_en': 'Gold Reseller', 'description_tr': 'Orta seviye', 'description_en': 'Mid level', 'commission_pct': 20.00, 'color': 'amber', 'sort_order': 2, 'benefits': [('Gelismis satis egitimi', 'Advanced sales training'), ('Ozel pazarlama destegi', 'Dedicated marketing support'), ('Oncelikli teknik destek', 'Priority technical support'), ('Co-branding imkani', 'Co-branding opportunity'), ('Ceyreklik performans bonusu', 'Quarterly performance bonus')]},
                 {'name_tr': 'Platin Bayi', 'name_en': 'Platinum Reseller', 'description_tr': 'Premium seviye', 'description_en': 'Premium level', 'commission_pct': 30.00, 'color': 'purple', 'sort_order': 3, 'benefits': [('1-1 hesap yoneticisi', 'Dedicated account manager'), ('Ozel fiyatlandirma', 'Custom pricing'), ('Beyaz etiket secenegi', 'White-label option'), ('Yillik is planlama desteği', 'Annual business planning support'), ('VIP etkinlik davetleri', 'VIP event invitations')]},
             ]},
            {'slug': 'referans-programi', 'title_tr': 'Referans Programi', 'title_en': 'Referral Program', 'program_type': 'referral', 'icon': 'ph-share-network', 'description_tr': '<p>Tanindiklarinizi E-Menum\'a yonlendirin, her basarili referans icin nakit veya kredi kazanin. Basit ve hizli.</p>', 'description_en': '<p>Refer people you know to E-Menum and earn cash or credit for every successful referral. Simple and fast.</p>', 'commission_info_tr': 'Her basarili referans: 1 ay ucretsiz veya ₺500 nakit', 'commission_info_en': 'Each successful referral: 1 month free or ₺500 cash', 'requirements_tr': '<ul><li>Aktif E-Menum musterisi olmak</li><li>Basarili kayit ve aktivasyon</li></ul>', 'requirements_en': '<ul><li>Be an active E-Menum customer</li><li>Successful registration and activation</li></ul>', 'contact_email': 'partners@e-menum.net', 'sort_order': 2, 'is_active': True,
             'tiers': [
                 {'name_tr': 'Standart Referans', 'name_en': 'Standard Referral', 'description_tr': 'Herkes icin acik', 'description_en': 'Open for everyone', 'commission_pct': 10.00, 'color': 'blue', 'sort_order': 1, 'benefits': [('Her referans icin 1 ay ucretsiz', 'One month free per referral'), ('Referans takip paneli', 'Referral tracking panel'), ('Otomatik odul sistemi', 'Automatic reward system')]},
             ]},
            {'slug': 'teknoloji-ortakligi', 'title_tr': 'Teknoloji Ortakligi Programi', 'title_en': 'Technology Partnership Program', 'program_type': 'technology', 'icon': 'ph-plugs-connected', 'description_tr': '<p>POS, muhasebe veya odeme sistemleri gelistiriyorsaniz, E-Menum API ile entegrasyon olusturun ve ortak musterilere deger katin.</p>', 'description_en': '<p>If you develop POS, accounting, or payment systems, build integration with E-Menum API and add value to shared customers.</p>', 'commission_info_tr': 'Komisyon orani entegrasyon tipine gore belirlenir', 'commission_info_en': 'Commission rate determined by integration type', 'requirements_tr': '<ul><li>Aktif yazilim urunu</li><li>API entegrasyon yetkinligi</li><li>Teknik destek ekibi</li></ul>', 'requirements_en': '<ul><li>Active software product</li><li>API integration capability</li><li>Technical support team</li></ul>', 'contact_email': 'partners@e-menum.net', 'sort_order': 3, 'is_active': True,
             'tiers': [
                 {'name_tr': 'Entegrasyon Ortagi', 'name_en': 'Integration Partner', 'description_tr': 'API entegrasyon ortagi', 'description_en': 'API integration partner', 'commission_pct': 10.00, 'color': 'emerald', 'sort_order': 1, 'benefits': [('API sandbox erisimi', 'API sandbox access'), ('Teknik dokumantasyon', 'Technical documentation'), ('Entegrasyon destek muhendisi', 'Integration support engineer'), ('Partner dizininde listeleme', 'Listing in partner directory')]},
                 {'name_tr': 'Stratejik Ortak', 'name_en': 'Strategic Partner', 'description_tr': 'Derin entegrasyon ortagi', 'description_en': 'Deep integration partner', 'commission_pct': 15.00, 'color': 'teal', 'sort_order': 2, 'benefits': [('Oncelikli API erisimi', 'Priority API access'), ('Ortak pazarlama kampanyalari', 'Joint marketing campaigns'), ('Ürün yol haritasi etkisi', 'Product roadmap influence'), ('Ozel entegrasyon destegi', 'Dedicated integration support'), ('Yillik ortaklik zirvesi', 'Annual partnership summit')]},
             ]},
        ]
        for prog_data in programs_data:
            tiers_data = prog_data.pop('tiers')
            prog, _ = PartnerProgram.objects.update_or_create(slug=prog_data['slug'], defaults=prog_data)
            for tier_data in tiers_data:
                benefits_data = tier_data.pop('benefits')
                tier, _ = PartnerTier.objects.update_or_create(
                    program=prog, sort_order=tier_data['sort_order'],
                    defaults=tier_data)
                for idx, (tr, en) in enumerate(benefits_data, start=1):
                    PartnerBenefit.objects.update_or_create(
                        tier=tier, sort_order=idx,
                        defaults={'text_tr': tr, 'text_en': en, 'icon': 'ph-check-circle', 'is_active': True})
        self.stdout.write(f'  ✓ PartnerProgram ({len(programs_data)}) + tiers + benefits')

    # =========================================================================
    # 30. HELP CATEGORIES (6)
    # =========================================================================
    def _seed_help_categories(self):
        cats = [
            {'slug': 'baslangic', 'name_tr': 'Baslangic Rehberi', 'name_en': 'Getting Started', 'description_tr': 'Kayit, kurulum ve ilk menu olusturma adimlari.', 'description_en': 'Registration, setup, and first menu creation steps.', 'icon': 'ph-rocket-launch', 'color': 'primary', 'sort_order': 1, 'is_active': True},
            {'slug': 'menu-yonetimi', 'name_tr': 'Menu Yonetimi', 'name_en': 'Menu Management', 'description_tr': 'Kategori, urun, fiyat ve menu tasarimi rehberleri.', 'description_en': 'Category, product, pricing, and menu design guides.', 'icon': 'ph-list-bullets', 'color': 'blue', 'sort_order': 2, 'is_active': True},
            {'slug': 'qr-kod', 'name_tr': 'QR Kod ve Erisim', 'name_en': 'QR Code & Access', 'description_tr': 'QR kod olusturma, ozellestirme ve yerlestirme rehberleri.', 'description_en': 'QR code creation, customization, and placement guides.', 'icon': 'ph-qr-code', 'color': 'green', 'sort_order': 3, 'is_active': True},
            {'slug': 'siparis-takibi', 'name_tr': 'Siparis ve Takip', 'name_en': 'Orders & Tracking', 'description_tr': 'Siparis alma, takip etme ve mutfak ekrani rehberleri.', 'description_en': 'Order receiving, tracking, and kitchen display guides.', 'icon': 'ph-receipt', 'color': 'orange', 'sort_order': 4, 'is_active': True},
            {'slug': 'faturalama', 'name_tr': 'Faturalama ve Abonelik', 'name_en': 'Billing & Subscription', 'description_tr': 'Odeme, fatura, plan degisikligi ve iptal islemleri.', 'description_en': 'Payment, invoicing, plan changes, and cancellation.', 'icon': 'ph-credit-card', 'color': 'purple', 'sort_order': 5, 'is_active': True},
            {'slug': 'api-entegrasyonlar', 'name_tr': 'API ve Entegrasyonlar', 'name_en': 'API & Integrations', 'description_tr': 'POS entegrasyonu, API kullanimi ve webhook ayarlari.', 'description_en': 'POS integration, API usage, and webhook settings.', 'icon': 'ph-plugs-connected', 'color': 'indigo', 'sort_order': 6, 'is_active': True},
        ]
        for c in cats:
            HelpCategory.objects.update_or_create(slug=c['slug'], defaults=c)
        self.stdout.write(f'  ✓ HelpCategory ({len(cats)})')

    # =========================================================================
    # 31. HELP ARTICLES (30)
    # =========================================================================
    def _seed_help_articles(self):
        cat_map = {c.slug: c for c in HelpCategory.objects.all()}
        articles = [
            # BASLANGIC (5)
            {'category': cat_map.get('baslangic'), 'slug': 'hesap-olusturma', 'title_tr': 'Hesap Olusturma ve Kayit', 'title_en': 'Account Creation and Registration', 'content_tr': '<h2>Hesap Olusturma</h2><p>E-Menum\'a kayit olmak icin:</p><ol><li>Ana sayfada "Ucretsiz Basla" butonuna tiklayin</li><li>E-posta adresinizi ve sifrenizi girin</li><li>Isletme bilgilerinizi doldurun</li><li>E-posta dogrulamanizi tamamlayin</li></ol><p>Kayit sureci 2 dakikadan kisa surer ve kredi karti gerektirmez.</p>', 'content_en': '<h2>Account Creation</h2><p>To register for E-Menum:</p><ol><li>Click "Start Free" on the homepage</li><li>Enter your email and password</li><li>Fill in your business information</li><li>Complete email verification</li></ol><p>Registration takes less than 2 minutes and requires no credit card.</p>', 'is_featured': True, 'sort_order': 1, 'is_active': True},
            {'category': cat_map.get('baslangic'), 'slug': 'ilk-menu-olusturma', 'title_tr': 'Ilk Menunuzu Olusturma', 'title_en': 'Creating Your First Menu', 'content_tr': '<h2>Ilk Menu</h2><p>Kayit olduktan sonra:</p><ol><li>Dashboard\'dan "Yeni Menu Olustur" butonuna tiklayin</li><li>Menu adini ve dilini secin</li><li>Kategoriler ekleyin (orn: Ana Yemekler, Icecekler)</li><li>Her kategoriye urunler ekleyin</li><li>"Yayinla" butonuyla menuyu canli yapin</li></ol>', 'content_en': '<h2>First Menu</h2><p>After registration:</p><ol><li>Click "Create New Menu" on dashboard</li><li>Choose menu name and language</li><li>Add categories (e.g., Main Courses, Drinks)</li><li>Add products to each category</li><li>Make menu live with "Publish" button</li></ol>', 'is_featured': True, 'sort_order': 2, 'is_active': True},
            {'category': cat_map.get('baslangic'), 'slug': 'panel-genel-bakis', 'title_tr': 'Yonetim Paneli Genel Bakis', 'title_en': 'Dashboard Overview', 'content_tr': '<h2>Yonetim Paneli</h2><p>E-Menum yonetim paneli sunlari icerir:</p><ul><li><strong>Dashboard:</strong> Ozet istatistikler ve hizli erisim</li><li><strong>Menuler:</strong> Menu olusturma ve duzenleme</li><li><strong>Siparisler:</strong> Gelen siparis yonetimi</li><li><strong>Analitik:</strong> Detayli raporlar ve grafikler</li><li><strong>Ayarlar:</strong> Isletme ve hesap ayarlari</li></ul>', 'content_en': '<h2>Dashboard</h2><p>E-Menum management panel includes:</p><ul><li><strong>Dashboard:</strong> Summary statistics and quick access</li><li><strong>Menus:</strong> Menu creation and editing</li><li><strong>Orders:</strong> Incoming order management</li><li><strong>Analytics:</strong> Detailed reports and charts</li><li><strong>Settings:</strong> Business and account settings</li></ul>', 'is_featured': False, 'sort_order': 3, 'is_active': True},
            {'category': cat_map.get('baslangic'), 'slug': 'tema-secimi-ozellestirme', 'title_tr': 'Tema Secimi ve Ozellestirme', 'title_en': 'Theme Selection and Customization', 'content_tr': '<h2>Tema Ozellestirme</h2><p>Menunuzun gorunumunu markaniza uygun hale getirin:</p><ol><li>Menu ayarlarindan "Tema" bolumune gidin</li><li>Hazir temalardan birini secin veya ozel tema olusturun</li><li>Marka renklerinizi ve fontlarinizi ayarlayin</li><li>Logo ve arka plan gorseli yukleyin</li></ol>', 'content_en': '<h2>Theme Customization</h2><p>Customize your menu appearance to match your brand:</p><ol><li>Go to "Theme" section in menu settings</li><li>Choose a ready theme or create custom</li><li>Set your brand colors and fonts</li><li>Upload logo and background image</li></ol>', 'is_featured': False, 'sort_order': 4, 'is_active': True},
            {'category': cat_map.get('baslangic'), 'slug': 'urun-ekleme-duzenleme', 'title_tr': 'Urun Ekleme ve Duzenleme', 'title_en': 'Adding and Editing Products', 'content_tr': '<h2>Urun Yonetimi</h2><p>Urun eklemek icin:</p><ol><li>Menu icerisinde bir kategori secin</li><li>"Urun Ekle" butonuna tiklayin</li><li>Ad, aciklama, fiyat ve gorseli girin</li><li>Alerjen bilgilerini isaretleyin</li><li>Kaydedin</li></ol><p><strong>Ipucu:</strong> AI butonuyla urun aciklamasini otomatik olustabilirsiniz.</p>', 'content_en': '<h2>Product Management</h2><p>To add a product:</p><ol><li>Select a category in the menu</li><li>Click "Add Product"</li><li>Enter name, description, price, and image</li><li>Mark allergen information</li><li>Save</li></ol><p><strong>Tip:</strong> Use the AI button to auto-generate descriptions.</p>', 'is_featured': False, 'sort_order': 5, 'is_active': True},
            # MENU YONETIMI (5)
            {'category': cat_map.get('menu-yonetimi'), 'slug': 'kategori-yonetimi', 'title_tr': 'Kategori Olusturma ve Yonetimi', 'title_en': 'Category Creation and Management', 'content_tr': '<h2>Kategoriler</h2><p>Menulerinizdeki urunleri kategoriler altinda organize edin. Surukle-birak ile siralama degistirin. Her kategoriye ikon ve renk atayabilirsiniz.</p>', 'content_en': '<h2>Categories</h2><p>Organize products in your menus under categories. Change order with drag-and-drop. Assign icon and color to each category.</p>', 'is_featured': False, 'sort_order': 1, 'is_active': True},
            {'category': cat_map.get('menu-yonetimi'), 'slug': 'fiyat-guncelleme', 'title_tr': 'Fiyat Guncelleme ve Toplu Islem', 'title_en': 'Price Update and Bulk Operations', 'content_tr': '<h2>Fiyat Yonetimi</h2><p>Tek tek veya toplu fiyat guncelleme yapabilirsiniz. Excel ile toplu aktar/iceri al ozelligi mevcuttur. Fiyat degisiklikleri aninda canli menuye yansir.</p>', 'content_en': '<h2>Price Management</h2><p>Update prices individually or in bulk. Excel export/import feature available. Price changes reflect instantly on live menu.</p>', 'is_featured': False, 'sort_order': 2, 'is_active': True},
            {'category': cat_map.get('menu-yonetimi'), 'slug': 'coklu-dil-menu', 'title_tr': 'Coklu Dil Destegi ile Menu Olusturma', 'title_en': 'Creating Menu with Multi-Language Support', 'content_tr': '<h2>Coklu Dil</h2><p>6 dilde menu olusturabilirsiniz: Turkce, Ingilizce, Arapca, Rusca, Almanca ve Farsca. AI ceviri destegi ile otomatik ceviri yapabilirsiniz.</p>', 'content_en': '<h2>Multi-Language</h2><p>Create menus in 6 languages: Turkish, English, Arabic, Russian, German, and Persian. Use AI translation for automatic translations.</p>', 'is_featured': False, 'sort_order': 3, 'is_active': True},
            {'category': cat_map.get('menu-yonetimi'), 'slug': 'alerjen-bilgi-yonetimi', 'title_tr': 'Alerjen Bilgi Yonetimi', 'title_en': 'Allergen Information Management', 'content_tr': '<h2>Alerjenler</h2><p>Her urun icin 14 temel alerjeni isaretleyebilirsiniz. Sistem otomatik olarak musteri tarafinda alerjen uyarisini gosterir.</p>', 'content_en': '<h2>Allergens</h2><p>Mark 14 core allergens for each product. The system automatically shows allergen warnings to customers.</p>', 'is_featured': False, 'sort_order': 4, 'is_active': True},
            {'category': cat_map.get('menu-yonetimi'), 'slug': 'ai-icerik-uretimi-rehberi', 'title_tr': 'AI Icerik Uretimi Kullanim Rehberi', 'title_en': 'AI Content Generation Usage Guide', 'content_tr': '<h2>AI Icerik Uretimi</h2><p>Urun ekleme ekraninda AI butonuna tiklayarak otomatik aciklama uretebilirsiniz. Marka sesi ayarlarinizdan ton ve stil belirleyebilirsiniz.</p>', 'content_en': '<h2>AI Content Generation</h2><p>Click the AI button on product add screen to auto-generate descriptions. Set tone and style from brand voice settings.</p>', 'is_featured': True, 'sort_order': 5, 'is_active': True},
            # QR KOD (5)
            {'category': cat_map.get('qr-kod'), 'slug': 'qr-kod-olusturma', 'title_tr': 'QR Kod Olusturma', 'title_en': 'QR Code Creation', 'content_tr': '<h2>QR Kod</h2><p>Ayarlar > QR Kodlar bolumunden masa veya genel QR kod olusturabilirsiniz. Renk, boyut ve logo ozellestirme mevcuttur.</p>', 'content_en': '<h2>QR Code</h2><p>Create table or general QR codes from Settings > QR Codes. Color, size, and logo customization available.</p>', 'is_featured': True, 'sort_order': 1, 'is_active': True},
            {'category': cat_map.get('qr-kod'), 'slug': 'qr-kod-tasarimi', 'title_tr': 'QR Kod Tasarimi ve Ozellestirme', 'title_en': 'QR Code Design and Customization', 'content_tr': '<h2>QR Tasarim</h2><p>Markaniza uygun renkler, logo yerlestirme ve cerceve secenekleri ile profesyonel QR kodlar olusturun.</p>', 'content_en': '<h2>QR Design</h2><p>Create professional QR codes with brand colors, logo placement, and frame options.</p>', 'is_featured': False, 'sort_order': 2, 'is_active': True},
            {'category': cat_map.get('qr-kod'), 'slug': 'qr-kod-yerlestirme', 'title_tr': 'QR Kod Yerlestirme Tavsiyeleri', 'title_en': 'QR Code Placement Tips', 'content_tr': '<h2>Yerlestirme</h2><p>QR kodlari masa uzerine, menu tutucu icine veya duvar posterine yerlestirin. Taranabilir boyutta ve iyi aydinlatilmis bir konumda olmasi onemlidir.</p>', 'content_en': '<h2>Placement</h2><p>Place QR codes on tables, in menu holders, or on wall posters. Ensure scannable size and well-lit location.</p>', 'is_featured': False, 'sort_order': 3, 'is_active': True},
            {'category': cat_map.get('qr-kod'), 'slug': 'masa-bazli-qr-kurulumu', 'title_tr': 'Masa Bazli QR Kod Kurulumu', 'title_en': 'Table-Based QR Code Setup', 'content_tr': '<h2>Masa QR</h2><p>Her masaya ozel QR kod olusturmak icin: Ayarlar > Masalar bolumunden masa tanimlayin, QR kodlari otomatik olusturulur.</p>', 'content_en': '<h2>Table QR</h2><p>To create table-specific QR codes: Define tables from Settings > Tables, QR codes are auto-generated.</p>', 'is_featured': False, 'sort_order': 4, 'is_active': True},
            {'category': cat_map.get('qr-kod'), 'slug': 'qr-tarama-istatistikleri', 'title_tr': 'QR Tarama Istatistikleri', 'title_en': 'QR Scan Statistics', 'content_tr': '<h2>Tarama Istatistikleri</h2><p>Analitik panelinden QR tarama sayilari, saatlik dagilim ve en cok taranan masalari takip edebilirsiniz.</p>', 'content_en': '<h2>Scan Statistics</h2><p>Track QR scan counts, hourly distribution, and most scanned tables from the analytics panel.</p>', 'is_featured': False, 'sort_order': 5, 'is_active': True},
            # SIPARIS TAKIBI (5)
            {'category': cat_map.get('siparis-takibi'), 'slug': 'siparis-alma-sureci', 'title_tr': 'Siparis Alma Sureci', 'title_en': 'Order Receiving Process', 'content_tr': '<h2>Siparis Alma</h2><p>Musteri QR menuden siparis verdiginde bildirim alirsiniz. Siparisi onaylayarak mutfaga gonderin veya revize edin.</p>', 'content_en': '<h2>Order Receiving</h2><p>You get notified when a customer places an order via QR menu. Approve and send to kitchen or revise.</p>', 'is_featured': True, 'sort_order': 1, 'is_active': True},
            {'category': cat_map.get('siparis-takibi'), 'slug': 'mutfak-ekrani-kds', 'title_tr': 'Mutfak Ekrani (KDS) Kullanimi', 'title_en': 'Kitchen Display System (KDS) Usage', 'content_tr': '<h2>KDS</h2><p>Mutfak ekrani siparisleri gercek zamanli gosterir. Hazir olan siparisleri isaretleyin, garson ve musteri otomatik bilgilendirilir.</p>', 'content_en': '<h2>KDS</h2><p>Kitchen display shows orders in real-time. Mark ready orders, waiters and customers are auto-notified.</p>', 'is_featured': False, 'sort_order': 2, 'is_active': True},
            {'category': cat_map.get('siparis-takibi'), 'slug': 'masa-takip-sistemi', 'title_tr': 'Masa Takip Sistemi', 'title_en': 'Table Tracking System', 'content_tr': '<h2>Masa Takibi</h2><p>Her masanin durumunu (bos, dolu, hesap istendi) canli takip edin. Masa bazli siparis gecmisi ve sure analizi mevcuttur.</p>', 'content_en': '<h2>Table Tracking</h2><p>Track each table status (empty, occupied, bill requested) live. Table-based order history and time analysis available.</p>', 'is_featured': False, 'sort_order': 3, 'is_active': True},
            {'category': cat_map.get('siparis-takibi'), 'slug': 'garson-cagirma-hesap-isteme', 'title_tr': 'Garson Cagirma ve Hesap Isteme', 'title_en': 'Waiter Call and Bill Request', 'content_tr': '<h2>Garson Cagirma</h2><p>Musteriler QR menu uzerinden garson cagirabilir veya hesap isteyebilir. Bildirimler aninda personele iletilir.</p>', 'content_en': '<h2>Waiter Call</h2><p>Customers can call waiter or request bill via QR menu. Notifications instantly delivered to staff.</p>', 'is_featured': False, 'sort_order': 4, 'is_active': True},
            {'category': cat_map.get('siparis-takibi'), 'slug': 'siparis-raporlari', 'title_tr': 'Siparis Raporlari ve Analiz', 'title_en': 'Order Reports and Analysis', 'content_tr': '<h2>Raporlar</h2><p>Gunluk, haftalik ve aylik siparis raporlarini inceleyin. En cok siparis edilen urunler, ortalama sepet tutari ve peak saatler.</p>', 'content_en': '<h2>Reports</h2><p>Review daily, weekly, and monthly order reports. Most ordered products, average basket value, and peak hours.</p>', 'is_featured': False, 'sort_order': 5, 'is_active': True},
            # FATURALAMA (5)
            {'category': cat_map.get('faturalama'), 'slug': 'plan-secimi-yukseltme', 'title_tr': 'Plan Secimi ve Yukseltme', 'title_en': 'Plan Selection and Upgrade', 'content_tr': '<h2>Plan Degistirme</h2><p>Ayarlar > Abonelik bolumunden mevcut planinizi gorebilir ve yukseltme yapabilirsiniz. Yukseltmeler aninda gecerli olur.</p>', 'content_en': '<h2>Plan Change</h2><p>View your current plan and upgrade from Settings > Subscription. Upgrades take effect immediately.</p>', 'is_featured': True, 'sort_order': 1, 'is_active': True},
            {'category': cat_map.get('faturalama'), 'slug': 'odeme-yontemleri', 'title_tr': 'Odeme Yontemleri', 'title_en': 'Payment Methods', 'content_tr': '<h2>Odeme</h2><p>Kredi karti, banka karti, havale/EFT ve iyzico ile odeme yapabilirsiniz. Kurumsal musteriler icin fatura ile odeme mevcuttur.</p>', 'content_en': '<h2>Payment</h2><p>Pay with credit card, debit card, bank transfer, or iyzico. Invoice payment available for corporate customers.</p>', 'is_featured': False, 'sort_order': 2, 'is_active': True},
            {'category': cat_map.get('faturalama'), 'slug': 'fatura-indirme', 'title_tr': 'Fatura Indirme ve Gecmis', 'title_en': 'Invoice Download and History', 'content_tr': '<h2>Faturalar</h2><p>Ayarlar > Faturalar bolumunden tum gecmis faturalarinizi PDF olarak indirebilirsiniz.</p>', 'content_en': '<h2>Invoices</h2><p>Download all past invoices as PDF from Settings > Invoices section.</p>', 'is_featured': False, 'sort_order': 3, 'is_active': True},
            {'category': cat_map.get('faturalama'), 'slug': 'abonelik-iptal-etme', 'title_tr': 'Abonelik Iptal Etme', 'title_en': 'Subscription Cancellation', 'content_tr': '<h2>Iptal</h2><p>Ayarlar > Abonelik > Iptal Et ile iptali baslatin. Mevcut donem sonuna kadar hizmet devam eder. Verileriniz 30 gun saklanir.</p>', 'content_en': '<h2>Cancellation</h2><p>Start cancellation from Settings > Subscription > Cancel. Service continues until period end. Data kept for 30 days.</p>', 'is_featured': False, 'sort_order': 4, 'is_active': True},
            {'category': cat_map.get('faturalama'), 'slug': 'yillik-plan-indirimi', 'title_tr': 'Yillik Plan Indirimi', 'title_en': 'Annual Plan Discount', 'content_tr': '<h2>Yillik Indirim</h2><p>Yillik plana gecis yaparak %20 indirim elde edin. Mevcut donem bitiminde yillik plana gecis yapilir.</p>', 'content_en': '<h2>Annual Discount</h2><p>Get 20% discount by switching to annual plan. Transition happens at end of current period.</p>', 'is_featured': False, 'sort_order': 5, 'is_active': True},
            # API & ENTEGRASYONLAR (5)
            {'category': cat_map.get('api-entegrasyonlar'), 'slug': 'api-baslangic-rehberi', 'title_tr': 'API Baslangic Rehberi', 'title_en': 'API Getting Started Guide', 'content_tr': '<h2>API Baslangic</h2><p>E-Menum REST API ile platformumuzu kendi uygulamalariniza entegre edin. API anahtarinizi Ayarlar > API bolumunden olusturun.</p>', 'content_en': '<h2>API Getting Started</h2><p>Integrate our platform into your applications with E-Menum REST API. Create your API key from Settings > API.</p>', 'is_featured': True, 'sort_order': 1, 'is_active': True},
            {'category': cat_map.get('api-entegrasyonlar'), 'slug': 'pos-entegrasyon-kurulumu', 'title_tr': 'POS Entegrasyon Kurulumu', 'title_en': 'POS Integration Setup', 'content_tr': '<h2>POS Entegrasyonu</h2><p>Ayarlar > Entegrasyonlar bolumunden POS sisteminizi secin. API anahtarini girin ve test siparisi vererek dogrulayin.</p>', 'content_en': '<h2>POS Integration</h2><p>Select your POS system from Settings > Integrations. Enter API key and verify with a test order.</p>', 'is_featured': False, 'sort_order': 2, 'is_active': True},
            {'category': cat_map.get('api-entegrasyonlar'), 'slug': 'webhook-ayarlari', 'title_tr': 'Webhook Ayarlari', 'title_en': 'Webhook Settings', 'content_tr': '<h2>Webhooks</h2><p>Siparis, menu guncelleme ve musteri olaylari icin webhook endpoint\'leri tanimlayin. JSON payload ile gercek zamanli bildirimler alin.</p>', 'content_en': '<h2>Webhooks</h2><p>Define webhook endpoints for order, menu update, and customer events. Get real-time notifications with JSON payloads.</p>', 'is_featured': False, 'sort_order': 3, 'is_active': True},
            {'category': cat_map.get('api-entegrasyonlar'), 'slug': 'muhasebe-entegrasyonu', 'title_tr': 'Muhasebe Yazilimi Entegrasyonu', 'title_en': 'Accounting Software Integration', 'content_tr': '<h2>Muhasebe</h2><p>Parasut, Logo ve diger muhasebe yazilimlariyla entegrasyon kurulumu. Faturalar ve satis verileri otomatik aktarilir.</p>', 'content_en': '<h2>Accounting</h2><p>Integration setup with accounting software. Invoices and sales data automatically transferred.</p>', 'is_featured': False, 'sort_order': 4, 'is_active': True},
            {'category': cat_map.get('api-entegrasyonlar'), 'slug': 'sandbox-ortami-kullanimi', 'title_tr': 'Sandbox Ortami Kullanimi', 'title_en': 'Sandbox Environment Usage', 'content_tr': '<h2>Sandbox</h2><p>Gelistirme ve test icin sandbox ortamini kullanin. Gercek verilerinizi etkilemeden API entegrasyonlarinizi test edin.</p>', 'content_en': '<h2>Sandbox</h2><p>Use sandbox environment for development and testing. Test API integrations without affecting your real data.</p>', 'is_featured': False, 'sort_order': 5, 'is_active': True},
        ]
        for a in articles:
            HelpArticle.objects.update_or_create(slug=a['slug'], defaults=a)
        self.stdout.write(f'  ✓ HelpArticle ({len(articles)})')

    # =========================================================================
    # 32. STOREFRONT NAV LINKS
    # =========================================================================
    def _seed_storefront_nav_links(self):
        # Header navigation links
        header_links = [
            {'location': 'header', 'label_tr': 'Ozellikler', 'label_en': 'Features', 'url': 'website:features', 'icon': 'ph-sparkle', 'sort_order': 1, 'is_active': True},
            {'location': 'header', 'label_tr': 'Cozumler', 'label_en': 'Solutions', 'url': 'website:solutions', 'icon': 'ph-lightbulb', 'sort_order': 2, 'is_active': True},
            {'location': 'header', 'label_tr': 'Fiyatlandirma', 'label_en': 'Pricing', 'url': 'website:pricing', 'icon': 'ph-tag', 'sort_order': 3, 'is_active': True},
            {'location': 'header', 'label_tr': 'Musteriler', 'label_en': 'Customers', 'url': 'website:customers', 'icon': 'ph-users', 'sort_order': 4, 'is_active': True},
            {'location': 'header', 'label_tr': 'Kaynaklar', 'label_en': 'Resources', 'url': 'website:resources', 'icon': 'ph-book-open', 'sort_order': 5, 'is_active': True},
        ]
        for link in header_links:
            NavigationLink.objects.update_or_create(
                location=link['location'], sort_order=link['sort_order'],
                defaults=link)
        self.stdout.write(f'  ✓ StorefrontNavLinks (header: {len(header_links)})')
