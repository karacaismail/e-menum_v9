# E-Menum Deploy Rehberi v2 - Huseyin

> **Tarih:** 2026-02-24
> **Proje:** E-Menum - Enterprise QR Menu SaaS
> **Repo:** https://github.com/karacaismail/e-menum_v9
> **Hedef Server:** Hetzner VPS (AMD64 Linux)
> **Onceki Versiyon:** huseyin.md (v1 - 2026-02-22)

---

## NELER DEGISTI (v1 → v2)

| Degisiklik | Aciklama |
|------------|----------|
| `Dockerfile.amd64linux` | AMD64 Linux icin yeni Dockerfile (heredoc hatasi yok) |
| `docker-compose.prod.yml` | Production-ready compose dosyasi (repo icinde) |
| `docker/entrypoint.sh` | Harici entrypoint scripti (DB bekle, migrate, superuser) |
| `.env.example` | Tum degiskenler eksiksiz, random sifreler |
| `Dockerfile` (orijinal) | Heredoc hatasi duzeltildi, CMD exec form |
| Dashboard app | Admin dashboard + KPI + charts eklendi |
| Website app | Corporate storefront eklendi |
| SEO app | SEO modulu + SEO Shield eklendi |

---

## REPO YAPISI

```
https://github.com/karacaismail/e-menum_v9
│
└── e_menum/                              ← UYGULAMA BURASI (manage.py burada)
    │
    ├── Dockerfile                        ← Genel Dockerfile (Mac + Linux)
    ├── Dockerfile.amd64linux             ← ⭐ HETZNER ICIN BU DOSYA
    ├── docker-compose.yml                ← Development compose (lokal icin)
    ├── docker-compose.prod.yml           ← ⭐ PRODUCTION COMPOSE (sunucu icin)
    ├── .env.example                      ← ⭐ ORTAM DEGISKENLERI SABLONU
    │
    ├── docker/
    │   ├── entrypoint.sh                 ← Container baslangic scripti
    │   └── init-db.sql                   ← PostgreSQL extension'lar
    │
    ├── manage.py                         ← Django CLI
    ├── requirements.txt                  ← Python production bagimliliklar
    ├── requirements-dev.txt              ← Python dev bagimliliklar
    ├── pytest.ini                        ← Test config
    ├── conftest.py                       ← Test fixtures
    │
    ├── config/                           ← Django ayarlari
    │   ├── settings/
    │   │   ├── base.py                   ← Temel ayarlar
    │   │   ├── development.py            ← Dev: DEBUG=True
    │   │   └── production.py             ← Prod: guvenlik + performans
    │   ├── urls.py
    │   ├── wsgi.py                       ← Gunicorn bunu kullanir
    │   └── celery.py                     ← Celery config
    │
    ├── apps/                             ← Django uygulamalari
    │   ├── core/                         ← Kullanicilar, organizasyonlar
    │   ├── menu/                         ← Menu, kategori, urunler
    │   ├── orders/                       ← Masalar, QR, siparisler
    │   ├── subscriptions/                ← Planlar, abonelik
    │   ├── customers/                    ← Musteri profilleri
    │   ├── dashboard/                    ← ⭐ Admin dashboard + KPI
    │   ├── website/                      ← ⭐ Corporate storefront
    │   ├── seo/                          ← ⭐ SEO modulu
    │   ├── seo_shield/                   ← ⭐ Bot koruma, rate limit
    │   ├── reporting/                    ← Raporlar
    │   ├── inventory/                    ← Stok yonetimi
    │   ├── campaigns/                    ← Kampanyalar
    │   ├── notifications/                ← Bildirimler
    │   ├── media/                        ← Dosya yonetimi
    │   ├── ai/                           ← AI icerik uretimi
    │   └── analytics/                    ← Veri toplama
    │
    ├── templates/                        ← HTML sablonlar
    ├── static/                           ← CSS, JS, resimler
    └── locale/                           ← i18n (tr, en, ar, fa, uk)
```

