# E-Menum Codebase Audit & Vibecoding Yonerge
# Tarih: 2026-02-24
# Kapsam: Tum katmanlar — DB modelleri, backend servisler, frontend, config, static dosyalar

---

## OZET

| Kategori | Tespit Sayisi |
|----------|---------------|
| KRITIK (Uretimi kirar) | 6 |
| YUKSEK (Onemli eksiklik) | 8 |
| ORTA (Tamamlanmasi gereken) | 7 |
| DUSUK (Iyilestirme) | 5 |
| **TOPLAM** | **26** |

---

## KATMAN-1: KRITIK — Uretimi Kirar

### K-01: requirements.txt Eksik Paketler

**Durum:** Settings ve koddaki importlar var ama requirements.txt'te paket yok. `pip install` yapildiginda uygulama CALISMAZM.

**Eksik paketler:**
```
django-modeltranslation>=0.18    # INSTALLED_APPS satirinda var, admin kullanyor
django-celery-beat>=2.5          # config/celery.py'de scheduler olarak ayarli
django-filer>=3.0                # INSTALLED_APPS'te var, core/signals.py import ediyor
easy-thumbnails>=2.8             # filer bagimliligi, INSTALLED_APPS'te var
```

**Dosya:** `requirements.txt`

**Cozum:**
```bash
# requirements.txt'e ekle:
django-modeltranslation>=0.18
django-celery-beat>=2.5
django-filer>=3.0
easy-thumbnails>=2.8
```

---

### K-02: Celery Beat Gorevleri Eksik — 3 Dosya Yok

**Durum:** `config/celery.py` icinde schedule tanimli ama tasks.py dosyalari YOK. Celery beat basladiginda ImportError alir.

| Gorev Adi | Beklenen Dosya | Durum |
|-----------|---------------|-------|
| `core.tasks.cleanup_expired_sessions` | `apps/core/tasks.py` | YOK |
| `core.tasks.cleanup_soft_deleted_records` | `apps/core/tasks.py` | YOK |
| `subscriptions.tasks.check_expiring_subscriptions` | `apps/subscriptions/tasks.py` | YOK |
| `notifications.tasks.send_weekly_digest` | `apps/notifications/tasks.py` | YOK |

**Dosya:** `config/celery.py` (satir ~50-80)

**Cozum:** Her biri icin tasks.py olustur:

```python
# apps/core/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task(name='core.tasks.cleanup_expired_sessions')
def cleanup_expired_sessions():
    """Suresi dolmus session kayitlarini temizle"""
    from django.contrib.sessions.models import Session
    Session.objects.filter(expire_date__lt=timezone.now()).delete()

@shared_task(name='core.tasks.cleanup_soft_deleted_records')
def cleanup_soft_deleted_records():
    """30 gunluk soft-delete kayitlari kalici sil (GDPR uyumlu)"""
    from apps.core.models import AuditLog
    cutoff = timezone.now() - timedelta(days=30)
    # Her model icin deletedAt < cutoff olanlari sil
    pass  # TODO: Tum soft-delete modelleri tara
```

```python
# apps/subscriptions/tasks.py
from celery import shared_task

@shared_task(name='subscriptions.tasks.check_expiring_subscriptions')
def check_expiring_subscriptions():
    """7 gun icinde bitecek aboneliklere bildirim gonder"""
    from apps.subscriptions.models import Subscription
    from django.utils import timezone
    from datetime import timedelta
    expiring = Subscription.objects.filter(
        end_date__lte=timezone.now() + timedelta(days=7),
        end_date__gt=timezone.now(),
        status='active'
    )
    for sub in expiring:
        pass  # TODO: Notification olustur
```

```python
# apps/notifications/tasks.py
from celery import shared_task

@shared_task(name='notifications.tasks.send_weekly_digest')
def send_weekly_digest():
    """Haftalik ozet e-posta gonder"""
    from apps.core.models import User
    users = User.objects.filter(is_active=True)
    for user in users:
        pass  # TODO: Digest email olustur ve gonder
```

---

### K-03: Import Hatasi — core/signals.py

