# E-Menum Module System Architecture

> **Auto-Claude Module System Document**
> Django app mimarisi, lifecycle, kayit mekanizmasi ve app-arasi iletisim.
> Django'nun native app sistemi uzerine kurulu, enterprise-ready modular yapi.
> Son Guncelleme: 2026-03-16

---

## 1. MODUL SISTEMI GENEL BAKIS

### 1.1 Felsefe

E-Menum, Django'nun native app sistemi uzerine kurulmustur. Her ozellik bir Django app olarak
`e_menum/apps/` dizini altinda bulunur. WordPress-tarz plugin mimarisinden farkli olarak,
burada Django'nun INSTALLED_APPS, AppConfig, signals ve URL include mekanizmalari kullanilir.

```
PRENSIPLER:

  1. Django-native app yapisi
     - Her ozellik bagimsiz bir Django app
     - AppConfig ile metadata ve baslatma
     - Django signals ile app-arasi iletisim
     - URL include() ile route kaydi

  2. Multi-Tenant by Default
     - Her queryset organizationId ile filtrelenmeli
     - BaseTenantViewSet ile otomatik tenant izolasyonu
     - TenantMiddleware ile request.organization enjeksiyonu

  3. Soft Delete Everywhere
     - Hicbir veri fiziksel silinmez
     - SoftDeleteMixin ile deleted_at timestamp
     - get_queryset() icinde otomatik filtreleme

  4. Shared Code Separation
     - App-spesifik kod apps/ altinda
     - Ortak mixinler, utility, middleware shared/ altinda
     - Cross-cutting concerns shared/ ile paylasilir
```

### 1.2 App Kategorileri

| Kategori | Applar | Aciklama |
|----------|--------|----------|
| **Core** | `core` | Organizasyon, kullanici, rol, yetki, auth - sistemin cekirdegi |
| **Feature** | `menu`, `orders`, `subscriptions`, `customers`, `inventory`, `campaigns`, `notifications`, `reporting` | Is ozellikleri, bagimsiz olarak gelistirilebilir |
| **AI** | `ai` | Yapay zeka destekli icerik uretimi, ceviri, oneri |
| **Analytics** | `analytics`, `dashboard` | Veri analizi, KPI izleme, dashboard metrikleri |
| **Media** | `media` | Dosya yukleme, filer entegrasyonu, gorsel yonetimi |
| **Website** | `website`, `seo`, `seo_shield` | Pazarlama siteleri, SEO, guvenlik |
| **Portal** | `accounts` | Restoran sahibi self-servis portalı (/account/) |

### 1.3 Tum Applar (17 adet)

```
e_menum/apps/
├── core/            # Organizasyon, User, Role, Permission, Auth
├── menu/            # Menu, Category, Product, Variant, Modifier, Allergen, Theme
├── orders/          # Order, OrderItem, Zone, Table, QRCode, ServiceRequest
├── subscriptions/   # Plan, Feature, Subscription, Invoice, Usage
├── customers/       # Customer, Feedback, LoyaltyHistory
├── analytics/       # AnalyticsEvent, PageView, heatmap verileri
├── ai/              # AIProvider, AIGenerationLog, prompt yonetimi
├── campaigns/       # Campaign, Coupon, Referral
├── inventory/       # InventoryItem, StockMovement, Supplier, PurchaseOrder, Recipe
├── media/           # MediaFile, MediaFolder (django-filer entegrasyonu)
├── notifications/   # Notification, NotificationTemplate, delivery kanallari
├── dashboard/       # Dashboard widget'lari, admin mainboard, metrik API'lari
├── reporting/       # ReportDefinition, ReportExecution, ReportSchedule, ReportFavorite
├── seo/             # Redirect, BrokenLink, NotFound404Log, CoreWebVitals, pSEO
├── seo_shield/      # BlockLog, IPRiskScore, bot koruma, rate limiting
├── website/         # BlogPost, Page, FAQ, pazarlama sayfalari (i18n prefixed)
└── accounts/        # Restoran sahibi portal goruntuleri, formlar
```

