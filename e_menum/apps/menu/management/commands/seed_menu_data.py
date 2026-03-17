"""
Management command to seed realistic Turkish restaurant data.

Creates a complete test dataset with:
- 1 Organization (Lezzet Sarayi)
- 1 Owner user
- 1 Theme (Sunset preset)
- 1 Menu (Ana Menu, published)
- 9 Categories with Phosphor icons
- ~35 Products with realistic names, descriptions, prices
- ProductVariants (sizes)
- ProductModifiers (extras + sauces)
- 8 Allergens (platform-level)
- ProductAllergens linking products to allergens
- NutritionInfo for select products
- Full i18n support (TR, EN, AR, FA, UK)

Usage:
    python manage.py seed_menu_data
    python manage.py seed_menu_data --clear  # Clear existing data first
"""

import logging
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.core.models import Organization
from apps.menu.models import (
    Allergen,
    AllergenSeverity,
    Category,
    Menu,
    NutritionInfo,
    Product,
    ProductAllergen,
    ProductModifier,
    ProductVariant,
    Theme,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with realistic Turkish restaurant data for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing seed data before creating new data",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_data()

        self.stdout.write("Seeding menu data...\n")

        # Step 1: Create user & organization
        user = self._create_user()
        org = self._create_organization(user)

        # Step 2: Create theme
        theme = self._create_theme(org)

        # Step 3: Create menu
        menu = self._create_menu(org, theme)

        # Step 4: Create allergens (platform-level)
        allergens = self._create_allergens()

        # Step 5: Create categories
        categories = self._create_categories(org, menu)

        # Step 6: Create products with variants, modifiers, allergens, nutrition
        self._create_products(org, categories, allergens)

        self.stdout.write(
            self.style.SUCCESS(
                "\nSeed data created successfully!\n"
                f"  Organization: {org.name}\n"
                f"  Menu: {menu.name} (slug: {menu.slug})\n"
                f"  Categories: {len(categories)}\n"
                f"  Products: {Product.objects.filter(organization=org).count()}\n"
                f"  Allergens: {len(allergens)}\n"
                f"\n  Visit: /m/{menu.slug}/"
            )
        )

    def _clear_data(self):
        self.stdout.write("Clearing existing seed data...")
        NutritionInfo.all_objects.all().delete()
        ProductAllergen.all_objects.all().delete()
        ProductModifier.all_objects.all().delete()
        ProductVariant.all_objects.all().delete()
        Product.all_objects.all().delete()
        Category.all_objects.all().delete()
        Menu.all_objects.all().delete()
        Theme.all_objects.all().delete()
        Allergen.all_objects.all().delete()
        Organization.objects.filter(slug="lezzet-sarayi").delete()
        User.objects.filter(email="admin@lezzetsarayi.com").delete()
        self.stdout.write(self.style.WARNING("  Cleared!"))

    def _create_user(self):
        user, created = User.objects.get_or_create(
            email="admin@lezzetsarayi.com",
            defaults={
                "first_name": "Ahmet",
                "last_name": "Yilmaz",
                "is_staff": True,
                "status": "ACTIVE",
            },
        )
        if created:
            user.set_password("LezzetSarayi2024!")
            user.save()
            self.stdout.write(f"  Created user: {user.email}")
        else:
            # Always ensure password matches expected value
            if not user.check_password("LezzetSarayi2024!"):
                user.set_password("LezzetSarayi2024!")
                user.save(update_fields=["password"])
                self.stdout.write(f"  Password reset: {user.email}")
            else:
                self.stdout.write(f"  User exists: {user.email}")
        return user

    def _create_organization(self, user):
        org, created = Organization.objects.get_or_create(
            slug="lezzet-sarayi",
            defaults={
                "name": "Lezzet Sarayi",
                "status": "active",
                "settings": {
                    "currency": "TRY",
                    "locale": "tr-TR",
                    "timezone": "Europe/Istanbul",
                },
            },
        )
        if created:
            self.stdout.write(f"  Created organization: {org.name}")
        else:
            self.stdout.write(f"  Organization exists: {org.name}")

        # Link user to organization
        if hasattr(user, "organization"):
            if user.organization != org:
                user.organization = org
                user.save(update_fields=["organization"])

        return org

    def _create_theme(self, org):
        theme, created = Theme.objects.get_or_create(
            organization=org,
            slug="sunset",
            defaults={
                "name_tr": "Sunset",
                "name_en": "Sunset",
                "name_ar": "غروب",
                "name_fa": "غروب",
                "name_uk": "Захід сонця",
                "description_tr": "Sicak ve davetkar renkler",
                "description_en": "Warm and inviting colors",
                "description_ar": "ألوان دافئة وجذابة",
                "description_fa": "رنگ‌های گرم و دلنشین",
                "description_uk": "Теплі та привітні кольори",
                "primary_color": "#E85D04",
                "secondary_color": "#1B4332",
                "background_color": "#FAFAF9",
                "text_color": "#1C1917",
                "accent_color": "#FFBA08",
                "font_family": "Plus Jakarta Sans",
                "heading_font_family": "Playfair Display",
                "is_default": True,
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(f"  Created theme: {theme.name}")
        return theme

    def _create_menu(self, org, theme):
        menu, created = Menu.objects.get_or_create(
            organization=org,
            slug="ana-menu",
            defaults={
                "name_tr": "Ana Menu",
                "name_en": "Main Menu",
                "name_ar": "القائمة الرئيسية",
                "name_fa": "منوی اصلی",
                "name_uk": "Головне меню",
                "description_tr": "Lezzet Sarayi - Gastronomi Deneyimi",
                "description_en": "Lezzet Sarayi - Gastronomy Experience",
                "description_ar": "قصر المذاق - تجربة فن الطهي",
                "description_fa": "کاخ لذت - تجربه گاسترونومی",
                "description_uk": "Палац Смаку - Гастрономічний Досвід",
                "is_published": True,
                "published_at": timezone.now(),
                "is_default": True,
                "theme": theme,
                "settings": {
                    "currency": "TRY",
                },
            },
        )
        if created:
            self.stdout.write(f"  Created menu: {menu.name}")
        return menu

    def _create_allergens(self):
        allergen_data = [
            {
                "code": "GLU",
                "sort_order": 1,
                "name_tr": "Gluten",
                "name_en": "Gluten",
                "name_ar": "الغلوتين",
                "name_fa": "گلوتن",
                "name_uk": "Глютен",
            },
            {
                "code": "DAI",
                "sort_order": 2,
                "name_tr": "Sut Urunleri",
                "name_en": "Dairy",
                "name_ar": "منتجات الألبان",
                "name_fa": "لبنیات",
                "name_uk": "Молочні продукти",
            },
            {
                "code": "EGG",
                "sort_order": 3,
                "name_tr": "Yumurta",
                "name_en": "Eggs",
                "name_ar": "البيض",
                "name_fa": "تخم‌مرغ",
                "name_uk": "Яйця",
            },
            {
                "code": "PEA",
                "sort_order": 4,
                "name_tr": "Fistik",
                "name_en": "Peanuts",
                "name_ar": "الفول السوداني",
                "name_fa": "بادام‌زمینی",
                "name_uk": "Арахіс",
            },
            {
                "code": "SOY",
                "sort_order": 5,
                "name_tr": "Soya",
                "name_en": "Soy",
                "name_ar": "الصويا",
                "name_fa": "سویا",
                "name_uk": "Соя",
            },
            {
                "code": "NUT",
                "sort_order": 6,
                "name_tr": "Findik",
                "name_en": "Tree Nuts",
                "name_ar": "المكسرات",
                "name_fa": "آجیل",
                "name_uk": "Горіхи",
            },
            {
                "code": "SES",
                "sort_order": 7,
                "name_tr": "Susam",
                "name_en": "Sesame",
                "name_ar": "السمسم",
                "name_fa": "کنجد",
                "name_uk": "Кунжут",
            },
            {
                "code": "SHE",
                "sort_order": 8,
                "name_tr": "Deniz Urunu",
                "name_en": "Shellfish",
                "name_ar": "المحار",
                "name_fa": "صدف‌داران",
                "name_uk": "Молюски",
            },
        ]

        allergens = {}
        for data in allergen_data:
            allergen, created = Allergen.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name_tr": data["name_tr"],
                    "name_en": data["name_en"],
                    "name_ar": data["name_ar"],
                    "name_fa": data["name_fa"],
                    "name_uk": data["name_uk"],
                    "slug": slugify(data["name_tr"]),
                    "sort_order": data["sort_order"],
                    "is_active": True,
                },
            )
            allergens[data["code"]] = allergen

        self.stdout.write(f"  Created/verified {len(allergens)} allergens")
        return allergens

    def _create_categories(self, org, menu):
        category_data = [
            {
                "name": "Kebaplar",
                "icon": "ph-fill ph-knife",
                "sort_order": 1,
                "name_tr": "Kebaplar",
                "name_en": "Kebabs",
                "name_ar": "الكباب",
                "name_fa": "کباب‌ها",
                "name_uk": "Кебаби",
                "desc_tr": "Odun atesinde pisirilmis geleneksel kebaplar",
                "desc_en": "Traditional kebabs cooked over wood fire",
                "desc_ar": "كباب تقليدي مطبوخ على نار الحطب",
                "desc_fa": "کباب‌های سنتی پخته‌شده روی آتش هیزم",
                "desc_uk": "Традиційні кебаби, приготовлені на дров'яному вогні",
            },
            {
                "name": "Burgerler",
                "icon": "ph-fill ph-hamburger",
                "sort_order": 2,
                "name_tr": "Burgerler",
                "name_en": "Burgers",
                "name_ar": "البرغر",
                "name_fa": "برگرها",
                "name_uk": "Бургери",
                "desc_tr": "El yapimi gurme burgerler",
                "desc_en": "Handmade gourmet burgers",
                "desc_ar": "برغر ذواقة مصنوع يدوياً",
                "desc_fa": "برگرهای گورمه دست‌ساز",
                "desc_uk": "Гурме бургери ручної роботи",
            },
            {
                "name": "Pizzalar",
                "icon": "ph-fill ph-pizza",
                "sort_order": 3,
                "name_tr": "Pizzalar",
                "name_en": "Pizzas",
                "name_ar": "البيتزا",
                "name_fa": "پیتزاها",
                "name_uk": "Піци",
                "desc_tr": "Tas firin pizzalar, ince ve kalin hamur",
                "desc_en": "Stone oven pizzas, thin and thick crust",
                "desc_ar": "بيتزا فرن حجري، عجينة رقيقة وسميكة",
                "desc_fa": "پیتزاهای تنور سنگی، خمیر نازک و ضخیم",
                "desc_uk": "Піци з кам'яної печі, тонке та товсте тісто",
            },
            {
                "name": "Salatalar",
                "icon": "ph-fill ph-leaf",
                "sort_order": 4,
                "name_tr": "Salatalar",
                "name_en": "Salads",
                "name_ar": "السلطات",
                "name_fa": "سالادها",
                "name_uk": "Салати",
                "desc_tr": "Taze ve saglikli salatalar",
                "desc_en": "Fresh and healthy salads",
                "desc_ar": "سلطات طازجة وصحية",
                "desc_fa": "سالادهای تازه و سالم",
                "desc_uk": "Свіжі та корисні салати",
            },
            {
                "name": "Deniz Urunleri",
                "icon": "ph-fill ph-fish",
                "sort_order": 5,
                "name_tr": "Deniz Urunleri",
                "name_en": "Seafood",
                "name_ar": "المأكولات البحرية",
                "name_fa": "غذاهای دریایی",
                "name_uk": "Морепродукти",
                "desc_tr": "Gunluk taze deniz urunleri",
                "desc_en": "Daily fresh seafood",
                "desc_ar": "مأكولات بحرية طازجة يومياً",
                "desc_fa": "غذاهای دریایی تازه روزانه",
                "desc_uk": "Щоденні свіжі морепродукти",
            },
            {
                "name": "Corbalar",
                "icon": "ph-fill ph-bowl-food",
                "sort_order": 6,
                "name_tr": "Corbalar",
                "name_en": "Soups",
                "name_ar": "الشوربات",
                "name_fa": "سوپ‌ها",
                "name_uk": "Супи",
                "desc_tr": "Ev yapimi sicak corbalar",
                "desc_en": "Homemade hot soups",
                "desc_ar": "شوربات ساخنة محلية الصنع",
                "desc_fa": "سوپ‌های داغ خانگی",
                "desc_uk": "Домашні гарячі супи",
            },
            {
                "name": "Mezeler",
                "icon": "ph-fill ph-carrot",
                "sort_order": 7,
                "name_tr": "Mezeler",
                "name_en": "Appetizers",
                "name_ar": "المقبلات",
                "name_fa": "پیش‌غذاها",
                "name_uk": "Закуски",
                "desc_tr": "Geleneksel Turk mezeleri",
                "desc_en": "Traditional Turkish appetizers",
                "desc_ar": "مقبلات تركية تقليدية",
                "desc_fa": "پیش‌غذاهای سنتی ترکی",
                "desc_uk": "Традиційні турецькі закуски",
            },
            {
                "name": "Tatlilar",
                "icon": "ph-fill ph-cake",
                "sort_order": 8,
                "name_tr": "Tatlilar",
                "name_en": "Desserts",
                "name_ar": "الحلويات",
                "name_fa": "دسرها",
                "name_uk": "Десерти",
                "desc_tr": "Ev yapimi tatlilar ve pastalar",
                "desc_en": "Homemade desserts and pastries",
                "desc_ar": "حلويات ومعجنات محلية الصنع",
                "desc_fa": "دسرها و شیرینی‌های خانگی",
                "desc_uk": "Домашні десерти та випічка",
            },
            {
                "name": "Icecekler",
                "icon": "ph-fill ph-wine",
                "sort_order": 9,
                "name_tr": "Icecekler",
                "name_en": "Beverages",
                "name_ar": "المشروبات",
                "name_fa": "نوشیدنی‌ها",
                "name_uk": "Напої",
                "desc_tr": "Sicak ve soguk icecekler",
                "desc_en": "Hot and cold beverages",
                "desc_ar": "مشروبات ساخنة وباردة",
                "desc_fa": "نوشیدنی‌های گرم و سرد",
                "desc_uk": "Гарячі та холодні напої",
            },
        ]

        categories = {}
        for data in category_data:
            cat, created = Category.objects.get_or_create(
                organization=org,
                menu=menu,
                slug=slugify(data["name"]),
                defaults={
                    "name_tr": data["name_tr"],
                    "name_en": data["name_en"],
                    "name_ar": data["name_ar"],
                    "name_fa": data["name_fa"],
                    "name_uk": data["name_uk"],
                    "icon": data["icon"],
                    "description_tr": data["desc_tr"],
                    "description_en": data["desc_en"],
                    "description_ar": data["desc_ar"],
                    "description_fa": data["desc_fa"],
                    "description_uk": data["desc_uk"],
                    "sort_order": data["sort_order"],
                    "is_active": True,
                },
            )
            categories[data["name"]] = cat

        self.stdout.write(f"  Created/verified {len(categories)} categories")
        return categories

    def _create_products(self, org, categories, allergens):
        """Create all products with variants, modifiers, allergens."""
        now = timezone.now()

        # ── KEBAPLAR ──
        kebap_products = [
            {
                "name": "Adana Kebap",
                "name_tr": "Adana Kebap",
                "name_en": "Adana Kebab",
                "name_ar": "كباب أضنة",
                "name_fa": "کباب آدانا",
                "name_uk": "Кебаб Адана",
                "price": 185,
                "prep": 25,
                "cal": 520,
                "desc_tr": "Aci biber ve kuyruk yagi ile yogrulan el kiymasi, odun atesinde sislenip pisirilir. Lavasin uzerinde servis edilir.",
                "desc_en": "Hand-minced meat kneaded with hot pepper and tail fat, skewered and cooked over wood fire. Served on lavash bread.",
                "desc_ar": "لحم مفروم يدوياً يُعجن بالفلفل الحار ودهن الذيل، يُشوى على نار الحطب. يُقدم على خبز اللافاش.",
                "desc_fa": "گوشت چرخ‌کرده دستی با فلفل تند و چربی دنبه ورز داده شده، روی سیخ و روی آتش هیزم پخته می‌شود. روی نان لواش سرو می‌شود.",
                "desc_uk": "М'ясний фарш ручної роботи з гострим перцем та курдючним жиром, нанизаний на шампур та приготований на дров'яному вогні. Подається на лаваші.",
                "image": "https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=600",
                "rating": 4.8,
                "reviews": 324,
                "featured": True,
                "spicy": 3,
                "tags": ["spicy"],
                "allergens": ["GLU"],
                "discount": 0,
                "variants": [
                    {
                        "name_tr": "Tek",
                        "name_en": "Single",
                        "name_ar": "واحد",
                        "name_fa": "تکی",
                        "name_uk": "Одинарний",
                        "price": 185,
                    },
                    {
                        "name_tr": "Bucuk",
                        "name_en": "Half",
                        "name_ar": "نصف",
                        "name_fa": "نیم",
                        "name_uk": "Половина",
                        "price": 140,
                    },
                    {
                        "name_tr": "Porsiyon",
                        "name_en": "Full Portion",
                        "name_ar": "حصة كاملة",
                        "name_fa": "پرس کامل",
                        "name_uk": "Повна порція",
                        "price": 230,
                    },
                ],
                "extras": [
                    {
                        "name_tr": "Ekstra Lavash",
                        "name_en": "Extra Lavash",
                        "name_ar": "لافاش إضافي",
                        "name_fa": "لواش اضافی",
                        "name_uk": "Додатковий лаваш",
                        "price": 15,
                    },
                    {
                        "name_tr": "Yogurt",
                        "name_en": "Yogurt",
                        "name_ar": "زبادي",
                        "name_fa": "ماست",
                        "name_uk": "Йогурт",
                        "price": 12,
                    },
                    {
                        "name_tr": "Kozde Biber",
                        "name_en": "Roasted Pepper",
                        "name_ar": "فلفل مشوي",
                        "name_fa": "فلفل کبابی",
                        "name_uk": "Печений перець",
                        "price": 10,
                    },
                ],
                "sauces": [
                    {
                        "name_tr": "Aci Sos",
                        "name_en": "Hot Sauce",
                        "name_ar": "صلصة حارة",
                        "name_fa": "سس تند",
                        "name_uk": "Гострий соус",
                    },
                    {
                        "name_tr": "Nar Eksisi",
                        "name_en": "Pomegranate Molasses",
                        "name_ar": "دبس الرمان",
                        "name_fa": "رب انار",
                        "name_uk": "Гранатовий соус",
                    },
                    {
                        "name_tr": "Sumak",
                        "name_en": "Sumac",
                        "name_ar": "سماق",
                        "name_fa": "سماق",
                        "name_uk": "Сумах",
                    },
                ],
            },
            {
                "name": "Urfa Kebap",
                "name_tr": "Urfa Kebap",
                "name_en": "Urfa Kebab",
                "name_ar": "كباب أورفة",
                "name_fa": "کباب اورفا",
                "name_uk": "Кебаб Урфа",
                "price": 175,
                "prep": 25,
                "cal": 490,
                "desc_tr": "Acisiz el kiymasi, odun atesinde yavas yavas pisirilir. Yumusacik dokusu ile meshurdur.",
                "desc_en": "Non-spicy hand-minced meat, slowly cooked over wood fire. Famous for its tender texture.",
                "desc_ar": "لحم مفروم يدوياً غير حار، يُطهى ببطء على نار الحطب. مشهور بقوامه الطري.",
                "desc_fa": "گوشت چرخ‌کرده دستی بدون تندی، به آرامی روی آتش هیزم پخته می‌شود. به خاطر بافت نرمش مشهور است.",
                "desc_uk": "Не гострий м'ясний фарш ручної роботи, повільно приготований на дров'яному вогні. Відомий своєю ніжною текстурою.",
                "image": "https://images.unsplash.com/photo-1603360946369-dc9bb6258143?w=600",
                "rating": 4.6,
                "reviews": 218,
                "featured": False,
                "spicy": 0,
                "tags": [],
                "allergens": ["GLU"],
                "discount": 10,
                "variants": [
                    {
                        "name_tr": "Tek",
                        "name_en": "Single",
                        "name_ar": "واحد",
                        "name_fa": "تکی",
                        "name_uk": "Одинарний",
                        "price": 175,
                    },
                    {
                        "name_tr": "Porsiyon",
                        "name_en": "Full Portion",
                        "name_ar": "حصة كاملة",
                        "name_fa": "پرس کامل",
                        "name_uk": "Повна порція",
                        "price": 220,
                    },
                ],
                "extras": [
                    {
                        "name_tr": "Yogurt",
                        "name_en": "Yogurt",
                        "name_ar": "زبادي",
                        "name_fa": "ماست",
                        "name_uk": "Йогурт",
                        "price": 12,
                    },
                ],
                "sauces": [
                    {
                        "name_tr": "Nar Eksisi",
                        "name_en": "Pomegranate Molasses",
                        "name_ar": "دبس الرمان",
                        "name_fa": "رب انار",
                        "name_uk": "Гранатовий соус",
                    },
                ],
            },
            {
                "name": "Beyti Kebap",
                "name_tr": "Beyti Kebap",
                "name_en": "Beyti Kebab",
                "name_ar": "كباب بيتي",
                "name_fa": "کباب بیتی",
                "name_uk": "Кебаб Бейті",
                "price": 220,
                "prep": 30,
                "cal": 680,
                "desc_tr": "Adana kebap, lavash ve yogurt ile sarildiktan sonra tereyagili domates sosu ile servis edilir.",
                "desc_en": "Adana kebab wrapped in lavash and yogurt, served with buttery tomato sauce.",
                "desc_ar": "كباب أضنة ملفوف بخبز اللافاش والزبادي، يُقدم مع صلصة الطماطم بالزبدة.",
                "desc_fa": "کباب آدانا پیچیده در لواش و ماست، با سس گوجه کره‌ای سرو می‌شود.",
                "desc_uk": "Кебаб Адана, загорнутий у лаваш з йогуртом, подається з томатним соусом на вершковому маслі.",
                "image": "https://images.unsplash.com/photo-1544025162-d76694265947?w=600",
                "rating": 4.9,
                "reviews": 412,
                "featured": True,
                "spicy": 2,
                "tags": ["spicy"],
                "allergens": ["GLU", "DAI"],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Ekstra Yogurt",
                        "name_en": "Extra Yogurt",
                        "name_ar": "زبادي إضافي",
                        "name_fa": "ماست اضافی",
                        "name_uk": "Додатковий йогурт",
                        "price": 15,
                    },
                    {
                        "name_tr": "Tereyagi Sosu",
                        "name_en": "Butter Sauce",
                        "name_ar": "صلصة الزبدة",
                        "name_fa": "سس کره",
                        "name_uk": "Вершковий соус",
                        "price": 20,
                    },
                ],
                "sauces": [
                    {
                        "name_tr": "Aci Sos",
                        "name_en": "Hot Sauce",
                        "name_ar": "صلصة حارة",
                        "name_fa": "سس تند",
                        "name_uk": "Гострий соус",
                    },
                    {
                        "name_tr": "Nar Eksisi",
                        "name_en": "Pomegranate Molasses",
                        "name_ar": "دبس الرمان",
                        "name_fa": "رب انار",
                        "name_uk": "Гранатовий соус",
                    },
                ],
            },
            {
                "name": "Kuzu Sis",
                "name_tr": "Kuzu Sis",
                "name_en": "Lamb Shish",
                "name_ar": "شيش لحم الضأن",
                "name_fa": "شیش کباب بره",
                "name_uk": "Шиш з ягнятини",
                "price": 245,
                "prep": 30,
                "cal": 560,
                "desc_tr": "Marine edilmis kuzu but parcalari, sebzeler ile sislenip odun atesinde pisirilir.",
                "desc_en": "Marinated lamb leg pieces, skewered with vegetables and cooked over wood fire.",
                "desc_ar": "قطع فخذ الضأن المتبلة، مشوية مع الخضروات على نار الحطب.",
                "desc_fa": "تکه‌های ران بره مارینه شده، با سبزیجات روی سیخ و روی آتش هیزم پخته می‌شود.",
                "desc_uk": "Мариновані шматочки бараньої ніжки, нанизані з овочами на шампур та приготовлені на дров'яному вогні.",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600",
                "rating": 4.7,
                "reviews": 189,
                "featured": False,
                "spicy": 0,
                "tags": [],
                "allergens": [],
                "discount": 0,
                "variants": [
                    {
                        "name_tr": "Tek",
                        "name_en": "Single",
                        "name_ar": "واحد",
                        "name_fa": "تکی",
                        "name_uk": "Одинарний",
                        "price": 245,
                    },
                    {
                        "name_tr": "Cift",
                        "name_en": "Double",
                        "name_ar": "مزدوج",
                        "name_fa": "دوتایی",
                        "name_uk": "Подвійний",
                        "price": 380,
                    },
                ],
                "extras": [
                    {
                        "name_tr": "Pilav",
                        "name_en": "Rice",
                        "name_ar": "أرز",
                        "name_fa": "برنج",
                        "name_uk": "Рис",
                        "price": 25,
                    },
                    {
                        "name_tr": "Kozde Sebze",
                        "name_en": "Grilled Vegetables",
                        "name_ar": "خضروات مشوية",
                        "name_fa": "سبزیجات کبابی",
                        "name_uk": "Овочі на грилі",
                        "price": 20,
                    },
                ],
                "sauces": [],
            },
        ]

        # ── BURGERLER ──
        burger_products = [
            {
                "name": "Classic Smash Burger",
                "name_tr": "Classic Smash Burger",
                "name_en": "Classic Smash Burger",
                "name_ar": "سماش برغر كلاسيكي",
                "name_fa": "اسمش برگر کلاسیک",
                "name_uk": "Класичний смеш бургер",
                "price": 165,
                "prep": 15,
                "cal": 720,
                "desc_tr": "Dana etinden el yapimi 2x120gr smash kofteler, cheddar peyniri, ozel sos, tursu.",
                "desc_en": "Handmade 2x120g beef smash patties, cheddar cheese, special sauce, pickles.",
                "desc_ar": "كفتة سماش يدوية الصنع 2×120غ من لحم البقر، جبنة شيدر، صلصة خاصة، مخلل.",
                "desc_fa": "کتلت اسمش دست‌ساز 2×120 گرم گوشت گاو، پنیر چدار، سس مخصوص، ترشی.",
                "desc_uk": "Котлети смеш ручної роботи 2x120г з яловичини, сир чедер, спеціальний соус, соління.",
                "image": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600",
                "rating": 4.7,
                "reviews": 567,
                "featured": True,
                "spicy": 0,
                "tags": [],
                "allergens": ["GLU", "DAI", "EGG", "SES"],
                "discount": 15,
                "variants": [
                    {
                        "name_tr": "Tek Kofte",
                        "name_en": "Single Patty",
                        "name_ar": "كفتة واحدة",
                        "name_fa": "تک کتلت",
                        "name_uk": "Одна котлета",
                        "price": 125,
                    },
                    {
                        "name_tr": "Cift Kofte",
                        "name_en": "Double Patty",
                        "name_ar": "كفتة مزدوجة",
                        "name_fa": "دو کتلت",
                        "name_uk": "Подвійна котлета",
                        "price": 165,
                    },
                    {
                        "name_tr": "Uclu",
                        "name_en": "Triple Patty",
                        "name_ar": "ثلاث كفتات",
                        "name_fa": "سه کتلت",
                        "name_uk": "Потрійна котлета",
                        "price": 205,
                    },
                ],
                "extras": [
                    {
                        "name_tr": "Ekstra Cheddar",
                        "name_en": "Extra Cheddar",
                        "name_ar": "شيدر إضافي",
                        "name_fa": "چدار اضافی",
                        "name_uk": "Додатковий чедер",
                        "price": 20,
                    },
                    {
                        "name_tr": "Bacon",
                        "name_en": "Bacon",
                        "name_ar": "لحم مقدد",
                        "name_fa": "بیکن",
                        "name_uk": "Бекон",
                        "price": 25,
                    },
                    {
                        "name_tr": "Jalapeno",
                        "name_en": "Jalapeño",
                        "name_ar": "هالابينو",
                        "name_fa": "هالاپینو",
                        "name_uk": "Халапеньо",
                        "price": 15,
                    },
                    {
                        "name_tr": "Avokado",
                        "name_en": "Avocado",
                        "name_ar": "أفوكادو",
                        "name_fa": "آووکادو",
                        "name_uk": "Авокадо",
                        "price": 30,
                    },
                ],
                "sauces": [
                    {
                        "name_tr": "Ozel Burger Sosu",
                        "name_en": "Special Burger Sauce",
                        "name_ar": "صلصة برغر خاصة",
                        "name_fa": "سس مخصوص برگر",
                        "name_uk": "Спеціальний бургер соус",
                    },
                    {
                        "name_tr": "BBQ",
                        "name_en": "BBQ",
                        "name_ar": "باربكيو",
                        "name_fa": "باربیکیو",
                        "name_uk": "BBQ",
                    },
                    {
                        "name_tr": "Ranch",
                        "name_en": "Ranch",
                        "name_ar": "رانش",
                        "name_fa": "رنچ",
                        "name_uk": "Ранч",
                    },
                    {
                        "name_tr": "Sriracha Mayo",
                        "name_en": "Sriracha Mayo",
                        "name_ar": "مايو سريراتشا",
                        "name_fa": "سس سریراچا مایو",
                        "name_uk": "Срірача майо",
                    },
                ],
            },
            {
                "name": "Truffle Mushroom Burger",
                "name_tr": "Truffle Mushroom Burger",
                "name_en": "Truffle Mushroom Burger",
                "name_ar": "برغر الفطر بالكمأة",
                "name_fa": "برگر قارچ ترافل",
                "name_uk": "Бургер з трюфелем та грибами",
                "price": 195,
                "prep": 18,
                "cal": 780,
                "desc_tr": "Truffle soslu mantar, karamelize sogan, gruyere peyniri ile gurme burger.",
                "desc_en": "Gourmet burger with truffle sauce mushrooms, caramelized onions, and gruyère cheese.",
                "desc_ar": "برغر ذواقة مع فطر بصلصة الكمأة، بصل مكرمل، وجبنة غرويير.",
                "desc_fa": "برگر گورمه با قارچ سس ترافل، پیاز کاراملی و پنیر گرویر.",
                "desc_uk": "Гурме бургер з грибами у трюфельному соусі, карамелізованою цибулею та сиром грюєр.",
                "image": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=600",
                "rating": 4.8,
                "reviews": 298,
                "featured": True,
                "spicy": 0,
                "tags": [],
                "allergens": ["GLU", "DAI", "EGG"],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Ekstra Mantar",
                        "name_en": "Extra Mushrooms",
                        "name_ar": "فطر إضافي",
                        "name_fa": "قارچ اضافی",
                        "name_uk": "Додаткові гриби",
                        "price": 20,
                    },
                    {
                        "name_tr": "Truffle Yag",
                        "name_en": "Truffle Oil",
                        "name_ar": "زيت الكمأة",
                        "name_fa": "روغن ترافل",
                        "name_uk": "Трюфельна олія",
                        "price": 25,
                    },
                ],
                "sauces": [
                    {
                        "name_tr": "Truffle Mayo",
                        "name_en": "Truffle Mayo",
                        "name_ar": "مايو الكمأة",
                        "name_fa": "مایونز ترافل",
                        "name_uk": "Трюфельний майонез",
                    },
                    {
                        "name_tr": "BBQ",
                        "name_en": "BBQ",
                        "name_ar": "باربكيو",
                        "name_fa": "باربیکیو",
                        "name_uk": "BBQ",
                    },
                ],
            },
            {
                "name": "Vegan Beyond Burger",
                "name_tr": "Vegan Beyond Burger",
                "name_en": "Vegan Beyond Burger",
                "name_ar": "برغر بيوند نباتي",
                "name_fa": "برگر بیاند وگان",
                "name_uk": "Веганський бургер Beyond",
                "price": 175,
                "prep": 15,
                "cal": 480,
                "desc_tr": "Beyond Meat kofte, vegan cheddar, avokado, taze sebzeler, vegan mayo.",
                "desc_en": "Beyond Meat patty, vegan cheddar, avocado, fresh vegetables, vegan mayo.",
                "desc_ar": "كفتة بيوند ميت، شيدر نباتي، أفوكادو، خضروات طازجة، مايونيز نباتي.",
                "desc_fa": "کتلت بیاند میت، چدار وگان، آووکادو، سبزیجات تازه، مایونز وگان.",
                "desc_uk": "Котлета Beyond Meat, веганський чедер, авокадо, свіжі овочі, веганський майонез.",
                "image": "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=600",
                "rating": 4.3,
                "reviews": 142,
                "featured": False,
                "spicy": 0,
                "tags": ["vegan"],
                "allergens": ["GLU", "SOY"],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Ekstra Avokado",
                        "name_en": "Extra Avocado",
                        "name_ar": "أفوكادو إضافي",
                        "name_fa": "آووکادو اضافی",
                        "name_uk": "Додаткове авокадо",
                        "price": 30,
                    },
                    {
                        "name_tr": "Jalapeno",
                        "name_en": "Jalapeño",
                        "name_ar": "هالابينو",
                        "name_fa": "هالاپینو",
                        "name_uk": "Халапеньо",
                        "price": 15,
                    },
                ],
                "sauces": [
                    {
                        "name_tr": "Vegan Mayo",
                        "name_en": "Vegan Mayo",
                        "name_ar": "مايونيز نباتي",
                        "name_fa": "مایونز وگان",
                        "name_uk": "Веганський майонез",
                    },
                    {
                        "name_tr": "BBQ",
                        "name_en": "BBQ",
                        "name_ar": "باربكيو",
                        "name_fa": "باربیکیو",
                        "name_uk": "BBQ",
                    },
                    {
                        "name_tr": "Hardal",
                        "name_en": "Mustard",
                        "name_ar": "خردل",
                        "name_fa": "خردل",
                        "name_uk": "Гірчиця",
                    },
                ],
            },
            {
                "name": "Spicy Chicken Burger",
                "name_tr": "Spicy Chicken Burger",
                "name_en": "Spicy Chicken Burger",
                "name_ar": "برغر الدجاج الحار",
                "name_fa": "برگر مرغ تند",
                "name_uk": "Гострий бургер з куркою",
                "price": 155,
                "prep": 15,
                "cal": 650,
                "desc_tr": "Crispy tavuk but, aci sos, coleslaw, tursu. Nashville hot tarzi.",
                "desc_en": "Crispy chicken thigh, hot sauce, coleslaw, pickles. Nashville hot style.",
                "desc_ar": "فخذ دجاج مقرمش، صلصة حارة، كول سلو، مخلل. على طريقة ناشفيل الحارة.",
                "desc_fa": "ران مرغ کریسپی، سس تند، کلسلاو، ترشی. به سبک نشویل هات.",
                "desc_uk": "Хрустке куряче стегно, гострий соус, капустяний салат, соління. У стилі Nashville hot.",
                "image": "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=600",
                "rating": 4.5,
                "reviews": 234,
                "featured": False,
                "spicy": 3,
                "tags": ["spicy"],
                "allergens": ["GLU", "DAI", "EGG"],
                "discount": 0,
                "variants": [
                    {
                        "name_tr": "Normal",
                        "name_en": "Regular",
                        "name_ar": "عادي",
                        "name_fa": "معمولی",
                        "name_uk": "Звичайний",
                        "price": 155,
                    },
                    {
                        "name_tr": "Double",
                        "name_en": "Double",
                        "name_ar": "مزدوج",
                        "name_fa": "دوتایی",
                        "name_uk": "Подвійний",
                        "price": 210,
                    },
                ],
                "extras": [
                    {
                        "name_tr": "Ekstra Coleslaw",
                        "name_en": "Extra Coleslaw",
                        "name_ar": "كول سلو إضافي",
                        "name_fa": "کلسلاو اضافی",
                        "name_uk": "Додатковий капустяний салат",
                        "price": 15,
                    },
                    {
                        "name_tr": "Sogan Halkasi",
                        "name_en": "Onion Rings",
                        "name_ar": "حلقات البصل",
                        "name_fa": "حلقه‌های پیاز",
                        "name_uk": "Цибульні кільця",
                        "price": 20,
                    },
                ],
                "sauces": [
                    {
                        "name_tr": "Nashville Hot",
                        "name_en": "Nashville Hot",
                        "name_ar": "ناشفيل هوت",
                        "name_fa": "نشویل هات",
                        "name_uk": "Nashville Hot",
                    },
                    {
                        "name_tr": "Ranch",
                        "name_en": "Ranch",
                        "name_ar": "رانش",
                        "name_fa": "رنچ",
                        "name_uk": "Ранч",
                    },
                    {
                        "name_tr": "BBQ",
                        "name_en": "BBQ",
                        "name_ar": "باربكيو",
                        "name_fa": "باربیکیو",
                        "name_uk": "BBQ",
                    },
                ],
            },
        ]

        # ── PIZZALAR ──
        pizza_products = [
            {
                "name": "Margherita",
                "name_tr": "Margherita",
                "name_en": "Margherita",
                "name_ar": "مارغريتا",
                "name_fa": "مارگاریتا",
                "name_uk": "Маргарита",
                "price": 140,
                "prep": 20,
                "cal": 580,
                "desc_tr": "San Marzano domates sosu, taze mozzarella, fesleden. Klasik Napoli tarifi.",
                "desc_en": "San Marzano tomato sauce, fresh mozzarella, basil. Classic Neapolitan recipe.",
                "desc_ar": "صلصة طماطم سان مارزانو، موزاريلا طازجة، ريحان. وصفة نابولي الكلاسيكية.",
                "desc_fa": "سس گوجه سن مارزانو، موزارلا تازه، ریحان. دستور کلاسیک ناپلی.",
                "desc_uk": "Соус з томатів Сан-Марзано, свіжа моцарела, базилік. Класичний неаполітанський рецепт.",
                "image": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=600",
                "rating": 4.6,
                "reviews": 432,
                "featured": False,
                "spicy": 0,
                "tags": ["vegetarian", "vejetaryen"],
                "allergens": ["GLU", "DAI"],
                "discount": 0,
                "variants": [
                    {
                        "name_tr": "Kucuk",
                        "name_en": "Small",
                        "name_ar": "صغير",
                        "name_fa": "کوچک",
                        "name_uk": "Маленька",
                        "price": 140,
                    },
                    {
                        "name_tr": "Orta",
                        "name_en": "Medium",
                        "name_ar": "وسط",
                        "name_fa": "متوسط",
                        "name_uk": "Середня",
                        "price": 175,
                    },
                    {
                        "name_tr": "Buyuk",
                        "name_en": "Large",
                        "name_ar": "كبير",
                        "name_fa": "بزرگ",
                        "name_uk": "Велика",
                        "price": 210,
                    },
                ],
                "extras": [
                    {
                        "name_tr": "Ekstra Mozzarella",
                        "name_en": "Extra Mozzarella",
                        "name_ar": "موزاريلا إضافية",
                        "name_fa": "موزارلا اضافی",
                        "name_uk": "Додаткова моцарела",
                        "price": 25,
                    },
                    {
                        "name_tr": "Zeytin",
                        "name_en": "Olives",
                        "name_ar": "زيتون",
                        "name_fa": "زیتون",
                        "name_uk": "Оливки",
                        "price": 15,
                    },
                ],
                "sauces": [],
            },
            {
                "name": "Karrisik Pizza",
                "name_tr": "Karrisik Pizza",
                "name_en": "Mixed Pizza",
                "name_ar": "بيتزا مشكلة",
                "name_fa": "پیتزا مخلوط",
                "name_uk": "Мікс піца",
                "price": 185,
                "prep": 22,
                "cal": 750,
                "desc_tr": "Sucuk, sosis, salam, biber, mantar, misir, zeytin ile yuklu pizza.",
                "desc_en": "Pizza loaded with sucuk, sausage, salami, peppers, mushrooms, corn, and olives.",
                "desc_ar": "بيتزا محملة بالسجق والنقانق والسلامي والفلفل والفطر والذرة والزيتون.",
                "desc_fa": "پیتزا پر شده با سوجوک، سوسیس، سالامی، فلفل، قارچ، ذرت و زیتون.",
                "desc_uk": "Піца з суджуком, сосисками, салямі, перцем, грибами, кукурудзою та оливками.",
                "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=600",
                "rating": 4.5,
                "reviews": 389,
                "featured": True,
                "spicy": 0,
                "tags": [],
                "allergens": ["GLU", "DAI"],
                "discount": 20,
                "variants": [
                    {
                        "name_tr": "Kucuk",
                        "name_en": "Small",
                        "name_ar": "صغير",
                        "name_fa": "کوچک",
                        "name_uk": "Маленька",
                        "price": 185,
                    },
                    {
                        "name_tr": "Orta",
                        "name_en": "Medium",
                        "name_ar": "وسط",
                        "name_fa": "متوسط",
                        "name_uk": "Середня",
                        "price": 225,
                    },
                    {
                        "name_tr": "Buyuk",
                        "name_en": "Large",
                        "name_ar": "كبير",
                        "name_fa": "بزرگ",
                        "name_uk": "Велика",
                        "price": 265,
                    },
                ],
                "extras": [
                    {
                        "name_tr": "Ekstra Sucuk",
                        "name_en": "Extra Sucuk",
                        "name_ar": "سجق إضافي",
                        "name_fa": "سوجوک اضافی",
                        "name_uk": "Додатковий суджук",
                        "price": 25,
                    },
                    {
                        "name_tr": "Ekstra Peynir",
                        "name_en": "Extra Cheese",
                        "name_ar": "جبنة إضافية",
                        "name_fa": "پنیر اضافی",
                        "name_uk": "Додатковий сир",
                        "price": 20,
                    },
                ],
                "sauces": [],
            },
            {
                "name": "Pepperoni",
                "name_tr": "Pepperoni",
                "name_en": "Pepperoni",
                "name_ar": "بيبروني",
                "name_fa": "پپرونی",
                "name_uk": "Пепероні",
                "price": 160,
                "prep": 18,
                "cal": 680,
                "desc_tr": "Bol pepperoni, mozzarella ve oregano. Amerikan klasigi.",
                "desc_en": "Generous pepperoni, mozzarella, and oregano. An American classic.",
                "desc_ar": "بيبروني وفير، موزاريلا وأوريغانو. كلاسيكية أمريكية.",
                "desc_fa": "پپرونی فراوان، موزارلا و پونه کوهی. کلاسیک آمریکایی.",
                "desc_uk": "Щедра пепероні, моцарела та орегано. Американська класика.",
                "image": "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=600",
                "rating": 4.4,
                "reviews": 278,
                "featured": False,
                "spicy": 1,
                "tags": [],
                "allergens": ["GLU", "DAI"],
                "discount": 0,
                "variants": [
                    {
                        "name_tr": "Kucuk",
                        "name_en": "Small",
                        "name_ar": "صغير",
                        "name_fa": "کوچک",
                        "name_uk": "Маленька",
                        "price": 160,
                    },
                    {
                        "name_tr": "Orta",
                        "name_en": "Medium",
                        "name_ar": "وسط",
                        "name_fa": "متوسط",
                        "name_uk": "Середня",
                        "price": 200,
                    },
                    {
                        "name_tr": "Buyuk",
                        "name_en": "Large",
                        "name_ar": "كبير",
                        "name_fa": "بزرگ",
                        "name_uk": "Велика",
                        "price": 240,
                    },
                ],
                "extras": [
                    {
                        "name_tr": "Ekstra Pepperoni",
                        "name_en": "Extra Pepperoni",
                        "name_ar": "بيبروني إضافي",
                        "name_fa": "پپرونی اضافی",
                        "name_uk": "Додаткова пепероні",
                        "price": 25,
                    },
                ],
                "sauces": [],
            },
        ]

        # ── SALATALAR ──
        salata_products = [
            {
                "name": "Sezar Salata",
                "name_tr": "Sezar Salata",
                "name_en": "Caesar Salad",
                "name_ar": "سلطة سيزر",
                "name_fa": "سالاد سزار",
                "name_uk": "Салат Цезар",
                "price": 95,
                "prep": 10,
                "cal": 320,
                "desc_tr": "Romaine marul, parmesan, kruton, sezar sos, izgara tavuk.",
                "desc_en": "Romaine lettuce, parmesan, croutons, Caesar dressing, grilled chicken.",
                "desc_ar": "خس روماني، بارميزان، خبز محمص، صلصة سيزر، دجاج مشوي.",
                "desc_fa": "کاهو رومین، پارمزان، نان برشته، سس سزار، مرغ گریل شده.",
                "desc_uk": "Салат ромен, пармезан, грінки, соус Цезар, курка гриль.",
                "image": "https://images.unsplash.com/photo-1550304943-4f24f54ddde9?w=600",
                "rating": 4.3,
                "reviews": 198,
                "featured": False,
                "spicy": 0,
                "tags": [],
                "allergens": ["GLU", "DAI", "EGG"],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Ekstra Tavuk",
                        "name_en": "Extra Chicken",
                        "name_ar": "دجاج إضافي",
                        "name_fa": "مرغ اضافی",
                        "name_uk": "Додаткова курка",
                        "price": 30,
                    },
                    {
                        "name_tr": "Avokado",
                        "name_en": "Avocado",
                        "name_ar": "أفوكادو",
                        "name_fa": "آووکادو",
                        "name_uk": "Авокадо",
                        "price": 25,
                    },
                ],
                "sauces": [
                    {
                        "name_tr": "Sezar Sos",
                        "name_en": "Caesar Dressing",
                        "name_ar": "صلصة سيزر",
                        "name_fa": "سس سزار",
                        "name_uk": "Соус Цезар",
                    },
                    {
                        "name_tr": "Balzamik",
                        "name_en": "Balsamic",
                        "name_ar": "بلسمي",
                        "name_fa": "بالزامیک",
                        "name_uk": "Бальзамік",
                    },
                ],
            },
            {
                "name": "Quinoa Bowl",
                "name_tr": "Quinoa Bowl",
                "name_en": "Quinoa Bowl",
                "name_ar": "طبق الكينوا",
                "name_fa": "کاسه کینوا",
                "name_uk": "Боул з кіноа",
                "price": 110,
                "prep": 12,
                "cal": 380,
                "desc_tr": "Quinoa, avokado, cherry domates, nohut, nar, limon sos. Saglikli ve doyurucu.",
                "desc_en": "Quinoa, avocado, cherry tomatoes, chickpeas, pomegranate, lemon dressing. Healthy and filling.",
                "desc_ar": "كينوا، أفوكادو، طماطم كرزية، حمص، رمان، صلصة ليمون. صحي ومشبع.",
                "desc_fa": "کینوا، آووکادو، گوجه گیلاسی، نخود، انار، سس لیمو. سالم و سیرکننده.",
                "desc_uk": "Кіноа, авокадо, помідори черрі, нут, гранат, лимонна заправка. Здорова та ситна страва.",
                "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600",
                "rating": 4.5,
                "reviews": 156,
                "featured": True,
                "spicy": 0,
                "tags": ["vegan", "gluten-free", "glutensiz"],
                "allergens": [],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Feta Peyniri",
                        "name_en": "Feta Cheese",
                        "name_ar": "جبنة فيتا",
                        "name_fa": "پنیر فتا",
                        "name_uk": "Сир фета",
                        "price": 20,
                    },
                    {
                        "name_tr": "Chia Tohumu",
                        "name_en": "Chia Seeds",
                        "name_ar": "بذور الشيا",
                        "name_fa": "دانه چیا",
                        "name_uk": "Насіння чіа",
                        "price": 10,
                    },
                ],
                "sauces": [
                    {
                        "name_tr": "Limon Sos",
                        "name_en": "Lemon Dressing",
                        "name_ar": "صلصة الليمون",
                        "name_fa": "سس لیمو",
                        "name_uk": "Лимонна заправка",
                    },
                    {
                        "name_tr": "Tahin Sos",
                        "name_en": "Tahini Dressing",
                        "name_ar": "صلصة الطحينة",
                        "name_fa": "سس تهینی",
                        "name_uk": "Тахіні заправка",
                    },
                ],
                "is_new": True,
            },
        ]

        # ── DENIZ URUNLERI ──
        deniz_products = [
            {
                "name": "Izgara Somon",
                "name_tr": "Izgara Somon",
                "name_en": "Grilled Salmon",
                "name_ar": "سلمون مشوي",
                "name_fa": "سالمون گریل شده",
                "name_uk": "Лосось на грилі",
                "price": 280,
                "prep": 25,
                "cal": 450,
                "desc_tr": "Taze Norverec somonu, tereyaginda pisirilmis sebzeler ve limon sos ile.",
                "desc_en": "Fresh Norwegian salmon, served with buttered vegetables and lemon sauce.",
                "desc_ar": "سلمون نرويجي طازج، يُقدم مع خضروات بالزبدة وصلصة الليمون.",
                "desc_fa": "سالمون تازه نروژی، با سبزیجات کره‌ای و سس لیمو سرو می‌شود.",
                "desc_uk": "Свіжий норвезький лосось, подається з овочами на вершковому маслі та лимонним соусом.",
                "image": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=600",
                "rating": 4.8,
                "reviews": 267,
                "featured": True,
                "spicy": 0,
                "tags": ["gluten-free", "glutensiz"],
                "allergens": ["SHE", "DAI"],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Pilav",
                        "name_en": "Rice",
                        "name_ar": "أرز",
                        "name_fa": "برنج",
                        "name_uk": "Рис",
                        "price": 25,
                    },
                    {
                        "name_tr": "Patates Pueresi",
                        "name_en": "Mashed Potatoes",
                        "name_ar": "بطاطس مهروسة",
                        "name_fa": "پوره سیب‌زمینی",
                        "name_uk": "Картопляне пюре",
                        "price": 20,
                    },
                ],
                "sauces": [
                    {
                        "name_tr": "Limon Tereyag",
                        "name_en": "Lemon Butter",
                        "name_ar": "ليمون بالزبدة",
                        "name_fa": "کره لیمویی",
                        "name_uk": "Лимонне масло",
                    },
                    {
                        "name_tr": "Dill Sos",
                        "name_en": "Dill Sauce",
                        "name_ar": "صلصة الشبت",
                        "name_fa": "سس شوید",
                        "name_uk": "Соус з кропу",
                    },
                ],
            },
            {
                "name": "Karides Tava",
                "name_tr": "Karides Tava",
                "name_en": "Pan-Fried Shrimp",
                "name_ar": "روبيان مقلي",
                "name_fa": "میگو تابه‌ای",
                "name_uk": "Смажені креветки",
                "price": 240,
                "prep": 20,
                "cal": 380,
                "desc_tr": "Tereyaginda sotelanmis jumbo karidesler, sarimsak ve maydanoz ile.",
                "desc_en": "Jumbo shrimp sautéed in butter with garlic and parsley.",
                "desc_ar": "روبيان جامبو مقلي بالزبدة مع الثوم والبقدونس.",
                "desc_fa": "میگوی جامبو سوته شده در کره با سیر و جعفری.",
                "desc_uk": "Джамбо креветки, обсмажені на вершковому маслі з часником та петрушкою.",
                "image": "https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=600",
                "rating": 4.6,
                "reviews": 178,
                "featured": False,
                "spicy": 1,
                "tags": ["gluten-free", "glutensiz"],
                "allergens": ["SHE", "DAI"],
                "discount": 10,
                "variants": [
                    {
                        "name_tr": "6 Adet",
                        "name_en": "6 Pieces",
                        "name_ar": "6 قطع",
                        "name_fa": "6 عدد",
                        "name_uk": "6 штук",
                        "price": 240,
                    },
                    {
                        "name_tr": "10 Adet",
                        "name_en": "10 Pieces",
                        "name_ar": "10 قطع",
                        "name_fa": "10 عدد",
                        "name_uk": "10 штук",
                        "price": 380,
                    },
                ],
                "extras": [
                    {
                        "name_tr": "Pilav",
                        "name_en": "Rice",
                        "name_ar": "أرز",
                        "name_fa": "برنج",
                        "name_uk": "Рис",
                        "price": 25,
                    },
                    {
                        "name_tr": "Ekmek",
                        "name_en": "Bread",
                        "name_ar": "خبز",
                        "name_fa": "نان",
                        "name_uk": "Хліб",
                        "price": 10,
                    },
                ],
                "sauces": [
                    {
                        "name_tr": "Sarimsak Sosu",
                        "name_en": "Garlic Sauce",
                        "name_ar": "صلصة الثوم",
                        "name_fa": "سس سیر",
                        "name_uk": "Часниковий соус",
                    },
                    {
                        "name_tr": "Limon",
                        "name_en": "Lemon",
                        "name_ar": "ليمون",
                        "name_fa": "لیمو",
                        "name_uk": "Лимон",
                    },
                ],
            },
            {
                "name": "Levrek Fileto",
                "name_tr": "Levrek Fileto",
                "name_en": "Sea Bass Fillet",
                "name_ar": "فيليه القاروص",
                "name_fa": "فیله سی‌بس",
                "name_uk": "Філе сібасу",
                "price": 260,
                "prep": 22,
                "cal": 350,
                "desc_tr": "Taze levrek fileto, zeytinyagi ve otlar ile firinda pisirilir.",
                "desc_en": "Fresh sea bass fillet, baked with olive oil and herbs.",
                "desc_ar": "فيليه قاروص طازج، مخبوز بزيت الزيتون والأعشاب.",
                "desc_fa": "فیله سی‌بس تازه، با روغن زیتون و سبزیجات معطر در فر پخته می‌شود.",
                "desc_uk": "Свіже філе сібасу, запечене з оливковою олією та травами.",
                "image": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=600",
                "rating": 4.7,
                "reviews": 145,
                "featured": False,
                "spicy": 0,
                "tags": ["gluten-free", "glutensiz"],
                "allergens": ["SHE"],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Roka Salata",
                        "name_en": "Arugula Salad",
                        "name_ar": "سلطة جرجير",
                        "name_fa": "سالاد روکولا",
                        "name_uk": "Салат з рукколи",
                        "price": 20,
                    },
                ],
                "sauces": [],
            },
        ]

        # ── CORBALAR ──
        corba_products = [
            {
                "name": "Mercimek Corbasi",
                "name_tr": "Mercimek Corbasi",
                "name_en": "Lentil Soup",
                "name_ar": "شوربة العدس",
                "name_fa": "سوپ عدس",
                "name_uk": "Сочевичний суп",
                "price": 55,
                "prep": 5,
                "cal": 180,
                "desc_tr": "Geleneksel kirmizi mercimek corbasi, limon ve kruton ile.",
                "desc_en": "Traditional red lentil soup, served with lemon and croutons.",
                "desc_ar": "شوربة العدس الأحمر التقليدية، تُقدم مع الليمون والخبز المحمص.",
                "desc_fa": "سوپ عدس قرمز سنتی، با لیمو و نان برشته سرو می‌شود.",
                "desc_uk": "Традиційний суп з червоної сочевиці, подається з лимоном та грінками.",
                "image": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=600",
                "rating": 4.4,
                "reviews": 567,
                "featured": False,
                "spicy": 0,
                "tags": ["vegan", "gluten-free", "glutensiz"],
                "allergens": [],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Ekmek",
                        "name_en": "Bread",
                        "name_ar": "خبز",
                        "name_fa": "نان",
                        "name_uk": "Хліб",
                        "price": 10,
                    },
                    {
                        "name_tr": "Limon",
                        "name_en": "Lemon",
                        "name_ar": "ليمون",
                        "name_fa": "لیمو",
                        "name_uk": "Лимон",
                        "price": 5,
                    },
                ],
                "sauces": [],
            },
            {
                "name": "Ezogelin Corbasi",
                "name_tr": "Ezogelin Corbasi",
                "name_en": "Ezogelin Soup",
                "name_ar": "شوربة إيزوجيلين",
                "name_fa": "سوپ ازوگلین",
                "name_uk": "Суп Езогелін",
                "price": 55,
                "prep": 5,
                "cal": 195,
                "desc_tr": "Bulgur, kirmizi mercimek ve domates ile zenginlestirilmis lezzetli corba.",
                "desc_en": "Delicious soup enriched with bulgur, red lentils, and tomatoes.",
                "desc_ar": "شوربة لذيذة غنية بالبرغل والعدس الأحمر والطماطم.",
                "desc_fa": "سوپ خوشمزه غنی‌شده با بلغور، عدس قرمز و گوجه‌فرنگی.",
                "desc_uk": "Смачний суп, збагачений булгуром, червоною сочевицею та томатами.",
                "image": "https://images.unsplash.com/photo-1603105037880-880cd4f50c55?w=600",
                "rating": 4.3,
                "reviews": 423,
                "featured": False,
                "spicy": 1,
                "tags": ["vegan"],
                "allergens": ["GLU"],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Ekmek",
                        "name_en": "Bread",
                        "name_ar": "خبز",
                        "name_fa": "نان",
                        "name_uk": "Хліб",
                        "price": 10,
                    },
                ],
                "sauces": [],
            },
            {
                "name": "Tavuk Suyu Corba",
                "name_tr": "Tavuk Suyu Corba",
                "name_en": "Chicken Soup",
                "name_ar": "شوربة الدجاج",
                "name_fa": "سوپ مرغ",
                "name_uk": "Курячий суп",
                "price": 60,
                "prep": 5,
                "cal": 150,
                "desc_tr": "Ev yapimi tavuk suyunda sehriye ve sebzeler. Sifa deposu.",
                "desc_en": "Homemade chicken broth with noodles and vegetables. A healing bowl.",
                "desc_ar": "مرق دجاج محلي الصنع مع الشعيرية والخضروات. وعاء شفاء.",
                "desc_fa": "آبگوشت مرغ خانگی با رشته و سبزیجات. کاسه‌ای شفابخش.",
                "desc_uk": "Домашній курячий бульйон з локшиною та овочами. Цілюща страва.",
                "image": "https://images.unsplash.com/photo-1604152135912-04a022e23696?w=600",
                "rating": 4.5,
                "reviews": 312,
                "featured": False,
                "spicy": 0,
                "tags": [],
                "allergens": ["GLU"],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Ekmek",
                        "name_en": "Bread",
                        "name_ar": "خبز",
                        "name_fa": "نان",
                        "name_uk": "Хліб",
                        "price": 10,
                    },
                    {
                        "name_tr": "Limon",
                        "name_en": "Lemon",
                        "name_ar": "ليمون",
                        "name_fa": "لیمو",
                        "name_uk": "Лимон",
                        "price": 5,
                    },
                ],
                "sauces": [],
            },
        ]

        # ── MEZELER ──
        meze_products = [
            {
                "name": "Humus",
                "name_tr": "Humus",
                "name_en": "Hummus",
                "name_ar": "حمص",
                "name_fa": "حمص",
                "name_uk": "Хумус",
                "price": 65,
                "prep": 5,
                "cal": 220,
                "desc_tr": "Nohut puresi, tahin, zeytinyagi, limon suyu. Lavasin yaninda muhtesem.",
                "desc_en": "Chickpea purée, tahini, olive oil, lemon juice. Perfect with lavash bread.",
                "desc_ar": "بيوريه الحمص، طحينة، زيت زيتون، عصير ليمون. رائع مع خبز اللافاش.",
                "desc_fa": "پوره نخود، تهینی، روغن زیتون، آب لیمو. عالی با نان لواش.",
                "desc_uk": "Пюре з нуту, тахіні, оливкова олія, лимонний сік. Чудово з лавашем.",
                "image": "https://images.unsplash.com/photo-1577805947697-89e18249d767?w=600",
                "rating": 4.4,
                "reviews": 234,
                "featured": False,
                "spicy": 0,
                "tags": ["vegan", "gluten-free", "glutensiz"],
                "allergens": ["SES"],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Lavash",
                        "name_en": "Lavash Bread",
                        "name_ar": "خبز لافاش",
                        "name_fa": "نان لواش",
                        "name_uk": "Лаваш",
                        "price": 15,
                    },
                ],
                "sauces": [],
            },
            {
                "name": "Sigara Boregi",
                "name_tr": "Sigara Boregi",
                "name_en": "Cheese Spring Roll",
                "name_ar": "بوريك السجائر",
                "name_fa": "بورک سیگارا",
                "name_uk": "Сигара бьорек",
                "price": 75,
                "prep": 12,
                "cal": 340,
                "desc_tr": "Incecik yufka icinde beyaz peynir ve maydanoz. Kitir kitir.",
                "desc_en": "Thin phyllo dough filled with white cheese and parsley. Crispy.",
                "desc_ar": "عجينة رقيقة محشوة بالجبنة البيضاء والبقدونس. مقرمشة.",
                "desc_fa": "خمیر یوفکای نازک پر شده با پنیر سفید و جعفری. ترد و خوشمزه.",
                "desc_uk": "Тонке тісто філо з білим сиром та петрушкою. Хрустке.",
                "image": "https://images.unsplash.com/photo-1519864600265-abb23847ef2c?w=600",
                "rating": 4.6,
                "reviews": 345,
                "featured": True,
                "spicy": 0,
                "tags": ["vegetarian", "vejetaryen"],
                "allergens": ["GLU", "DAI", "EGG"],
                "discount": 0,
                "variants": [
                    {
                        "name_tr": "4 Adet",
                        "name_en": "4 Pieces",
                        "name_ar": "4 قطع",
                        "name_fa": "4 عدد",
                        "name_uk": "4 штуки",
                        "price": 75,
                    },
                    {
                        "name_tr": "8 Adet",
                        "name_en": "8 Pieces",
                        "name_ar": "8 قطع",
                        "name_fa": "8 عدد",
                        "name_uk": "8 штук",
                        "price": 130,
                    },
                ],
                "extras": [],
                "sauces": [],
            },
            {
                "name": "Babagannush",
                "name_tr": "Babagannush",
                "name_en": "Baba Ganoush",
                "name_ar": "بابا غنوج",
                "name_fa": "بابا قنوش",
                "name_uk": "Баба гануш",
                "price": 60,
                "prep": 8,
                "cal": 180,
                "desc_tr": "Kozlenmis patlican, tahin, sarimsak ve zeytinyagi ile.",
                "desc_en": "Roasted eggplant with tahini, garlic, and olive oil.",
                "desc_ar": "باذنجان مشوي مع الطحينة والثوم وزيت الزيتون.",
                "desc_fa": "بادمجان کبابی با تهینی، سیر و روغن زیتون.",
                "desc_uk": "Печений баклажан з тахіні, часником та оливковою олією.",
                "image": "https://images.unsplash.com/photo-1541518763669-27fef04b14ea?w=600",
                "rating": 4.3,
                "reviews": 167,
                "featured": False,
                "spicy": 0,
                "tags": ["vegan", "gluten-free", "glutensiz"],
                "allergens": ["SES"],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Lavash",
                        "name_en": "Lavash Bread",
                        "name_ar": "خبز لافاش",
                        "name_fa": "نان لواش",
                        "name_uk": "Лаваш",
                        "price": 15,
                    },
                    {
                        "name_tr": "Nar",
                        "name_en": "Pomegranate",
                        "name_ar": "رمان",
                        "name_fa": "انار",
                        "name_uk": "Гранат",
                        "price": 10,
                    },
                ],
                "sauces": [],
            },
        ]

        # ── TATLILAR ──
        tatli_products = [
            {
                "name": "Kunefe",
                "name_tr": "Kunefe",
                "name_en": "Künefe",
                "name_ar": "كنافة",
                "name_fa": "کنافه",
                "name_uk": "Кюнефе",
                "price": 120,
                "prep": 15,
                "cal": 480,
                "desc_tr": "Antep fistigi ile suslanmis, sicak servis edilen geleneksel kunefe.",
                "desc_en": "Traditional künefe garnished with pistachios, served hot.",
                "desc_ar": "كنافة تقليدية مزينة بالفستق الحلبي، تُقدم ساخنة.",
                "desc_fa": "کنافه سنتی تزیین‌شده با پسته، گرم سرو می‌شود.",
                "desc_uk": "Традиційне кюнефе, прикрашене фісташками, подається гарячим.",
                "image": "https://images.unsplash.com/photo-1579888944880-d98341245702?w=600",
                "rating": 4.9,
                "reviews": 512,
                "featured": True,
                "spicy": 0,
                "tags": ["vegetarian", "vejetaryen"],
                "allergens": ["GLU", "DAI", "NUT"],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Ekstra Fistik",
                        "name_en": "Extra Pistachios",
                        "name_ar": "فستق إضافي",
                        "name_fa": "پسته اضافی",
                        "name_uk": "Додаткові фісташки",
                        "price": 20,
                    },
                    {
                        "name_tr": "Dondurma",
                        "name_en": "Ice Cream",
                        "name_ar": "آيس كريم",
                        "name_fa": "بستنی",
                        "name_uk": "Морозиво",
                        "price": 25,
                    },
                ],
                "sauces": [],
            },
            {
                "name": "Baklava (6 Adet)",
                "name_tr": "Baklava (6 Adet)",
                "name_en": "Baklava (6 Pieces)",
                "name_ar": "بقلاوة (6 قطع)",
                "name_fa": "باقلوا (6 عدد)",
                "name_uk": "Баклава (6 штук)",
                "price": 95,
                "prep": 5,
                "cal": 420,
                "desc_tr": "Antep fistikli ev yapimi baklava. Ince ince acilmis yufkalarla.",
                "desc_en": "Homemade baklava with pistachios. Thinly layered phyllo dough.",
                "desc_ar": "بقلاوة منزلية الصنع بالفستق الحلبي. عجينة رقيقة متعددة الطبقات.",
                "desc_fa": "باقلوای خانگی با پسته. خمیر یوفکای لایه لایه نازک.",
                "desc_uk": "Домашня баклава з фісташками. Тонко розкатане тісто філо.",
                "image": "https://images.unsplash.com/photo-1519676867240-f03562e64548?w=600",
                "rating": 4.8,
                "reviews": 389,
                "featured": False,
                "spicy": 0,
                "tags": ["vegetarian", "vejetaryen"],
                "allergens": ["GLU", "DAI", "NUT", "EGG"],
                "discount": 0,
                "variants": [
                    {
                        "name_tr": "6 Adet",
                        "name_en": "6 Pieces",
                        "name_ar": "6 قطع",
                        "name_fa": "6 عدد",
                        "name_uk": "6 штук",
                        "price": 95,
                    },
                    {
                        "name_tr": "12 Adet",
                        "name_en": "12 Pieces",
                        "name_ar": "12 قطعة",
                        "name_fa": "12 عدد",
                        "name_uk": "12 штук",
                        "price": 170,
                    },
                ],
                "extras": [
                    {
                        "name_tr": "Kaymak",
                        "name_en": "Clotted Cream",
                        "name_ar": "قيمق",
                        "name_fa": "سرشیر",
                        "name_uk": "Каймак",
                        "price": 25,
                    },
                    {
                        "name_tr": "Dondurma",
                        "name_en": "Ice Cream",
                        "name_ar": "آيس كريم",
                        "name_fa": "بستنی",
                        "name_uk": "Морозиво",
                        "price": 25,
                    },
                ],
                "sauces": [],
            },
            {
                "name": "Cikolata Sufle",
                "name_tr": "Cikolata Sufle",
                "name_en": "Chocolate Soufflé",
                "name_ar": "سوفليه الشوكولاتة",
                "name_fa": "سوفله شکلات",
                "name_uk": "Шоколадне суфле",
                "price": 85,
                "prep": 18,
                "cal": 450,
                "desc_tr": "Sicak cikolata suflesi, vanilyali dondurma ile. Icinden akan cikolata.",
                "desc_en": "Hot chocolate soufflé with vanilla ice cream. Flowing chocolate inside.",
                "desc_ar": "سوفليه الشوكولاتة الساخن مع آيس كريم الفانيليا. شوكولاتة سائلة من الداخل.",
                "desc_fa": "سوفله شکلات داغ با بستنی وانیلی. شکلات روان در داخل آن.",
                "desc_uk": "Гаряче шоколадне суфле з ванільним морозивом. З рідким шоколадом всередині.",
                "image": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=600",
                "rating": 4.7,
                "reviews": 278,
                "featured": False,
                "spicy": 0,
                "tags": ["vegetarian", "vejetaryen"],
                "allergens": ["GLU", "DAI", "EGG"],
                "discount": 0,
                "variants": [],
                "extras": [
                    {
                        "name_tr": "Ekstra Dondurma",
                        "name_en": "Extra Ice Cream",
                        "name_ar": "آيس كريم إضافي",
                        "name_fa": "بستنی اضافی",
                        "name_uk": "Додаткове морозиво",
                        "price": 25,
                    },
                ],
                "sauces": [],
                "is_new": True,
            },
        ]

        # ── ICECEKLER ──
        icecek_products = [
            {
                "name": "Turk Kahvesi",
                "name_tr": "Turk Kahvesi",
                "name_en": "Turkish Coffee",
                "name_ar": "قهوة تركية",
                "name_fa": "قهوه ترک",
                "name_uk": "Турецька кава",
                "price": 45,
                "prep": 5,
                "cal": 10,
                "desc_tr": "Geleneksel Turk kahvesi, lokum ile servis edilir.",
                "desc_en": "Traditional Turkish coffee, served with Turkish delight.",
                "desc_ar": "قهوة تركية تقليدية، تُقدم مع راحة الحلقوم.",
                "desc_fa": "قهوه ترک سنتی، با لوکوم سرو می‌شود.",
                "desc_uk": "Традиційна турецька кава, подається з лукумом.",
                "image": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefda?w=600",
                "rating": 4.6,
                "reviews": 678,
                "featured": False,
                "spicy": 0,
                "tags": ["vegan", "gluten-free", "glutensiz"],
                "allergens": [],
                "discount": 0,
                "variants": [
                    {
                        "name_tr": "Tek",
                        "name_en": "Single",
                        "name_ar": "واحد",
                        "name_fa": "تکی",
                        "name_uk": "Одинарна",
                        "price": 45,
                    },
                    {
                        "name_tr": "Cift",
                        "name_en": "Double",
                        "name_ar": "مزدوج",
                        "name_fa": "دوتایی",
                        "name_uk": "Подвійна",
                        "price": 80,
                    },
                ],
                "extras": [
                    {
                        "name_tr": "Lokum",
                        "name_en": "Turkish Delight",
                        "name_ar": "راحة الحلقوم",
                        "name_fa": "لوکوم",
                        "name_uk": "Лукум",
                        "price": 10,
                    },
                ],
                "sauces": [],
            },
            {
                "name": "Taze Portakal Suyu",
                "name_tr": "Taze Portakal Suyu",
                "name_en": "Fresh Orange Juice",
                "name_ar": "عصير برتقال طازج",
                "name_fa": "آب پرتقال تازه",
                "name_uk": "Свіжий апельсиновий сік",
                "price": 50,
                "prep": 3,
                "cal": 110,
                "desc_tr": "5 adet taze sikilmis portakal. Tamamen dogal, seker eklenmez.",
                "desc_en": "5 freshly squeezed oranges. Completely natural, no added sugar.",
                "desc_ar": "5 حبات برتقال معصورة طازجة. طبيعي بالكامل، بدون سكر مضاف.",
                "desc_fa": "5 عدد پرتقال تازه فشرده. کاملاً طبیعی، بدون شکر افزوده.",
                "desc_uk": "5 свіжовичавлених апельсинів. Повністю натуральний, без доданого цукру.",
                "image": "https://images.unsplash.com/photo-1534353473418-4cfa6c56fd38?w=600",
                "rating": 4.5,
                "reviews": 345,
                "featured": False,
                "spicy": 0,
                "tags": ["vegan", "gluten-free", "glutensiz"],
                "allergens": [],
                "discount": 0,
                "variants": [
                    {
                        "name_tr": "300ml",
                        "name_en": "300ml",
                        "name_ar": "300 مل",
                        "name_fa": "300 میلی‌لیتر",
                        "name_uk": "300 мл",
                        "price": 50,
                    },
                    {
                        "name_tr": "500ml",
                        "name_en": "500ml",
                        "name_ar": "500 مل",
                        "name_fa": "500 میلی‌لیتر",
                        "name_uk": "500 мл",
                        "price": 75,
                    },
                ],
                "extras": [],
                "sauces": [],
            },
            {
                "name": "Limonata",
                "name_tr": "Limonata",
                "name_en": "Lemonade",
                "name_ar": "عصير ليمون",
                "name_fa": "لیموناد",
                "name_uk": "Лимонад",
                "price": 40,
                "prep": 3,
                "cal": 90,
                "desc_tr": "Ev yapimi taze limonata, nane yapraklari ile. Ferahlatici.",
                "desc_en": "Homemade fresh lemonade with mint leaves. Refreshing.",
                "desc_ar": "عصير ليمون طازج محلي الصنع مع أوراق النعناع. منعش.",
                "desc_fa": "لیموناد تازه خانگی با برگ نعنا. خنک‌کننده.",
                "desc_uk": "Домашній свіжий лимонад з листям м'яти. Освіжаючий.",
                "image": "https://images.unsplash.com/photo-1621263764928-df1444c5e859?w=600",
                "rating": 4.4,
                "reviews": 456,
                "featured": False,
                "spicy": 0,
                "tags": ["vegan", "gluten-free", "glutensiz"],
                "allergens": [],
                "discount": 0,
                "variants": [
                    {
                        "name_tr": "Bardak",
                        "name_en": "Glass",
                        "name_ar": "كوب",
                        "name_fa": "لیوان",
                        "name_uk": "Склянка",
                        "price": 40,
                    },
                    {
                        "name_tr": "Surahi",
                        "name_en": "Pitcher",
                        "name_ar": "إبريق",
                        "name_fa": "پارچ",
                        "name_uk": "Глечик",
                        "price": 95,
                    },
                ],
                "extras": [],
                "sauces": [],
            },
            {
                "name": "Ayran",
                "name_tr": "Ayran",
                "name_en": "Ayran",
                "name_ar": "عيران",
                "name_fa": "دوغ",
                "name_uk": "Айран",
                "price": 25,
                "prep": 2,
                "cal": 60,
                "desc_tr": "Ev yapimi ayran, taze yogurttan.",
                "desc_en": "Homemade ayran, from fresh yogurt.",
                "desc_ar": "عيران محلي الصنع من زبادي طازج.",
                "desc_fa": "دوغ خانگی، از ماست تازه.",
                "desc_uk": "Домашній айран, зі свіжого йогурту.",
                "image": "https://images.unsplash.com/photo-1584433144859-1fc3ab64a957?w=600",
                "rating": 4.3,
                "reviews": 789,
                "featured": False,
                "spicy": 0,
                "tags": ["vegetarian", "vejetaryen", "gluten-free", "glutensiz"],
                "allergens": ["DAI"],
                "discount": 0,
                "variants": [
                    {
                        "name_tr": "Bardak",
                        "name_en": "Glass",
                        "name_ar": "كوب",
                        "name_fa": "لیوان",
                        "name_uk": "Склянка",
                        "price": 25,
                    },
                    {
                        "name_tr": "Buyuk",
                        "name_en": "Large",
                        "name_ar": "كبير",
                        "name_fa": "بزرگ",
                        "name_uk": "Великий",
                        "price": 40,
                    },
                ],
                "extras": [],
                "sauces": [],
            },
        ]

        # Map categories to products
        all_products = {
            "Kebaplar": kebap_products,
            "Burgerler": burger_products,
            "Pizzalar": pizza_products,
            "Salatalar": salata_products,
            "Deniz Urunleri": deniz_products,
            "Corbalar": corba_products,
            "Mezeler": meze_products,
            "Tatlilar": tatli_products,
            "Icecekler": icecek_products,
        }

        product_count = 0
        for cat_name, products in all_products.items():
            category = categories[cat_name]
            for idx, p_data in enumerate(products):
                product = self._create_single_product(
                    org=org,
                    category=category,
                    data=p_data,
                    allergens=allergens,
                    sort_order=idx + 1,
                    now=now,
                )
                if product:
                    product_count += 1

        self.stdout.write(f"  Created/verified {product_count} products")

    def _create_single_product(self, org, category, data, allergens, sort_order, now):
        """Create a single product with all related data."""
        slug = slugify(data["name"])

        # Build short descriptions for all languages
        desc_tr = data["desc_tr"]
        desc_en = data["desc_en"]
        desc_ar = data["desc_ar"]
        desc_fa = data["desc_fa"]
        desc_uk = data["desc_uk"]

        product, created = Product.objects.get_or_create(
            organization=org,
            category=category,
            slug=slug,
            defaults={
                "name_tr": data["name_tr"],
                "name_en": data["name_en"],
                "name_ar": data["name_ar"],
                "name_fa": data["name_fa"],
                "name_uk": data["name_uk"],
                "description_tr": desc_tr,
                "description_en": desc_en,
                "description_ar": desc_ar,
                "description_fa": desc_fa,
                "description_uk": desc_uk,
                "short_description_tr": desc_tr[:100]
                if len(desc_tr) > 100
                else desc_tr,
                "short_description_en": desc_en[:100]
                if len(desc_en) > 100
                else desc_en,
                "short_description_ar": desc_ar[:100]
                if len(desc_ar) > 100
                else desc_ar,
                "short_description_fa": desc_fa[:100]
                if len(desc_fa) > 100
                else desc_fa,
                "short_description_uk": desc_uk[:100]
                if len(desc_uk) > 100
                else desc_uk,
                "base_price": Decimal(str(data["price"])),
                "currency": "TRY",
                "image": data.get("image", ""),
                "is_active": True,
                "is_available": True,
                "is_featured": data.get("featured", False),
                "preparation_time": data.get("prep", 15),
                "calories": data.get("cal", 0),
                "spicy_level": data.get("spicy", 0),
                "discount_percentage": data.get("discount", 0),
                "rating": Decimal(str(data.get("rating", 0))),
                "review_count": data.get("reviews", 0),
                "tags": data.get("tags", []),
                "sort_order": sort_order,
            },
        )

        if not created:
            return product

        # Force isNew for select products
        if data.get("is_new"):
            product.created_at = now
            product.save(update_fields=["created_at"])

        # Create variants
        for v_idx, v_data in enumerate(data.get("variants", [])):
            ProductVariant.objects.get_or_create(
                product=product,
                name=v_data["name_tr"],
                defaults={
                    "name_tr": v_data["name_tr"],
                    "name_en": v_data["name_en"],
                    "name_ar": v_data["name_ar"],
                    "name_fa": v_data["name_fa"],
                    "name_uk": v_data["name_uk"],
                    "price": Decimal(str(v_data["price"])),
                    "is_default": v_idx == 0,
                    "is_available": True,
                    "sort_order": v_idx,
                },
            )

        # Create extras (modifiers with price > 0)
        for e_idx, e_data in enumerate(data.get("extras", [])):
            ProductModifier.objects.get_or_create(
                product=product,
                name=e_data["name_tr"],
                defaults={
                    "name_tr": e_data["name_tr"],
                    "name_en": e_data["name_en"],
                    "name_ar": e_data["name_ar"],
                    "name_fa": e_data["name_fa"],
                    "name_uk": e_data["name_uk"],
                    "price": Decimal(str(e_data["price"])),
                    "is_default": False,
                    "is_required": False,
                    "max_quantity": 2,
                    "sort_order": e_idx,
                },
            )

        # Create sauces (modifiers with price = 0)
        for s_idx, s_data in enumerate(data.get("sauces", [])):
            ProductModifier.objects.get_or_create(
                product=product,
                name=s_data["name_tr"],
                defaults={
                    "name_tr": s_data["name_tr"],
                    "name_en": s_data["name_en"],
                    "name_ar": s_data["name_ar"],
                    "name_fa": s_data["name_fa"],
                    "name_uk": s_data["name_uk"],
                    "price": Decimal("0"),
                    "is_default": False,
                    "is_required": False,
                    "max_quantity": 1,
                    "sort_order": 100 + s_idx,  # After extras
                },
            )

        # Create allergen associations
        for a_code in data.get("allergens", []):
            if a_code in allergens:
                ProductAllergen.objects.get_or_create(
                    product=product,
                    allergen=allergens[a_code],
                    defaults={
                        "severity": AllergenSeverity.CONTAINS,
                    },
                )

        # Create nutrition info for some products
        if data.get("cal") and data["cal"] > 0:
            NutritionInfo.objects.get_or_create(
                product=product,
                defaults={
                    "serving_size": "1 porsiyon",
                    "calories": data["cal"],
                },
            )

        return product
