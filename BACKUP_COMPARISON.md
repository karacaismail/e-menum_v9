# e-menum_v9 vs e-menum_v9_backup – Karşılaştırma

Yedek klasör (`e-menum_v9_backup`) incelendi. Çalışan yedekte olup mevcut repoda sorun çıkaran farklar aşağıda.

---

## 1. Core migrations

| | Yedek (backup) | Mevcut (current) |
|---|----------------|------------------|
| **Dosyalar** | 0001, 0002, 0003, 0004 **sadece** | 0001, 0002, 0003, 0004, **0007** |
| **0005 / 0006** | Yok | Yok (0007 bunlara bağımlıydı → hata) |
| **0007_add_migration_log** | **Yok** | Var (MigrationLog tablosu) |

**Sonuç:** Yedekte `safe_migrate` yok, sadece `migrate --noinput` kullanılıyor. Mevcut repoda 0007 vardı ve var olmayan 0006’ya bağımlıydı; bağımlılık 0004’e çekilerek düzeltildi.

---

## 2. Subscriptions admin & model

| | Yedek | Mevcut |
|---|-------|--------|
| **FeaturePermission** | Admin’de **yok** (import yok) | Admin’de var; model + 0003 migration eklendi |
| **Import** | Feature, Invoice, OrganizationUsage, Plan, PlanFeature, Subscription | Aynıları + **FeaturePermission** |

**Sonuç:** Yedekte FeaturePermission modeli ve admin’i yok; mevcut repoda eklendi ve migration (0003_featurepermission) ile uyumlu hale getirildi.

---

## 3. Entrypoint (docker/entrypoint.sh)

| | Yedek | Mevcut |
|---|-------|--------|
| **DB bekleme** | `django.setup()` + `connection.ensure_connection()` | **psycopg** ile bağlantı (Django yok) – filer/populate hatası yok |
| **Migrate** | `python manage.py migrate --noinput` | `safe_migrate` deniyor, fallback: `migrate --noinput` |
| **.env / DATABASE_URL** | Sadece .env oluşturma | .env’e DATABASE_URL yazma + “Database host” log |

**Sonuç:** Yedekte sadece `migrate` var; mevcut repoda DB bekleme Django’suz yapılıyor ve migrate için `safe_migrate` kullanılıyor (doğru migration zinciri gerekli).

---

## 4. Requirements

| | Yedek | Mevcut |
|---|-------|--------|
| **django-filer** | Var (`django-filer>=3.0`) | Var (eklendi) |
| **easy-thumbnails** | Var (`>=2.8`) | Var (`>=2.0`) |
| **python-magic, qrcode, xhtml2pdf, Pillow, reportlab** | Yedekte kısa liste (grep’te görünmüyor) | Mevcut repoda var (pycairo için pkg-config + libcairo eklendi) |

**Sonuç:** Yedekte filer/thumbnails vardı; mevcut repoda da eklendi. Mevcut repoda ek paketler ve Dockerfile’da cairo/pycairo düzeltmesi var.

---

## 5. Settings – ENV_FILE

| | Yedek | Mevcut |
|---|-------|--------|
| **ENV_FILE** | `BASE_DIR.parent / '.env'` (Docker’da `/` altında aranır) | `BASE_DIR / '.env'` (Docker’da `/app/.env` okunur) |

**Sonuç:** Mevcut repoda ENV_FILE düzeltmesi doğru; yedekteki hali Docker’da .env’i proje kökünde okumaz.

---

## Özet – Yedekte “neden çalışıyordu?”

1. **safe_migrate yok** → Migration grafiği (0006/0007) hiç çalışmıyordu, sadece `migrate` vardı.
2. **FeaturePermission yok** → Admin’de böyle bir import ve model beklentisi yoktu.
3. **Filer requirements’ta** → Django yüklenirken “No module named filer” olmuyordu.
4. **Entrypoint’te Django ile DB bekleme** → Filer yüklü olduğu için populate/filer hatası da yoktu.

---

## Mevcut repoda yapılan düzeltmeler (özet)

- 0007’nin bağımlılığı: `0006_add_file_and_hash` → `0004_organization_plan_organization_subscription`.
- FeaturePermission modeli + subscriptions 0003 migration eklendi.
- Entrypoint: DB bekleme psycopg ile (Django’suz); .env’e DATABASE_URL yazılıyor.
- requirements: django-filer, easy-thumbnails eklendi.
- base.py: ENV_FILE = BASE_DIR / '.env'.
- Dockerfile: pkg-config, libcairo2-dev (builder), libcairo2 (runtime).

Bu haliyle mevcut repo yedekten daha “tam” (FeaturePermission, safe_migrate, doğru ENV_FILE). Migration zinciri 0007→0004 ile düzgün; deploy sonrası `migrate` / `safe_migrate` çalışmalı.
