# E-Menum Hetzner Deploy Rehberi

> **Haziran 2026 — Huseyin Cengiz (DevOps)**
> Son guncelleme: 2026-02-25

---

## Icindekiler

1. [Sunucu Gereksinimleri](#1-sunucu-gereksinimleri)
2. [Hetzner Sunucu Kurulumu](#2-hetzner-sunucu-kurulumu)
3. [Proje Deployment](#3-proje-deployment)
4. [Nginx Reverse Proxy & SSL](#4-nginx-reverse-proxy--ssl)
5. [Ilk Calistirma Sonrasi](#5-ilk-calistirma-sonrasi)
6. [Guncelleme (CI/CD)](#6-guncelleme-cicd)
7. [Monitoring & Loglar](#7-monitoring--loglar)
8. [Backup & Restore](#8-backup--restore)
9. [Troubleshooting (Gecmis Hatalar)](#9-troubleshooting-gecmis-hatalar)
10. [Faydali Komutlar](#10-faydali-komutlar)

---

## 1. Sunucu Gereksinimleri

### Minimum (CX21 — Starter/Professional Tier)

| Kaynak | Minimum | Onerilen |
|--------|---------|----------|
| CPU | 2 vCPU | 4 vCPU |
| RAM | 4 GB | 8 GB |
| Disk | 40 GB SSD | 80 GB NVMe |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| Arch | **AMD64 (x86_64)** | AMD64 |

### Yazilim Gereksinimleri

| Yazilim | Min. Surum | Kontrol Komutu |
|---------|------------|----------------|
| Docker Engine | 24.0+ | `docker --version` |
| Docker Compose | v2.20+ | `docker compose version` |
| Git | 2.34+ | `git --version` |
| Nginx | 1.18+ | `nginx -v` |
| Certbot | 2.0+ | `certbot --version` |

> **NOT:** Docker Compose v2 (plugin) kullaniyoruz, v1 (standalone) degil.
> Komut: `docker compose` (tire yok), ~~`docker-compose`~~ degil.

---

## 2. Hetzner Sunucu Kurulumu

### 2.1 Sunucuya Baglan

```bash
ssh root@SUNUCU_IP
```

### 2.2 Sistem Guncelleme

```bash
apt update && apt upgrade -y
apt install -y curl git wget nano ufw fail2ban
```

### 2.3 Docker Kurulumu

```bash
# Docker resmi GPG anahtari
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Docker repo ekle
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Kur
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Dogrula
docker --version
docker compose version
```

### 2.4 Deploy Kullanicisi Olustur (root ile calisma!)

```bash
adduser emenum
usermod -aG docker emenum
usermod -aG sudo emenum

# SSH key kopyala
mkdir -p /home/emenum/.ssh
cp ~/.ssh/authorized_keys /home/emenum/.ssh/
chown -R emenum:emenum /home/emenum/.ssh
chmod 700 /home/emenum/.ssh
chmod 600 /home/emenum/.ssh/authorized_keys
```

### 2.5 Firewall Ayarlari

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
ufw status
```

### 2.6 Nginx Kurulumu

```bash
apt install -y nginx certbot python3-certbot-nginx
systemctl enable nginx
systemctl start nginx
```

---

## 3. Proje Deployment

### 3.1 Projeyi Cek

```bash
# emenum kullanicisina gec
su - emenum

# Proje dizini
mkdir -p ~/apps
cd ~/apps

# GitHub'dan cek
git clone https://github.com/karacaismail/e-menum_v9.git
cd e-menum_v9/e_menum
```

### 3.2 Environment Dosyasi Olustur

```bash
cp .env.example .env
nano .env
```

#### ZORUNLU degistirilecek degerler:

```env
# ──────────────────────────────────────────────────
# 1. GUVENLIK — Mutlaka degistir!
# ──────────────────────────────────────────────────
DJANGO_SECRET_KEY=<asagidaki komutla uret>
POSTGRES_PASSWORD=<guclu-sifre-min-20-karakter>
DJANGO_SUPERUSER_PASSWORD=<admin-sifresi-min-12-karakter>

# ──────────────────────────────────────────────────
# 2. DOMAIN AYARLARI
# ──────────────────────────────────────────────────
ALLOWED_HOSTS=e-menum.com,www.e-menum.com,api.e-menum.com,SUNUCU_IP
CSRF_TRUSTED_ORIGINS=https://e-menum.com,https://www.e-menum.com
CORS_ALLOWED_ORIGINS=https://e-menum.com,https://www.e-menum.com
SITE_URL=https://e-menum.com

# ──────────────────────────────────────────────────
# 3. DOCKER INTERNAL — Degistirme!
# ──────────────────────────────────────────────────
DATABASE_SSL_REQUIRE=false
SECURE_SSL_REDIRECT=false
# (SSL, Nginx tarafindan yonetilir)

# ──────────────────────────────────────────────────
# 4. ILK CALISTIRMA AYARLARI
# ──────────────────────────────────────────────────
DJANGO_MIGRATE=true
DJANGO_COLLECTSTATIC=true
DJANGO_CREATE_SUPERUSER=true
DJANGO_SUPERUSER_EMAIL=admin@emenum.com

# ──────────────────────────────────────────────────
# 5. E-POSTA (Opsiyonel — sonra ayarlanabilir)
# ──────────────────────────────────────────────────
# EMAIL_HOST=smtp.example.com
# EMAIL_HOST_USER=
# EMAIL_HOST_PASSWORD=
```

#### Django Secret Key Uretme

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 3.3 Build & Start

```bash
cd ~/apps/e-menum_v9/e_menum

# Image'lari build et (ilk seferde 5-10 dk surebilir)
docker compose -f docker-compose.prod.yml build

# Servisleri baslat
docker compose -f docker-compose.prod.yml up -d

# Loglari takip et (Ctrl+C ile cik)
docker compose -f docker-compose.prod.yml logs -f web
```

### 3.4 Basarili Calismayi Dogrula

```bash
# Container durumlari
docker compose -f docker-compose.prod.yml ps

# Beklenen cikti:
# emenum_db              running (healthy)
# emenum_redis           running (healthy)
# emenum_web             running (healthy)
# emenum_celery_worker   running
# emenum_celery_beat     running

# Health check
curl -s http://localhost:8000/health/ | python3 -m json.tool

# Beklenen cikti:
# { "status": "healthy", ... }
```

### 3.5 CMS Icerik Yukleme (Seed)

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py seed_cms_content
```

---

## 4. Nginx Reverse Proxy & SSL

### 4.1 Nginx Konfigurasyonu

```bash
sudo nano /etc/nginx/sites-available/emenum
```

Asagidaki icerigi yapistir:

```nginx
# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name e-menum.com www.e-menum.com;

    # Let's Encrypt challenge icin
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS — Ana Site
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name e-menum.com www.e-menum.com;

    # SSL sertifikalari (certbot tarafindan yonetilir)
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
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript image/svg+xml;

    # Client body size (dosya yukleme limiti)
    client_max_body_size 50M;

    # Static dosyalar (Docker volume'dan)
    location /static/ {
        alias /home/emenum/apps/e-menum_v9/e_menum/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media dosyalar (Docker volume'dan)
    location /media/ {
        alias /home/emenum/apps/e-menum_v9/e_menum/media/;
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

        # WebSocket destegi (ileride lazim olabilir)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeout ayarlari
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 120s;
    }

    # Health check (internal only)
    location /health/ {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
}
```

### 4.2 Static/Media Dizinleri Baglama

Docker volume'lar container icinde. Nginx host'tan erisebilmesi icin:

**Yontem A: Symlink (basit)**

```bash
# Static volume'un gercek yolunu bul
docker volume inspect emenum_static --format '{{ .Mountpoint }}'
# Ornek cikti: /var/lib/docker/volumes/emenum_static/_data

# Symlink olustur
sudo ln -sf /var/lib/docker/volumes/emenum_static/_data /home/emenum/apps/e-menum_v9/e_menum/staticfiles
sudo ln -sf /var/lib/docker/volumes/emenum_media/_data /home/emenum/apps/e-menum_v9/e_menum/media
```

**Yontem B: Host bind mount (docker-compose.prod.yml'de degisiklik)**

```yaml
# docker-compose.prod.yml icinde web servisinin volumes kismini degistir:
volumes:
  - /home/emenum/apps/e-menum_v9/e_menum/staticfiles:/app/staticfiles
  - /home/emenum/apps/e-menum_v9/e_menum/media:/app/media
```

### 4.3 Nginx Etkinlestir

```bash
# Symlink olustur
sudo ln -sf /etc/nginx/sites-available/emenum /etc/nginx/sites-enabled/

# Default siteyi kaldir
sudo rm -f /etc/nginx/sites-enabled/default

# Konfigurasyon test
sudo nginx -t

# Yeniden yukle
sudo systemctl reload nginx
```

### 4.4 SSL Sertifikasi (Let's Encrypt)

> **ONEMLI:** DNS kayitlarinin sunucu IP'sine yonlendirilmis olmasi gerekir!

```bash
# SSL sertifika al
sudo certbot --nginx -d e-menum.com -d www.e-menum.com

# Otomatik yenileme test
sudo certbot renew --dry-run
```

Certbot otomatik olarak cron job olusturur. Manuel kontrol:

```bash
sudo systemctl status certbot.timer
```

---

## 5. Ilk Calistirma Sonrasi

### 5.1 Superuser Olusturuldu mu Kontrol Et

```bash
docker compose -f docker-compose.prod.yml logs web | grep -i "superuser"
```

### 5.2 .env'de Superuser Flag'ini Kapat

```bash
# .env dosyasinda su satiri degistir:
DJANGO_CREATE_SUPERUSER=false
```

### 5.3 Admin Panele Eris

```
https://e-menum.com/admin/
Email: admin@emenum.com
Sifre: .env'de belirledigin sifre
```

### 5.4 CMS Icerikleri Yukle

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py seed_cms_content
```

### 5.5 Siteyi Test Et

```bash
# Tum sayfalari kontrol et
for url in / /tr/ozellikler/ /tr/fiyatlandirma/ /tr/hakkimizda/ /tr/blog/ /tr/cozumler/ /tr/musteriler/ /tr/kaynaklar/ /tr/kariyer/ /tr/basin/ /tr/partnerler/ /tr/yatirimci/ /tr/destek/ /tr/iletisim/; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$url")
  echo "$code $url"
done
```

---

## 6. Guncelleme (CI/CD)

### 6.1 Manuel Guncelleme

```bash
cd ~/apps/e-menum_v9/e_menum

# 1. Degisiklikleri cek
git pull origin main

# 2. Image'lari yeniden build et
docker compose -f docker-compose.prod.yml build

# 3. Servisleri yeniden baslat (zero downtime degil)
docker compose -f docker-compose.prod.yml up -d

# 4. Loglari kontrol et
docker compose -f docker-compose.prod.yml logs -f web --tail=50
```

### 6.2 Zero-Downtime Guncelleme (Rolling)

```bash
# 1. Yeni image build et
docker compose -f docker-compose.prod.yml build web

# 2. Sadece web servisini yeniden baslat
docker compose -f docker-compose.prod.yml up -d --no-deps web

# 3. Celery worker'i guncelle
docker compose -f docker-compose.prod.yml up -d --no-deps celery_worker celery_beat
```

### 6.3 Coolify Entegrasyonu (Opsiyonel)

Coolify kullaniyorsaniz, GitHub webhook ile otomatik deploy mumkun:

1. Coolify panelinde yeni proje olustur
2. GitHub repo'yu bagla: `karacaismail/e-menum_v9`
3. Build command: `docker compose -f docker-compose.prod.yml build`
4. Start command: `docker compose -f docker-compose.prod.yml up -d`
5. Environment variables: `.env` icerigi ekle

---

## 7. Monitoring & Loglar

### 7.1 Container Loglari

```bash
# Tum servisler
docker compose -f docker-compose.prod.yml logs -f

# Sadece web
docker compose -f docker-compose.prod.yml logs -f web --tail=100

# Sadece hatalar
docker compose -f docker-compose.prod.yml logs web 2>&1 | grep -i error

# Celery worker
docker compose -f docker-compose.prod.yml logs -f celery_worker

# Database
docker compose -f docker-compose.prod.yml logs -f db
```

### 7.2 Kaynak Kullanimi

```bash
# Container kaynak kullanimi (canli)
docker stats

# Disk kullanimi
docker system df
df -h

# PostgreSQL boyutu
docker compose -f docker-compose.prod.yml exec db psql -U emenum_user -d emenum -c "SELECT pg_size_pretty(pg_database_size('emenum'));"
```

### 7.3 Health Check

```bash
# Uygulama health
curl -s http://localhost:8000/health/ | python3 -m json.tool

# Container health durumu
docker inspect --format='{{json .State.Health}}' emenum_web | python3 -m json.tool

# PostgreSQL baglanti
docker compose -f docker-compose.prod.yml exec db pg_isready -U emenum_user -d emenum

# Redis baglanti
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### 7.4 Sentry (Opsiyonel ama Onerilen)

`.env` dosyasinda:

```env
SENTRY_DSN=https://xxx@o123.ingest.sentry.io/456
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

---

## 8. Backup & Restore

### 8.1 PostgreSQL Backup

```bash
# Manuel backup
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U emenum_user -d emenum --format=custom \
  > ~/backups/emenum_$(date +%Y%m%d_%H%M%S).dump

# Gunluk otomatik backup (crontab -e)
0 3 * * * cd ~/apps/e-menum_v9/e_menum && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U emenum_user -d emenum --format=custom > ~/backups/emenum_$(date +\%Y\%m\%d).dump 2>/dev/null
```

### 8.2 PostgreSQL Restore

```bash
# Restore
docker compose -f docker-compose.prod.yml exec -T db \
  pg_restore -U emenum_user -d emenum --clean --if-exists \
  < ~/backups/emenum_20260225.dump
```

### 8.3 Media Dosyalari Backup

```bash
# Backup
tar -czf ~/backups/media_$(date +%Y%m%d).tar.gz \
  -C /var/lib/docker/volumes/emenum_media/_data .

# Restore
tar -xzf ~/backups/media_20260225.tar.gz \
  -C /var/lib/docker/volumes/emenum_media/_data
```

### 8.4 Tam Backup Script

```bash
#!/bin/bash
# ~/scripts/backup_emenum.sh
set -e

BACKUP_DIR=~/backups
DATE=$(date +%Y%m%d_%H%M%S)
COMPOSE="docker compose -f ~/apps/e-menum_v9/e_menum/docker-compose.prod.yml"

mkdir -p $BACKUP_DIR

echo "[$(date)] Backup basladi..."

# Database
$COMPOSE exec -T db pg_dump -U emenum_user -d emenum --format=custom \
  > $BACKUP_DIR/db_$DATE.dump
echo "  Database OK"

# Media
tar -czf $BACKUP_DIR/media_$DATE.tar.gz \
  -C /var/lib/docker/volumes/emenum_media/_data . 2>/dev/null || true
echo "  Media OK"

# Env dosyasi
cp ~/apps/e-menum_v9/e_menum/.env $BACKUP_DIR/env_$DATE.bak
echo "  .env OK"

# 30 gunden eski backup'lari sil
find $BACKUP_DIR -name "*.dump" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.bak" -mtime +30 -delete

echo "[$(date)] Backup tamamlandi: $BACKUP_DIR"
```

```bash
chmod +x ~/scripts/backup_emenum.sh

# Crontab'a ekle (her gece 03:00)
# crontab -e
0 3 * * * ~/scripts/backup_emenum.sh >> ~/logs/backup.log 2>&1
```

---

## 9. Troubleshooting (Gecmis Hatalar)

### Hata 1: "server does not support SSL, but SSL was required"

**Sebep:** Django, PostgreSQL'e SSL ile baglanmaya calisiyor ama Docker internal network'te PostgreSQL SSL desteklemiyor.

**Cozum:** `.env` dosyasinda:
```env
DATABASE_SSL_REQUIRE=false
```

Bu ayar `docker-compose.prod.yml`'de zaten tanimli. Ancak `.env` dosyasinda override ediliyorsa kontrol et.

**Dogrulama:**
```bash
docker compose -f docker-compose.prod.yml exec web python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.db import connection
connection.ensure_connection()
print('DB connection OK')
"
```

---

### Hata 2: "Dockerfile parse error on line 102: unknown instruction: set"

**Sebep:** Eski Dockerfile'da heredoc (`<<-'EOF'`) syntax'i kullanilmisti, eski Docker surumlerinde desteklenmiyordu.

**Cozum:** Duzeltildi. Entrypoint artik ayri dosyada: `docker/entrypoint.sh`. Dockerfile'da heredoc yok.

**Docker surumunu kontrol et:**
```bash
docker --version   # 24.0+ olmali
docker compose version  # v2.20+ olmali
```

---

### Hata 3: AMD64/ARM Image Uyumsuzlugu

**Sebep:** MacBook (Apple Silicon/ARM) uzerinde build edilen image, Hetzner (AMD64) sunucuda calismaz.

**Cozum:** `Dockerfile.amd64linux` dosyasi `--platform=linux/amd64` flag'i kullaniyor. Hetzner'da build ettiginde otomatik olarak dogru mimari kullanilir.

**NOT:** Image'i her zaman Hetzner sunucusunda build et, MacBook'ta degil!

```bash
# DOGRU: Hetzner'da build et
ssh emenum@SUNUCU_IP
cd ~/apps/e-menum_v9/e_menum
docker compose -f docker-compose.prod.yml build

# YANLIS: MacBook'ta build edip push etme
```

---

### Hata 4: Container'lar Arasinda Baglanti Sorunu

**Dogrulama:**
```bash
# Web container'dan DB'ye baglanti test
docker compose -f docker-compose.prod.yml exec web telnet db 5432

# Web container'dan Redis'e baglanti test
docker compose -f docker-compose.prod.yml exec web telnet redis 6379

# Network kontrol
docker network inspect emenum_network
```

---

### Hata 5: Migration Hatalari

```bash
# Migration durumunu kontrol et
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations | grep "\[ \]"

# Tek migration calistir
docker compose -f docker-compose.prod.yml exec web python manage.py migrate APP_NAME MIGRATION_NUMBER

# Migration sifirla (DIKKAT — veri kaybi!)
# docker compose -f docker-compose.prod.yml exec web python manage.py migrate APP_NAME zero
```

---

### Hata 6: Static Dosyalar 404 Veriyor

```bash
# Collectstatic yeniden calistir
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput --clear

# Nginx static dizin kontrolu
ls -la /var/lib/docker/volumes/emenum_static/_data/

# Nginx log
sudo tail -f /var/log/nginx/error.log
```

---

## 10. Faydali Komutlar

### Container Yonetimi

```bash
# Tum servisleri baslat
docker compose -f docker-compose.prod.yml up -d

# Tum servisleri durdur
docker compose -f docker-compose.prod.yml down

# Tek servisi yeniden baslat
docker compose -f docker-compose.prod.yml restart web

# Container'a shell ac
docker compose -f docker-compose.prod.yml exec web bash

# Django shell
docker compose -f docker-compose.prod.yml exec web python manage.py shell

# Django management komutu calistir
docker compose -f docker-compose.prod.yml exec web python manage.py <KOMUT>
```

### Veritabani

```bash
# PostgreSQL shell
docker compose -f docker-compose.prod.yml exec db psql -U emenum_user -d emenum

# Tablo boyutlari
docker compose -f docker-compose.prod.yml exec db psql -U emenum_user -d emenum -c "
SELECT relname AS table, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 10;"

# Aktif baglantilar
docker compose -f docker-compose.prod.yml exec db psql -U emenum_user -d emenum -c "
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
```

### Temizlik

```bash
# Kullanilmayan Docker objeleri temizle
docker system prune -f

# Eski image'lari temizle (dikkatli kullan)
docker image prune -a --filter "until=168h"

# Log boyutlarini kontrol et
docker compose -f docker-compose.prod.yml logs web --tail=1 2>&1 | wc -c
```

---

## Mimari Diyagram

```
                    INTERNET
                       |
                   [ Hetzner VPS ]
                       |
                 [ UFW Firewall ]
                   80 / 443
                       |
                 [ Nginx + SSL ]
                  (reverse proxy)
                       |
              http://127.0.0.1:8000
                       |
          ┌────────────┴────────────┐
          |     Docker Network      |
          |    (emenum_network)      |
          |                         |
          |  ┌─────────────────┐    |
          |  |   web (gunicorn)|    |
          |  |   :8000         |    |
          |  └────┬───────┬────┘    |
          |       |       |         |
          |  ┌────┴──┐ ┌──┴─────┐  |
          |  |  db   | | redis  |  |
          |  | :5432 | | :6379  |  |
          |  └───────┘ └────┬───┘  |
          |                 |      |
          |  ┌──────────────┴──┐   |
          |  | celery_worker   |   |
          |  | celery_beat     |   |
          |  └─────────────────┘   |
          └────────────────────────┘
```

---

## Kontrol Listesi (Deploy Oncesi)

- [ ] Hetzner sunucu olusturuldu (CX21+, Ubuntu 22/24 LTS)
- [ ] Docker & Docker Compose kuruldu
- [ ] `emenum` kullanicisi olusturuldu ve docker grubuna eklendi
- [ ] UFW firewall aktif (22, 80, 443)
- [ ] Nginx kuruldu
- [ ] DNS kayitlari sunucu IP'sine yonlendirildi
- [ ] Repo klonlandi (`git clone`)
- [ ] `.env` dosyasi olusturuldu ve duzenlendi
- [ ] `DJANGO_SECRET_KEY` uretildi
- [ ] `POSTGRES_PASSWORD` guclu sifre ile degistirildi
- [ ] `DATABASE_SSL_REQUIRE=false` ayarlandi
- [ ] `docker compose -f docker-compose.prod.yml build` basarili
- [ ] `docker compose -f docker-compose.prod.yml up -d` basarili
- [ ] `curl http://localhost:8000/health/` — `healthy` dondurdu
- [ ] Nginx reverse proxy konfigurasyonu yapildi
- [ ] SSL sertifikasi alindi (certbot)
- [ ] `https://e-menum.com` erisilebildi
- [ ] Admin panel calisiyorr (`/admin/`)
- [ ] `seed_cms_content` komutu calistirildi
- [ ] Backup cron job eklendi
- [ ] `DJANGO_CREATE_SUPERUSER=false` olarak guncellendi

---

**Sorular icin:** ismail@emenum.com | Slack: #devops

