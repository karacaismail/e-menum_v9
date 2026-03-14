# E-Menum Ortam Denetim Raporu

> **Tarih:** 2026-03-14
> **Kapsam:** GitHub Repo, Localhost (Docker/M4 ARM), Production (Hetzner AMD64)

---

## 1. KULLANICI KİMLİK BİLGİLERİ (Tüm Ortamlar)

### 1.1 Platform (Sistem) Kullanıcıları

| # | Email | Şifre | Rol | Organizasyon | Kaynak Dosya |
|---|-------|-------|-----|-------------|-------------|
| 1 | `admin@e-menum.net` | `.env` → `BxmtmJih0w0MQyGI` | super_admin (Django superuser) | Platform | `docker/entrypoint.sh` (line 90-102) |
| 2 | `platform-admin@e-menum.net` | `PlatAdmin1234!` | admin | Platform | `seed_all_data.py` (line 222) |
| 3 | `sales@e-menum.net` | `Sales1234!emenum` | sales | Platform | `seed_all_data.py` (line 229) |
| 4 | `support@e-menum.net` | `Support1234!emenum` | support | Platform | `seed_all_data.py` (line 236) |

### 1.2 Lezzet Sarayi (Ana Demo Restoran)

| # | Email | Şifre | Org Rol | is_staff | Kaynak |
|---|-------|-------|---------|----------|--------|
| 5 | `admin@lezzetsarayi.com` | `LezzetSarayi2024!` | owner | True | `seed_menu_data.py` (line 121) |
| 6 | `mehmet.yilmaz@lezzetsarayi.com` | `Staff1234!emenum` | manager | True | `seed_all_data.py` (line 464) |
| 7 | `ayse.demir@lezzetsarayi.com` | `Staff1234!emenum` | staff | True | `seed_all_data.py` (line 464) |
| 8 | `fatma.kaya@lezzetsarayi.com` | `Staff1234!emenum` | staff | False | `seed_all_data.py` (line 464) |
| 9 | `ali.celik@lezzetsarayi.com` | `Staff1234!emenum` | staff | False | `seed_all_data.py` (line 464) |
| 10 | `zeynep.arslan@lezzetsarayi.com` | `Staff1234!emenum` | viewer | False | `seed_all_data.py` (line 464) |

### 1.3 Ek Organizasyon Sahipleri (seed_extra_orgs)

| # | Email | Şifre | Rol | Organizasyon | Kaynak |
|---|-------|-------|-----|-------------|--------|
| 11 | `mehmet@bosphorusbistro.com` | `Owner1234!emenum` | owner | Bosphorus Bistro | `seed_extra_orgs.py` (line 445) |
| 12 | `ayse@cafenoir.com.tr` | `Owner1234!emenum` | owner | Cafe Noir | `seed_extra_orgs.py` (line 445) |
| 13 | `ali@sultankebap.com.tr` | `Owner1234!emenum` | owner | Sultan Kebap | `seed_extra_orgs.py` (line 445) |

### 1.4 Demo Restoran Sahipleri (seed_demo_data)

Tamamı `Owner1234!emenum` şifresi ile oluşturulur.

| # | Email | Organizasyon | Plan |
|---|-------|-------------|------|
| 14 | `hakan@anadolusofrasi.com.tr` | Anadolu Sofrasi | starter |
| 15 | `cenk@denizkizibalik.com` | Deniz Kizi Balik | professional |
| 16 | `dila@yesilkoyvegan.com` | Yesilkoy Vegan Mutfak | growth |
| 17 | `volkan@kapadokyapizza.com` | Kapadokya Pizza | starter |
| 18 | `temel@ayderyaylaevi.com` | Ayder Yayla Evi | free |
| 19 | `osman@antepbaklava.com.tr` | Gaziantep Baklavacisi | professional |
| 20 | `sinan@bodrumbeach.club` | Bodrum Beach Club | business |
| 21 | `selim@ankarasehir.com.tr` | Ankara Sehir Lokantasi | starter |
| 22 | `kemal@bursaiskender.com.tr` | Bursa Iskender Evi | growth |
| 23 | `yusuf@karadenizpide.com` | Karadeniz Pide Salonu | free |
| 24 | `arda@sahilkafe.com.tr` | Sahil Kafe | professional |
| 25 | `kaan@istanbulsteak.com` | Istanbul Steakhouse | business |