---

## 2. APP YAPISI

### 2.1 Standart App Klasor Yapisi

Her Django app asagidaki dosya yapisini takip eder:

```
apps/menu/                       # Ornek: Menu app
├── __init__.py                  # Python package marker
├── apps.py                      # AppConfig (metadata + ready() hook)
├── models.py                    # Django ORM modelleri (SoftDeleteMixin ile)
├── serializers.py               # DRF serializers (validation + API ciktisi)
├── views.py                     # DRF ViewSets (BaseTenantViewSet extend)
├── urls.py                      # URL patterns (DRF router + custom paths)
├── admin.py                     # Django admin site kaydi
├── signals.py                   # Django signals (post_save, pre_delete vb.)
├── tasks.py                     # Celery async gorevler
├── choices.py                   # TextChoices / IntegerChoices enums
├── filters.py                   # DRF FilterSet siniflar (django-filter)
├── forms.py                     # Django forms (admin/portal SSR sayfalar icin)
├── public_views.py              # Halka acik SSR goruntuler (ornegin menü goruntuleme)
├── management/
│   └── commands/                # Django management komutlari
│       └── seed_menus.py
├── migrations/                  # Django DB migration dosyalari
│   ├── __init__.py
│   ├── 0001_initial.py
│   └── ...
└── tests/                       # Test dosyalari
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    └── test_serializers.py
```

> **Not:** Her app'in tum dosyalari olmak zorunda degildir. Sadece ihtiyac duyulanlar
> olusturulur. Ornegin `dashboard` app'inde `models.py` vardir ancak `serializers.py`
> olmayabilir; `accounts` app'inde `forms.py` ve `views.py` vardir ancak modeller
> `core` app'indedir.

### 2.2 AppConfig (apps.py)

Her app bir `AppConfig` sinifi tanimlar. Bu sinif Django'ya app hakkinda metadata saglar
ve `ready()` hook'u ile baslatma gorevlerini yurutur.

```python
# apps/menu/apps.py

from django.apps import AppConfig


class MenuConfig(AppConfig):
    """
    Configuration for the E-Menum Menu application.
    """
    name = "apps.menu"
    verbose_name = "Menu Management"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """
        App hazir oldugunda calistir.
        Signal'leri kaydet, startup gorevlerini baslat.
        """
        try:
            from apps.menu import signals  # noqa: F401
        except ImportError:
            pass
```

**Onemli:** `name` alani `apps.{app_name}` formatinda olmali. Django bu deger ile
app'i bulur ve yukler.

### 2.3 INSTALLED_APPS Kaydi

Tum applar `config/settings/base.py` icinde `INSTALLED_APPS` listesine eklenir:

```python
# config/settings/base.py

EMENUM_APPS = (
    "apps.core.apps.CoreConfig",
    "apps.menu.apps.MenuConfig",
    "apps.orders.apps.OrdersConfig",
    "apps.subscriptions.apps.SubscriptionsConfig",
    "apps.customers.apps.CustomersConfig",
    "apps.media.apps.MediaConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.analytics.apps.AnalyticsConfig",
    "apps.reporting.apps.ReportingConfig",
    "apps.inventory.apps.InventoryConfig",
    "apps.campaigns.apps.CampaignsConfig",
    "apps.ai.apps.AiConfig",
    "apps.website.apps.WebsiteConfig",
    "apps.seo.apps.SEOConfig",
    "apps.seo_shield.apps.SEOShieldConfig",
    "apps.dashboard.apps.DashboardConfig",
    "apps.accounts.apps.AccountsConfig",
)

INSTALLED_APPS = (
    # Django built-in apps
    ...
    # Third-party apps
    ...
) + EMENUM_APPS
```

---

## 3. URL ROUTING

### 3.1 Merkezi URL Konfigurasyonu

Tum app URL'leri `config/urls.py` icinde `include()` ile baglanir:

