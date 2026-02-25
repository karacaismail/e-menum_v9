"""
seed_demo_data — One command to rule them all.

Orchestrates every seed command, then creates 12 additional restaurants
with full operational data (users, roles, menus, orders, customers,
subscriptions, etc.).

Usage:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --skip-deps   # only new orgs
    python manage.py seed_demo_data --clear        # wipe new orgs first
"""

import logging
import random
import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

logger = logging.getLogger(__name__)
User = get_user_model()
now = timezone.now


# ── helpers ─────────────────────────────────────────────────────────
def _rp(days=90):
    """Random past datetime."""
    return now() - timedelta(days=random.randint(1, days), hours=random.randint(0, 23), minutes=random.randint(0, 59))


def _rr(hours=48):
    """Random recent datetime."""
    return now() - timedelta(hours=random.randint(0, hours), minutes=random.randint(0, 59))


# ── Turkish first/last name pools ──────────────────────────────────
FIRST_NAMES = [
    'Ahmet', 'Mehmet', 'Mustafa', 'Ali', 'Hasan', 'Ibrahim', 'Huseyin',
    'Emre', 'Burak', 'Cem', 'Murat', 'Serkan', 'Oguz', 'Baris', 'Koray',
    'Ayse', 'Fatma', 'Emine', 'Zeynep', 'Elif', 'Selin', 'Deniz',
    'Gizem', 'Ipek', 'Merve', 'Esra', 'Tugce', 'Ceren', 'Ece', 'Pinar',
]
LAST_NAMES = [
    'Yilmaz', 'Kaya', 'Demir', 'Celik', 'Sahin', 'Ozturk', 'Acar',
    'Yildiz', 'Aksoy', 'Dogan', 'Polat', 'Aydin', 'Erdogan', 'Arslan',
    'Bulut', 'Kilic', 'Gunes', 'Uzun', 'Koc', 'Tas',
]
CITIES_DISTRICTS = [
    ('Istanbul', 'Uskudar'), ('Istanbul', 'Kadikoy'), ('Istanbul', 'Besiktas'),
    ('Istanbul', 'Beyoglu'), ('Istanbul', 'Nisantasi'), ('Istanbul', 'Yesilkoy'),
    ('Ankara', 'Cankaya'), ('Ankara', 'Kizilay'),
    ('Izmir', 'Alsancak'), ('Izmir', 'Karsiyaka'),
    ('Bursa', 'Osmangazi'), ('Antalya', 'Konyaalti'),
    ('Gaziantep', 'Sehitkamil'), ('Trabzon', 'Ortahisar'),
    ('Mugla', 'Bodrum'), ('Nevsehir', 'Merkez'), ('Rize', 'Merkez'),
]
FEEDBACK_TR = [
    'Yemekler muhtesemdı, kesinlikle tekrar geleceğiz!',
    'Servis biraz yavaştı ama lezzetler harikaydı.',
    'Fiyat/performans oranı çok iyi.',
    'Manzara ve atmosfer olağanüstü.',
    'Garson çok ilgili ve güler yüzlüydü.',
    'Porsiyon miktarları tatmin edici.',
    'Menüdeki çeşitlilik bizi şaşırttı.',
    'Tatlılar ev yapımı, harika!',
    'Çocuk menüsü olması çok iyi.',
    'Hijyen konusunda çok titizler.',
    'Kahvaltı tabağı doyurucu ve lezzetli.',
    'Akşam yemeği için rezervasyon şart.',
    'Vejetaryen seçenekler yeterli değildi.',
    'Balık taze ve güzel pişirilmişti.',
    'İkinci ziyaretimiz, yine memnun kaldık.',
]