**Durum:** `apps/core/signals.py` icinde `from filer.models import Folder` import var ama `django-filer` requirements.txt'te YOK.

**Dosya:** `apps/core/signals.py`

**Cozum:** K-01'deki filer paketini requirements.txt'e ekle. Alternatif: filer kullanilmayacaksa importu kaldir ve ilgili signal kodunu devre disi birak.

---

### K-04: 10 Eksik Static Dosya — UI Kirik

**Durum:** Template'ler `{% static '...' %}` ile referans veriyor ama dosyalar FIZIKSEL olarak YOK. Tarayicida 404 hatasi verir.

| Dosya | Referans Veren Template | Oncelik |
|-------|------------------------|---------|
| `static/css/tailwind.min.css` | `layouts/base.html` | EN KRITIK — Tum sayfalari etkiler |
| `static/images/favicon.svg` | `layouts/base.html` | Yuksek — Favicon eksik |
| `static/images/logo.svg` | `layouts/admin.html` | Yuksek — Admin logo eksik |
| `static/images/apple-touch-icon.png` | `layouts/base.html` | Orta |
| `static/images/og-default.png` | `layouts/base.html` | Orta — Social media paylasimda gorsel yok |
| `static/admin/css/base.css` | `admin/base.html` | Yuksek — Admin panel stili |
| `static/admin/css/changelists.css` | `admin/change_list.html` | Orta |
| `static/admin/css/forms.css` | `admin/change_form.html` | Orta |
| `static/admin/js/change_form.js` | `admin/change_form.html` | Orta |
| `static/admin/js/filters.js` | `admin/change_list.html` | Orta |

**Cozum:**
1. `static/css/tailwind.min.css` — Tailwind build pipeline kur veya CDN link kullan
2. `static/images/` — Logo, favicon, OG image tasarlat ve ekle
3. `static/admin/css/` ve `static/admin/js/` — Custom admin stilleri olustur veya Django default'lara birak

---

### K-05: django_filters Konfigurasyonu Tutarsiz

**Durum:** REST_FRAMEWORK settings'te `DjangoFilterBackend` aktif ama `django_filters` INSTALLED_APPS'te YORUM SATIRI icinde.

**Dosya:** `config/settings/base.py`
- Satir ~141: `# 'django_filters',` (yorum)
- Satir ~341: `'django_filters.rest_framework.DjangoFilterBackend'` (aktif)

**Cozum:** Yorum isaretini kaldir:
```python
THIRD_PARTY_APPS = [
    ...
    'django_filters',  # Yorum isaretini kaldir
    ...
]
```

---

### K-06: CORS Middleware Devre Disi

**Durum:** `django-cors-headers` requirements.txt'te var ama hem INSTALLED_APPS hem MIDDLEWARE'de yorum satiri icinde. API cross-origin istekleri REDDEDILIR.

**Dosya:** `config/settings/base.py`
- `'corsheaders'` INSTALLED_APPS'te yorum
- `'corsheaders.middleware.CorsMiddleware'` MIDDLEWARE'de yorum

**Cozum:** Uretim icin CORS ayarla:
```python
INSTALLED_APPS = [..., 'corsheaders', ...]
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware', ...]  # SecurityMiddleware'den sonra
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
```

---

## KATMAN-2: YUKSEK — Onemli Eksiklik

### Y-01: Analytics App — Model Var, Backend YOK

**Durum:** 4 model tanimli ama admin, views, serializers HIC YOK. Tamamen bos bir kabuk.

| Bilesentler | Durum |
|-------------|-------|
| Models (4) | DashboardMetric, SalesAggregation, ProductPerformance, CustomerMetric |
| Admin | YOK — admin.py bos veya yok |
| Views | YOK |
| Serializers | YOK |
| Tasks | VAR (aggregate_hourly_analytics) |

**Dosya:** `apps/analytics/`

**Cozum:**
1. `apps/analytics/admin.py` — 4 model icin admin kaydi
2. `apps/analytics/serializers.py` — DRF serializer'lar
3. `apps/analytics/views.py` — Okuma view'lari (ListAPIView, RetrieveAPIView)
4. URL'leri `apps/analytics/urls.py`'ye ekle

---