```python
# config/urls.py

# API v1 endpointleri
api_v1_patterns = [
    path("auth/", include((core_auth_urlpatterns, "core"), namespace="auth")),
    path("", include(core_router.urls)),                                    # organizations/, users/
    path("", include(("apps.menu.urls", "menu"), namespace="menu")),        # menus/, categories/, products/
    path("", include(("apps.orders.urls", "orders"), namespace="orders")),  # orders/, tables/, qr-codes/
    path("", include(("apps.subscriptions.urls", "subscriptions"), namespace="subscriptions")),
    path("", include(("apps.notifications.urls", "notifications"), namespace="notifications")),
    path("media/", include(("apps.media.urls", "media"), namespace="media")),
    path("", include(("apps.customers.urls", "customers"), namespace="customers")),
    path("", include(("apps.reporting.urls", "reporting"), namespace="reporting")),
    path("", include(("apps.inventory.urls", "inventory"), namespace="inventory")),
    path("", include(("apps.campaigns.urls", "campaigns"), namespace="campaigns")),
    path("ai/", include(("apps.ai.urls", "ai"), namespace="ai")),
]

urlpatterns = [
    path("", include("apps.seo.urls")),                          # robots.txt, sitemap
    path("admin/", include(("apps.dashboard.urls", "dashboard"), namespace="dashboard")),
    path("admin/", admin.site.urls),                             # Django admin
    path("account/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("api/v1/", include((api_v1_patterns, "api"), namespace="api-v1")),
    path("m/<slug:menu_slug>/", PublicMenuView.as_view()),       # Public menu (SSR)
    path("q/<str:code>/", qr_short_url_redirect),                # QR code redirect
    path("health/", health_check),
]

# i18n-prefixed website URLs
urlpatterns += i18n_patterns(
    path("", include(("apps.website.urls", "website"), namespace="website")),
)
```

### 3.2 App-Level URL Tanimlama

Her app kendi `urls.py` dosyasinda DRF router ve/veya path tanimlar:

```python
# apps/menu/urls.py

from rest_framework.routers import DefaultRouter
from apps.menu.views import (
    MenuViewSet, CategoryViewSet, ProductViewSet,
    AllergenViewSet, ThemeViewSet,
)

router = DefaultRouter()
router.register(r"menus", MenuViewSet, basename="menu")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"allergens", AllergenViewSet, basename="allergen")
router.register(r"themes", ThemeViewSet, basename="theme")

urlpatterns = router.urls
```

### 3.3 URL Yapisi Haritasi

| Prefix | App | Scope | Aciklama |
|--------|-----|-------|----------|
| `/api/v1/auth/` | core | Public/Auth | Login, logout, token refresh |
| `/api/v1/organizations/` | core | Auth | Organizasyon CRUD |
| `/api/v1/users/` | core | Auth | Kullanici yonetimi |
| `/api/v1/menus/` | menu | Tenant | Menu CRUD |
| `/api/v1/categories/` | menu | Tenant | Kategori CRUD |
| `/api/v1/products/` | menu | Tenant | Urun CRUD + variants/modifiers |
| `/api/v1/orders/` | orders | Tenant | Siparis CRUD |
| `/api/v1/tables/` | orders | Tenant | Masa yonetimi |
| `/api/v1/qr-codes/` | orders | Tenant | QR kod yonetimi |
| `/api/v1/subscriptions/` | subscriptions | Auth | Abonelik yonetimi |
| `/api/v1/plans/` | subscriptions | Public | Plan listeleme |
| `/api/v1/notifications/` | notifications | Auth | Bildirim yonetimi |
| `/api/v1/customers/` | customers | Tenant | Musteri CRM |
| `/api/v1/inventory/` | inventory | Tenant | Stok yonetimi |
| `/api/v1/campaigns/` | campaigns | Tenant | Kampanya/kupon |
| `/api/v1/reports/` | reporting | Tenant | Raporlama |
| `/api/v1/ai/` | ai | Tenant | AI icerik uretimi |
| `/api/v1/media/` | media | Tenant | Dosya yukleme |
| `/admin/` | dashboard | Admin | Admin paneli (SSR) |
| `/account/` | accounts | Auth | Restoran portal (SSR) |
| `/m/{slug}/` | menu | Public | Herkese acik menu (SSR) |
| `/q/{code}/` | orders | Public | QR kod yonlendirme |
| `/{lang}/` | website | Public | Pazarlama sitesi (i18n) |