# ═══════════════════════════════════════════════════════════════════
# 12 NEW RESTAURANT DEFINITIONS
# ═══════════════════════════════════════════════════════════════════
NEW_ORGS = [
    # ── 1. Anadolu Sofrası (Ev Yemekleri · İstanbul · Growth) ─────
    {
        'name': 'Anadolu Sofrasi',
        'slug': 'anadolu-sofrasi',
        'email': 'info@anadolusofrasi.com.tr',
        'phone': '+90 216 778 90 12',
        'city': 'Istanbul', 'district': 'Uskudar',
        'owner': ('hakan', 'Hakan', 'Yildirim', 'hakan@anadolusofrasi.com.tr'),
        'staff_count': 3,
        'plan': 'growth',
        'theme': {'name': 'Warm Terracotta', 'primary': '#c2410c', 'secondary': '#ea580c', 'bg': '#fff7ed', 'text': '#1c1917', 'accent': '#f97316'},
        'categories': [
            ('Corbalar', 'ph-bowl-steam', [
                ('Mercimek Corbasi', 'Geleneksel kirmizi mercimek corbasi', 45),
                ('Tarhana Corbasi', 'Ev yapimi tarhana ile', 50),
                ('Ezogelin Corbasi', 'Kirmizi mercimek ve bulgur', 45),
                ('Yayla Corbasi', 'Yogurtlu pirinc corbasi', 45),
            ]),
            ('Ana Yemekler', 'ph-cooking-pot', [
                ('Kuru Fasulye', 'Pilavli kuru fasulye, tursu ile', 95),
                ('Etli Yaprak Sarma', 'Anne usulu yaprak sarma', 120),
                ('Hünkar Begendi', 'Kuzu kusleme, patlicanli', 140),
                ('Tas Kebabi', 'Yumusacik dana eti', 130),
                ('Karniyarik', 'Kiymali karniyarik', 110),
                ('Mantu', 'El acmasi Kayseri mantisi', 100),
            ]),
            ('Zeytinyagli', 'ph-leaf', [
                ('Imam Bayildi', 'Zeytinyagli imam bayildi', 75),
                ('Fasulye Pilaki', 'Zeytinyagli barbunya', 65),
                ('Enginar', 'Zeytinyagli enginar', 80),
                ('Yaprak Sarma', 'Zeytinyagli yaprak sarma', 70),
            ]),
            ('Tatlilar', 'ph-cake', [
                ('Sutlac', 'Firinlanmis sutlac', 55),
                ('Asure', 'Geleneksel asure', 50),
                ('Kazandibi', 'Karamelize sutlu tatli', 60),
                ('Gullac', 'Mevsim tatlisi gullac', 65),
            ]),
            ('Icecekler', 'ph-coffee', [
                ('Turk Cayi', 'Ince belli bardakta cay', 15),
                ('Ayran', 'Ev yapimi ayran', 20),
                ('Salgam', 'Taze salgam suyu', 25),
                ('Turk Kahvesi', 'Cezvede pisirilen', 40),
            ]),
        ],
    },
    # ── 2. Deniz Kızı Balık (Balık · İzmir · Professional) ───────
    {
        'name': 'Deniz Kizi Balik',
        'slug': 'deniz-kizi-balik',
        'email': 'info@denizkizibalik.com',
        'phone': '+90 232 463 55 66',
        'city': 'Izmir', 'district': 'Alsancak',
        'owner': ('cenk', 'Cenk', 'Aksoy', 'cenk@denizkizibalik.com'),
        'staff_count': 4,
        'plan': 'professional',
        'theme': {'name': 'Deep Ocean', 'primary': '#0369a1', 'secondary': '#0284c7', 'bg': '#f0f9ff', 'text': '#0c4a6e', 'accent': '#06b6d4'},
        'categories': [
            ('Baslangiclar', 'ph-fork-knife', [
                ('Ahtapot Salatasi', 'Marine ahtapot, roka, kapari', 195),
                ('Karides Güvec', 'Firin karides, domates sosu', 180),
                ('Midye Dolma', 'Baharatli midye dolma (6 adet)', 90),
                ('Deniz Borulcesi', 'Zeytinyagli deniz borulcesi', 75),
                ('Kalamar Tava', 'Citir kalamar halkalari', 160),
            ]),
            ('Baliklar', 'ph-fish', [
                ('Levrek Izgara', 'Taze levrek, sebze garnisi', 320),
                ('Cipura Tava', 'Tavada cipura fileto', 290),
                ('Lufer Izgara', 'Mevsim luferi, arugula', 350),
                ('Somon Fume', 'Ince dilim somon fume', 220),
                ('Hamsi Tava', 'Karadeniz hamsisi, misir unu', 140),
                ('Barbunya Izgara', 'Taze barbunya, limon', 260),
            ]),
            ('Deniz Urunleri', 'ph-shrimp', [
                ('Karides Sote', 'Tereyagli karides, sarimsak', 280),
                ('Istakoz', 'Izgarada istakoz (pors. fiyat)', 650),
                ('Karişık Deniz Tabagi', 'Karides, kalamar, midye, ahtapot', 380),
            ]),
            ('Salatalar', 'ph-leaf', [
                ('Ege Salatasi', 'Domates, salatalik, otlar, peynir', 85),
                ('Roka Salatasi', 'Roka, parmesan, nar eksisi', 95),
            ]),
            ('Tatlilar', 'ph-cake', [
                ('San Sebastian Cheesecake', 'Yanmis cheesecake', 110),
                ('Supangle', 'Cikolatali supangle', 65),
                ('Kazandibi', 'Karamelize sutlu tatli', 70),
            ]),
            ('Icecekler', 'ph-wine', [
                ('Beyaz Sarap (kadeh)', 'Evin ozel secimi', 95),
                ('Raki', 'Yeni Raki (tek)', 85),
                ('Limonata', 'Ev yapimi limonata', 45),
                ('Turk Cayi', 'Bardak cay', 15),
            ]),
        ],
    },
    # ── 3. Yeşilköy Vegan Mutfak (Vegan · İstanbul · Starter) ───
    {
        'name': 'Yesilkoy Vegan Mutfak',
        'slug': 'yesilkoy-vegan',
        'email': 'merhaba@yesilkoyvegan.com',
        'phone': '+90 212 599 44 55',
        'city': 'Istanbul', 'district': 'Yesilkoy',
        'owner': ('dila', 'Dila', 'Cetin', 'dila@yesilkoyvegan.com'),
        'staff_count': 2,
        'plan': 'starter',
        'theme': {'name': 'Green Life', 'primary': '#15803d', 'secondary': '#22c55e', 'bg': '#f0fdf4', 'text': '#14532d', 'accent': '#4ade80'},
        'categories': [
            ('Bowl\'lar', 'ph-bowl-food', [
                ('Buddha Bowl', 'Kinoa, avokado, nohut, tatli patates', 110),
                ('Poke Bowl', 'Edamame, mango, sushi pirinci', 120),
                ('Protein Bowl', 'Tofu, mercimek, sebze', 105),
            ]),
            ('Burgerler', 'ph-hamburger', [
                ('Beyond Burger', 'Bitkisel burger, vegan peynir', 135),
                ('Falafel Burger', 'Nohut koftesi, humus', 100),
                ('Mantar Burger', 'Portobello, avokado', 115),
            ]),
            ('Salatalar', 'ph-leaf', [
                ('Kale Salatasi', 'Kale, nar, ceviz, nar eksisi', 90),
                ('Akdeniz Salatasi', 'Domates, salatalik, zeytin', 75),
            ]),
            ('Tatlilar', 'ph-cookie', [
                ('Raw Cheesecake', 'Kaju bazli, meyveli', 85),
                ('Chia Puding', 'Hindistan cevizi sutu, mango', 65),
                ('Brownie', 'Vegan cikolatali brownie', 70),
            ]),
            ('Icecekler', 'ph-orange-slice', [
                ('Yesil Smoothie', 'Ispanak, muz, elma, zencefil', 65),
                ('Detox Suyu', 'Havuc, portakal, zencefil', 55),
                ('Badem Sutu Latte', 'Espresso, badem sutu', 60),
                ('Kombucha', 'Ev yapimi kombucha', 50),
            ]),
        ],
    },
    # ── 4. Kapadokya Pizza (Pizzeria · Nevşehir · Starter) ──────
    {
        'name': 'Kapadokya Pizza',
        'slug': 'kapadokya-pizza',
        'email': 'siparis@kapadokyapizza.com',
        'phone': '+90 384 271 33 44',
        'city': 'Nevsehir', 'district': 'Merkez',
        'owner': ('volkan', 'Volkan', 'Tas', 'volkan@kapadokyapizza.com'),
        'staff_count': 2,
        'plan': 'starter',
        'theme': {'name': 'Pizza Red', 'primary': '#dc2626', 'secondary': '#f87171', 'bg': '#fef2f2', 'text': '#1f2937', 'accent': '#ef4444'},
        'categories': [
            ('Pizzalar', 'ph-pizza', [
                ('Margarita', 'Domates sosu, mozzarella, fesleğen', 120),
                ('Kapadokya Ozel', 'Pastirmali, kasarli, biberli', 155),
                ('Pepperoni', 'Bol pepperoni, mozzarella', 145),
                ('Dort Peynirli', 'Mozzarella, kasar, roquefort, parmesan', 160),
                ('Sucuklu Pizza', 'Turk sucugu, kasar, domates', 140),
                ('Vejeteryan', 'Mantar, biber, misir, zeytin', 130),
            ]),
            ('Makarnalar', 'ph-bowl-food', [
                ('Penne Arabiata', 'Acili domates sosu, fesleğen', 95),
                ('Fettuccine Alfredo', 'Kremali sos, parmesan', 110),
                ('Bolognese', 'Kiymali domates sosu, spagetti', 105),
            ]),
            ('Baslangiclar', 'ph-bread', [
                ('Sarimsak Ekmegi', 'Tereyagli sarimsak ekmegi', 55),
                ('Bruschetta', 'Domates, fesleğen, zeytinyagi', 65),
                ('Soguk Meze Tabagi', 'Zeytin, peynir, kuru domates', 80),
            ]),
            ('Icecekler', 'ph-beer-bottle', [
                ('Kola', 'Coca-Cola (330ml)', 30),
                ('Ayran', 'Soguk ayran', 20),
                ('Limonata', 'Ev yapimi limonata', 35),
            ]),
        ],
    },
    # ── 5. Ayder Yayla Evi (Karadeniz · Rize · Free) ────────────
    {
        'name': 'Ayder Yayla Evi',
        'slug': 'ayder-yayla-evi',
        'email': 'bilgi@ayderyaylaevi.com',
        'phone': '+90 464 657 22 33',
        'city': 'Rize', 'district': 'Camlihemsin',
        'owner': ('temel', 'Temel', 'Uzun', 'temel@ayderyaylaevi.com'),
        'staff_count': 1,
        'plan': 'free',
        'theme': {'name': 'Mountain Green', 'primary': '#166534', 'secondary': '#16a34a', 'bg': '#f0fdf4', 'text': '#14532d', 'accent': '#22c55e'},
        'categories': [
            ('Kahvalti', 'ph-sun', [
                ('Yayla Kahvaltisi', 'Kuymak, muhlama, tereyag, bal', 180),
                ('Kuymak', 'Misir unlu peynirli kuymak', 85),
                ('Muhlama', 'Karadeniz muhlama', 90),
            ]),
            ('Ana Yemekler', 'ph-cooking-pot', [
                ('Karadeniz Pidesi', 'Kiymali Karadeniz pidesi', 110),
                ('Hamsi Tava', 'Taze hamsi, misir ununda', 95),
                ('Hamsi Pilavı', 'Hamsi ve pirinc pilavı', 100),
                ('Lahana Sarmasi', 'Kiymali lahana dolmasi', 85),
                ('Karalahana Corbasi', 'Geleneksel karalahana', 50),
            ]),
            ('Tatlilar', 'ph-cake', [
                ('Laz Boregi', 'Geleneksel Laz boregi', 65),
                ('Findikli Baklava', 'Karadeniz findigi ile', 75),
            ]),
            ('Icecekler', 'ph-coffee', [
                ('Rize Cayi', 'Organik Rize cayi', 10),
                ('Linden Cayi', 'Ihlamur cayi', 20),
            ]),
        ],
    },
    # ── 6. Gaziantep Baklavacısı (Pastane · Gaziantep · Growth) ──
    {
        'name': 'Gaziantep Baklavacisi',
        'slug': 'gaziantep-baklavacisi',
        'email': 'info@antepbaklava.com.tr',
        'phone': '+90 342 220 11 22',
        'city': 'Gaziantep', 'district': 'Sehitkamil',
        'owner': ('osman', 'Osman', 'Gunes', 'osman@antepbaklava.com.tr'),
        'staff_count': 3,
        'plan': 'growth',
        'theme': {'name': 'Golden Baklava', 'primary': '#a16207', 'secondary': '#ca8a04', 'bg': '#fefce8', 'text': '#422006', 'accent': '#eab308'},
        'categories': [
            ('Baklavalar', 'ph-cookie', [
                ('Fistikli Baklava', 'Antep fistikli ince yufka baklava (kg)', 650),
                ('Katmer', 'Fistikli katmer, kaymakli', 120),
                ('Burma Kadayif', 'Fistikli burma kadayif', 550),
                ('Sobitli', 'Antep sobitlisi', 500),
                ('Havuc Dilim', 'Havuc dilim baklava', 580),
            ]),
            ('Sutlu Tatlilar', 'ph-bowl-food', [
                ('Kazandibi', 'Geleneksel kazandibi', 65),
                ('Sutlac', 'Firinlanmis sutlac', 55),
                ('Tavuk Gogsu', 'Osmanli tavuk gogsu', 70),
                ('Muhallebi', 'Findik parcali muhallebi', 50),
            ]),
            ('Dondurmalar', 'ph-ice-cream', [
                ('Antep Fistikli', 'Kesme dondurma (2 top)', 65),
                ('Kaymakli', 'Kaymakli kesme dondurma', 55),
                ('Cikolatali', 'Belçika cikolata', 60),
                ('Karisik', 'Uc cesit (3 top)', 80),
            ]),
            ('Sicak Icecekler', 'ph-coffee', [
                ('Turk Kahvesi', 'Antep usulu dibek kahvesi', 45),
                ('Cay', 'Demlik cay', 10),
                ('Salep', 'Sicak salep, tarcin', 40),
            ]),
            ('Soguk Icecekler', 'ph-drop', [
                ('Ayran', 'Ev yapimi ayran', 20),
                ('Limonata', 'Nane limonata', 35),
                ('Salgam', 'Antep salgami', 25),
            ]),
        ],
    },
    # ── 7. Bodrum Beach Club (Beach · Muğla · Professional) ──────
    {
        'name': 'Bodrum Beach Club',
        'slug': 'bodrum-beach-club',
        'email': 'info@bodrumbeach.club',
        'phone': '+90 252 316 77 88',
        'city': 'Mugla', 'district': 'Bodrum',
        'owner': ('sinan', 'Sinan', 'Kilic', 'sinan@bodrumbeach.club'),
        'staff_count': 4,
        'plan': 'professional',
        'theme': {'name': 'Beach Sunset', 'primary': '#0891b2', 'secondary': '#22d3ee', 'bg': '#ecfeff', 'text': '#164e63', 'accent': '#f59e0b'},
        'categories': [
            ('Kahvalti', 'ph-sun', [
                ('Beach Kahvalti', 'Zengin serpme, deniz manzarasi', 350),
                ('Avokado Toast', 'Eksi maya, avokado, yumurta', 130),
                ('Acai Bowl', 'Acai, granola, meyve', 110),
            ]),
            ('Salatalar', 'ph-leaf', [
                ('Sezar Salata', 'Tavuklu sezar salata', 130),
                ('Quinoa Bowl', 'Kinoa, nar, roka, feta', 120),
                ('Ton Balikli Salata', 'Taze ton, yesillik', 160),
            ]),
            ('Burgerler & Sandvicler', 'ph-hamburger', [
                ('Beach Burger', 'Angus kofte, ozel sos', 175),
                ('Tavuk Wrap', 'Izgara tavuk, avokado', 130),
                ('Club Sandwich', 'Klasik club, patates', 145),
            ]),
            ('Deniz Urunleri', 'ph-fish', [
                ('Karides Izgara', 'Jumbo karides, limon tereyag', 280),
                ('Kalamar Tava', 'Citir kalamar, tarator', 180),
                ('Levrek Fileto', 'Izgarada levrek, roka', 320),
            ]),
            ('Cocktails & Icecekler', 'ph-cocktail', [
                ('Mojito', 'Klasik mojito', 140),
                ('Aperol Spritz', 'Aperol, prosecco, soda', 160),
                ('Fresh Limonata', 'Nane limonata', 65),
                ('Smoothie', 'Mevsim meyveli smoothie', 80),
                ('Espresso', 'Double espresso', 55),
            ]),
        ],
    },
    # ── 8. Ankara Şehir Lokantası (Lokanta · Ankara · Growth) ───
    {
        'name': 'Ankara Sehir Lokantasi',
        'slug': 'ankara-sehir-lokantasi',
        'email': 'bilgi@ankarasehir.com.tr',
        'phone': '+90 312 431 22 33',
        'city': 'Ankara', 'district': 'Cankaya',
        'owner': ('selim', 'Selim', 'Polat', 'selim@ankarasehir.com.tr'),
        'staff_count': 3,
        'plan': 'growth',
        'theme': {'name': 'Ankara Stone', 'primary': '#78350f', 'secondary': '#a16207', 'bg': '#fffbeb', 'text': '#1c1917', 'accent': '#d97706'},
        'categories': [
            ('Corbalar', 'ph-bowl-steam', [
                ('Iskembe Corbasi', 'Geleneksel iskembe', 60),
                ('Mercimek Corbasi', 'Kirmizi mercimek', 40),
                ('Tavuk Suyu', 'Sehriyeli tavuk suyu', 45),
            ]),
            ('Et Yemekleri', 'ph-knife', [
                ('Ankara Tavasi', 'Kuzu eti, patates, biber', 160),
                ('Etli Ekmek', 'Ankara usulu etli ekmek', 120),
                ('Kavurma', 'Kuzu kavurma', 155),
                ('Tandir', 'Kuzu tandir, pilav', 180),
                ('Kofte', 'Izgara kofte, pilav, salata', 110),
            ]),
            ('Sebze Yemekleri', 'ph-leaf', [
                ('Karniyarik', 'Kiymali karniyarik', 95),
                ('Turlu', 'Mevsim turlusu', 80),
                ('Bamya', 'Etli bamya', 90),
            ]),
            ('Pilavlar', 'ph-cooking-pot', [
                ('Ic Pilav', 'Fistikli, kuş uzumlu', 45),
                ('Bulgur Pilavi', 'Tereyagli bulgur', 35),
            ]),
            ('Tatlilar', 'ph-cake', [
                ('Kunefe', 'Antep fistikli kunefe', 85),
                ('Revani', 'Sekerli revani', 50),
                ('Kabak Tatlisi', 'Tahinli kabak tatlisi', 55),
            ]),
            ('Icecekler', 'ph-coffee', [
                ('Cay', 'Bardak cay', 10),
                ('Ayran', 'Ayran', 15),
                ('Soda', 'Sade / Meyveli soda', 20),
            ]),
        ],
    },
    # ── 9. Bursa İskender Evi (Kebap · Bursa · Starter) ─────────
    {
        'name': 'Bursa Iskender Evi',
        'slug': 'bursa-iskender-evi',
        'email': 'info@bursaiskender.com.tr',
        'phone': '+90 224 223 44 55',
        'city': 'Bursa', 'district': 'Osmangazi',
        'owner': ('kemal', 'Kemal', 'Bulut', 'kemal@bursaiskender.com.tr'),
        'staff_count': 2,
        'plan': 'starter',
        'theme': {'name': 'Ottoman Burgundy', 'primary': '#881337', 'secondary': '#be123c', 'bg': '#fff1f2', 'text': '#1c1917', 'accent': '#e11d48'},
        'categories': [
            ('Iskenderler', 'ph-fire', [
                ('Iskender Kebap', 'Pide uzerinde doner, tereyag, yogurt', 195),
                ('Porsiyon Iskender', 'Buyuk porsiyon iskender', 260),
                ('Yogurtlu Kebap', 'Yogurt yatagi uzerinde', 180),
            ]),
            ('Kebaplar', 'ph-knife', [
                ('Patlican Kebap', 'Kozlenmis patlican ile', 170),
                ('Adana Kebap', 'Acili kiyma kebap', 155),
                ('Inegol Kofte', 'Bursa inegol koftesi', 130),
                ('Pideli Kofte', 'Pide uzerinde kofte', 140),
            ]),
            ('Pideler', 'ph-bread', [
                ('Kiymali Pide', 'Kiymali taze pide', 100),
                ('Kasarli Pide', 'Kasar peynirli', 90),
                ('Lahmacun', 'Ince hamur lahmacun (3 adet)', 75),
            ]),
            ('Icecekler', 'ph-coffee', [
                ('Ayran', 'Ev yapimi ayran', 15),
                ('Cay', 'Bardak cay', 10),
                ('Sira', 'Taze uzum sirasi', 30),
            ]),
        ],
    },
    # ── 10. Karadeniz Pide Salonu (Pideci · Trabzon · Free) ─────
    {
        'name': 'Karadeniz Pide Salonu',
        'slug': 'karadeniz-pide',
        'email': 'bilgi@karadenizpide.com',
        'phone': '+90 462 321 55 66',
        'city': 'Trabzon', 'district': 'Ortahisar',
        'owner': ('yusuf', 'Yusuf', 'Acar', 'yusuf@karadenizpide.com'),
        'staff_count': 1,
        'plan': 'free',
        'theme': {'name': 'Black Sea Blue', 'primary': '#1e3a5f', 'secondary': '#2563eb', 'bg': '#eff6ff', 'text': '#1e293b', 'accent': '#3b82f6'},
        'categories': [
            ('Pideler', 'ph-bread', [
                ('Trabzon Pidesi', 'Kiymali Karadeniz pidesi', 100),
                ('Kasarli Pide', 'Kasar peynirli pide', 85),
                ('Yumurtali Pide', 'Kasarli yumurtali', 90),
                ('Sucuklu Pide', 'Sucuk, kasar, yumurta', 105),
                ('Kusbasi Pide', 'Dana kusbasi etli', 120),
                ('Karisik Pide', 'Kiymali kasarli karisik', 110),
            ]),
            ('Lahmacun', 'ph-fire', [
                ('Lahmacun', 'Ince hamur lahmacun', 25),
                ('Acili Lahmacun', 'Biberli acili lahmacun', 30),
            ]),
            ('Corbalar', 'ph-bowl-steam', [
                ('Karalahana Corbasi', 'Geleneksel karalahana', 40),
                ('Mercimek Corbasi', 'Kirmizi mercimek', 35),
            ]),
            ('Icecekler', 'ph-coffee', [
                ('Cay', 'Rize cayi', 8),
                ('Ayran', 'Ayran', 12),
            ]),
        ],
    },
    # ── 11. Sahil Kafe (Sahil · Antalya · Growth) ───────────────
    {
        'name': 'Sahil Kafe',
        'slug': 'sahil-kafe-antalya',
        'email': 'info@sahilkafe.com.tr',
        'phone': '+90 242 238 99 00',
        'city': 'Antalya', 'district': 'Konyaalti',
        'owner': ('arda', 'Arda', 'Aydin', 'arda@sahilkafe.com.tr'),
        'staff_count': 3,
        'plan': 'growth',
        'theme': {'name': 'Mediterranean', 'primary': '#0e7490', 'secondary': '#06b6d4', 'bg': '#ecfeff', 'text': '#155e75', 'accent': '#f97316'},
        'categories': [
            ('Kahvalti', 'ph-sun', [
                ('Sahil Kahvalti', 'Serpme kahvalti, deniz manzarasi', 250),
                ('Omlet Cesitleri', 'Peynirli / Sebzeli / Karisik', 85),
                ('Pankek', 'Meyveli pankek, akçaagaç surubu', 90),
            ]),
            ('Sandvicler', 'ph-bread', [
                ('Tost', 'Karisik tost', 65),
                ('Bazlama Tost', 'Bazlamada sucuklu tost', 80),
                ('Waffle Tost', 'Waffle ekmeğinde tost', 90),
            ]),
            ('Soguk Icecekler', 'ph-drop', [
                ('Limonata', 'Ev yapimi limonata', 45),
                ('Frozen', 'Meyveli frozen (mango/cilek)', 55),
                ('Smoothie', 'Detox smoothie', 60),
                ('Buzlu Cay', 'Seftali buzlu cay', 35),
            ]),
            ('Kahveler', 'ph-coffee', [
                ('Latte', 'Klasik latte', 55),
                ('Cappuccino', 'Italyan cappuccino', 55),
                ('Filtre Kahve', 'Gunun filtre kahvesi', 45),
                ('Turk Kahvesi', 'Cezvede pisirilen', 40),
                ('Iced Latte', 'Buzlu latte', 60),
            ]),
            ('Tatlilar', 'ph-cake', [
                ('Waffle', 'Cikolatali meyveli waffle', 85),
                ('Cheesecake', 'Limonlu cheesecake', 75),
                ('Tiramisu', 'Klasik tiramisu', 80),
            ]),
        ],
    },
    # ── 12. İstanbul Steakhouse (Fine Dining · İstanbul · Enterprise)
    {
        'name': 'Istanbul Steakhouse',
        'slug': 'istanbul-steakhouse',
        'email': 'reservation@istanbulsteak.com',
        'phone': '+90 212 233 88 99',
        'city': 'Istanbul', 'district': 'Nisantasi',
        'owner': ('kaan', 'Kaan', 'Erdogan', 'kaan@istanbulsteak.com'),
        'staff_count': 5,
        'plan': 'enterprise',
        'theme': {'name': 'Black Gold', 'primary': '#1c1917', 'secondary': '#292524', 'bg': '#fafaf9', 'text': '#1c1917', 'accent': '#ca8a04'},
        'categories': [
            ('Baslangiclar', 'ph-fork-knife', [
                ('Carpaccio', 'Ince dilim dana, truf yagi, parmesan', 220),
                ('Tuna Tartare', 'Taze ton baligı tartare', 260),
                ('Burrata', 'Taze burrata, domates, fesleğen', 195),
                ('Karides Kokteyl', 'Jumbo karides, kokteyl sosu', 240),
            ]),
            ('Steakler', 'ph-fire', [
                ('Ribeye (300g)', 'Black Angus ribeye, izgara', 650),
                ('NY Strip (250g)', 'New York strip steak', 580),
                ('Filet Mignon (200g)', 'Dana bonfile, truf sos', 720),
                ('T-Bone (400g)', 'T-Bone steak, kemikli', 750),
                ('Wagyu A5 (150g)', 'Japon Wagyu A5 sınıfı', 1500),
                ('Tomahawk (800g)', 'Kemikli tomahawk (2 kişilik)', 1200),
            ]),
            ('Garniturler', 'ph-leaf', [
                ('Truf Patates Puresi', 'Truflu patates puresi', 85),
                ('Izgara Sebzeler', 'Mevsim sebzeleri', 75),
                ('Caesar Salata', 'Klasik sezar, kruton', 95),
                ('Sote Mantar', 'Tereyagli mantar sote', 80),
            ]),
            ('Tatlilar', 'ph-cake', [
                ('Cikolatali Sufle', 'Sicak cikolata sufle, dondurma', 140),
                ('Creme Brulee', 'Klasik creme brulee', 110),
                ('Tiramisu', 'Ozel tarif tiramisu', 120),
            ]),
            ('Saraplar', 'ph-wine', [
                ('Kirmizi Sarap (kadeh)', 'Somelier secimi', 150),
                ('Beyaz Sarap (kadeh)', 'Somelier secimi', 130),
                ('Sampanya (kadeh)', 'Brut sampanya', 200),
            ]),
            ('Kokteyl & Icecekler', 'ph-cocktail', [
                ('Old Fashioned', 'Bourbon, seker, bitters', 180),
                ('Espresso Martini', 'Vodka, espresso, kahlua', 170),
                ('San Pellegrino', 'Italyan maden suyu (750ml)', 65),
            ]),
        ],
    },
]