### Y-02: Media App — Model Var, Backend YOK

**Durum:** MediaFolder ve Media modeli var ama views/serializers YOK. Dosya yuklenemiyor.

| Bilesentler | Durum |
|-------------|-------|
| Models (2) | MediaFolder, Media |
| Admin | VAR (2 kayit) |
| Views | YOK |
| Serializers | YOK |
| URLs | VAR ama bos |

**Dosya:** `apps/media/`

**Cozum:**
1. `apps/media/serializers.py` — Upload/list serializer'lar
2. `apps/media/views.py` — FileUploadView, MediaListView, MediaDeleteView
3. S3 veya local storage backend ayarla
4. URL'leri guncelle

---

### Y-03: SEO App — 9 Model, Admin Var, API YOK

**Durum:** 9 model + 8 admin kaydi + middleware'ler var ama DRF API view'lari YOK. Admin disinda yonetilemez.

| Bilesentler | Durum |
|-------------|-------|
| Models (9) | SEOMixin, AuthorProfile, Redirect, BrokenLink, TXTFileConfig, PSEOTemplate, PSEOPage, NotFound404Log, CrawlReport |
| Admin | VAR (8 kayit) |
| Views | YOK (sadece middleware'ler) |
| Serializers | YOK |
| Tasks | VAR |
| Signals | VAR |

**Dosya:** `apps/seo/`

**Cozum:** Bu app middleware+admin odakli calisiyor, API opsiyonel. Ama en azindan:
1. Redirect yonetimi icin API endpoint
2. BrokenLink raporu icin API endpoint
3. CrawlReport durumu icin API endpoint

---

### Y-04: SEO Shield App — urls.py YOK

**Durum:** 4 model + admin + tasks + signals var ama `urls.py` yok. URL routing'e dahil edilemiyor.

**Dosya:** `apps/seo_shield/`

**Cozum:** Eger API gerekli degilse (sadece middleware), urls.py bos birak ama olustur. Eger admin API gerekiyorsa:
```python
# apps/seo_shield/urls.py
from django.urls import path
urlpatterns = []  # Middleware-only app
```

---

### Y-05: Website App — 31 Model, Frontend Template Var, Views/API YOK

**Durum:** En buyuk model sayisina sahip app (31 model), template'ler var ama views.py'de view class'lari YOK veya yetersiz.

**Not:** Plan dosyasina gore website views/ package olusturulacak (Faz 4'te). Bu yonerge o plan ile UYUMLU olmali.

| Bilesentler | Durum |
|-------------|-------|
| Models (31) | Website CMS modelleri (forms, content, features, social_proof, solutions, customers, partners vb.) |
| Admin | VAR (37 kayit — mevcut) |
| Views | YOK veya yetersiz |
| Serializers | YOK (SSR app, serializer gerekmez) |
| Templates | VAR (48 dosya) |
| Tasks | VAR |

**Dosya:** `apps/website/`

**Cozum:** Plan Faz 4'e gore views/ package olustur:
- home.py, features.py, pricing.py, about.py, blog.py, contact.py, legal.py
- solutions.py, customers.py, resources.py, company.py, investor.py, partners.py, support.py

---

### Y-06: Dashboard App — API Views Var, DRF Serializer YOK

**Durum:** 2 model + admin var. Custom API views (JsonResponse) var ama DRF serializer yok.

| Bilesentler | Durum |
|-------------|-------|
| Models (2) | DashboardInsight, UserPreference |
| Admin | VAR (2 kayit) |
| Views | VAR (custom JsonResponse views) |
| Serializers | YOK |
| Tasks | VAR |

**Dosya:** `apps/dashboard/`

**Cozum:** Opsiyonel — mevcut JsonResponse API'lari calisiyor. Eger standartlastirmak istiyorsan DRF serializer'lar ekle.

---

### Y-07: WhiteNoise Middleware Devre Disi

**Durum:** WhiteNoise requirements.txt'te var ama middleware yorum satiri icinde. Production'da Django static dosyalari sunMAZ, Nginx gerekir.

**Dosya:** `config/settings/base.py`

**Cozum:** Ya WhiteNoise'u aktif et (Docker icinde pratik):
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Aktif et
    ...
]
```
Ya da Nginx'in static dosyalari sunmasini sagla (huseyin-v2.md'de zaten var).

---

### Y-08: Guardian Yorum Satiri — Object-Level Permission YOK

**Durum:** `django-guardian` requirements.txt'te var ama INSTALLED_APPS'te yorum. Object-level permission calismaz.

**Dosya:** `config/settings/base.py`

**Cozum:** Aktif et:
```python
INSTALLED_APPS = [..., 'guardian', ...]
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]
```

---

## KATMAN-3: ORTA — Tamamlanmasi Gereken

### O-01: Notifications App — Minimal (1 Model, 1 View, 2 Serializer)

**Durum:** Sadece 1 Notification modeli var. Push notification, email notification, in-app notification altyapisi eksik.

**Dosya:** `apps/notifications/`

**Cozum:**
1. NotificationType modeli ekle (email, push, in-app, sms)
2. NotificationPreference modeli ekle (kullanicinin bildirim tercihleri)
3. NotificationTemplate modeli ekle (sablonlar)
4. Email gonderme servisi
5. tasks.py (K-02'de olusturulacak)

---

### O-02: Customers App — 6 Model, 2 View, 8 Serializer

**Durum:** Model ve serializer'lar var ama sadece 2 view. CRUD tam degil.

**Dosya:** `apps/customers/`

**Cozum:** Eksik view'lari ekle:
- CustomerListView, CustomerDetailView, CustomerUpdateView
- FeedbackCreateView
- LoyaltyPointHistoryView
- NPSSurveyCreateView

---

### O-03: Campaigns App — 4 Model, 4 View, 4 Serializer

**Durum:** Temel CRUD var ama tasks.py YOK. Kampanya zamanlama ve otomatik kupon dagitimi icin async gorevler gerekli.

**Dosya:** `apps/campaigns/`

**Cozum:**
```python
# apps/campaigns/tasks.py
@shared_task
def activate_scheduled_campaigns():
    """Zamani gelen kampanyalari aktif et"""
    pass

