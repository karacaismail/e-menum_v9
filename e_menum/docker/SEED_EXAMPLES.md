# E-Menum – Seed tetikleme örnekleri

Container içinden veya sunucuda seed komutlarını nasıl çalıştıracağınız aşağıda.

---

## 1. Tüm seed’leri sırayla (tek seferde)

```bash
# Web container’a bağlanıp hepsini sırayla çalıştır
docker exec -it emenum_web bash -c '
python manage.py seed_roles &&
python manage.py seed_plans &&
python manage.py seed_allergens &&
python manage.py seed_menu_data &&
python manage.py seed_extra_orgs &&
python manage.py seed_all_data &&
python manage.py seed_demo_data &&
python manage.py seed_cms_content &&
python manage.py seed_seo_data &&
python manage.py seed_report_definitions &&
python manage.py seed_shield_data
'
```

---

## 2. Tek tek (denemek için)

```bash
# Roller ve yetkiler
docker exec -it emenum_web python manage.py seed_roles

# Planlar ve özellikler
docker exec -it emenum_web python manage.py seed_plans

# Alerjenler
docker exec -it emenum_web python manage.py seed_allergens

# Base org + menü (Lezzet Sarayı)
docker exec -it emenum_web python manage.py seed_menu_data

# Ekstra organizasyonlar
docker exec -it emenum_web python manage.py seed_extra_orgs

# Lezzet Sarayı tam veri (branches, siparişler, müşteriler vb.)
docker exec -it emenum_web python manage.py seed_all_data

# Demo orglar + orchestration
docker exec -it emenum_web python manage.py seed_demo_data

# CMS (sayfalar, blog, FAQ vb.)
docker exec -it emenum_web python manage.py seed_cms_content

# SEO (robots, sitemap, redirects)
docker exec -it emenum_web python manage.py seed_seo_data

# Rapor tanımları
docker exec -it emenum_web python manage.py seed_report_definitions

# Shield (bot whitelist, kurallar)
docker exec -it emenum_web python manage.py seed_shield_data
```

---

## 3. Sadece “üst seviye” 5’li (entrypoint’teki eski set)

```bash
docker exec -it emenum_web bash -c '
python manage.py seed_demo_data &&
python manage.py seed_cms_content &&
python manage.py seed_seo_data &&
python manage.py seed_report_definitions &&
python manage.py seed_shield_data
'
```

---

## 4. Opsiyonlu parametreler

```bash
# seed_roles: force / dry-run
docker exec -it emenum_web python manage.py seed_roles --force
docker exec -it emenum_web python manage.py seed_roles --dry-run

# seed_plans
docker exec -it emenum_web python manage.py seed_plans --force
docker exec -it emenum_web python manage.py seed_plans --dry-run

# seed_allergens
docker exec -it emenum_web python manage.py seed_allergens --force
docker exec -it emenum_web python manage.py seed_allergens --dry-run

# seed_demo_data: sadece yeni orglar, bağımlılıkları atla
docker exec -it emenum_web python manage.py seed_demo_data --skip-deps

# seed_demo_data: mevcut demo orgları silip yeniden
docker exec -it emenum_web python manage.py seed_demo_data --clear

# seed_menu_data: önce mevcut menü verisini temizle
docker exec -it emenum_web python manage.py seed_menu_data --clear

# seed_extra_orgs: önce ekstra orgları temizle
docker exec -it emenum_web python manage.py seed_extra_orgs --clear

# seed_seo_data / seed_shield_data: mevcut veriyi temizleyip yeniden
docker exec -it emenum_web python manage.py seed_seo_data --clear
docker exec -it emenum_web python manage.py seed_shield_data --clear
```

---

## 5. Otomatik tetikleme (entrypoint)

`DJANGO_SEED_DATA=true` (compose’ta varsayılan) ise:

- Gunicorn ayağa kalkar, port dinlenir.
- `Role` sayısı 0 ise yukarıdaki **11 seed** sırayla çalışır.
- Veri varsa seed atlanır.

Kurulumu sıfırdan denemek için:

```bash
# Volume’leri de silerek sıfırdan
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d
docker logs -f emenum_web   # seed loglarını izle
```

---

## Sıra özeti

| Sıra | Komut | Açıklama |
|------|--------|----------|
| 1 | seed_roles | Roller ve yetkiler |
| 2 | seed_plans | Planlar ve özellikler |
| 3 | seed_allergens | Alerjen listesi |
| 4 | seed_menu_data | Lezzet Sarayı org + menü |
| 5 | seed_extra_orgs | Ekstra organizasyonlar |
| 6 | seed_all_data | Lezzet Sarayı tam veri |
| 7 | seed_demo_data | Demo orglar + orchestration |
| 8 | seed_cms_content | CMS içerik |
| 9 | seed_seo_data | SEO verileri |
| 10 | seed_report_definitions | Rapor tanımları |
| 11 | seed_shield_data | Shield kuralları |