---

## BOLUM 1: HIZLI KURULUM (5 ADIM)

> Acele ediyorsan sadece bu bolumu takip et.

### Adim 1: Repo'yu cek

```bash
ssh deploy@HETZNER_IP

cd /opt
git clone https://github.com/karacaismail/e-menum_v9.git emenum-src
cd /opt/emenum-src/e_menum
```

### Adim 2: .env dosyasini olustur

```bash
cp .env.example .env
nano .env
```

**MUTLAKA degistirilecek degerler:**

| Degisken | Ne yapacaksin |
|----------|---------------|
| `DJANGO_SECRET_KEY` | Yeni random key uret (asagiya bak) |
| `POSTGRES_PASSWORD` | Yeni guclu sifre yaz |
| `DATABASE_URL` | Icindeki sifreyi POSTGRES_PASSWORD ile ayni yap |
| `DJANGO_SUPERUSER_PASSWORD` | Admin panel sifresi |
| `ALLOWED_HOSTS` | Domain veya IP adresini yaz |
| `CSRF_TRUSTED_ORIGINS` | Domain'in tam URL'si |
| `SITE_URL` | Domain'in tam URL'si |

**Secret key uretmek icin:**

```bash
python3 -c "from secrets import token_urlsafe; print(token_urlsafe(50))"
```

**Guclu sifre uretmek icin:**

```bash
python3 -c "from secrets import token_urlsafe; print(token_urlsafe(24))"
```

### Adim 3: Build et

```bash
cd /opt/emenum-src/e_menum
docker compose -f docker-compose.prod.yml build
```

### Adim 4: Baslat

```bash
docker compose -f docker-compose.prod.yml up -d
```

### Adim 5: Kontrol et

```bash
# Container durumlarini goster
docker compose -f docker-compose.prod.yml ps

# Beklenen cikti:
# NAME                  STATUS              PORTS
# emenum_db             Up (healthy)        127.0.0.1:5432->5432/tcp
# emenum_redis          Up (healthy)        127.0.0.1:6379->6379/tcp
# emenum_web            Up (healthy)        0.0.0.0:8000->8000/tcp
# emenum_celery_worker  Up
# emenum_celery_beat    Up

# Web testi
curl http://localhost:8000/health/
# Beklenen: {"success": true, ...}

# Admin paneline eris
curl -I http://localhost:8000/admin/
# Beklenen: HTTP 302 (login'e yonlendirir)
```

> **NOT:** entrypoint.sh otomatik olarak:
> - DB hazir olana kadar bekler (30 deneme)
> - Migration calistirir (`DJANGO_MIGRATE=true`)
> - Static dosyalari toplar (`DJANGO_COLLECTSTATIC=true`)
> - Superuser olusturur (`DJANGO_CREATE_SUPERUSER=true`)

---

## BOLUM 2: .ENV DEGISKENLERI (TAM LISTE)

### 2.1 Django Core (ZORUNLU)

| Degisken | Varsayilan | Aciklama |
|----------|-----------|----------|
| `DJANGO_SECRET_KEY` | *(random)* | **MUTLAKA degistir!** 50+ karakter |
| `DEBUG` | `False` | Uretimde MUTLAKA False |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` | Ayar dosyasi |
| `ALLOWED_HOSTS` | `e-menum.com,...` | Izin verilen hostlar (virgul ile) |
| `CSRF_TRUSTED_ORIGINS` | `https://e-menum.com,...` | CSRF guvenilir URL'ler |
| `CORS_ALLOWED_ORIGINS` | `https://e-menum.com,...` | CORS izinli originler |
| `SITE_URL` | `https://e-menum.com` | Mutlak URL uretimi icin |

### 2.2 PostgreSQL (ZORUNLU)