@shared_task
def expire_ended_campaigns():
    """Biten kampanyalari deaktif et"""
    pass
```

---

### O-04: AI App — 2 Model, 5 View, Serializer YOK

**Durum:** View'lar mevcut ama DRF serializer yok. Validation eksik olabilir.

**Dosya:** `apps/ai/`

**Cozum:**
1. `apps/ai/serializers.py` olustur
2. AIGenerationSerializer, AIProviderConfigSerializer
3. View'larda serializer_class ata

---

### O-05: admin/includes/fieldset.html Eksik

**Durum:** `admin/menu/product/change_form.html` bu template'i referans aliyor ama dosya yok.

**Dosya:** `templates/admin/includes/fieldset.html`

**Cozum:** Django'nun default fieldset.html'i kullaniliyor olabilir. Eger custom fieldset gerekiyorsa olustur, degilse referansi kaldir.

---

### O-06: Reporting App — TODO'lar

**Durum:** `apps/reporting/services/scheduler_service.py` icinde 3 TODO var:
- Email delivery via notifications app
- Push notification
- Webhook delivery

**Dosya:** `apps/reporting/services/scheduler_service.py`

**Cozum:** Notifications app tamamlaninca (O-01) buradaki TODO'lari implement et.

---

### O-07: Core Model TODO

**Durum:** `apps/core/models.py` icinde TODO: "Add plan FK when subscriptions app is created"

**Dosya:** `apps/core/models.py`

**Cozum:** Subscriptions app zaten var. Organization modeline plan FK ekle:
```python
class Organization(models.Model):
    ...
    subscription = models.OneToOneField(
        'subscriptions.Subscription',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='organization'
    )
