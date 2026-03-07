"""
Management command to seed additional organizations with menus, categories, and products.

Creates realistic Turkish restaurant data for multiple organizations beyond
the initial Lezzet Sarayi, so the admin panel looks populated.

Usage:
    python manage.py seed_extra_orgs
    python manage.py seed_extra_orgs --clear
"""

import logging
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

logger = logging.getLogger(__name__)
User = get_user_model()
now = timezone.now


def rand_past(days_back=90):
    return now() - timedelta(days=random.randint(1, days_back), hours=random.randint(0, 23))


# ---------------------------------------------------------------------------
# Organization definitions
# ---------------------------------------------------------------------------
ORGS = [
    {
        'name': 'Bosphorus Bistro',
        'slug': 'bosphorus-bistro',
        'email': 'info@bosphorusbistro.com',
        'phone': '+90 212 445 67 89',
        'owner_email': 'mehmet@bosphorusbistro.com',
        'owner_first': 'Mehmet',
        'owner_last': 'Ozturk',
        'theme': {
            'name': 'Ocean Blue',
            'primary_color': '#1e40af',
            'secondary_color': '#60a5fa',
            'background_color': '#f8fafc',
            'text_color': '#1e293b',
            'accent_color': '#0ea5e9',
        },
        'categories': [
            {
                'name': 'Kahvalti',
                'slug': 'kahvalti',
                'icon': 'ph-sun',
                'products': [
                    ('Serpme Kahvalti', 'Zengin serpme kahvalti tabagi, peynir cesitleri, zeytin, bal, kaymak', 280, 'https://images.unsplash.com/photo-1525351484163-7529414344d8?w=400'),
                    ('Menemen', 'Geleneksel domates ve biberli menemen', 75, 'https://images.unsplash.com/photo-1590412200988-a436970781fa?w=400'),
                    ('Sucuklu Yumurta', 'Kasap sucugu ile sahanda yumurta', 85, 'https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=400'),
                    ('Acma & Pogaca', 'Taze firinda acma ve peynirli pogaca (4 adet)', 55, None),
                ],
            },
            {
                'name': 'Balik & Deniz Urunleri',
                'slug': 'balik-deniz-urunleri',
                'icon': 'ph-fish',
                'products': [
                    ('Levrek Izgara', 'Taze levrek filetosunun izgarada pisirimi, sebze garnisi', 320, 'https://images.unsplash.com/photo-1534766555764-ce878a5e3a2b?w=400'),
                    ('Karides Tava', 'Tereyagli karides tava, roka salatasiyla', 280, 'https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=400'),
                    ('Kalamar Tava', 'Citir kalamar halkalari, tarator sosla', 180, 'https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=400'),
                    ('Hamsi Tava', 'Mevsim hamsisi, misir ununda kizartilmis', 140, None),
                    ('Somon Fume', 'Ince dilimli somon fume, kapari ve krema peynir', 195, None),
                ],
            },
            {
                'name': 'Salatalar',
                'slug': 'salatalar',
                'icon': 'ph-leaf',
                'products': [
                    ('Sezar Salata', 'Romaine marulu, parmesan, kruton, sezar sosu', 110, 'https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400'),
                    ('Bosphorus Salata', 'Akdeniz yesillik, nar eksisi, ceviz', 95, None),
                    ('Ahtapot Salatasi', 'Haslama ahtapot, zeytin yagi, limon', 195, None),
                ],
            },
            {
                'name': 'Ana Yemekler',
                'slug': 'ana-yemekler',
                'icon': 'ph-cooking-pot',
                'products': [
                    ('Kuzu Tandir', 'Firinlenmis kuzu tandir, pilav ve salata', 350, 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400'),
                    ('Tas Kebabi', 'Yumusacik dana eti, patates ve havuc', 220, None),
                    ('Hunkar Begendi', 'Kuzu kusleme, patlicanli besamel sos', 260, 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400'),
                    ('Islak Hamburger', 'Istanbul usulu islak hamburger', 95, None),
                ],
            },
            {
                'name': 'Tatlilar',
                'slug': 'tatlilar-bb',
                'icon': 'ph-cake',
                'products': [
                    ('San Sebastian Cheesecake', 'Ozel tarif, yanmis cheesecake', 120, 'https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=400'),
                    ('Sutlac', 'Firinlanmis geleneksel sutlac', 65, None),
                    ('Kazandibi', 'Karamelize sutlu tatli', 70, None),
                ],
            },
            {
                'name': 'Icecekler',
                'slug': 'icecekler-bb',
                'icon': 'ph-coffee',
                'products': [
                    ('Turk Cayi', 'Geleneksel ince belli bardakta cay', 20, None),
                    ('Turk Kahvesi', 'Cezvede pisirilen Turk kahvesi', 45, None),
                    ('Taze Portakal Suyu', 'Sikma portakal suyu (300ml)', 55, None),
                    ('Ayran', 'Ev yapimi ayran', 25, None),
                ],
            },
        ],
    },
    {
        'name': 'Cafe Noir',
        'slug': 'cafe-noir',
        'email': 'hello@cafenoir.com.tr',
        'phone': '+90 216 334 55 66',
        'owner_email': 'ayse@cafenoir.com.tr',
        'owner_first': 'Ayse',
        'owner_last': 'Demir',
        'theme': {
            'name': 'Dark Elegance',
            'primary_color': '#1c1917',
            'secondary_color': '#a16207',
            'background_color': '#fafaf9',
            'text_color': '#1c1917',
            'accent_color': '#d97706',
        },
        'categories': [
            {
                'name': 'Espresso Bar',
                'slug': 'espresso-bar',
                'icon': 'ph-coffee',
                'products': [
                    ('Espresso', 'Tek shot, %100 Arabica', 45, 'https://images.unsplash.com/photo-1510707577719-ae7c14805e3a?w=400'),
                    ('Flat White', 'Double shot, ipeksi sut kopu', 65, 'https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=400'),
                    ('Cortado', 'Espresso + esit miktarda sut', 55, None),
                    ('Latte', 'Single origin, latte art', 60, 'https://images.unsplash.com/photo-1534778101976-62847782c213?w=400'),
                    ('Cappuccino', 'Klasik italyan cappuccino', 60, None),
                    ('Americano', 'Double shot + sicak su', 50, None),
                    ('V60 Pour Over', 'El demleme, single origin', 75, None),
                ],
            },
            {
                'name': 'Soguk Kahveler',
                'slug': 'soguk-kahveler',
                'icon': 'ph-drop',
                'products': [
                    ('Iced Latte', 'Buz uzerinde espresso + sut', 70, 'https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=400'),
                    ('Cold Brew', '24 saat demlenmis soguk kahve', 75, None),
                    ('Frappe', 'Buzlu calkama kahve', 65, None),
                    ('Affogato', 'Vanilya dondurmasi + espresso', 80, None),
                ],
            },
            {
                'name': 'Pastane',
                'slug': 'pastane',
                'icon': 'ph-cake',
                'products': [
                    ('Croissant', 'Taze tereyagli croissant', 55, 'https://images.unsplash.com/photo-1555507036-ab1f4038024a?w=400'),
                    ('Pain au Chocolat', 'Cikolatali fransiz pastasi', 60, None),
                    ('Brownie', 'Yogun cikolatali brownie', 65, 'https://images.unsplash.com/photo-1564355808539-22fda35bed7e?w=400'),
                    ('Cookie', 'Cikolatali chip cookie (2 adet)', 50, None),
                    ('Carrot Cake', 'Havuclu tarcinli pasta', 75, None),
                    ('Tiramisu', 'Klasik Italyan tiramisu', 85, None),
                ],
            },
            {
                'name': 'Sandvicler',
                'slug': 'sandvicler',
                'icon': 'ph-bread',
                'products': [
                    ('Club Sandwich', 'Tavuk, pastirma, marul, domates, mayonez', 125, 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=400'),
                    ('Avocado Toast', 'Eksi maya ekmegi, avokado, yumurta', 110, 'https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=400'),
                    ('Grilled Cheese', 'Karisik peynirli tost', 85, None),
                    ('Tuna Melt', 'Ton balikli sicak sandvic', 105, None),
                ],
            },
        ],
    },
    {
        'name': 'Sultan Kebap',
        'slug': 'sultan-kebap',
        'email': 'info@sultankebap.com.tr',
        'phone': '+90 312 222 33 44',
        'owner_email': 'ali@sultankebap.com.tr',
        'owner_first': 'Ali',
        'owner_last': 'Kaya',
        'theme': {
            'name': 'Ottoman Red',
            'primary_color': '#991b1b',
            'secondary_color': '#dc2626',
            'background_color': '#fef2f2',
            'text_color': '#1f2937',
            'accent_color': '#b91c1c',
        },
        'categories': [
            {
                'name': 'Kebaplar',
                'slug': 'kebaplar-sk',
                'icon': 'ph-fire',
                'products': [
                    ('Adana Kebap', 'Aci kiyma kebap, mangal atesi', 185, 'https://images.unsplash.com/photo-1603360946369-dc9bb6258143?w=400'),
                    ('Urfa Kebap', 'Acsiz kiyma kebap', 185, None),
                    ('Iskender', 'Pide uzerinde doner, tereyagi, yogurt', 220, 'https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=400'),
                    ('Patlican Kebap', 'Kozlenmis patlican ile kebap', 195, None),
                    ('Karisik Kebap', 'Adana, urfa, tavuk sis, kuzu sis', 280, None),
                    ('Beyti Sarma', 'Lavasa sarili kebap, yogurt sosu', 210, None),
                ],
            },
            {
                'name': 'Pideler',
                'slug': 'pideler',
                'icon': 'ph-bread',
                'products': [
                    ('Kiymali Pide', 'Taze firindan kiymali pide', 120, None),
                    ('Kasarli Pide', 'Kasar peynirli pide', 100, None),
                    ('Kusbasi Pide', 'Kusbasi etli pide', 145, None),
                    ('Lahmacun', 'Ince hamur, kiymali (3 adet)', 90, None),
                ],
            },
            {
                'name': 'Baslangiclar',
                'slug': 'baslangiclar-sk',
                'icon': 'ph-bowl-food',
                'products': [
                    ('Mercimek Corbasi', 'Kirmizi mercimek corbasi', 50, None),
                    ('Humus', 'Tahinli nohut ezme', 55, None),
                    ('Piyaz', 'Antep usulu piyaz', 45, None),
                    ('Cacik', 'Ev yapimi cacik', 35, None),
                    ('Ezme Salata', 'Aci ezme', 40, None),
                ],
            },
            {
                'name': 'Icecekler',
                'slug': 'icecekler-sk',
                'icon': 'ph-beer-bottle',
                'products': [
                    ('Ayran', 'Ev yapimi ayran', 20, None),
                    ('Salgam', 'Adana salgam suyu', 25, None),
                    ('Sira', 'Uzum sirasi', 30, None),
                    ('Turk Cayi', 'Bardak cay', 15, None),
                ],
            },
        ],
    },
]

# Extra media files for all orgs
MEDIA_FILES = [
    ('hero-banner.jpg', 'IMAGE', 'image/jpeg', 2456000, 1920, 1080),
    ('logo.png', 'IMAGE', 'image/png', 45000, 512, 512),
    ('menu-bg.jpg', 'IMAGE', 'image/jpeg', 1890000, 1920, 1280),
    ('promo-video.mp4', 'VIDEO', 'video/mp4', 15600000, 1920, 1080),
    ('about-us.jpg', 'IMAGE', 'image/jpeg', 980000, 1200, 800),
    ('instagram-1.jpg', 'IMAGE', 'image/jpeg', 456000, 1080, 1080),
    ('instagram-2.jpg', 'IMAGE', 'image/jpeg', 523000, 1080, 1080),
    ('instagram-3.jpg', 'IMAGE', 'image/jpeg', 487000, 1080, 1080),
]


class Command(BaseCommand):
    help = 'Seed additional organizations with menus, products, media and more'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing extra data first')

    def handle(self, *args, **options):
        from apps.core.models import Organization
        from apps.menu.models import Menu, Category, Product, Theme, Allergen
        from apps.media.models import Media, MediaFolder

        if options['clear']:
            self.stdout.write('Clearing extra organizations...')
            for org_data in ORGS:
                Organization.objects.filter(slug=org_data['slug']).delete()
            self.stdout.write(self.style.SUCCESS('Cleared.'))

        allergens = list(Allergen.objects.filter(deleted_at__isnull=True))

        for org_data in ORGS:
            # --- Organization ---
            org, created = Organization.objects.get_or_create(
                slug=org_data['slug'],
                defaults={
                    'name': org_data['name'],
                    'email': org_data['email'],
                    'phone': org_data['phone'],
                    'status': 'ACTIVE',
                    'settings': {'currency': 'TRY', 'timezone': 'Europe/Istanbul'},
                }
            )
            if created:
                self.stdout.write(f'  Created org: {org.name}')
            else:
                self.stdout.write(f'  Org exists: {org.name}')

            # --- Owner user ---
            owner, _ = User.objects.get_or_create(
                email=org_data['owner_email'],
                defaults={
                    'first_name': org_data['owner_first'],
                    'last_name': org_data['owner_last'],
                    'organization': org,
                    'is_staff': True,
                    'status': 'ACTIVE',
                }
            )
            if _:
                owner.set_password('Owner1234!emenum')
                owner.save()

            # --- Theme ---
            td = org_data['theme']
            theme, _ = Theme.objects.get_or_create(
                organization=org,
                slug=slugify(td['name']),
                defaults={
                    'name': td['name'],
                    'primary_color': td['primary_color'],
                    'secondary_color': td['secondary_color'],
                    'background_color': td['background_color'],
                    'text_color': td['text_color'],
                    'accent_color': td['accent_color'],
                    'is_default': True,
                    'is_active': True,
                }
            )

            # --- Menu ---
            menu_name = f'{org_data["name"]} Menu'
            menu_slug = f'{org_data["slug"]}-menu'
            menu, _ = Menu.objects.get_or_create(
                organization=org,
                slug=menu_slug,
                defaults={
                    'name': menu_name,
                    'description': f'{org_data["name"]} ana menusu',
                    'is_published': True,
                    'published_at': rand_past(30),
                    'is_default': True,
                    'theme': theme,
                }
            )
            self.stdout.write(f'    Menu: {menu.name} (slug={menu.slug})')

            # --- Categories & Products ---
            for sort_idx, cat_data in enumerate(org_data['categories']):
                cat, _ = Category.objects.get_or_create(
                    organization=org,
                    menu=menu,
                    slug=cat_data['slug'],
                    defaults={
                        'name': cat_data['name'],
                        'icon': cat_data['icon'],
                        'is_active': True,
                        'sort_order': sort_idx * 10,
                    }
                )

                for prod_idx, (pname, pdesc, pprice, pimg) in enumerate(cat_data['products']):
                    pslug = slugify(pname)[:50]
                    prod_defaults = {
                        'name': pname,
                        'short_description': pdesc[:100] if pdesc else '',
                        'description': pdesc,
                        'base_price': Decimal(str(pprice)),
                        'currency': 'TRY',
                        'is_active': True,
                        'is_available': random.random() > 0.1,
                        'is_featured': random.random() > 0.8,
                        'is_chef_recommended': random.random() > 0.85,
                        'sort_order': prod_idx * 10,
                        'preparation_time': random.choice([5, 10, 15, 20, 25, 30]),
                        'calories': random.randint(100, 900) if random.random() > 0.3 else None,
                    }
                    if pimg:
                        prod_defaults['image'] = pimg

                    product, _ = Product.objects.get_or_create(
                        organization=org,
                        category=cat,
                        slug=pslug,
                        defaults=prod_defaults,
                    )

                    # Add random allergens
                    if allergens and random.random() > 0.5:
                        from apps.menu.models import ProductAllergen
                        for allergen in random.sample(allergens, min(random.randint(1, 3), len(allergens))):
                            ProductAllergen.objects.get_or_create(
                                product=product,
                                allergen=allergen,
                                defaults={'severity': random.choice(['contains', 'may_contain', 'traces'])}
                            )

            # --- Media Folders ---
            root_folder, _ = MediaFolder.objects.get_or_create(
                organization=org,
                slug=f'{org_data["slug"]}-media',
                defaults={
                    'name': f'{org_data["name"]} Media',
                    'is_public': True,
                }
            )

            products_folder, _ = MediaFolder.objects.get_or_create(
                organization=org,
                slug=f'{org_data["slug"]}-products',
                defaults={
                    'name': 'Product Images',
                    'parent': root_folder,
                    'is_public': True,
                }
            )

            branding_folder, _ = MediaFolder.objects.get_or_create(
                organization=org,
                slug=f'{org_data["slug"]}-branding',
                defaults={
                    'name': 'Branding',
                    'parent': root_folder,
                    'is_public': True,
                }
            )

            # --- Media Files ---
            for fname, mtype, mime, fsize, w, h in MEDIA_FILES:
                Media.objects.get_or_create(
                    organization=org,
                    name=f'{org_data["name"]} - {fname}',
                    defaults={
                        'original_filename': fname,
                        'media_type': mtype,
                        'mime_type': mime,
                        'file_size': fsize,
                        'width': w,
                        'height': h,
                        'status': 'READY',
                        'storage': 'LOCAL',
                        'folder': branding_folder if 'logo' in fname else products_folder,
                        'uploaded_by': owner,
                        'is_public': True,
                        'file_path': f'media/{org_data["slug"]}/{fname}',
                        'url': f'/media/{org_data["slug"]}/{fname}',
                    }
                )

            self.stdout.write(self.style.SUCCESS(f'  ✓ {org.name}: done'))

        # Also add more media to existing Lezzet Sarayi
        try:
            lezzet = Organization.objects.get(slug='lezzet-sarayi')
            lezzet_owner = User.objects.filter(organization=lezzet, is_staff=True).first()
            if lezzet_owner:
                root, _ = MediaFolder.objects.get_or_create(
                    organization=lezzet, slug='lezzet-root',
                    defaults={'name': 'Lezzet Sarayi Media', 'is_public': True}
                )
                for fname, mtype, mime, fsize, w, h in MEDIA_FILES[:5]:
                    Media.objects.get_or_create(
                        organization=lezzet,
                        name=f'Lezzet Sarayi - {fname}',
                        defaults={
                            'original_filename': fname,
                            'media_type': mtype,
                            'mime_type': mime,
                            'file_size': fsize,
                            'width': w, 'height': h,
                            'status': 'READY',
                            'storage': 'LOCAL',
                            'folder': root,
                            'uploaded_by': lezzet_owner,
                            'is_public': True,
                            'file_path': f'media/lezzet-sarayi/{fname}',
                            'url': f'/media/lezzet-sarayi/{fname}',
                        }
                    )
                self.stdout.write(self.style.SUCCESS('  ✓ Lezzet Sarayi: extra media added'))
        except Organization.DoesNotExist:
            pass

        self.stdout.write(self.style.SUCCESS('\n✅ All extra organizations seeded!'))