# ═══════════════════════════════════════════════════════════════════
# PlanDisplayFeature definitions (TR + EN)
# ═══════════════════════════════════════════════════════════════════
PLAN_DISPLAY_FEATURES = {
    'free': [
        ('1 menu, 50 urun', '1 menu, 50 products', True),
        ('3 QR kod', '3 QR codes', False),
        ('2 kullanici', '2 users', False),
        ('100 MB depolama', '100 MB storage', False),
        ('Temel analitik', 'Basic analytics', False),
        ('Siparis yonetimi', 'Order management', False),
        ('Musteri geri bildirimi', 'Customer feedback', False),
        ('E-posta destegi', 'Email support', False),
    ],
    'starter': [
        ('3 menu, 200 urun', '3 menus, 200 products', True),
        ('10 QR kod (ozel tasarim)', '10 QR codes (custom design)', True),
        ('5 kullanici', '5 users', False),
        ('500 MB depolama', '500 MB storage', False),
        ('AI icerik uretimi (100 kredi/ay)', 'AI content generation (100 credits/mo)', False),
        ('Temel analitik dashboard', 'Basic analytics dashboard', False),
        ('Siparis yonetimi', 'Order management', False),
        ('Alerjen yonetimi', 'Allergen management', False),
        ('Musteri geri bildirimi', 'Customer feedback', False),
        ('Canli sohbet destegi', 'Live chat support', False),
    ],
    'growth': [
        ('10 menu, 500 urun', '10 menus, 500 products', True),
        ('50 QR kod', '50 QR codes', True),
        ('15 kullanici, 3 sube', '15 users, 3 branches', True),
        ('2 GB depolama', '2 GB storage', False),
        ('AI icerik uretimi (500 kredi/ay)', 'AI content generation (500 credits/mo)', False),
        ('Gelismis analitik', 'Advanced analytics', False),
        ('API erisimi', 'API access', False),
        ('Coklu dil destegi', 'Multi-language support', False),
        ('Sadakat programi', 'Loyalty program', False),
        ('Canli sohbet destegi', 'Live chat support', False),
    ],
    'professional': [
        ('25 menu, 1.000 urun', '25 menus, 1,000 products', True),
        ('100 QR kod', '100 QR codes', True),
        ('30 kullanici, 5 sube', '30 users, 5 branches', True),
        ('5 GB depolama', '5 GB storage', False),
        ('AI icerik uretimi (1.000 kredi/ay)', 'AI content generation (1,000 credits/mo)', False),
        ('Gelismis analitik ve raporlama', 'Advanced analytics & reporting', False),
        ('Ozel domain', 'Custom domain', False),
        ('White-label (markasiz)', 'White-label (no branding)', False),
        ('API erisimi', 'API access', False),
        ('Coklu dil destegi', 'Multi-language support', False),
        ('Oncelikli destek', 'Priority support', False),
        ('Sadakat programi', 'Loyalty program', False),
    ],
    'enterprise': [
        ('Sinirsiz menu ve urun', 'Unlimited menus & products', True),
        ('Sinirsiz QR kod', 'Unlimited QR codes', True),
        ('Sinirsiz kullanici ve sube', 'Unlimited users & branches', True),
        ('20 GB depolama', '20 GB storage', False),
        ('Sinirsiz AI icerik uretimi', 'Unlimited AI content generation', False),
        ('Ozel hesap yoneticisi', 'Dedicated account manager', False),
        ('SLA garantisi (%99.9)', 'SLA guarantee (99.9%)', False),
        ('7/24 telefon destegi', '24/7 phone support', False),
        ('White-label', 'White-label', False),
        ('Ozel entegrasyon destegi', 'Custom integration support', False),
        ('Yerinde egitim', 'On-site training', False),
        ('Yillik is planlama', 'Annual business planning', False),
    ],
}