---

## 4. SHARED MODUL (Cross-Cutting Concerns)

### 4.1 Shared Dizin Yapisi

Applar arasi paylasilan kod `e_menum/shared/` altinda bulunur:

```
e_menum/shared/
├── __init__.py
├── context_processors.py        # Django template context processors
├── decorators.py                # Ozel decorator'lar (superadmin_required vb.)
│
├── middleware/
│   ├── __init__.py
│   └── tenant.py                # TenantMiddleware (request.organization enjeksiyonu)
│
├── permissions/
│   ├── __init__.py
│   ├── abilities.py             # CASL-like ability tanimlari
│   ├── drf_permissions.py       # DRF permission siniflari
│   ├── plan_enforcement.py      # Plan/tier bazli erisim kontrolu
│   └── admin_permission_mixin.py # Admin panel yetki mixin'i
│
├── serializers/
│   ├── __init__.py
│   └── base.py                  # Temel serializer siniflari
│
├── views/
│   ├── __init__.py
│   ├── base.py                  # BaseTenantViewSet, BaseModelViewSet, mixinler
│   └── admin_upload.py          # Admin AJAX upload endpoint
│
├── utils/
│   ├── __init__.py
│   ├── exceptions.py            # AppException, ErrorCodes
│   ├── impersonate.py           # Kullanici taklit (admin icin)
│   ├── media.py                 # Media utility fonksiyonlari
│   └── text.py                  # Metin isleme yardimcilari
│
└── widgets/
    ├── __init__.py
    ├── image_upload.py          # Gorsel yukleme widget'i
    └── gallery_upload.py        # Galeri yukleme widget'i
```

### 4.2 Base ViewSet Hiyerarsisi

Tum ViewSet'ler `shared/views/base.py` icindeki temel siniflardan turetilir:

```
StandardResponseMixin          # {"success": true, "data": ...} formatinda response
SoftDeleteMixin                # perform_destroy() -> soft_delete()
TenantFilterMixin              # get_queryset() -> organization filtresi

BaseModelViewSet               # StandardResponse + SoftDelete + ModelViewSet
BaseTenantViewSet              # TenantFilter + StandardResponse + SoftDelete + ModelViewSet
BaseReadOnlyViewSet            # StandardResponse + ReadOnlyModelViewSet
BaseTenantReadOnlyViewSet      # TenantFilter + StandardResponse + ReadOnlyModelViewSet
BaseAPIView                    # StandardResponse + APIView
BaseTenantAPIView              # TenantFilter + StandardResponse + APIView
```

**Kullanim:**

```python
from shared.views.base import BaseTenantViewSet

class MenuViewSet(BaseTenantViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    permission_resource = "menu"
```

`BaseTenantViewSet` otomatik olarak:
- `get_queryset()` icinde `organization` filtresi uygular
- `perform_create()` icinde `organization` enjekte eder
- `perform_destroy()` icinde soft delete kullanir
- Tum response'lari standart formata sarar

### 4.3 TenantMiddleware

`shared/middleware/tenant.py` icindeki `TenantMiddleware`, her request'e organization
context'i enjekte eder:

```
Cozumleme Sirasi:
1. Authenticated user'in organizasyonu (user.organization FK)
2. X-Organization-ID header (multi-org kullanicilar/admin icin)
3. emenum_org_id cookie (session persistence)
4. None (public endpoint'ler icin)

Request'e eklenen attribute'lar:
- request.organization      -> Organization instance veya None
- request.organization_id   -> UUID veya None
- request.is_tenant_aware   -> Boolean
```

### 4.4 Permission Sistemi

`shared/permissions/drf_permissions.py` icinde DRF permission siniflari bulunur:

```python
# Kullanim ornegi
class MenuViewSet(BaseTenantViewSet):
    permission_classes = [IsAuthenticated, IsTenantMember, OrganizationScopedPermission]
    permission_resource = "menu"

    action_permissions = {
        "list": "menu.view",
        "retrieve": "menu.view",
        "create": "menu.create",
        "update": "menu.update",
        "destroy": "menu.delete",
    }
```

Permission format: `{resource}.{action}` (ornek: `menu.view`, `order.create`)

---

## 5. APP-ARASI ILETISIM

### 5.1 Django Signals

Applar arasi iletisim Django signals uzerinden yapilir. Bu, loose coupling saglar.

```python
# apps/core/signals.py - Signal tanimlama ve dinleme

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender="core.Organization")
def create_organization_folders(sender, instance, created, **kwargs):
    """
    Yeni organizasyon olusturuldiginda filer klasor yapisi olustur.
    """
    if not created:
        return

    from filer.models import Folder

    root_folder, _ = Folder.objects.get_or_create(
        name=str(instance.id), parent=None
    )
    for subfolder_name in ["menu_items", "logos", "gallery"]:
        Folder.objects.get_or_create(
            name=subfolder_name, parent=root_folder
        )
```

**Signal kayit kurali:** Signaller `apps/{app}/signals.py` icinde tanimlanir
ve `AppConfig.ready()` icinde import edilir:

```python
# apps/core/apps.py
class CoreConfig(AppConfig):
    name = "apps.core"

    def ready(self):
        try:
            from apps.core import signals  # noqa: F401
        except ImportError:
            pass
```

### 5.2 Celery Tasks (Async Islemler)

Uzun suren islemler icin Celery task'lari kullanilir:

```python
# apps/analytics/tasks.py

from celery import shared_task


@shared_task
def aggregate_daily_analytics(organization_id: str, date: str):
    """
    Gunluk analitik verilerini toplar.
    """
    # ... aggregation logic
```

Task'lar su app'larda bulunur:
- `analytics/tasks.py` - Analitik agregasyonlari
- `campaigns/tasks.py` - Kampanya bildirim gonderimleri
- `notifications/tasks.py` - Bildirim delivery (email, push)
- `core/tasks.py` - Sistem bakim gorevleri
- `dashboard/tasks.py` - Dashboard metrik onbellegi
- `reporting/tasks.py` - Rapor uretimi (async)

### 5.3 Dogru ve Yanlis Iletisim Ornekleri

```python
# DOGRU: Signal ile loose coupling
# orders app, menu'ye bagimli degildir
@receiver(post_save, sender="menu.Menu")
def refresh_order_cache(sender, instance, **kwargs):
    from apps.orders.cache import invalidate_menu_cache
    invalidate_menu_cache(instance.id)

# YANLIS: Dogrudan app import ile siki baglanti
# Bu, dongusel import sorunlarina yol acar
from apps.menu.services import MenuService  # Dikkatli olun!

# KABUL EDILEBILIR: Model import (read-only cross reference)
from apps.core.models import Organization  # Core modele referans OK
```

---

## 6. MODEL CONVENTIONS

### 6.1 Soft Delete Pattern

Tum modeller `deleted_at` alani ile soft delete desteklemelidir:

```python
# apps/menu/models.py

from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteMixin(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Silinmisleri de icerir

    class Meta:
        abstract = True

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])
```

### 6.2 Tenant-Scoped Model Pattern

Tenant-scoped modeller `organization` FK icermelidir:

```python
class Menu(SoftDeleteMixin, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="menus",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    # ... diger alanlar

    class Meta:
        unique_together = [("organization", "slug")]
```

### 6.3 Choices Pattern

Enum degerleri `choices.py` icinde Django TextChoices ile tanimlanir:

```python
# apps/orders/choices.py

from django.db import models


class OrderStatus(models.TextChoices):
    PENDING = "PENDING", "Beklemede"
    CONFIRMED = "CONFIRMED", "Onaylandi"
    PREPARING = "PREPARING", "Hazirlaniyor"
    READY = "READY", "Hazir"
    DELIVERED = "DELIVERED", "Teslim Edildi"
    CANCELLED = "CANCELLED", "Iptal Edildi"
```

---

## 7. YENI APP OLUSTURMA REHBERI

### 7.1 Adim Adim

```bash
# 1. App klasorunu olustur
mkdir -p e_menum/apps/new_feature

# 2. Temel dosyalari olustur
touch e_menum/apps/new_feature/__init__.py
touch e_menum/apps/new_feature/apps.py
touch e_menum/apps/new_feature/models.py
touch e_menum/apps/new_feature/serializers.py
touch e_menum/apps/new_feature/views.py
touch e_menum/apps/new_feature/urls.py
touch e_menum/apps/new_feature/admin.py
mkdir -p e_menum/apps/new_feature/migrations
touch e_menum/apps/new_feature/migrations/__init__.py

# 3. AppConfig yaz (apps.py)
# 4. INSTALLED_APPS'e ekle (config/settings/base.py)
# 5. URL'leri config/urls.py'ye ekle
# 6. Migration olustur
python manage.py makemigrations new_feature
python manage.py migrate
```

### 7.2 Kontrol Listesi

Yeni app olusturulurken:

- [ ] `apps.py` icinde AppConfig tanimla (`name = "apps.new_feature"`)
- [ ] `config/settings/base.py` EMENUM_APPS'e `"apps.new_feature.apps.NewFeatureConfig"` ekle
- [ ] Modellerde `SoftDeleteMixin` kullan, `deleted_at` alani ekle
- [ ] Tenant-scoped ise `organization` FK ekle
- [ ] ViewSet'ler `BaseTenantViewSet` veya `BaseModelViewSet` extend etsin
- [ ] `serializers.py` icinde DRF serializer tanimla
- [ ] `urls.py` icinde DRF router ile endpoint tanimla
- [ ] `config/urls.py` icinde `include()` ile baglanti yap
- [ ] `admin.py` icinde Django admin kaydi yap
- [ ] Signal'ler varsa `signals.py` olustur ve `ready()` icinde import et
- [ ] Async islemler varsa `tasks.py` icinde Celery task tanimla
- [ ] Migration olustur: `python manage.py makemigrations`
- [ ] Testleri yaz: `tests/test_models.py`, `tests/test_views.py`

---

## 8. APP BAGIMLILIKLARI

### 8.1 Bagimlilik Haritasi

```
core (bagimsiz - tum app'lerin temeli)
├── menu         (core'a bagimli: Organization, User)
├── orders       (core + menu'ye bagimli: Menu, Product, Table)
├── subscriptions (core'a bagimli: Organization)
├── customers    (core'a bagimli: Organization)
├── analytics    (core'a bagimli: Organization, User)
├── ai           (core + menu'ye bagimli: Product icin icerik uretimi)
├── campaigns    (core + customers'a bagimli)
├── inventory    (core + menu'ye bagimli: Product-Recipe baglantisi)
├── media        (core'a bagimli: Organization)
├── notifications (core'a bagimli: User)
├── dashboard    (core + analitik verilere bagimli)
├── reporting    (core + tum feature app'lere bagimli)
├── seo          (bagimsiz - website ile gevrek baglanti)
├── seo_shield   (bagimsiz - middleware olarak calisir)
├── website      (core + seo ile gevrek baglanti)
└── accounts     (core + menu + orders - portal goruntumleri)
```

### 8.2 Import Kurallari

```python
# DOGRU: Core model import (her app yapabilir)
from apps.core.models import Organization, User

# DOGRU: Shared utility import
from shared.views.base import BaseTenantViewSet
from shared.utils.exceptions import AppException
from shared.permissions.drf_permissions import OrganizationScopedPermission

# DIKKAT: Cross-app model import (sadece FK referansi icin)
# Fonksiyon icinde lazy import tercih edin
def my_function():
    from apps.menu.models import Menu
    return Menu.objects.filter(...)

# YASAK: Circular import olusturacak siki baglantilar
# apps/menu/views.py icinde apps/orders/views.py import etmeyin
```