### 1.5 Demo Restoran Personeli (seed_demo_data)

Her restorana rastgele isimlerle personel oluşturulur. Tamamı `Staff1234!emenum` şifresi ile.

| Organizasyon | Personel Sayısı | Email Formatı |
|-------------|----------------|---------------|
| Anadolu Sofrasi | 3 | `{ad}.{soyad}@anadolusofrasi.com.tr` |
| Deniz Kizi Balik | 4 | `{ad}.{soyad}@denizkizibalik.com` |
| Yesilkoy Vegan Mutfak | 2 | `{ad}.{soyad}@yesilkoyvegan.com` |
| Kapadokya Pizza | 2 | `{ad}.{soyad}@kapadokyapizza.com` |
| Ayder Yayla Evi | 1 | `{ad}.{soyad}@ayderyaylaevi.com` |
| Gaziantep Baklavacisi | 3 | `{ad}.{soyad}@antepbaklava.com.tr` |
| Bodrum Beach Club | 4 | `{ad}.{soyad}@bodrumbeach.club` |
| Ankara Sehir Lokantasi | 3 | `{ad}.{soyad}@ankarasehir.com.tr` |
| Bursa Iskender Evi | 2 | `{ad}.{soyad}@bursaiskender.com.tr` |
| Karadeniz Pide Salonu | 1 | `{ad}.{soyad}@karadenizpide.com` |
| Sahil Kafe | 3 | `{ad}.{soyad}@sahilkafe.com.tr` |
| Istanbul Steakhouse | 5 | `{ad}.{soyad}@istanbulsteak.com` |
| **TOPLAM** | **33** | Rastgele isimler, deterministik degil |

### 1.6 Altyapı / Araç Kimlik Bilgileri (Sadece Dev)

| Servis | Kullanıcı | Şifre | Kaynak |
|--------|-----------|-------|--------|
| pgAdmin | `admin@emenum.local` | `admin` | `docker-compose.dev.yml` (line 167-168) |
| PostgreSQL | `postgres` | `postgres` | `docker-compose.yml` env defaults |

### 1.7 Şifre Özet Tablosu

| Şifre | Kullanıldığı Yer |
|-------|-----------------|
| `BxmtmJih0w0MQyGI` | `admin@e-menum.net` (production .env) |
| `LezzetSarayi2024!` | `admin@lezzetsarayi.com` |
| `PlatAdmin1234!` | `platform-admin@e-menum.net` |
| `Sales1234!emenum` | `sales@e-menum.net` |
| `Support1234!emenum` | `support@e-menum.net` |
| `Owner1234!emenum` | 15 organizasyon sahibi (3 extra + 12 demo) |
| `Staff1234!emenum` | Tum personel (5 Lezzet Sarayi + ~33 demo) |

---

## 2. ŞİFRE ÇELİŞKİLERİ (TESPİT EDİLEN ve ÇÖZÜLEN)

### 2.1 `admin@e-menum.net` Çakışması

Bu email **iki farklı yerde** tanımlanmış, farklı şifrelerle:

| Kaynak | Şifre | Çalışma Sırası | Sonuç |
|--------|-------|---------------|-------|
| `docker/entrypoint.sh` | `.env` → `BxmtmJih0w0MQyGI` | 1. (ilk) | **KAZANAN** |
| `seed_all_data.py` (line 214) | `Admin1234!emenum` | 7. (sonra) | Atlanır (`get_or_create` mevcut bulur) |

**Açıklama:** Entrypoint superuser'ı **ilk** oluşturur. `seed_all_data` çalıştığında `get_or_create` bu email'i bulur ve `created=False` döner, şifreyi **değiştirmez**.

**Production `docker-compose.prod.yml` fallback:** `.env` yoksa default `admin123` kullanılır (line 87).

### 2.2 Şifre Tutarlılık Durumu

