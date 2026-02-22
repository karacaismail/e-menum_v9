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
    help = 'Seed database with realistic Turkish restaurant data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing seed data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self._clear_data()

        self.stdout.write('Seeding menu data...\n')

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

        self.stdout.write(self.style.SUCCESS(
            '\nSeed data created successfully!\n'
            f'  Organization: {org.name}\n'
            f'  Menu: {menu.name} (slug: {menu.slug})\n'
            f'  Categories: {len(categories)}\n'
            f'  Products: {Product.objects.filter(organization=org).count()}\n'
            f'  Allergens: {len(allergens)}\n'
            f'\n  Visit: /m/{menu.slug}/'
        ))

    def _clear_data(self):
        self.stdout.write('Clearing existing seed data...')
        NutritionInfo.all_objects.all().delete()
        ProductAllergen.all_objects.all().delete()
        ProductModifier.all_objects.all().delete()
        ProductVariant.all_objects.all().delete()
        Product.all_objects.all().delete()
        Category.all_objects.all().delete()
        Menu.all_objects.all().delete()
        Theme.all_objects.all().delete()
        Allergen.all_objects.all().delete()
        Organization.objects.filter(slug='lezzet-sarayi').delete()
        User.objects.filter(email='admin@lezzetsarayi.com').delete()
        self.stdout.write(self.style.WARNING('  Cleared!'))

    def _create_user(self):
        user, created = User.objects.get_or_create(
            email='admin@lezzetsarayi.com',
            defaults={
                'first_name': 'Ahmet',
                'last_name': 'Yilmaz',
                'is_staff': True,
                'status': 'ACTIVE',
            }
        )
        if created:
            user.set_password('LezzetSarayi2024!')
            user.save()
            self.stdout.write(f'  Created user: {user.email}')
        else:
            self.stdout.write(f'  User exists: {user.email}')
        return user

    def _create_organization(self, user):
        org, created = Organization.objects.get_or_create(
            slug='lezzet-sarayi',
            defaults={
                'name': 'Lezzet Sarayi',
                'status': 'active',
                'settings': {
                    'currency': 'TRY',
                    'locale': 'tr-TR',
                    'timezone': 'Europe/Istanbul',
                },
            }
        )
        if created:
            self.stdout.write(f'  Created organization: {org.name}')
        else:
            self.stdout.write(f'  Organization exists: {org.name}')

        # Link user to organization
        if hasattr(user, 'organization'):
            if user.organization != org:
                user.organization = org
                user.save(update_fields=['organization'])

        return org

    def _create_theme(self, org):
        theme, created = Theme.objects.get_or_create(
            organization=org,
            slug='sunset',
            defaults={
                'name': 'Sunset',
                'description': 'Sicak ve davetkar renkler',
                'primary_color': '#E85D04',
                'secondary_color': '#1B4332',
                'background_color': '#FAFAF9',
                'text_color': '#1C1917',
                'accent_color': '#FFBA08',
                'font_family': 'Plus Jakarta Sans',
                'heading_font_family': 'Playfair Display',
                'is_default': True,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(f'  Created theme: {theme.name}')
        return theme

    def _create_menu(self, org, theme):
        menu, created = Menu.objects.get_or_create(
            organization=org,
            slug='ana-menu',
            defaults={
                'name': 'Ana Menu',
                'description': 'Lezzet Sarayi - Gastronomi Deneyimi',
                'is_published': True,
                'published_at': timezone.now(),
                'is_default': True,
                'theme': theme,
                'settings': {
                    'currency': 'TRY',
                },
            }
        )
        if created:
            self.stdout.write(f'  Created menu: {menu.name}')
        return menu

    def _create_allergens(self):
        allergen_data = [
            {'name': 'Gluten', 'code': 'GLU', 'sort_order': 1},
            {'name': 'Sut Urunleri', 'code': 'DAI', 'sort_order': 2},
            {'name': 'Yumurta', 'code': 'EGG', 'sort_order': 3},
            {'name': 'Fistik', 'code': 'PEA', 'sort_order': 4},
            {'name': 'Soya', 'code': 'SOY', 'sort_order': 5},
            {'name': 'Findik', 'code': 'NUT', 'sort_order': 6},
            {'name': 'Susam', 'code': 'SES', 'sort_order': 7},
            {'name': 'Deniz Urunu', 'code': 'SHE', 'sort_order': 8},
        ]

        allergens = {}
        for data in allergen_data:
            allergen, created = Allergen.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'slug': slugify(data['name']),
                    'sort_order': data['sort_order'],
                    'is_active': True,
                }
            )
            allergens[data['code']] = allergen

        self.stdout.write(f'  Created/verified {len(allergens)} allergens')
        return allergens

    def _create_categories(self, org, menu):
        category_data = [
            {'name': 'Kebaplar', 'icon': 'ph-fill ph-knife', 'description': 'Odun atesinde pisirilmis geleneksel kebaplar', 'sort_order': 1},
            {'name': 'Burgerler', 'icon': 'ph-fill ph-hamburger', 'description': 'El yapimi gurme burgerler', 'sort_order': 2},
            {'name': 'Pizzalar', 'icon': 'ph-fill ph-pizza', 'description': 'Tas firin pizzalar, ince ve kalin hamur', 'sort_order': 3},
            {'name': 'Salatalar', 'icon': 'ph-fill ph-leaf', 'description': 'Taze ve saglikli salatalar', 'sort_order': 4},
            {'name': 'Deniz Urunleri', 'icon': 'ph-fill ph-fish', 'description': 'Gunluk taze deniz urunleri', 'sort_order': 5},
            {'name': 'Corbalar', 'icon': 'ph-fill ph-bowl-food', 'description': 'Ev yapimi sicak corbalar', 'sort_order': 6},
            {'name': 'Mezeler', 'icon': 'ph-fill ph-carrot', 'description': 'Geleneksel Turk mezeleri', 'sort_order': 7},
            {'name': 'Tatlilar', 'icon': 'ph-fill ph-cake', 'description': 'Ev yapimi tatlilar ve pastalar', 'sort_order': 8},
            {'name': 'Icecekler', 'icon': 'ph-fill ph-wine', 'description': 'Sicak ve soguk icecekler', 'sort_order': 9},
        ]

        categories = {}
        for data in category_data:
            cat, created = Category.objects.get_or_create(
                organization=org,
                menu=menu,
                slug=slugify(data['name']),
                defaults={
                    'name': data['name'],
                    'icon': data['icon'],
                    'description': data['description'],
                    'sort_order': data['sort_order'],
                    'is_active': True,
                }
            )
            categories[data['name']] = cat

        self.stdout.write(f'  Created/verified {len(categories)} categories')
        return categories

    def _create_products(self, org, categories, allergens):
        """Create all products with variants, modifiers, allergens."""
        now = timezone.now()

        # ── KEBAPLAR ──
        kebap_products = [
            {
                'name': 'Adana Kebap', 'price': 185, 'prep': 25, 'cal': 520,
                'desc': 'Aci biber ve kuyruk yagi ile yogrulan el kiymasi, odun atesinde sislenip pisirilir. Lavasin uzerinde servis edilir.',
                'image': 'https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=600',
                'rating': 4.8, 'reviews': 324, 'featured': True, 'spicy': 3,
                'tags': ['spicy'], 'allergens': ['GLU'],
                'discount': 0,
                'variants': [('Tek', 185), ('Bucuk', 140), ('Porsiyon', 230)],
                'extras': [('Ekstra Lavash', 15), ('Yogurt', 12), ('Kozde Biber', 10)],
                'sauces': ['Aci Sos', 'Nar Eksisi', 'Sumak'],
            },
            {
                'name': 'Urfa Kebap', 'price': 175, 'prep': 25, 'cal': 490,
                'desc': 'Acisiz el kiymasi, odun atesinde yavas yavas pisirilir. Yumusacik dokusu ile meshurdur.',
                'image': 'https://images.unsplash.com/photo-1603360946369-dc9bb6258143?w=600',
                'rating': 4.6, 'reviews': 218, 'featured': False, 'spicy': 0,
                'tags': [], 'allergens': ['GLU'],
                'discount': 10,
                'variants': [('Tek', 175), ('Porsiyon', 220)],
                'extras': [('Yogurt', 12)],
                'sauces': ['Nar Eksisi'],
            },
            {
                'name': 'Beyti Kebap', 'price': 220, 'prep': 30, 'cal': 680,
                'desc': 'Adana kebap, lavash ve yogurt ile sarildiktan sonra tereyagili domates sosu ile servis edilir.',
                'image': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=600',
                'rating': 4.9, 'reviews': 412, 'featured': True, 'spicy': 2,
                'tags': ['spicy'], 'allergens': ['GLU', 'DAI'],
                'discount': 0,
                'variants': [],
                'extras': [('Ekstra Yogurt', 15), ('Tereyagi Sosu', 20)],
                'sauces': ['Aci Sos', 'Nar Eksisi'],
            },
            {
                'name': 'Kuzu Sis', 'price': 245, 'prep': 30, 'cal': 560,
                'desc': 'Marine edilmis kuzu but parcalari, sebzeler ile sislenip odun atesinde pisirilir.',
                'image': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600',
                'rating': 4.7, 'reviews': 189, 'featured': False, 'spicy': 0,
                'tags': [], 'allergens': [],
                'discount': 0,
                'variants': [('Tek', 245), ('Cift', 380)],
                'extras': [('Pilav', 25), ('Kozde Sebze', 20)],
                'sauces': [],
            },
        ]

        # ── BURGERLER ──
        burger_products = [
            {
                'name': 'Classic Smash Burger', 'price': 165, 'prep': 15, 'cal': 720,
                'desc': 'Dana etinden el yapimi 2x120gr smash kofteler, cheddar peyniri, ozel sos, tursu.',
                'image': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600',
                'rating': 4.7, 'reviews': 567, 'featured': True, 'spicy': 0,
                'tags': [], 'allergens': ['GLU', 'DAI', 'EGG', 'SES'],
                'discount': 15,
                'variants': [('Tek Kofte', 125), ('Cift Kofte', 165), ('Uclu', 205)],
                'extras': [('Ekstra Cheddar', 20), ('Bacon', 25), ('Jalapeno', 15), ('Avokado', 30)],
                'sauces': ['Ozel Burger Sosu', 'BBQ', 'Ranch', 'Sriracha Mayo'],
            },
            {
                'name': 'Truffle Mushroom Burger', 'price': 195, 'prep': 18, 'cal': 780,
                'desc': 'Truffle soslu mantar, karamelize sogan, gruyere peyniri ile gurme burger.',
                'image': 'https://images.unsplash.com/photo-1550547660-d9450f859349?w=600',
                'rating': 4.8, 'reviews': 298, 'featured': True, 'spicy': 0,
                'tags': [], 'allergens': ['GLU', 'DAI', 'EGG'],
                'discount': 0,
                'variants': [],
                'extras': [('Ekstra Mantar', 20), ('Truffle Yag', 25)],
                'sauces': ['Truffle Mayo', 'BBQ'],
            },
            {
                'name': 'Vegan Beyond Burger', 'price': 175, 'prep': 15, 'cal': 480,
                'desc': 'Beyond Meat kofte, vegan cheddar, avokado, taze sebzeler, vegan mayo.',
                'image': 'https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=600',
                'rating': 4.3, 'reviews': 142, 'featured': False, 'spicy': 0,
                'tags': ['vegan'], 'allergens': ['GLU', 'SOY'],
                'discount': 0,
                'variants': [],
                'extras': [('Ekstra Avokado', 30), ('Jalapeno', 15)],
                'sauces': ['Vegan Mayo', 'BBQ', 'Hardal'],
            },
            {
                'name': 'Spicy Chicken Burger', 'price': 155, 'prep': 15, 'cal': 650,
                'desc': 'Crispy tavuk but, aci sos, coleslaw, tursu. Nashville hot tarzi.',
                'image': 'https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=600',
                'rating': 4.5, 'reviews': 234, 'featured': False, 'spicy': 3,
                'tags': ['spicy'], 'allergens': ['GLU', 'DAI', 'EGG'],
                'discount': 0,
                'variants': [('Normal', 155), ('Double', 210)],
                'extras': [('Ekstra Coleslaw', 15), ('Sogan Halkasi', 20)],
                'sauces': ['Nashville Hot', 'Ranch', 'BBQ'],
            },
        ]

        # ── PIZZALAR ──
        pizza_products = [
            {
                'name': 'Margherita', 'price': 140, 'prep': 20, 'cal': 580,
                'desc': 'San Marzano domates sosu, taze mozzarella, fesleden. Klasik Napoli tarifi.',
                'image': 'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=600',
                'rating': 4.6, 'reviews': 432, 'featured': False, 'spicy': 0,
                'tags': ['vegetarian', 'vejetaryen'], 'allergens': ['GLU', 'DAI'],
                'discount': 0,
                'variants': [('Kucuk', 140), ('Orta', 175), ('Buyuk', 210)],
                'extras': [('Ekstra Mozzarella', 25), ('Zeytin', 15)],
                'sauces': [],
            },
            {
                'name': 'Karrisik Pizza', 'price': 185, 'prep': 22, 'cal': 750,
                'desc': 'Sucuk, sosis, salam, biber, mantar, misir, zeytin ile yuklu pizza.',
                'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=600',
                'rating': 4.5, 'reviews': 389, 'featured': True, 'spicy': 0,
                'tags': [], 'allergens': ['GLU', 'DAI'],
                'discount': 20,
                'variants': [('Kucuk', 185), ('Orta', 225), ('Buyuk', 265)],
                'extras': [('Ekstra Sucuk', 25), ('Ekstra Peynir', 20)],
                'sauces': [],
            },
            {
                'name': 'Pepperoni', 'price': 160, 'prep': 18, 'cal': 680,
                'desc': 'Bol pepperoni, mozzarella ve oregano. Amerikan klasigi.',
                'image': 'https://images.unsplash.com/photo-1628840042765-356cda07504e?w=600',
                'rating': 4.4, 'reviews': 278, 'featured': False, 'spicy': 1,
                'tags': [], 'allergens': ['GLU', 'DAI'],
                'discount': 0,
                'variants': [('Kucuk', 160), ('Orta', 200), ('Buyuk', 240)],
                'extras': [('Ekstra Pepperoni', 25)],
                'sauces': [],
            },
        ]

        # ── SALATALAR ──
        salata_products = [
            {
                'name': 'Sezar Salata', 'price': 95, 'prep': 10, 'cal': 320,
                'desc': 'Romaine marul, parmesan, kruton, sezar sos, izgara tavuk.',
                'image': 'https://images.unsplash.com/photo-1550304943-4f24f54ddde9?w=600',
                'rating': 4.3, 'reviews': 198, 'featured': False, 'spicy': 0,
                'tags': [], 'allergens': ['GLU', 'DAI', 'EGG'],
                'discount': 0,
                'variants': [],
                'extras': [('Ekstra Tavuk', 30), ('Avokado', 25)],
                'sauces': ['Sezar Sos', 'Balzamik'],
            },
            {
                'name': 'Quinoa Bowl', 'price': 110, 'prep': 12, 'cal': 380,
                'desc': 'Quinoa, avokado, cherry domates, nohut, nar, limon sos. Saglikli ve doyurucu.',
                'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600',
                'rating': 4.5, 'reviews': 156, 'featured': True, 'spicy': 0,
                'tags': ['vegan', 'gluten-free', 'glutensiz'], 'allergens': [],
                'discount': 0,
                'variants': [],
                'extras': [('Feta Peyniri', 20), ('Chia Tohumu', 10)],
                'sauces': ['Limon Sos', 'Tahin Sos'],
                'is_new': True,
            },
        ]

        # ── DENIZ URUNLERI ──
        deniz_products = [
            {
                'name': 'Izgara Somon', 'price': 280, 'prep': 25, 'cal': 450,
                'desc': 'Taze Norverec somonu, tereyaginda pisirilmis sebzeler ve limon sos ile.',
                'image': 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=600',
                'rating': 4.8, 'reviews': 267, 'featured': True, 'spicy': 0,
                'tags': ['gluten-free', 'glutensiz'], 'allergens': ['SHE', 'DAI'],
                'discount': 0,
                'variants': [],
                'extras': [('Pilav', 25), ('Patates Pueresi', 20)],
                'sauces': ['Limon Tereyag', 'Dill Sos'],
            },
            {
                'name': 'Karides Tava', 'price': 240, 'prep': 20, 'cal': 380,
                'desc': 'Tereyaginda sotelanmis jumbo karidesler, sarimsak ve maydanoz ile.',
                'image': 'https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=600',
                'rating': 4.6, 'reviews': 178, 'featured': False, 'spicy': 1,
                'tags': ['gluten-free', 'glutensiz'], 'allergens': ['SHE', 'DAI'],
                'discount': 10,
                'variants': [('6 Adet', 240), ('10 Adet', 380)],
                'extras': [('Pilav', 25), ('Ekmek', 10)],
                'sauces': ['Sarimsak Sosu', 'Limon'],
            },
            {
                'name': 'Levrek Fileto', 'price': 260, 'prep': 22, 'cal': 350,
                'desc': 'Taze levrek fileto, zeytinyagi ve otlar ile firinda pisirilir.',
                'image': 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=600',
                'rating': 4.7, 'reviews': 145, 'featured': False, 'spicy': 0,
                'tags': ['gluten-free', 'glutensiz'], 'allergens': ['SHE'],
                'discount': 0,
                'variants': [],
                'extras': [('Roka Salata', 20)],
                'sauces': [],
            },
        ]

        # ── CORBALAR ──
        corba_products = [
            {
                'name': 'Mercimek Corbasi', 'price': 55, 'prep': 5, 'cal': 180,
                'desc': 'Geleneksel kirmizi mercimek corbasi, limon ve kruton ile.',
                'image': 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=600',
                'rating': 4.4, 'reviews': 567, 'featured': False, 'spicy': 0,
                'tags': ['vegan', 'gluten-free', 'glutensiz'], 'allergens': [],
                'discount': 0,
                'variants': [],
                'extras': [('Ekmek', 10), ('Limon', 5)],
                'sauces': [],
            },
            {
                'name': 'Ezogelin Corbasi', 'price': 55, 'prep': 5, 'cal': 195,
                'desc': 'Bulgur, kirmizi mercimek ve domates ile zenginlestirilmis lezzetli corba.',
                'image': 'https://images.unsplash.com/photo-1603105037880-880cd4f50c55?w=600',
                'rating': 4.3, 'reviews': 423, 'featured': False, 'spicy': 1,
                'tags': ['vegan'], 'allergens': ['GLU'],
                'discount': 0,
                'variants': [],
                'extras': [('Ekmek', 10)],
                'sauces': [],
            },
            {
                'name': 'Tavuk Suyu Corba', 'price': 60, 'prep': 5, 'cal': 150,
                'desc': 'Ev yapimi tavuk suyunda sehriye ve sebzeler. Sifa deposu.',
                'image': 'https://images.unsplash.com/photo-1604152135912-04a022e23696?w=600',
                'rating': 4.5, 'reviews': 312, 'featured': False, 'spicy': 0,
                'tags': [], 'allergens': ['GLU'],
                'discount': 0,
                'variants': [],
                'extras': [('Ekmek', 10), ('Limon', 5)],
                'sauces': [],
            },
        ]

        # ── MEZELER ──
        meze_products = [
            {
                'name': 'Humus', 'price': 65, 'prep': 5, 'cal': 220,
                'desc': 'Nohut puresi, tahin, zeytinyagi, limon suyu. Lavasin yaninda muhtesem.',
                'image': 'https://images.unsplash.com/photo-1577805947697-89e18249d767?w=600',
                'rating': 4.4, 'reviews': 234, 'featured': False, 'spicy': 0,
                'tags': ['vegan', 'gluten-free', 'glutensiz'], 'allergens': ['SES'],
                'discount': 0,
                'variants': [],
                'extras': [('Lavash', 15)],
                'sauces': [],
            },
            {
                'name': 'Sigara Boregi', 'price': 75, 'prep': 12, 'cal': 340,
                'desc': 'Incecik yufka icinde beyaz peynir ve maydanoz. Kitir kitir.',
                'image': 'https://images.unsplash.com/photo-1519864600265-abb23847ef2c?w=600',
                'rating': 4.6, 'reviews': 345, 'featured': True, 'spicy': 0,
                'tags': ['vegetarian', 'vejetaryen'], 'allergens': ['GLU', 'DAI', 'EGG'],
                'discount': 0,
                'variants': [('4 Adet', 75), ('8 Adet', 130)],
                'extras': [],
                'sauces': [],
            },
            {
                'name': 'Babagannush', 'price': 60, 'prep': 8, 'cal': 180,
                'desc': 'Kozlenmis patlican, tahin, sarimsak ve zeytinyagi ile.',
                'image': 'https://images.unsplash.com/photo-1541518763669-27fef04b14ea?w=600',
                'rating': 4.3, 'reviews': 167, 'featured': False, 'spicy': 0,
                'tags': ['vegan', 'gluten-free', 'glutensiz'], 'allergens': ['SES'],
                'discount': 0,
                'variants': [],
                'extras': [('Lavash', 15), ('Nar', 10)],
                'sauces': [],
            },
        ]

        # ── TATLILAR ──
        tatli_products = [
            {
                'name': 'Kunefe', 'price': 120, 'prep': 15, 'cal': 480,
                'desc': 'Antep fistigi ile suslanmis, sicak servis edilen geleneksel kunefe.',
                'image': 'https://images.unsplash.com/photo-1579888944880-d98341245702?w=600',
                'rating': 4.9, 'reviews': 512, 'featured': True, 'spicy': 0,
                'tags': ['vegetarian', 'vejetaryen'], 'allergens': ['GLU', 'DAI', 'NUT'],
                'discount': 0,
                'variants': [],
                'extras': [('Ekstra Fistik', 20), ('Dondurma', 25)],
                'sauces': [],
            },
            {
                'name': 'Baklava (6 Adet)', 'price': 95, 'prep': 5, 'cal': 420,
                'desc': 'Antep fistikli ev yapimi baklava. Ince ince acilmis yufkalarla.',
                'image': 'https://images.unsplash.com/photo-1519676867240-f03562e64548?w=600',
                'rating': 4.8, 'reviews': 389, 'featured': False, 'spicy': 0,
                'tags': ['vegetarian', 'vejetaryen'], 'allergens': ['GLU', 'DAI', 'NUT', 'EGG'],
                'discount': 0,
                'variants': [('6 Adet', 95), ('12 Adet', 170)],
                'extras': [('Kaymak', 25), ('Dondurma', 25)],
                'sauces': [],
            },
            {
                'name': 'Cikolata Sufle', 'price': 85, 'prep': 18, 'cal': 450,
                'desc': 'Sicak cikolata suflesi, vanilyali dondurma ile. Icinden akan cikolata.',
                'image': 'https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=600',
                'rating': 4.7, 'reviews': 278, 'featured': False, 'spicy': 0,
                'tags': ['vegetarian', 'vejetaryen'], 'allergens': ['GLU', 'DAI', 'EGG'],
                'discount': 0,
                'variants': [],
                'extras': [('Ekstra Dondurma', 25)],
                'sauces': [],
                'is_new': True,
            },
        ]

        # ── ICECEKLER ──
        icecek_products = [
            {
                'name': 'Turk Kahvesi', 'price': 45, 'prep': 5, 'cal': 10,
                'desc': 'Geleneksel Turk kahvesi, lokum ile servis edilir.',
                'image': 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefda?w=600',
                'rating': 4.6, 'reviews': 678, 'featured': False, 'spicy': 0,
                'tags': ['vegan', 'gluten-free', 'glutensiz'], 'allergens': [],
                'discount': 0,
                'variants': [('Tek', 45), ('Cift', 80)],
                'extras': [('Lokum', 10)],
                'sauces': [],
            },
            {
                'name': 'Taze Portakal Suyu', 'price': 50, 'prep': 3, 'cal': 110,
                'desc': '5 adet taze sikilmis portakal. Tamamen dogal, seker eklenmez.',
                'image': 'https://images.unsplash.com/photo-1534353473418-4cfa6c56fd38?w=600',
                'rating': 4.5, 'reviews': 345, 'featured': False, 'spicy': 0,
                'tags': ['vegan', 'gluten-free', 'glutensiz'], 'allergens': [],
                'discount': 0,
                'variants': [('300ml', 50), ('500ml', 75)],
                'extras': [],
                'sauces': [],
            },
            {
                'name': 'Limonata', 'price': 40, 'prep': 3, 'cal': 90,
                'desc': 'Ev yapimi taze limonata, nane yapraklari ile. Ferahlatici.',
                'image': 'https://images.unsplash.com/photo-1621263764928-df1444c5e859?w=600',
                'rating': 4.4, 'reviews': 456, 'featured': False, 'spicy': 0,
                'tags': ['vegan', 'gluten-free', 'glutensiz'], 'allergens': [],
                'discount': 0,
                'variants': [('Bardak', 40), ('Surahi', 95)],
                'extras': [],
                'sauces': [],
            },
            {
                'name': 'Ayran', 'price': 25, 'prep': 2, 'cal': 60,
                'desc': 'Ev yapimi ayran, taze yogurttan.',
                'image': 'https://images.unsplash.com/photo-1584433144859-1fc3ab64a957?w=600',
                'rating': 4.3, 'reviews': 789, 'featured': False, 'spicy': 0,
                'tags': ['vegetarian', 'vejetaryen', 'gluten-free', 'glutensiz'], 'allergens': ['DAI'],
                'discount': 0,
                'variants': [('Bardak', 25), ('Buyuk', 40)],
                'extras': [],
                'sauces': [],
            },
        ]

        # Map categories to products
        all_products = {
            'Kebaplar': kebap_products,
            'Burgerler': burger_products,
            'Pizzalar': pizza_products,
            'Salatalar': salata_products,
            'Deniz Urunleri': deniz_products,
            'Corbalar': corba_products,
            'Mezeler': meze_products,
            'Tatlilar': tatli_products,
            'Icecekler': icecek_products,
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

        self.stdout.write(f'  Created/verified {product_count} products')

    def _create_single_product(self, org, category, data, allergens, sort_order, now):
        """Create a single product with all related data."""
        slug = slugify(data['name'])

        product, created = Product.objects.get_or_create(
            organization=org,
            category=category,
            slug=slug,
            defaults={
                'name': data['name'],
                'description': data['desc'],
                'short_description': data['desc'][:100] if len(data['desc']) > 100 else data['desc'],
                'base_price': Decimal(str(data['price'])),
                'currency': 'TRY',
                'image': data.get('image', ''),
                'is_active': True,
                'is_available': True,
                'is_featured': data.get('featured', False),
                'preparation_time': data.get('prep', 15),
                'calories': data.get('cal', 0),
                'spicy_level': data.get('spicy', 0),
                'discount_percentage': data.get('discount', 0),
                'rating': Decimal(str(data.get('rating', 0))),
                'review_count': data.get('reviews', 0),
                'tags': data.get('tags', []),
                'sort_order': sort_order,
            }
        )

        if not created:
            return product

        # Force isNew for select products
        if data.get('is_new'):
            product.created_at = now
            product.save(update_fields=['created_at'])

        # Create variants
        for v_idx, (v_name, v_price) in enumerate(data.get('variants', [])):
            ProductVariant.objects.get_or_create(
                product=product,
                name=v_name,
                defaults={
                    'price': Decimal(str(v_price)),
                    'is_default': v_idx == 0,
                    'is_available': True,
                    'sort_order': v_idx,
                }
            )

        # Create extras (modifiers with price > 0)
        for e_idx, (e_name, e_price) in enumerate(data.get('extras', [])):
            ProductModifier.objects.get_or_create(
                product=product,
                name=e_name,
                defaults={
                    'price': Decimal(str(e_price)),
                    'is_default': False,
                    'is_required': False,
                    'max_quantity': 2,
                    'sort_order': e_idx,
                }
            )

        # Create sauces (modifiers with price = 0)
        for s_idx, s_name in enumerate(data.get('sauces', [])):
            ProductModifier.objects.get_or_create(
                product=product,
                name=s_name,
                defaults={
                    'price': Decimal('0'),
                    'is_default': False,
                    'is_required': False,
                    'max_quantity': 1,
                    'sort_order': 100 + s_idx,  # After extras
                }
            )

        # Create allergen associations
        for a_code in data.get('allergens', []):
            if a_code in allergens:
                ProductAllergen.objects.get_or_create(
                    product=product,
                    allergen=allergens[a_code],
                    defaults={
                        'severity': AllergenSeverity.CONTAINS,
                    }
                )

        # Create nutrition info for some products
        if data.get('cal') and data['cal'] > 0:
            NutritionInfo.objects.get_or_create(
                product=product,
                defaults={
                    'serving_size': '1 porsiyon',
                    'calories': data['cal'],
                }
            )

        return product