---

## 9. DATABASE MIGRATION YONETIMI

### 9.1 Migration Komutlari

```bash
# Tum app'ler icin migration olustur
python manage.py makemigrations

# Belirli bir app icin migration olustur
python manage.py makemigrations menu

# Migration'lari uygula
python manage.py migrate

# Migration durumunu goster
python manage.py showmigrations

# Belirli bir migration'a geri don
python manage.py migrate menu 0005_auto_20260101
```

### 9.2 Migration Kurallari

- Her app kendi `migrations/` dizininde migration dosyalarini tutar
- Migration dosyalari version control'e commit edilir
- Cross-app migration bagimliliklari `dependencies` ile tanimlanir
- Veri migration'lari (RunPython) ayri dosyada olusturulur
- Production'da migration oncesi backup alinir

---

## 10. MIDDLEWARE ZINCIRI

Istekler su middleware zincirinden gecer (sirasi onemli):

```python
MIDDLEWARE = [
    "apps.seo_shield.middleware.SEOShieldMiddleware",  # Bot koruma (en basta)
    "django.middleware.security.SecurityMiddleware",
    "apps.seo.middleware.CanonicalDomainMiddleware",   # Domain yonlendirme
    "apps.seo.middleware.RedirectMiddleware",           # SEO redirect'leri
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",        # i18n
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "shared.middleware.tenant.TenantMiddleware",        # Tenant context (auth'dan SONRA)
    "django.contrib.messages.middleware.MessageMiddleware",
    "apps.seo.middleware.SEOHeadersMiddleware",         # SEO header'lari
    "apps.seo.middleware.Track404Middleware",            # 404 izleme (en sonda)
]
```

---

## 11. NE ZAMAN RESTART / REBUILD GEREKIR

```yaml
RESTART GEREKLI:
  - Migration sonrasi (python manage.py migrate)
  - Environment variable degisikligi
  - INSTALLED_APPS degisikligi
  - Middleware degisikligi
  - settings.py degisikligi

RESTART GEREKMIYOR (hot-reload dev server'da otomatik):
  - View, serializer, model degisiklikleri
  - Template degisiklikleri
  - Signal degisiklikleri
  - URL pattern degisiklikleri
  - Static dosya degisiklikleri

COLLECTSTATIC GEREKLI (production):
  - CSS/JS/image dosyasi eklendiginde veya degistiginde
  - python manage.py collectstatic
```

---

## 12. TEST YAPISI

### 12.1 Test Dosya Konumlari

```
apps/menu/
├── tests/
│   ├── __init__.py
│   ├── test_models.py           # Model unit testleri
│   ├── test_views.py            # ViewSet API testleri
│   ├── test_serializers.py      # Serializer testleri
│   └── test_signals.py          # Signal testleri
```

### 12.2 Test Komutlari

```bash
# Tum testleri calistir
python manage.py test

# Belirli bir app'in testlerini calistir
python manage.py test apps.menu

# Belirli bir test dosyasini calistir
python manage.py test apps.menu.tests.test_views

# Coverage ile calistir
coverage run manage.py test
coverage report
```

---

## 13. KOMUT REFERANSI

### 13.1 Development

```bash
# Dev server baslat (hot reload)
python manage.py runserver

# Shell (Django ORM ile interaktif)
python manage.py shell_plus

# Veritabani islemleri
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations

# Statik dosyalar
python manage.py collectstatic

# Seed data
python manage.py seed_demo_data
```

### 13.2 Celery (Async Tasks)

```bash
# Celery worker baslat
celery -A config worker -l info

# Celery beat (periyodik gorevler)
celery -A config beat -l info
```

---

*Bu dokuman, E-Menum'un Django app tabanli modul mimarisini tanimlar.
Yeni ozellik gelistirme icin bu yapiya uyulmasi zorunludur.*