```

---

## KATMAN-4: DUSUK — Iyilestirme

### D-01: Diger App'ler Icin translation.py Eksik

**Durum:** Sadece website app'inin translation.py dosyasi var (475 satir, 46 model kaydi). Diger app'ler (menu, orders, subscriptions vb.) icin model-level translation YOK.

**Cozum:** Gerekirse diger app'ler icin translation.py ekle. Oncelik: menu app (urun isimleri, aciklamalari cok dilli olmali).

---

### D-02: Signals.py Sadece 3 App'te Var

**Durum:** Sadece core, seo, seo_shield'da signals.py var. Domain event'leri yeterince kullanilmiyor.

**Cozum:** Onemli domain event'leri icin signal ekle:
- `orders` — siparis olusturuldu, iptal edildi
- `subscriptions` — abonelik basladi, bitti
- `customers` — yeni musteri, sadakat puani kazandi

---

### D-03: Test Dosyalari Eksik App'ler

**Durum:** Bazi app'lerin tests.py veya tests/ dizini bos. Test coverage dusuk olabilir.

**Cozum:** Her app icin minimum unit test yaz:
- Model creation testleri
- Admin panel testleri
- API endpoint testleri (varsa)

---

### D-04: requirements-dev.txt Eksik

**Durum:** Dockerfile'da `COPY requirements-dev.txt .` var ama dosyanin var olup olmadigi kontrol edilmeli.

**Cozum:** Yoksa olustur:
```
# requirements-dev.txt
pytest>=7.0
pytest-django>=4.5
pytest-cov>=4.0
factory-boy>=3.3
faker>=22.0
django-debug-toolbar>=4.2
ipython>=8.0
flake8>=7.0
black>=24.0
isort>=5.13
```

---

### D-05: Logging Konfigurasyonu Eksik App'ler

**Durum:** Settings'te LOGGING ayarli ama bazi app'ler logger kullanmiyor olabilir.

**Cozum:** Her app'in views.py/tasks.py basina:
```python
import logging
logger = logging.getLogger(__name__)
```

---

## KATMAN-ARASI CAPRAZ REFERANS

### Model → Backend → Frontend Eslesme Tablosu

| App | Model Sayisi | Admin | Views | Serializers | Templates | Durum |
|-----|-------------|-------|-------|-------------|-----------|-------|
| core | 13 | 10 | 11 | 21 | - | Calisiyor |
| menu | 9 | 10 | 7 | 27 | - | Calisiyor |
| orders | 10 | 8 | 5 | 26 | - | Calisiyor |
| subscriptions | 6 | 6 | 6 | 30 | - | Calisiyor |
| customers | 6 | 4 | 2 | 8 | - | Eksik views (O-02) |
| inventory | 7 | 7 | 7 | 7 | - | Calisiyor |
| campaigns | 4 | 4 | 4 | 4 | - | Tasks eksik (O-03) |
| ai | 2 | - | 5 | 0 | - | Serializer eksik (O-04) |
| **analytics** | **4** | **0** | **0** | **0** | - | **TAMAMEN BOS (Y-01)** |
| **media** | **2** | **2** | **0** | **0** | - | **Views/Ser. eksik (Y-02)** |
| notifications | 1 | 1 | 1 | 2 | - | Minimal (O-01) |
| dashboard | 2 | 2 | custom | 0 | 9 | Calisiyor (JsonResponse) |
| reporting | 5 | 4 | 13 | 7 | - | TODO'lar var (O-06) |
| seo | 9 | 8 | 0 | 0 | 4 | Middleware-only (Y-03) |
| seo_shield | 4 | 4 | 0 | 0 | - | Middleware-only (Y-04) |
| **website** | **31** | **37** | **0** | **0** | **48** | **Views eksik (Y-05)** |

### En Acil 5 Aksiyon (Sira ile)

1. **requirements.txt'i duzelt** (K-01) — `pip install -r requirements.txt` basarisiz olur
2. **Eksik Celery tasks olustur** (K-02) — Celery beat crash eder
3. **django_filters + corsheaders aktif et** (K-05, K-06) — API filtreleme ve CORS kirik
4. **10 eksik static dosya olustur** (K-04) — UI 404 hatalari
5. **Analytics + Media app backend'ini tamamla** (Y-01, Y-02) — Veri var, erisim yok

---

## VIBECODING SESSION PLANLARI

### Session 1: Kritik Duzeltmeler (Tahmini: 30 dk)
```
- requirements.txt'e 4 paket ekle
- 3 tasks.py dosyasi olustur (core, subscriptions, notifications)
- django_filters, corsheaders, guardian yorum isaretlerini kaldir
- WhiteNoise middleware aktif et
- `python manage.py check` ile dogrula
```

### Session 2: Eksik Static Dosyalar (Tahmini: 45 dk)
```
- tailwind.min.css olustur veya CDN'e gecis yap
- Logo SVG, favicon SVG, apple-touch-icon PNG, OG image PNG olustur
- Admin custom CSS (base.css, changelists.css, forms.css) olustur
- Admin custom JS (change_form.js, filters.js) olustur
- Tarayicida test et — 404 kalmamali
```

### Session 3: Analytics App Tamamla (Tahmini: 1 saat)
```
- apps/analytics/admin.py — 4 model kaydi
- apps/analytics/serializers.py — read-only serializer'lar
- apps/analytics/views.py — ListAPIView + RetrieveAPIView
- apps/analytics/urls.py — guncelle
- Test yaz
```

### Session 4: Media App Tamamla (Tahmini: 1 saat)
```
- apps/media/serializers.py — upload + list serializer
- apps/media/views.py — FileUploadView, MediaListView
- Storage backend ayarla (local veya S3)
- apps/media/urls.py — guncelle
- Test yaz
```

### Session 5: Website Views (Tahmini: 2-3 saat)
```
- apps/website/views/ package olustur (Plan Faz 4 ile uyumlu)
- 15 alt modul: home, features, pricing, about, blog, contact, legal,
  solutions, customers, resources, company, investor, partners, support, newsletter