# ═══════════════════════════════════════════════════════════════════
# COMMAND
# ═══════════════════════════════════════════════════════════════════
class Command(BaseCommand):
    help = 'Seed comprehensive demo data: 16+ orgs with full operational data'

    def add_arguments(self, parser):
        parser.add_argument('--skip-deps', action='store_true', help='Skip calling dependent seed commands')
        parser.add_argument('--clear', action='store_true', help='Clear new orgs before re-creating')

    def handle(self, *args, **options):
        if options['clear']:
            self._clear_new_orgs()

        if not options['skip_deps']:
            self.stdout.write(self.style.MIGRATE_HEADING('\n══ Running dependent seed commands ══\n'))
            deps = [
                ('seed_roles', 'Roles & permissions'),
                ('seed_plans', 'Plans & features'),
                ('seed_allergens', 'Allergens'),
                ('seed_menu_data', 'Lezzet Sarayi (base org)'),
                ('seed_extra_orgs', 'Extra organizations (+3)'),
                ('seed_all_data', 'Full data for Lezzet Sarayi'),
                ('seed_cms_content', 'CMS website content'),
            ]
            for cmd, label in deps:
                try:
                    self.stdout.write(f'  Running {cmd}...')
                    call_command(cmd, stdout=self.stdout)
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {label}'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  ⚠ {cmd}: {e}'))

        self.stdout.write(self.style.MIGRATE_HEADING('\n══ Fixing PlanDisplayFeature ══\n'))
        self._fix_plan_display_features()

        self.stdout.write(self.style.MIGRATE_HEADING('\n══ Creating 12 new restaurants ══\n'))
        for org_def in NEW_ORGS:
            self._create_full_org(org_def)

        self.stdout.write(self.style.SUCCESS('\n🎉 All demo data seeded successfully!\n'))

    # ───────────────────────────────────────────────────────────────
    # CLEAR
    # ───────────────────────────────────────────────────────────────
    def _clear_new_orgs(self):
        from apps.core.models import Organization
        self.stdout.write(self.style.WARNING('Clearing new organizations...'))
        slugs = [o['slug'] for o in NEW_ORGS]
        for slug in slugs:
            try:
                org = Organization.objects.get(slug=slug)
                # Delete all related data via cascade
                User.objects.filter(organization=org).delete()
                org.delete()
                self.stdout.write(f'  Deleted: {slug}')
            except Organization.DoesNotExist:
                pass
        self.stdout.write(self.style.WARNING('  Cleared!'))

    # ───────────────────────────────────────────────────────────────
    # PLAN DISPLAY FEATURES
    # ───────────────────────────────────────────────────────────────
    def _fix_plan_display_features(self):
        from apps.subscriptions.models import Plan
        from apps.website.models import PlanDisplayFeature

        for slug, features in PLAN_DISPLAY_FEATURES.items():
            plan = Plan.objects.filter(slug=slug).first()
            if not plan:
                self.stdout.write(f'  Plan not found: {slug}')
                continue

            # Clear existing and recreate for accuracy
            PlanDisplayFeature.objects.filter(plan=plan).delete()

            for idx, feat in enumerate(features, start=1):
                text_tr, text_en, highlighted = feat
                PlanDisplayFeature.objects.create(
                    plan=plan,
                    text_tr=text_tr,
                    text_en=text_en,
                    is_highlighted=highlighted,
                    sort_order=idx,
                    is_active=True,
                )
            self.stdout.write(self.style.SUCCESS(f'  ✓ {plan.name}: {len(features)} display features'))

    # ───────────────────────────────────────────────────────────────
    # FULL ORG CREATION
    # ───────────────────────────────────────────────────────────────
    def _create_full_org(self, od):
        self.stdout.write(f'\n  ── {od["name"]} ({od["city"]}) ──')

        org = self._create_org(od)
        owner = self._create_owner(org, od)
        staff = self._create_staff(org, owner, od)
        self._assign_roles(org, owner, staff)
        branch = self._create_branch(org, od)
        theme = self._create_theme(org, od)
        menu = self._create_menu(org, theme, od)
        products = self._create_categories_products(org, menu, od)
        zones = self._create_zones(org, branch)
        tables = self._create_tables(org, zones)
        self._create_qr_codes(org, tables, menu)
        customers = self._create_customers(org)
        orders = self._create_orders(org, tables, customers, staff + [owner], products)
        self._create_feedback(org, customers, orders)
        self._create_subscription(org, od)
        self._create_notifications(org, owner)

        self.stdout.write(self.style.SUCCESS(f'  ✓ {od["name"]}: done'))

    # ───────────────────────────────────────────────────────────────
    def _create_org(self, od):
        from apps.core.models import Organization
        org, created = Organization.objects.get_or_create(
            slug=od['slug'],
            defaults={
                'name': od['name'],
                'email': od['email'],
                'phone': od['phone'],
                'status': 'ACTIVE',
                'settings': {'currency': 'TRY', 'timezone': 'Europe/Istanbul'},
            },
        )
        if created:
            self.stdout.write(f'    + Org: {org.name}')
        return org

    # ───────────────────────────────────────────────────────────────
    def _create_owner(self, org, od):
        _, fn, ln, email = od['owner']
        owner, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': fn,
                'last_name': ln,
                'organization': org,
                'is_staff': True,
                'status': 'ACTIVE',
            },
        )
        if created:
            owner.set_password('Owner1234!emenum')
            owner.save()
        return owner

    # ───────────────────────────────────────────────────────────────
    def _create_staff(self, org, owner, od):
        staff_users = []
        domain = od['email'].split('@')[1]
        for i in range(od['staff_count']):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            email = f'{fn.lower()}.{ln.lower()}@{domain}'
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': fn,
                    'last_name': ln,
                    'organization': org,
                    'is_staff': i == 0,  # first staff member is manager
                    'status': 'ACTIVE',
                    'phone': f'+90 5{random.randint(30,59)} {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}',
                },
            )
            if created:
                user.set_password('Staff1234!emenum')
                user.save()
            staff_users.append(user)
        return staff_users

    # ───────────────────────────────────────────────────────────────
    def _assign_roles(self, org, owner, staff):
        from apps.core.models import Role, UserRole

        owner_role = Role.objects.filter(name='owner', scope='ORGANIZATION').first()
        if owner_role:
            UserRole.objects.get_or_create(
                user=owner, role=owner_role, organization=org,
                defaults={'granted_by': owner},
            )

        role_names = ['manager'] + ['staff'] * max(0, len(staff) - 2) + ['viewer']
        for i, user in enumerate(staff):
            rn = role_names[min(i, len(role_names) - 1)]
            role = Role.objects.filter(name=rn, scope='ORGANIZATION').first()
            if role:
                UserRole.objects.get_or_create(
                    user=user, role=role, organization=org,
                    defaults={'granted_by': owner},
                )

    # ───────────────────────────────────────────────────────────────
    def _create_branch(self, org, od):
        from apps.core.models import Branch
        branch, _ = Branch.objects.get_or_create(
            organization=org, slug=f'{od["slug"]}-merkez',
            defaults={
                'name': f'{od["name"]} Merkez',
                'address': f'{od["district"]} Mah. Ataturk Cad. No:{random.randint(1, 120)}',
                'city': od['city'],
                'district': od['district'],
                'postal_code': f'{random.randint(10, 99)}{random.randint(100, 999)}',
                'country': 'TR',
                'phone': od['phone'],
                'email': od['email'],
                'is_main': True,
                'status': 'ACTIVE',
                'operating_hours': {
                    d: {'open': '10:00', 'close': '22:00'}
                    for d in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                },
            },
        )
        return branch

    # ───────────────────────────────────────────────────────────────
    def _create_theme(self, org, od):
        from apps.menu.models import Theme
        td = od['theme']
        theme, _ = Theme.objects.get_or_create(
            organization=org, slug=slugify(td['name']),
            defaults={
                'name': td['name'],
                'primary_color': td['primary'],
                'secondary_color': td['secondary'],
                'background_color': td['bg'],
                'text_color': td['text'],
                'accent_color': td['accent'],
                'is_default': True,
                'is_active': True,
            },
        )
        return theme

    # ───────────────────────────────────────────────────────────────
    def _create_menu(self, org, theme, od):
        from apps.menu.models import Menu
        menu, _ = Menu.objects.get_or_create(
            organization=org, slug=f'{od["slug"]}-menu',
            defaults={
                'name': f'{od["name"]} Menu',
                'description': f'{od["name"]} ana menusu',
                'is_published': True,
                'published_at': _rp(30),
                'is_default': True,
                'theme': theme,
            },
        )
        return menu

    # ───────────────────────────────────────────────────────────────
    def _create_categories_products(self, org, menu, od):
        from apps.menu.models import Category, Product, ProductVariant, ProductModifier, Allergen, ProductAllergen

        allergens = list(Allergen.objects.filter(deleted_at__isnull=True))
        all_products = []

        for sort_idx, (cat_name, cat_icon, prods) in enumerate(od['categories']):
            cat_slug = slugify(cat_name)[:50]
            # Make slug unique within this org/menu
            cat_slug_full = f'{cat_slug}-{od["slug"][:8]}'
            cat, _ = Category.objects.get_or_create(
                organization=org, menu=menu, slug=cat_slug_full,
                defaults={
                    'name': cat_name,
                    'icon': cat_icon,
                    'is_active': True,
                    'sort_order': sort_idx * 10,
                },
            )

            for prod_idx, (pname, pdesc, pprice) in enumerate(prods):
                pslug = slugify(pname)[:45]
                pslug_full = f'{pslug}-{od["slug"][:5]}'
                prod, created = Product.objects.get_or_create(
                    organization=org, category=cat, slug=pslug_full,
                    defaults={
                        'name': pname,
                        'description': pdesc,
                        'short_description': pdesc[:100],
                        'base_price': Decimal(str(pprice)),
                        'currency': 'TRY',
                        'is_active': True,
                        'is_available': random.random() > 0.05,
                        'is_featured': random.random() > 0.85,
                        'is_chef_recommended': random.random() > 0.9,
                        'sort_order': prod_idx * 10,
                        'preparation_time': random.choice([5, 10, 15, 20, 25]),
                        'calories': random.randint(80, 800) if random.random() > 0.4 else None,
                    },
                )
                all_products.append(prod)

                # Random allergens
                if created and allergens and random.random() > 0.6:
                    for a in random.sample(allergens, min(random.randint(1, 2), len(allergens))):
                        ProductAllergen.objects.get_or_create(
                            product=prod, allergen=a,
                            defaults={'severity': random.choice(['contains', 'may_contain', 'traces'])},
                        )

                # Add variants to ~20% of products
                if created and random.random() > 0.8:
                    for vi, (vn, vp) in enumerate([('Kucuk', pprice - 20), ('Buyuk', pprice + 30)]):
                        if vp > 0:
                            ProductVariant.objects.get_or_create(
                                product=prod, name=vn,
                                defaults={
                                    'price': Decimal(str(max(vp, 10))),
                                    'is_default': vi == 0,
                                    'is_available': True,
                                    'sort_order': vi,
                                },
                            )

                # Add modifiers to ~15% of products
                if created and random.random() > 0.85:
                    mods = [('Ekstra Peynir', 15), ('Sos Ekle', 10), ('Buyuk Porsiyon', 25)]
                    for mi, (mn, mp) in enumerate(mods[:random.randint(1, 3)]):
                        ProductModifier.objects.get_or_create(
                            product=prod, name=mn,
                            defaults={
                                'price': Decimal(str(mp)),
                                'is_default': False,
                                'is_required': False,
                                'sort_order': mi,
                            },
                        )

        return all_products

    # ───────────────────────────────────────────────────────────────
    def _create_zones(self, org, branch):
        from apps.orders.models import Zone

        zone_defs = [
            ('Ic Mekan', f'ic-mekan-{org.slug[:10]}', '#3B82F6', 'ph-fill ph-house', 40, False),
            ('Bahce', f'bahce-{org.slug[:10]}', '#10B981', 'ph-fill ph-tree', 24, True),
            ('Teras', f'teras-{org.slug[:10]}', '#8B5CF6', 'ph-fill ph-sun', 16, True),
        ]
        zones = []
        for i, (name, slug, color, icon, cap, outdoor) in enumerate(zone_defs):
            z, _ = Zone.objects.get_or_create(
                organization=org, slug=slug,
                defaults={
                    'name': name, 'color': color, 'icon': icon,
                    'capacity': cap, 'is_outdoor': outdoor,
                    'is_smoking_allowed': outdoor,
                    'is_reservable': True, 'branch': branch,
                    'sort_order': i,
                },
            )
            zones.append(z)
        return zones

    # ───────────────────────────────────────────────────────────────
    def _create_tables(self, org, zones):
        from apps.orders.models import Table

        statuses = ['AVAILABLE', 'AVAILABLE', 'AVAILABLE', 'OCCUPIED', 'RESERVED']
        tables = []
        num = 1
        counts = [8, 5, 3]  # per zone
        for zi, zone in enumerate(zones):
            for j in range(counts[min(zi, len(counts) - 1)]):
                slug = f'masa-{num}-{org.slug[:8]}'
                t, _ = Table.objects.get_or_create(
                    organization=org, slug=slug,
                    defaults={
                        'zone': zone, 'branch': zone.branch,
                        'name': f'Masa {num}', 'number': num,
                        'capacity': random.randint(2, 6),
                        'min_capacity': 1,
                        'status': random.choice(statuses),
                        'sort_order': num,
                    },
                )
                tables.append(t)
                num += 1
        return tables

    # ───────────────────────────────────────────────────────────────
    def _create_qr_codes(self, org, tables, menu):
        from apps.orders.models import QRCode

        for table in tables:
            code = f'{org.slug[:6].upper()}-{table.number:03d}-{uuid.uuid4().hex[:4].upper()}'
            QRCode.objects.get_or_create(
                organization=org, code=code,
                defaults={
                    'branch': table.branch, 'menu': menu, 'table': table,
                    'type': 'TABLE',
                    'name': f'QR - {table.name}',
                    'short_url': f'https://e-menum.net/q/{code}',
                    'redirect_url': f'https://e-menum.net/m/{org.slug}/?table={table.number}',
                    'scan_count': random.randint(5, 150),
                    'unique_scan_count': random.randint(3, 80),
                    'last_scanned_at': _rr(72),
                },
            )

    # ───────────────────────────────────────────────────────────────
    def _create_customers(self, org):
        from apps.customers.models import Customer

        customers = []
        for _ in range(random.randint(5, 10)):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            email = f'{fn.lower()}.{ln.lower()}{random.randint(1,99)}@gmail.com'
            cust, _ = Customer.objects.get_or_create(
                organization=org, email=email,
                defaults={
                    'name': f'{fn} {ln}',
                    'phone': f'+90 5{random.randint(30,59)} {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}',
                    'source': random.choice(['QR_SCAN', 'QR_SCAN', 'WEB', 'STAFF']),
                    'total_orders': random.randint(1, 20),
                    'total_spent': Decimal(str(random.randint(100, 5000))),
                    'loyalty_points_balance': random.randint(0, 500),
                },
            )
            customers.append(cust)
        return customers

    # ───────────────────────────────────────────────────────────────
    def _create_orders(self, org, tables, customers, staff, products):
        from apps.orders.models import Order, OrderItem

        if not products:
            return []

        order_statuses = ['COMPLETED', 'COMPLETED', 'COMPLETED', 'PENDING', 'CONFIRMED',
                          'PREPARING', 'READY', 'DELIVERED', 'CANCELLED']
        payment_methods = ['CASH', 'CREDIT_CARD', 'CREDIT_CARD', 'DEBIT_CARD']
        orders = []

        for i in range(random.randint(8, 15)):
            order_num = f'ORD-{org.slug[:4].upper()}-{i + 1:04d}'
            status = random.choice(order_statuses)
            table = random.choice(tables) if tables else None
            customer = random.choice(customers) if customers and random.random() > 0.3 else None
            placed_by = random.choice(staff) if staff else None

            order, created = Order.objects.get_or_create(
                organization=org, order_number=order_num,
                defaults={
                    'branch': table.branch if table else None,
                    'table': table,
                    'customer': customer,
                    'status': status,
                    'type': random.choice(['DINE_IN', 'DINE_IN', 'DINE_IN', 'TAKEAWAY']),
                    'payment_status': 'PAID' if status == 'COMPLETED' else 'PENDING',
                    'payment_method': random.choice(payment_methods) if status == 'COMPLETED' else 'CASH',
                    'subtotal': Decimal('0'),
                    'tax_amount': Decimal('0'),
                    'total_amount': Decimal('0'),
                    'guest_count': random.randint(1, 6),
                    'placed_by': placed_by,
                    'assigned_to': random.choice(staff) if staff else None,
                    'placed_at': _rp(30),
                },
            )

            if created:
                # Add order items
                subtotal = Decimal('0')
                item_count = random.randint(2, 5)
                selected = random.sample(products, min(item_count, len(products)))
                for pi, prod in enumerate(selected):
                    qty = random.randint(1, 3)
                    unit_price = prod.base_price
                    line_total = unit_price * qty
                    subtotal += line_total
                    OrderItem.objects.create(
                        order=order,
                        product=prod,
                        quantity=qty,
                        unit_price=unit_price,
                        total_price=line_total,
                        status='DELIVERED' if status == 'COMPLETED' else 'PENDING',
                    )

                tax = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
                order.subtotal = subtotal
                order.tax_amount = tax
                order.total_amount = subtotal + tax
                order.save(update_fields=['subtotal', 'tax_amount', 'total_amount'])

            orders.append(order)

        return orders

    # ───────────────────────────────────────────────────────────────
    def _create_feedback(self, org, customers, orders):
        from apps.customers.models import Feedback

        # Skip if we already have feedback for this org
        if Feedback.objects.filter(organization=org).exists():
            return

        for _ in range(random.randint(3, 8)):
            customer = random.choice(customers) if customers else None
            Feedback.objects.create(
                organization=org,
                customer=customer,
                feedback_type=random.choice(['FOOD', 'SERVICE', 'AMBIANCE', 'GENERAL']),
                rating=random.randint(3, 5),
                comment=random.choice(FEEDBACK_TR),
                status=random.choice(['PENDING', 'REVIEWED', 'RESPONDED']),
            )

    # ───────────────────────────────────────────────────────────────
    def _create_subscription(self, org, od):
        from apps.subscriptions.models import Plan, Subscription, Invoice

        plan = Plan.objects.filter(slug=od['plan']).first()
        if not plan:
            return

        sub, created = Subscription.objects.get_or_create(
            organization=org,
            defaults={
                'plan': plan,
                'status': 'ACTIVE' if od['plan'] != 'free' else 'ACTIVE',
                'billing_period': 'MONTHLY',
                'current_price': plan.price_monthly,
                'current_period_start': _rp(25),
                'current_period_end': now() + timedelta(days=5),
                'next_billing_date': now() + timedelta(days=5),
            },
        )

        # Create invoices for paid plans
        if created and od['plan'] != 'free':
            for m in range(3):
                inv_num = f'INV-{org.slug[:4].upper()}-2026-{m + 1:05d}'
                ps = now() - timedelta(days=30 * (3 - m))
                pe = ps + timedelta(days=30)
                Invoice.objects.get_or_create(
                    organization=org, invoice_number=inv_num,
                    defaults={
                        'subscription': sub,
                        'status': 'PAID' if m < 2 else 'PENDING',
                        'amount_subtotal': plan.price_monthly,
                        'amount_tax': (plan.price_monthly * Decimal('0.20')).quantize(Decimal('0.01')),
                        'amount_total': (plan.price_monthly * Decimal('1.20')).quantize(Decimal('0.01')),
                        'amount_paid': plan.price_monthly * Decimal('1.20') if m < 2 else Decimal('0'),
                        'due_date': pe,
                        'paid_at': ps + timedelta(days=2) if m < 2 else None,
                        'period_start': ps,
                        'period_end': pe,
                        'currency': 'TRY',
                    },
                )

    # ───────────────────────────────────────────────────────────────
    def _create_notifications(self, org, owner):
        from apps.notifications.models import Notification

        notifs = [
            ('Yeni siparis alindi', 'ORDER', 'NORMAL'),
            ('Musteri geri bildirimi', 'FEEDBACK', 'NORMAL'),
            ('Odeme alindi', 'PAYMENT', 'NORMAL'),
            ('Abonelik yenilendi', 'SYSTEM', 'LOW'),
            ('Yeni musteri kaydi', 'SYSTEM', 'LOW'),
        ]
        for title, ntype, priority in notifs:
            Notification.objects.get_or_create(
                organization=org,
                user=owner,
                title=title,
                defaults={
                    'notification_type': ntype,
                    'priority': priority,
                    'message': f'{title} - {org.name}',
                    'status': random.choice(['PENDING', 'SENT', 'DELIVERED', 'READ']),
                },
            )