| Degisken | Varsayilan | Aciklama |
|----------|-----------|----------|
| `POSTGRES_USER` | `emenum_user` | DB kullanici adi |
| `POSTGRES_PASSWORD` | *(random)* | **MUTLAKA degistir!** |
| `POSTGRES_DB` | `emenum` | DB adi |
| `POSTGRES_PORT` | `5432` | DB portu |
| `DATABASE_URL` | `postgresql://USER:PASS@db:5432/DB` | Tam baglanti URL'i |
| `DATABASE_SSL_REQUIRE` | `false` | Docker icinde false |

### 2.3 Redis

| Degisken | Varsayilan | Aciklama |
|----------|-----------|----------|
| `REDIS_URL` | `redis://redis:6379/0` | Cache icin |
| `REDIS_PORT` | `6379` | Redis portu |

### 2.4 Celery

| Degisken | Varsayilan | Aciklama |
|----------|-----------|----------|
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/1` | Celery sonuc |
| `CELERY_WORKER_CONCURRENCY` | `4` | Worker eslezamanlilik |

### 2.5 Web Server

| Degisken | Varsayilan | Aciklama |
|----------|-----------|----------|
| `WEB_PORT` | `8000` | Web portu |
| `SECURE_SSL_REDIRECT` | `false` | Nginx arkasinda false |
| `TZ` | `Europe/Istanbul` | Zaman dilimi |
| `LANGUAGE_CODE` | `tr` | Varsayilan dil |

### 2.6 Docker Entrypoint

| Degisken | Varsayilan | Aciklama |
|----------|-----------|----------|
| `DJANGO_MIGRATE` | `true` | Otomatik migration |
| `DJANGO_COLLECTSTATIC` | `true` | Otomatik static toplama |
| `DJANGO_CREATE_SUPERUSER` | `true` | Otomatik superuser (ilk seferde true, sonra false) |
| `DJANGO_SUPERUSER_EMAIL` | `admin@emenum.com` | Superuser e-posta |
| `DJANGO_SUPERUSER_PASSWORD` | *(random)* | **MUTLAKA degistir!** |

### 2.7 JWT

| Degisken | Varsayilan | Aciklama |
|----------|-----------|----------|
| `JWT_ACCESS_TOKEN_LIFETIME` | `15` | Access token suresi (dakika) |
| `JWT_REFRESH_TOKEN_LIFETIME` | `10080` | Refresh token suresi (7 gun) |

### 2.8 Email (OPSIYONEL)

| Degisken | Varsayilan | Aciklama |
|----------|-----------|----------|
| `EMAIL_BACKEND` | `smtp.EmailBackend` | Email backend |
| `EMAIL_HOST` | `smtp.example.com` | SMTP host |
| `EMAIL_PORT` | `587` | SMTP port |
| `EMAIL_HOST_USER` | *(bos)* | SMTP kullanici |
| `EMAIL_HOST_PASSWORD` | *(bos)* | SMTP sifre |
| `EMAIL_USE_TLS` | `True` | TLS kullan |
| `DEFAULT_FROM_EMAIL` | `noreply@e-menum.com` | Gonderen e-posta |

### 2.9 Monitoring (OPSIYONEL)

| Degisken | Varsayilan | Aciklama |
|----------|-----------|----------|
| `DJANGO_LOG_LEVEL` | `INFO` | Log seviyesi |
| `DB_LOG_LEVEL` | `WARNING` | DB log seviyesi |
| `SENTRY_DSN` | *(bos)* | Sentry hata takibi |
| `SENTRY_ENVIRONMENT` | `production` | Sentry ortam |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Sentry sampling |

### 2.10 AI & Storage (OPSIYONEL)

| Degisken | Varsayilan | Aciklama |
|----------|-----------|----------|
| `OPENAI_API_KEY` | *(bos)* | AI icerik uretimi |
| `OPENAI_MODEL` | `gpt-4` | AI model |
| `AWS_ACCESS_KEY_ID` | *(bos)* | S3 media |
| `AWS_SECRET_ACCESS_KEY` | *(bos)* | S3 media |
| `AWS_STORAGE_BUCKET_NAME` | *(bos)* | S3 bucket |
| `AWS_S3_REGION_NAME` | `eu-central-1` | S3 bolge |

---

## BOLUM 3: SERVER HAZIRLIK (Hetzner)

### 3.1 Server Gereksinimleri

| Kaynak | Minimum | Onerilen |
|--------|---------|----------|
| CPU | 2 vCPU (CX21) | 4 vCPU (CX31) |
| RAM | 4 GB | 8 GB |
| Disk | 40 GB SSD | 80 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |

### 3.2 Ilk Server Hazirlik

```bash
# Root olarak baglan
ssh root@HETZNER_IP

