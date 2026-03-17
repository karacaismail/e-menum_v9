"""
Django management command for seeding standard Allergen definitions.

This command creates the standard allergen definitions used across E-Menum.
Allergens are platform-level entities (not tenant-specific) and are used
to label products with allergen information for customer safety.

The allergens follow EU allergen labeling regulations (EU FIC 1169/2011)
which require declaration of the 14 major allergens.

Standard Allergens (EU 14):
| Code | Name         | Description                                          |
|------|--------------|------------------------------------------------------|
| GLU  | Gluten       | Cereals containing gluten (wheat, barley, rye, oats) |
| CRU  | Crustaceans  | Shrimp, crab, lobster, crayfish                      |
| EGG  | Eggs         | All egg products                                     |
| FSH  | Fish         | All fish species                                     |
| PNT  | Peanuts      | Peanuts and peanut products                          |
| SOY  | Soy          | Soybeans and soy products                            |
| MLK  | Milk         | All dairy products containing lactose                |
| NUT  | Tree Nuts    | Almonds, hazelnuts, walnuts, cashews, pecans, etc.   |
| CEL  | Celery       | Celery and celeriac                                  |
| MUS  | Mustard      | All mustard products                                 |
| SES  | Sesame       | Sesame seeds and sesame oil                          |
| SUL  | Sulphites    | Sulphur dioxide and sulphites (>10mg/kg or >10mg/L)  |
| LUP  | Lupin        | Lupin seeds and flour                                |
| MOL  | Molluscs     | Oysters, mussels, clams, squid, octopus              |

Usage:
    python manage.py seed_allergens
    python manage.py seed_allergens --force  # Force update existing records
    python manage.py seed_allergens --dry-run  # Show what would be created
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.menu.models import Allergen


class Command(BaseCommand):
    """Management command to seed standard allergen definitions."""

    help = "Seed standard allergen definitions for E-Menum (EU 14 allergens)"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update existing records",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without making changes",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        force = options["force"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))

        try:
            with transaction.atomic():
                # Create allergens
                allergens = self._create_allergens(force, dry_run)
                self.stdout.write(f"Created/updated {len(allergens)} allergens")

                if dry_run:
                    # Rollback in dry run
                    raise DryRunException()

        except DryRunException:
            self.stdout.write(
                self.style.WARNING("Dry run completed - no changes were made")
            )
        except Exception as e:
            raise CommandError(f"Failed to seed allergens: {str(e)}")

        if not dry_run:
            self.stdout.write(self.style.SUCCESS("Successfully seeded allergens!"))

    def _create_allergens(self, force: bool, dry_run: bool) -> dict:
        """Create or update allergen definitions."""
        # Standard EU 14 allergens as per EU FIC 1169/2011
        allergens_data = [
            {
                "code": "GLU",
                "name_tr": "Gluten",
                "name_en": "Gluten",
                "slug": "gluten",
                "description_tr": "Gluten içeren tahıllar: buğday (spelt ve khorasan buğdayı dahil), çavdar, arpa, yulaf veya bunların melezleri ve ürünleri.",
                "description_en": "Cereals containing gluten, namely: wheat (such as spelt and khorasan wheat), rye, barley, oats or their hybridised strains, and products thereof.",
                "name_ar": "الغلوتين",
                "name_fa": "گلوتن",
                "name_uk": "Глютен",
                "description_ar": "الحبوب المحتوية على الغلوتين: القمح والجاودار والشعير والشوفان أو سلالاتها المهجنة ومنتجاتها.",
                "description_fa": "غلات حاوی گلوتن: گندم، چاودار، جو، جو دوسر یا گونه‌های هیبریدی و محصولات آنها.",
                "description_uk": "Злаки, що містять глютен: пшениця, жито, ячмінь, овес або їх гібриди та продукти з них.",
                "sort_order": 10,
                "is_active": True,
            },
            {
                "code": "CRU",
                "name_tr": "Kabuklular",
                "name_en": "Crustaceans",
                "slug": "crustaceans",
                "description_tr": "Kabuklular ve ürünleri: karides, yengeç, ıstakoz, kerevit ve karides türleri.",
                "description_en": "Crustaceans and products thereof, including shrimp, crab, lobster, crayfish, and prawns.",
                "name_ar": "القشريات",
                "name_fa": "سخت‌پوستان",
                "name_uk": "Ракоподібні",
                "description_ar": "القشريات ومنتجاتها: الروبيان والسلطعون والكركند وجراد البحر.",
                "description_fa": "سخت‌پوستان و محصولات آنها: میگو، خرچنگ، لابستر و شاه‌میگو.",
                "description_uk": "Ракоподібні та продукти з них: креветки, краби, омари, раки.",
                "sort_order": 20,
                "is_active": True,
            },
            {
                "code": "EGG",
                "name_tr": "Yumurta",
                "name_en": "Eggs",
                "slug": "eggs",
                "description_tr": "Yumurta ve ürünleri: bütün yumurta, yumurta akı, yumurta sarısı, yumurta tozu ve yumurta içeren tüm hazır ürünler.",
                "description_en": "Eggs and products thereof, including whole eggs, egg whites, egg yolks, egg powder, and any preparations containing eggs.",
                "name_ar": "البيض",
                "name_fa": "تخم‌مرغ",
                "name_uk": "Яйця",
                "description_ar": "البيض ومنتجاته: البيض الكامل وبياض البيض وصفار البيض ومسحوق البيض وجميع المنتجات المحتوية على البيض.",
                "description_fa": "تخم‌مرغ و محصولات آن: تخم‌مرغ کامل، سفیده، زرده، پودر تخم‌مرغ و تمام فرآورده‌های حاوی تخم‌مرغ.",
                "description_uk": "Яйця та продукти з них: цілі яйця, білки, жовтки, яєчний порошок та будь-які вироби з яєць.",
                "sort_order": 30,
                "is_active": True,
            },
            {
                "code": "FSH",
                "name_tr": "Balık",
                "name_en": "Fish",
                "slug": "fish",
                "description_tr": "Balık ve ürünleri: tüm balık türleri, balık sosu, balık yağı ve balık türevi içerenler.",
                "description_en": "Fish and products thereof, including all fish species, fish sauce, fish oil, and products containing fish-derived ingredients.",
                "name_ar": "الأسماك",
                "name_fa": "ماهی",
                "name_uk": "Риба",
                "description_ar": "الأسماك ومنتجاتها: جميع أنواع الأسماك وصلصة السمك وزيت السمك والمنتجات المحتوية على مشتقات الأسماك.",
                "description_fa": "ماهی و محصولات آن: تمام گونه‌های ماهی، سس ماهی، روغن ماهی و محصولات حاوی مشتقات ماهی.",
                "description_uk": "Риба та продукти з неї: усі види риби, рибний соус, рибний жир та продукти з рибних інгредієнтів.",
                "sort_order": 40,
                "is_active": True,
            },
            {
                "code": "PNT",
                "name_tr": "Yer Fıstığı",
                "name_en": "Peanuts",
                "slug": "peanuts",
                "description_tr": "Yer fıstığı ve ürünleri: fıstık ezmesi, fıstık yağı ve yer fıstığı türevi içerenler.",
                "description_en": "Peanuts and products thereof, including peanut butter, peanut oil, and products containing peanut-derived ingredients.",
                "name_ar": "الفول السوداني",
                "name_fa": "بادام‌زمینی",
                "name_uk": "Арахіс",
                "description_ar": "الفول السوداني ومنتجاته: زبدة الفول السوداني وزيت الفول السوداني والمنتجات المحتوية على مشتقاته.",
                "description_fa": "بادام‌زمینی و محصولات آن: کره بادام‌زمینی، روغن بادام‌زمینی و محصولات حاوی مشتقات آن.",
                "description_uk": "Арахіс та продукти з нього: арахісова паста, арахісова олія та продукти з арахісових інгредієнтів.",
                "sort_order": 50,
                "is_active": True,
            },
            {
                "code": "SOY",
                "name_tr": "Soya",
                "name_en": "Soy",
                "slug": "soy",
                "description_tr": "Soya fasulyesi ve ürünleri: soya sosu, tofu, soya sütü, soya lesitini ve soya türevi içerenler.",
                "description_en": "Soybeans and products thereof, including soy sauce, tofu, soy milk, soy lecithin, and products containing soy-derived ingredients.",
                "name_ar": "الصويا",
                "name_fa": "سویا",
                "name_uk": "Соя",
                "description_ar": "فول الصويا ومنتجاته: صلصة الصويا والتوفو وحليب الصويا وليسيثين الصويا.",
                "description_fa": "سویا و محصولات آن: سس سویا، توفو، شیر سویا، لسیتین سویا و محصولات حاوی مشتقات سویا.",
                "description_uk": "Соєві боби та продукти з них: соєвий соус, тофу, соєве молоко, соєвий лецитин.",
                "sort_order": 60,
                "is_active": True,
            },
            {
                "code": "MLK",
                "name_tr": "Süt",
                "name_en": "Milk",
                "slug": "milk",
                "description_tr": "Süt ve ürünleri: laktoz, tereyağı, peynir, krema, yoğurt ve süt proteini içeren tüm ürünler.",
                "description_en": "Milk and products thereof, including lactose, butter, cheese, cream, yogurt, and any preparations containing milk proteins.",
                "name_ar": "الحليب",
                "name_fa": "شیر",
                "name_uk": "Молоко",
                "description_ar": "الحليب ومنتجاته: اللاكتوز والزبدة والجبن والقشدة والزبادي وجميع المنتجات المحتوية على بروتينات الحليب.",
                "description_fa": "شیر و محصولات آن: لاکتوز، کره، پنیر، خامه، ماست و تمام فرآورده‌های حاوی پروتئین شیر.",
                "description_uk": "Молоко та продукти з нього: лактоза, масло, сир, вершки, йогурт та будь-які вироби з молочних білків.",
                "sort_order": 70,
                "is_active": True,
            },
            {
                "code": "NUT",
                "name_tr": "Sert Kabuklu Meyveler",
                "name_en": "Tree Nuts",
                "slug": "tree-nuts",
                "description_tr": "Sert kabuklu meyveler: badem, fındık, ceviz, kaju, pekan, brezilya fıstığı, antep fıstığı, makadamya ve ürünleri.",
                "description_en": "Tree nuts: almonds, hazelnuts, walnuts, cashews, pecans, Brazil nuts, pistachios, macadamia nuts, and products thereof.",
                "name_ar": "المكسرات",
                "name_fa": "آجیل درختی",
                "name_uk": "Горіхи",
                "description_ar": "المكسرات: اللوز والبندق والجوز والكاجو والفستق والمكاديميا وجوز البقان وجوز البرازيل ومنتجاتها.",
                "description_fa": "آجیل درختی: بادام، فندق، گردو، بادام هندی، پسته، ماکادمیا، پکان، بادام برزیلی و محصولات آنها.",
                "description_uk": "Горіхи: мигдаль, фундук, волоські горіхи, кешʼю, фісташки, макадамія, пекан, бразильські горіхи та продукти з них.",
                "sort_order": 80,
                "is_active": True,
            },
            {
                "code": "CEL",
                "name_tr": "Kereviz",
                "name_en": "Celery",
                "slug": "celery",
                "description_tr": "Kereviz ve ürünleri: kereviz sapı, yaprakları, tohumları, kök kereviz ve kereviz tuzu.",
                "description_en": "Celery and products thereof, including celery stalks, leaves, seeds, celeriac (celery root), and celery salt.",
                "name_ar": "الكرفس",
                "name_fa": "کرفس",
                "name_uk": "Селера",
                "description_ar": "الكرفس ومنتجاته: سيقان الكرفس وأوراقه وبذوره وجذر الكرفس وملح الكرفس.",
                "description_fa": "کرفس و محصولات آن: ساقه، برگ، دانه، ریشه کرفس و نمک کرفس.",
                "description_uk": "Селера та продукти з неї: стебла, листя, насіння, коренева селера та сіль із селери.",
                "sort_order": 90,
                "is_active": True,
            },
            {
                "code": "MUS",
                "name_tr": "Hardal",
                "name_en": "Mustard",
                "slug": "mustard",
                "description_tr": "Hardal ve ürünleri: hardal tohumu, hardal tozu, hazır hardal ve hardal yağı.",
                "description_en": "Mustard and products thereof, including mustard seeds, mustard powder, prepared mustard, and mustard oil.",
                "name_ar": "الخردل",
                "name_fa": "خردل",
                "name_uk": "Гірчиця",
                "description_ar": "الخردل ومنتجاته: بذور الخردل ومسحوق الخردل والخردل الجاهز وزيت الخردل.",
                "description_fa": "خردل و محصولات آن: دانه خردل، پودر خردل، خردل آماده و روغن خردل.",
                "description_uk": "Гірчиця та продукти з неї: насіння гірчиці, гірчичний порошок, готова гірчиця та гірчична олія.",
                "sort_order": 100,
                "is_active": True,
            },
            {
                "code": "SES",
                "name_tr": "Susam",
                "name_en": "Sesame",
                "slug": "sesame",
                "description_tr": "Susam tohumu ve ürünleri: susam yağı, tahin, helva ve susam türevi içerenler.",
                "description_en": "Sesame seeds and products thereof, including sesame oil, tahini, halva, and products containing sesame-derived ingredients.",
                "name_ar": "السمسم",
                "name_fa": "کنجد",
                "name_uk": "Кунжут",
                "description_ar": "بذور السمسم ومنتجاتها: زيت السمسم والطحينة والحلاوة والمنتجات المحتوية على مشتقات السمسم.",
                "description_fa": "دانه کنجد و محصولات آن: روغن کنجد، ارده، حلوا و محصولات حاوی مشتقات کنجد.",
                "description_uk": "Насіння кунжуту та продукти з нього: кунжутна олія, тахіні, халва та продукти з кунжутних інгредієнтів.",
                "sort_order": 110,
                "is_active": True,
            },
            {
                "code": "SUL",
                "name_tr": "Sülfitler",
                "name_en": "Sulphites",
                "slug": "sulphites",
                "description_tr": "Kükürt dioksit ve sülfitler (10 mg/kg veya 10 mg/litre üzeri SO2). Şarap, kurutulmuş meyveler ve işlenmiş gıdalarda yaygın.",
                "description_en": "Sulphur dioxide and sulphites at concentrations of more than 10 mg/kg or 10 mg/litre expressed as SO2. Common in wine, dried fruits, and processed foods.",
                "name_ar": "الكبريتات",
                "name_fa": "سولفیت‌ها",
                "name_uk": "Сульфіти",
                "description_ar": "ثاني أكسيد الكبريت والكبريتات بتركيز أكثر من 10 مغ/كغ أو 10 مغ/لتر. شائعة في النبيذ والفواكه المجففة والأطعمة المصنعة.",
                "description_fa": "دی‌اکسید گوگرد و سولفیت‌ها با غلظت بیش از ۱۰ میلی‌گرم بر کیلوگرم یا ۱۰ میلی‌گرم بر لیتر. رایج در شراب، میوه‌های خشک و غذاهای فرآوری شده.",
                "description_uk": "Діоксид сірки та сульфіти в концентрації понад 10 мг/кг або 10 мг/л. Поширені у вині, сухофруктах та оброблених продуктах.",
                "sort_order": 120,
                "is_active": True,
            },
            {
                "code": "LUP",
                "name_tr": "Acı Bakla",
                "name_en": "Lupin",
                "slug": "lupin",
                "description_tr": "Acı bakla ve ürünleri: acı bakla tohumu, acı bakla unu ve türevi içerenler. Glutensiz alternatiflerde sıkça bulunur.",
                "description_en": "Lupin and products thereof, including lupin seeds, lupin flour, and products containing lupin-derived ingredients. Often found in gluten-free alternatives.",
                "name_ar": "الترمس",
                "name_fa": "لوبیای لوپین",
                "name_uk": "Люпин",
                "description_ar": "الترمس ومنتجاته: بذور الترمس ودقيق الترمس. يوجد غالباً في البدائل الخالية من الغلوتين.",
                "description_fa": "لوپین و محصولات آن: دانه و آرد لوپین. اغلب در جایگزین‌های بدون گلوتن یافت می‌شود.",
                "description_uk": "Люпин та продукти з нього: насіння та борошно люпину. Часто зустрічається у безглютенових альтернативах.",
                "sort_order": 130,
                "is_active": True,
            },
            {
                "code": "MOL",
                "name_tr": "Yumuşakçalar",
                "name_en": "Molluscs",
                "slug": "molluscs",
                "description_tr": "Yumuşakçalar ve ürünleri: istiridye, midye, tarak, kalamar, ahtapot ve salyangoz.",
                "description_en": "Molluscs and products thereof, including oysters, mussels, clams, scallops, squid, octopus, and snails.",
                "name_ar": "الرخويات",
                "name_fa": "نرم‌تنان",
                "name_uk": "Молюски",
                "description_ar": "الرخويات ومنتجاتها: المحار وبلح البحر والأسقلوب والحبار والأخطبوط والحلزون.",
                "description_fa": "نرم‌تنان و محصولات آنها: صدف، میگوی دریایی، اسکالوپ، ماهی مرکب، اختاپوس و حلزون.",
                "description_uk": "Молюски та продукти з них: устриці, мідії, гребінці, кальмари, восьминоги та равлики.",
                "sort_order": 140,
                "is_active": True,
            },
        ]

        created_allergens = {}
        for data in allergens_data:
            code = data["code"]

            if force:
                allergen, created = Allergen.objects.update_or_create(
                    code=code,
                    defaults=data,
                )
                action = "+" if created else "~"
            else:
                allergen, created = Allergen.objects.get_or_create(
                    code=code,
                    defaults=data,
                )
                action = "+" if created else "-"

            self.stdout.write(f"  {action} Allergen: {data['name_tr']} ({code})")
            created_allergens[code] = allergen

        return created_allergens


class DryRunException(Exception):
    """Exception raised to rollback dry run transactions."""

    pass