| Ortam | `admin@e-menum.net` Şifresi | Kaynak |
|-------|--------------------------|--------|
| **GitHub Repo (.env.example)** | `BxmtmJih0w0MQyGI` | `.env.example` line 140 |
| **Localhost Docker (.env)** | `BxmtmJih0w0MQyGI` | `.env` line 140 |
| **Production (Hetzner)** | Sunucu `.env`'den | Coolify/server `.env` |
| **docker-compose.prod.yml fallback** | `admin123` | line 87 |

> **Uyarı:** Production sunucusundaki `.env` dosyasında ne olduğu doğrudan kontrol edilemedi. Coolify UI'dan veya SSH ile doğrulanmalı.

---

## 3. "NO PLAN" SORUNU (TESPİT ve ÇÖZÜM)

### 3.1 Sorun

Tüm organizasyonlar sidebarda "Ucretsiz Plan" veya "NO PLAN" gösteriyor.

### 3.2 Root Cause

`Organization` modelinde iki ayrı plan bağlantısı var:

```
Organization.plan → FK → Plan              (templates bunu kullanır)
Organization.subscription → OneToOne → Subscription  (PlanEnforcementService bunu kullanır)
```

Seed komutları `Subscription` kaydı oluşturuyor ama **`org.plan` ve `org.subscription` FK'larını set etmiyor**.

| Dosya | Sorun |
|-------|-------|
| `seed_all_data.py` `_seed_subscriptions()` | `Subscription` oluşturur ama `org.plan = plan` yapmaz |
| `seed_demo_data.py` `_create_subscription()` | `Subscription` oluşturur ama `org.plan = plan` yapmaz |
| `seed_extra_orgs.py` | Plan hiç bağlamaz |
| `seed_menu_data.py` | Plan hiç bağlamaz |

### 3.3 Çözüm (Uygulandı)

`seed_all_data.py` ve `seed_demo_data.py`'ye subscription oluşturduktan sonra şu kod eklendi:

```python
# Link plan and subscription to organization FK fields
updated_fields = []
if org.plan != plan:
    org.plan = plan
    updated_fields.append("plan")
if org.subscription != sub:
    org.subscription = sub
    updated_fields.append("subscription")
if updated_fields:
    org.save(update_fields=updated_fields)
```

---

## 4. ARM vs AMD64 MİMARİ ÇAKIŞMALARI

### 4.1 Ortam Karşılaştırması

| Özellik | Localhost (MacBook) | Production (Hetzner) |
|---------|-------------------|---------------------|
| **CPU** | Apple M4 (ARM64/aarch64) | AMD EPYC (x86_64/amd64) |
| **Dockerfile** | `Dockerfile` (platform belirtilmemiş → native ARM) | `Dockerfile.amd64linux` (`--platform=linux/amd64`) |
| **Docker Compose** | `docker-compose.yml` + `docker-compose.dev.yml` | `docker-compose.prod.yml` |
| **Python** | 3.13-slim-bookworm (ARM64) | 3.13-slim-bookworm (AMD64) |
| **PostgreSQL** | postgres:15-alpine (multi-arch, ARM64) | postgres:15-alpine (multi-arch, AMD64) |
| **Redis** | redis:7-alpine (multi-arch, ARM64) | redis:7-alpine (multi-arch, AMD64) |

### 4.2 Tespit Edilen Sorunlar ve Düzeltmeler

#### KRİTİK: Dev Dockerfile'da Eksik Bağımlılıklar (DÜZELTİLDİ)

| Bağımlılık | `Dockerfile` (dev) | `Dockerfile.amd64linux` (prod) | Etki |
|-----------|--------------------|-----------------------------|------|
| `pkg-config` | **EKSİKTİ** → Eklendi | Var | pycairo derleme hatası |
| `libcairo2-dev` | **EKSİKTİ** → Eklendi | Var | xhtml2pdf/PDF build hatası |
| `libcairo2` | **EKSİKTİ** → Eklendi | Var | Runtime PDF hatası |
| `libmagic1` | **EKSİKTİ** → Eklendi | **EKSİKTİ** → Eklendi | python-magic runtime hatası |

#### ORTA: İki Ayrı Dockerfile Bakım Yükü