# Sistem guncelle
apt update && apt upgrade -y

# Gerekli paketler
apt install -y \
  curl wget git ufw fail2ban htop nano unzip \
  software-properties-common apt-transport-https \
  ca-certificates gnupg lsb-release

# Timezone
timedatectl set-timezone Europe/Istanbul
```

### 3.3 Guvenlik Ayarlari

```bash
# --- Deploy kullanicisi olustur ---
adduser deploy
usermod -aG sudo deploy

# SSH key kopyala
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# --- SSH Hardening ---
nano /etc/ssh/sshd_config
#   PermitRootLogin no
#   PasswordAuthentication no
#   PubkeyAuthentication yes
#   Port 2222  (opsiyonel)
#   AllowUsers deploy
systemctl restart sshd

# --- Firewall ---
ufw default deny incoming
ufw default allow outgoing
ufw allow 2222/tcp   # SSH (veya 22)
ufw allow 80/tcp     # HTTP
ufw allow 443/tcp    # HTTPS
ufw enable

# --- Fail2ban ---
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
systemctl enable fail2ban && systemctl start fail2ban
```

### 3.4 Docker Kurulumu

```bash
# Docker GPG key ve repo
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker kur
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Deploy kullanicisini docker grubuna ekle
usermod -aG docker deploy

# Dogrula
docker --version
docker compose version
```

### 3.5 Nginx Kurulumu

```bash
apt install -y nginx certbot python3-certbot-nginx
systemctl enable nginx && systemctl start nginx
```

---

## BOLUM 4: UYGULAMA DEPLOY

### 4.1 Repo'yu Server'a Al

```bash
su - deploy
sudo mkdir -p /opt/emenum-src
sudo chown deploy:deploy /opt/emenum-src
cd /opt/emenum-src

git clone https://github.com/karacaismail/e-menum_v9.git
cd e-menum_v9/e_menum
```

### 4.2 Environment Dosyasini Olustur

```bash
cp .env.example .env
nano .env
```

**DEGISTIRILMESI GEREKEN DEGERLER:**

```bash
# 1. Yeni secret key uret ve yapistir
python3 -c "from secrets import token_urlsafe; print(token_urlsafe(50))"

# 2. Yeni DB sifresi uret ve yapistir
python3 -c "from secrets import token_urlsafe; print(token_urlsafe(24))"

# 3. Yeni superuser sifresi uret ve yapistir
python3 -c "from secrets import token_urlsafe; print(token_urlsafe(16))"
```

`.env` icinde su satirlari guncelle:

```bash
DJANGO_SECRET_KEY=BURAYA-URETILEN-SECRET-KEY
POSTGRES_PASSWORD=BURAYA-URETILEN-DB-SIFRESI
DATABASE_URL=postgresql://emenum_user:BURAYA-AYNI-DB-SIFRESI@db:5432/emenum
DJANGO_SUPERUSER_PASSWORD=BURAYA-URETILEN-ADMIN-SIFRESI
ALLOWED_HOSTS=e-menum.com,www.e-menum.com,HETZNER_IP
CSRF_TRUSTED_ORIGINS=https://e-menum.com,https://www.e-menum.com
SITE_URL=https://e-menum.com
```

### 4.3 Build ve Baslat

```bash
cd /opt/emenum-src/e-menum_v9/e_menum