- apps/website/urls.py guncelle (~25 yeni URL)
- Template-view eslesmesini dogrula
```

### Session 6: Customers + Campaigns + AI Tamamla (Tahmini: 1.5 saat)
```
- Customers: Eksik CRUD views ekle
- Campaigns: tasks.py olustur
- AI: serializers.py olustur
```

### Session 7: Notifications Genislet (Tahmini: 1.5 saat)
```
- NotificationType, NotificationPreference, NotificationTemplate modelleri
- Email gonderme servisi
- Push notification altyapisi
- Admin kayitlari
```

### Session 8: Cross-Cutting (Tahmini: 1 saat)
```
- Core model TODO: Organization → Subscription FK ekle
- Reporting TODO'lari: Email + webhook delivery
- Menu app: translation.py olustur
- Eksik test'leri yaz
```

---

## DOSYA LISTESI — Olusturulacak / Degistirilecek

### Olusturulacak Dosyalar (17)
```
apps/core/tasks.py
apps/subscriptions/tasks.py
apps/notifications/tasks.py
apps/campaigns/tasks.py
apps/analytics/admin.py (veya guncelle)
apps/analytics/serializers.py
apps/analytics/views.py (veya guncelle)
apps/media/serializers.py
apps/media/views.py (veya guncelle)
apps/ai/serializers.py
apps/seo_shield/urls.py (bos)
static/css/tailwind.min.css
static/images/favicon.svg
static/images/logo.svg
static/images/apple-touch-icon.png
static/images/og-default.png
static/admin/css/base.css
static/admin/css/changelists.css
static/admin/css/forms.css
static/admin/js/change_form.js
static/admin/js/filters.js
```

### Degistirilecek Dosyalar (5)
```
requirements.txt                    — 4 paket ekle
config/settings/base.py             — INSTALLED_APPS + MIDDLEWARE yorumlari ac
apps/core/models.py                 — Subscription FK ekle, TODO temizle
apps/analytics/urls.py              — Yeni endpoint'ler
apps/media/urls.py                  — Yeni endpoint'ler
```

---

## NOTLAR

1. Bu yonerge, `wiggly-hugging-abelson.md` planindaki Faz 1-5 ile UYUMLUDUR. Plan oncelikli — bu yonerge onu tamamlar.
2. Website app views (Y-05) Plan Faz 4'te zaten kapsanmis. Burada tekrar listelendi ama plan uygulama sirasinda atlanabilir.
3. Tum duzeltmelerden sonra `python manage.py check` ve `pytest` caliltirilmalidir.
4. Docker rebuild gerekir: `docker compose build --no-cache`