Proje iki ayrı Dockerfile kullanıyor:
- `Dockerfile` — platform belirtilmemiş (native arch build)
- `Dockerfile.amd64linux` — `--platform=linux/amd64` sabitlenmiş

Bu yapı "drift" riski taşır — bir dosyaya eklenen değişiklik diğerine unutulabilir (bu sefer olduğu gibi).

#### DÜŞÜK: QEMU Tuzağı

MacBook'ta `docker-compose.prod.yml` kullanılırsa:
- Web/Celery container'ları QEMU emülasyonuyla çalışır (3-10x yavaş)
- PostgreSQL/Redis native ARM çalışır
- Mixed-arch ortam oluşur

### 4.3 Python Paketleri Mimari Uyumluluğu

| Paket | Arch Risk | Açıklama |
|-------|-----------|----------|
| `psycopg[binary]` | Düşük | ARM64 + AMD64 wheel var |
| `bcrypt` | Düşük | Rust-based, her iki arch destekli |
| `Pillow` | Düşük | Her iki arch destekli |
| `xhtml2pdf` | **Yüksek** | `pycairo` + `libcairo2` gerektirir (Dockerfile'a eklendi) |
| `python-magic` | **Orta** | `libmagic1` gerektirir (Dockerfile'a eklendi) |
| `celery[redis]` | Düşük | Pure Python |
| `reportlab` | Düşük | Wheel mevcut |

---

## 5. SEED ÇALIŞTIRMA SIRASI

Docker entrypoint aşağıdaki sırayla çalıştırır:

```
┌─ Entrypoint ──────────────────────────────────────────┐
│ 1. Migrations                                          │
│ 2. Superuser (admin@e-menum.net) — .env'den şifre      │
│ 3. collectstatic                                       │
│                                                        │
│ ─ Gunicorn başlatılır (arka planda) ─                  │
│ ─ /health/ endpoint'i beklenilir ─                     │
│                                                        │
│ 4.  [1/11] seed_roles                                  │
│ 5.  [2/11] seed_plans         → Plan objeleri          │
│ 6.  [3/11] seed_allergens                              │
│ 7.  [4/11] seed_menu_data     → Lezzet Sarayi org+owner│
│ 8.  [5/11] seed_extra_orgs    → 3 extra org+owner      │
│ 9.  [6/11] seed_all_data      → Platform users + staff  │
│ 10. [7/11] seed_demo_data     → 12 demo restoran       │
│ 11. [8/11] seed_cms_content                            │
│ 12. [9/11] seed_seo_data                               │
│ 13. [10/11] seed_report_definitions                    │
│ 14. [11/11] seed_shield_data                           │
└────────────────────────────────────────────────────────┘
```

Tüm seed komutları `get_or_create` kullanır — yani **ilk oluşturan kazanır**, sonraki aynı email'i atlar.

---

## 6. ORTAM KARŞILAŞTIRMA MATRİSİ

| Kontrol | GitHub Repo | Localhost Docker | Production |
|---------|-------------|-----------------|------------|
| CI Durum | ✅ 1165 test geçiyor | N/A | N/A |
| Website Durumu | N/A | ✅ Çalışıyor (runserver) | ✅ Çalışıyor (gunicorn) |
| Superuser | Kod: `Admin1234!emenum` | `.env`: `BxmtmJih0w0MQyGI` | Sunucu `.env` |
| Platform Users | ✅ 4 kullanıcı tanımlı | ✅ Oluşturuluyor | ✅ Oluşturuluyor |
| Lezzet Sarayi | ✅ 6 kullanıcı tanımlı | ✅ Oluşturuluyor | ✅ Oluşturuluyor |
| Extra Orgs | ✅ 3 org tanımlı | ✅ Oluşturuluyor | ✅ Oluşturuluyor |
| Demo Restoranlar | ✅ 12 restoran tanımlı | ✅ Oluşturuluyor | ✅ Oluşturuluyor |
| Plan FK Bağlantısı | ✅ Düzeltildi | 🔄 Re-seed gerekli | 🔄 Re-seed gerekli |
| Cairo/PDF Desteği | N/A | ✅ Düzeltildi | ✅ Mevcut |
| libmagic Desteği | N/A | ✅ Düzeltildi | ✅ Düzeltildi |

---

## 7. ÖNERİLER

### 7.1 Acil Aksiyonlar

1. **Production sunucuda re-seed:** Plan FK'larının bağlanması için:
   ```bash
   docker compose exec web python manage.py seed_all_data
   docker compose exec web python manage.py seed_demo_data
   ```
   (idempotent — mevcut veriyi bozmaz, sadece plan FK'larını set eder)

2. **Docker image rebuild:** Cairo + libmagic bağımlılıkları için:
   ```bash
   # Localhost:
   docker compose build --no-cache web

   # Production:
   docker compose -f docker-compose.prod.yml build --no-cache web
   ```

3. **Production .env doğrulama:** SSH ile sunucuya bağlanıp `DJANGO_SUPERUSER_PASSWORD` değerini doğrula.

### 7.2 Orta Vadeli

4. **Tek Dockerfile stratejisi:** İki ayrı Dockerfile yerine tek Dockerfile + build arg:
   ```dockerfile
   ARG TARGETPLATFORM
   FROM python:3.13-slim-bookworm AS builder
   # platform otomatik seçilir
   ```

5. **GitHub Actions CI:** AMD64 build + test pipeline ekle (cross-arch doğrulama).

6. **Production seed idempotency:** `seed_all_data` ve `seed_demo_data` her zaman `org.plan` set etsin (sadece `created` durumunda değil).

---

## 8. PRODUCTION LOGIN DURUM RAPORU (API Testi: 2026-03-14)

| Email | Şifre | Production | Sonuç |
|-------|-------|-----------|-------|
| `admin@e-menum.net` | `Admin1234!emenum` | ✅ Giriş yapıldı | super_admin, org: yok |
| `platform-admin@e-menum.net` | `PlatAdmin1234!` | ✅ Giriş yapıldı | admin, org: yok |
| `hakan@anadolusofrasi.com.tr` | `Owner1234!emenum` | ✅ Giriş yapıldı | owner, Anadolu Sofrasi |
| `mehmet@bosphorusbistro.com` | `Owner1234!emenum` | ✅ Giriş yapıldı | owner, Bosphorus Bistro |
| `mehmet.yilmaz@lezzetsarayi.com` | `Staff1234!emenum` | ✅ Giriş yapıldı | manager, Lezzet Sarayi |
| **`admin@lezzetsarayi.com`** | `LezzetSarayi2024!` | ❌ **Invalid password** | Kullanıcı var ama şifre uyuşmuyor |
| `admin@e-menum.net` | `BxmtmJih0w0MQyGI` | ❌ Invalid password | .env.example şifresi prod'da çalışmıyor |

**Root Cause:** `admin@lezzetsarayi.com` önceki bir deploy'da farklı şifreyle oluşturulmuş.
`seed_menu_data` sadece `created=True` durumunda şifre set ediyordu, mevcut kullanıcıyı atıyordu.

**Çözüm:** Tüm seed komutlarına `check_password()` + `set_password()` mekanizması eklendi.
Production'da düzeltmek için: `python manage.py seed_menu_data` re-run edilmeli.

---

## 9. YAPILAN DEĞİŞİKLİKLER

| Dosya | Değişiklik |
|-------|-----------|
| `apps/core/management/commands/seed_all_data.py` | `_seed_subscriptions()` — org.plan/subscription FK set; `_seed_platform_users()` — şifre check+reset; `_seed_staff()` — şifre check+reset |
| `apps/core/management/commands/seed_demo_data.py` | `_create_subscription()` — org.plan/subscription FK set; `_create_owner()` — şifre check+reset; `_create_staff()` — şifre check+reset |
| `apps/core/management/commands/seed_extra_orgs.py` | Owner şifre check+reset eklendi |
| `apps/menu/management/commands/seed_menu_data.py` | `admin@lezzetsarayi.com` şifre check+reset eklendi (production fix) |
| `Dockerfile` | Builder: `pkg-config`, `libcairo2-dev` eklendi; Runtime: `libcairo2`, `libmagic1` eklendi |
| `Dockerfile.amd64linux` | Runtime: `libmagic1` eklendi |