# Build (ilk sefer uzun surer ~5 dk)
docker compose -f docker-compose.prod.yml build

# Baslat
docker compose -f docker-compose.prod.yml up -d

# Loglari izle (ilk baslatmada migration calisacak)
docker compose -f docker-compose.prod.yml logs -f web
```

**Beklenen log ciktisi:**

```
========================================
E-Menum Django Application Starting...
========================================
Settings: config.settings.production
Port: 8000
========================================
Checking database connection...
Database is ready!
Running database migrations...
Migrations complete.
Creating superuser if not exists...
Superuser created.
Collecting static files...
Starting application...
[INFO] Starting gunicorn 25.1.0
[INFO] Listening at: http://0.0.0.0:8000
```

### 4.4 Nginx Konfigurasyonu

```bash
sudo nano /etc/nginx/sites-available/emenum
```

```nginx
# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name e-menum.com www.e-menum.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name e-menum.com www.e-menum.com;

    # SSL (certbot olusturacak)
    ssl_certificate /etc/letsencrypt/live/e-menum.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/e-menum.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss image/svg+xml;

    # Max upload (menu fotograflari)
    client_max_body_size 10M;

    # Static files
    location /static/ {
        alias /opt/emenum-src/e-menum_v9/e_menum/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media files
    location /media/ {
        alias /opt/emenum-src/e-menum_v9/e_menum/media/;
        expires 7d;
        add_header Cache-Control "public";
        access_log off;
    }

    # Django uygulamasi
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60;
        proxy_send_timeout 120;
        proxy_read_timeout 120;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/emenum /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

### 4.5 SSL Sertifikasi

```bash
# DNS A record'u Hetzner IP'ye yonlendirdikten sonra:
sudo certbot --nginx -d e-menum.com -d www.e-menum.com

# Auto-renewal test
sudo certbot renew --dry-run
```

### 4.6 Static Dosya Erisimi (Nginx icin)

Nginx container disinda calistigi icin static dosyalara host'tan erismesi gerekir:

```bash
# Static dosyalari container'dan host'a kopyala
docker cp emenum_web:/app/staticfiles /opt/emenum-src/e-menum_v9/e_menum/staticfiles

# Media dizini olustur
mkdir -p /opt/emenum-src/e-menum_v9/e_menum/media
```

> **ALTERNATIF:** docker-compose.prod.yml'daki volumes'u bind mount'a cevir:
> ```yaml
> volumes:
>   - /opt/emenum-src/e-menum_v9/e_menum/staticfiles:/app/staticfiles
>   - /opt/emenum-src/e-menum_v9/e_menum/media:/app/media
> ```

---

## BOLUM 5: DOGRULAMA

### 5.1 Container Durumu

```bash
cd /opt/emenum-src/e-menum_v9/e_menum
docker compose -f docker-compose.prod.yml ps

# Beklenen:
# NAME                  STATUS              PORTS
# emenum_db             Up (healthy)        127.0.0.1:5432->5432
# emenum_redis          Up (healthy)        127.0.0.1:6379->6379
# emenum_web            Up (healthy)        0.0.0.0:8000->8000
# emenum_celery_worker  Up
# emenum_celery_beat    Up
```

### 5.2 Servis Testleri

```bash
# Health check
curl http://localhost:8000/health/

# Admin panel (302 = basarili, login'e yonlendirir)
curl -I http://localhost:8000/admin/

# Nginx arkasindan (SSL sonrasi)
curl -I https://e-menum.com/admin/

# Redis testi
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
# Beklenen: PONG

# DB testi
docker compose -f docker-compose.prod.yml exec web python manage.py check --deploy
```

### 5.3 Endpoint Listesi

| URL | Aciklama |
|-----|----------|
| `/admin/` | Admin Panel (Metronic dark theme) |
| `/admin/dashboard/` | Dashboard (KPI, charts) |
| `/health/` | Health check |
| `/` | Corporate website (anasayfa) |
| `/pricing/` | Fiyatlandirma sayfasi |
| `/features/` | Ozellikler sayfasi |
| `/about/` | Hakkimizda |
| `/contact/` | Iletisim |
| `/blog/` | Blog |
| `/api/v1/` | REST API root |
| `/api/v1/auth/login/` | JWT login |
| `/m/<slug>/` | Public menu (QR ile erisim) |

---

## BOLUM 6: BAKIM ISLEMLERI

### 6.1 Guncelleme (Yeni versiyon deploy)

```bash
cd /opt/emenum-src/e-menum_v9

# Yeni kodu cek
git pull origin main

# Rebuild ve restart
cd e_menum
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Loglari izle
docker compose -f docker-compose.prod.yml logs -f web
```

> **NOT:** entrypoint.sh otomatik migration ve collectstatic yapar.
> Manuel calistirmak istersen:
> ```bash
> docker compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput
> docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
> ```

### 6.2 Yedekleme

```bash
# PostgreSQL yedekle
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U emenum_user emenum | gzip > /opt/backups/db_$(date +%Y%m%d_%H%M%S).sql.gz

# Media yedekle
tar -czf /opt/backups/media_$(date +%Y%m%d_%H%M%S).tar.gz \
  /opt/emenum-src/e-menum_v9/e_menum/media/

# Cron ile otomatik (her gece 03:00)
crontab -e
# Ekle:
# 0 3 * * * cd /opt/emenum-src/e-menum_v9/e_menum && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U emenum_user emenum | gzip > /opt/backups/db_$(date +\%Y\%m\%d).sql.gz
# 0 4 * * * find /opt/backups/ -type f -mtime +30 -delete
```

### 6.3 Yedekten Geri Yukleme

```bash
cd /opt/emenum-src/e-menum_v9/e_menum

# Container'lari durdur
docker compose -f docker-compose.prod.yml stop web celery_worker celery_beat

# DB'yi geri yukle
gunzip < /opt/backups/db_20260224.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T db psql -U emenum_user emenum

# Baslat
docker compose -f docker-compose.prod.yml start web celery_worker celery_beat
```

### 6.4 Log Izleme

```bash
CD=/opt/emenum-src/e-menum_v9/e_menum

# Tum loglar
docker compose -f docker-compose.prod.yml logs -f

# Sadece web
docker compose -f docker-compose.prod.yml logs -f web

# Sadece hatalar
docker compose -f docker-compose.prod.yml logs -f web 2>&1 | grep -i error

# Celery
docker compose -f docker-compose.prod.yml logs -f celery_worker

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 6.5 Sorun Giderme

```bash
CD=/opt/emenum-src/e-menum_v9/e_menum

# Container restart
docker compose -f docker-compose.prod.yml restart web

# Tamamen yeniden baslat
docker compose -f docker-compose.prod.yml down && docker compose -f docker-compose.prod.yml up -d

# Container icine gir
docker compose -f docker-compose.prod.yml exec web bash

# Django shell
docker compose -f docker-compose.prod.yml exec web python manage.py shell

# Django deploy check
docker compose -f docker-compose.prod.yml exec web python manage.py check --deploy

# Kaynak kullanimi
docker stats

# Disk kullanimi
docker system df
```

---

## BOLUM 7: TEKNIK DETAYLAR

### 7.1 Dockerfile.amd64linux Stages

```
Stage 1: builder       → Python venv + pip install (--platform=linux/amd64)
Stage 2: production    → Minimal runtime, non-root user (emenum:1000), Gunicorn
Stage 3: development   → + dev dependencies, Django runserver
Stage 4: celery-worker → Celery worker CMD
Stage 5: celery-beat   → Celery beat CMD
```

- Base image: `python:3.11-slim-bookworm`
- Non-root user: `emenum` (UID/GID 1000)
- Entrypoint: `tini` (signal handling) + `entrypoint.sh` (DB wait + migrate + superuser)
- Health check: `curl http://localhost:8000/health/`

### 7.2 docker/entrypoint.sh Ne Yapar?

```
1. DATABASE_URL varsa → DB'ye baglanmayi bekler (30 deneme, 2sn aralik)
2. DJANGO_MIGRATE=true → python manage.py migrate --noinput
3. DJANGO_CREATE_SUPERUSER=true → admin kullanici olusturur (varsa atlar)
4. DJANGO_COLLECTSTATIC=true → python manage.py collectstatic --noinput
5. exec "$@" → Asil komutu calistirir (gunicorn, celery, vb.)
```

### 7.3 PostgreSQL Extensions

| Extension | Amac |
|-----------|------|
| `uuid-ossp` | UUID uretimi |
| `unaccent` | Turkce full-text search |
| `pgcrypto` | Kriptografik fonksiyonlar |
| `citext` | Case-insensitive text |
| `pg_trgm` | Fuzzy search (trigram) |

### 7.4 Versiyon Matrisi

| Yazilim | Versiyon |
|---------|----------|
| Python | 3.11 |
| Django | 5.2.x |
| PostgreSQL | 15-alpine |
| Redis | 7-alpine |
| Gunicorn | 25.x |
| Celery | 5.6.x |
| DRF | 3.16.x |
| Nginx | latest |

### 7.5 Guvenlik

- `SECRET_KEY`: Env variable, kod icinde yok
- `DEBUG=False`: Uretimde zorunlu
- Password: BCrypt SHA256
- JWT: Access 15dk, Refresh 7 gun
- HSTS: 1 yil, preload aktif
- Cookie: Secure + HttpOnly + SameSite=Lax
- Ports: DB ve Redis sadece 127.0.0.1 (dis erisim yok)

---

## DEPLOY CHECKLIST

```
[ ] 1. Hetzner server hazirla (Ubuntu 22/24, Docker, Nginx)
[ ] 2. Guvenlik: SSH hardening, UFW, fail2ban
[ ] 3. git clone https://github.com/karacaismail/e-menum_v9.git
[ ] 4. cd e-menum_v9/e_menum && cp .env.example .env
[ ] 5. .env icindeki sifreleri degistir (SECRET_KEY, POSTGRES_PASSWORD, SUPERUSER_PASSWORD)
[ ] 6. .env icindeki domain/IP bilgilerini guncelle
[ ] 7. docker compose -f docker-compose.prod.yml build
[ ] 8. docker compose -f docker-compose.prod.yml up -d
[ ] 9. docker compose -f docker-compose.prod.yml logs -f web (migration calistigini dogrula)
[ ] 10. curl http://localhost:8000/health/ (200 OK beklenir)
[ ] 11. Nginx config yaz ve aktifle
[ ] 12. DNS A record'u Hetzner IP'ye yonlendir
[ ] 13. certbot ile SSL sertifikasi al
[ ] 14. https://e-menum.com/admin/ test et (login sayfasi gelmeli)
[ ] 15. .env'de DJANGO_CREATE_SUPERUSER=false yap (bir kere yeterli)
[ ] 16. Cron backup job'u kur
```

---

> **Sorularin icin:** Ismail'e ulas (Strategic Lead)
> **Repo:** https://github.com/karacaismail/e-menum_v9
> **Uygulama dizini:** `e-menum_v9/e_menum/`
> **Production Dockerfile:** `e_menum/Dockerfile.amd64linux`
> **Production Compose:** `e_menum/docker-compose.prod.yml`
> **Env sablonu:** `e_menum/.env.example`
