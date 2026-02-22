# E-Menum Deploy Rehberi - Huseyin

> **Tarih:** 2026-02-22
> **Proje:** E-Menum - Enterprise QR Menu SaaS
> **Repo:** https://github.com/karacaismail/e-menum_v9
> **Hedef Server:** NetCup VPS

---

## GENEL BAKIS

| Bilgi | Deger |
|-------|-------|
| **Framework** | Django 5.0 |
| **Python** | 3.11 (3.10+ destekli) |
| **Veritabani** | PostgreSQL 15 |
| **Cache/Broker** | Redis 7 |
| **Queue** | Celery 5.4 + Celery Beat |
| **WSGI Server** | Gunicorn 21+ (gthread worker) |
| **Reverse Proxy** | Nginx |
| **Containerization** | Docker multi-stage build |
| **SSL** | Let's Encrypt (certbot) |

### Servisler

| Servis | Port | Aciklama |
|--------|------|----------|
| Django/Gunicorn | 8000 (internal) | Ana web uygulamasi |
| PostgreSQL | 5432 | Veritabani |
| Redis | 6379 | Cache + Celery broker |
| Celery Worker | - | Background task worker |
| Celery Beat | - | Periodic task scheduler |
| Nginx | 80/443 | Reverse proxy + SSL |

---

## BOLUM 1: LOCAL GELISTIRME ORTAMI

### 1.1 Repo'yu Clone Et

```bash
git clone https://github.com/karacaismail/e-menum_v9.git
cd e-menum_v9/e_menum
```

> **ONEMLI:** Django proje kodu `e_menum/` dizini icindedir. `manage.py` buradadir.

### 1.2 Dizin Yapisi

```
e-menum_v9/
├── CLAUDE.md                    # Proje dokumantasyonu
├── e_menum/                     # <<< DJANGO PROJE ROOT
│   ├── manage.py                # Django CLI
│   ├── Dockerfile               # Multi-stage Docker build
│   ├── docker-compose.yml       # Production compose
│   ├── docker-compose.dev.yml   # Development compose overrides
│   ├── gunicorn.conf.py         # Gunicorn production config
│   ├── requirements.txt         # Production dependencies
│   ├── requirements-dev.txt     # Dev dependencies
│   ├── .env.example             # Ornek environment dosyasi
│   ├── conftest.py              # Test configuration
│   ├── pytest.ini               # Pytest config
│   │
│   ├── config/                  # Django settings
│   │   ├── __init__.py
│   │   ├── urls.py              # URL routing
│   │   ├── wsgi.py              # WSGI entrypoint (Gunicorn kullanir)
│   │   ├── asgi.py              # ASGI entrypoint
│   │   └── settings/
│   │       ├── __init__.py
│   │       ├── base.py          # Base settings (844 satir)
│   │       ├── development.py   # Dev: SQLite, DEBUG=True
│   │       ├── staging.py       # Staging: PostgreSQL, DEBUG=False
│   │       └── production.py    # Prod: PostgreSQL zorunlu, tum guvenlik
│   │
│   ├── apps/                    # Django uygulamalari (12 adet)
│   │   ├── core/                # Users, organizations, auth, roles, permissions
│   │   ├── menu/                # Menu, categories, products, variants
│   │   ├── orders/              # Tables, QR codes, orders
│   │   ├── subscriptions/       # Plans, features, billing
│   │   ├── customers/           # Customer profiles, loyalty
│   │   ├── reporting/           # Report engine, AI analytics
│   │   ├── inventory/           # Stock, suppliers, recipes
│   │   ├── campaigns/           # Campaigns, coupons
│   │   ├── notifications/       # In-app, email, push
│   │   ├── media/               # File management (django-filer)
│   │   ├── ai/                  # AI content generation
│   │   └── analytics/           # Data aggregation (stub)
│   │
│   ├── shared/                  # Paylasilan kod
│   │   ├── middleware/          # TenantMiddleware
│   │   ├── permissions/         # RBAC/ABAC, plan enforcement
│   │   ├── serializers/         # Base serializers
│   │   ├── views/               # Base viewsets
│   │   ├── widgets/             # Custom admin widgets
│   │   └── utils/               # Exceptions, media helpers
│   │
│   ├── templates/               # HTML templates
│   │   ├── admin/               # Metronic dark theme admin
│   │   └── public/              # Public menu pages
│   │
│   ├── static/                  # Static dosyalar
│   │   ├── admin/css/           # Admin CSS
│   │   └── public/              # Public CSS/JS
│   │
│   ├── locale/                  # i18n (tr, en)
│   ├── docker/
│   │   └── init-db.sql          # PostgreSQL extension'lar
│   └── tests/                   # Test suite
│
└── (docs, specs vb.)
```

### 1.3 Local Calistirma (Docker Compose ile)

```bash
cd e-menum_v9/e_menum

# .env dosyasini olustur
cp .env.example .env
# .env icini duzenle (asagidaki env degiskenlerini incele)

# Development modunda calistir (PostgreSQL + Redis + Django + Celery)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Sadece Django + DB + Redis (Celery olmadan)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build web db redis

# Ayri terminalde migration
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### 1.4 Local Calistirma (Docker'siz / Hizli Test)

```bash
cd e-menum_v9/e_menum

# Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt
# (Dev icin: pip install -r requirements-dev.txt)

# SQLite ile calistir (development.py default)
export DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000

# Erisim: http://127.0.0.1:8000/admin/
```

---

## BOLUM 2: GITHUB REPOSITORY AYARLARI

### 2.1 Repo Bilgisi

```
URL:     https://github.com/karacaismail/e-menum_v9
Branch:  main (production)
```

### 2.2 Branch Stratejisi

```
main          → Production deploy (korunmali)
staging       → Staging test ortami
develop       → Aktif gelistirme
feature/*     → Yeni ozellikler
hotfix/*      → Acil duzeltmeler
```

### 2.3 GitHub Secrets (Settings > Secrets > Actions)

Asagidaki secret'lari GitHub repo'ya ekle:

```
DOCKER_REGISTRY_URL        → Docker registry (ghcr.io veya DockerHub)
DOCKER_USERNAME             → Registry kullanici adi
DOCKER_PASSWORD             → Registry sifre/token

NETCUP_SSH_HOST             → Server IP adresi
NETCUP_SSH_USER             → SSH kullanici adi (deploy kullanicisi)
NETCUP_SSH_KEY              → SSH private key (ed25519)
NETCUP_SSH_PORT             → SSH port (default: 22)

DJANGO_SECRET_KEY           → Production secret key
DATABASE_URL                → Production PostgreSQL URL
REDIS_URL                   → Production Redis URL
SENTRY_DSN                  → Sentry error tracking DSN (opsiyonel)
```

### 2.4 GitHub Actions CI/CD Ornegi

`.github/workflows/deploy.yml` dosyasi olustur:

```yaml
name: Deploy to NetCup

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: emenum_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        working-directory: ./e_menum
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        working-directory: ./e_menum
        env:
          DJANGO_SETTINGS_MODULE: config.settings.development
          DATABASE_URL: postgresql://test:test@localhost:5432/emenum_test
        run: pytest --cov=apps --cov-report=xml

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./e_menum
          file: ./e_menum/Dockerfile
          target: production
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/web:latest
            ghcr.io/${{ github.repository }}/web:${{ github.sha }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to NetCup
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.NETCUP_SSH_HOST }}
          username: ${{ secrets.NETCUP_SSH_USER }}
          key: ${{ secrets.NETCUP_SSH_KEY }}
          port: ${{ secrets.NETCUP_SSH_PORT }}
          script: |
            cd /opt/emenum
            docker compose pull
            docker compose up -d --remove-orphans
            docker compose exec -T web python manage.py migrate --noinput
            docker compose exec -T web python manage.py collectstatic --noinput
            echo "Deploy basarili: $(date)"
```

---

## BOLUM 3: NETCUP SERVER KURULUMU

### 3.1 Server Gereksinimleri

| Kaynak | Minimum | Onerilen |
|--------|---------|----------|
| CPU | 2 vCPU | 4 vCPU |
| RAM | 4 GB | 8 GB |
| Disk | 40 GB SSD | 80 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |

### 3.2 Ilk Server Hazirlik

```bash
# Root olarak baglan
ssh root@NETCUP_IP

# Sistem guncelle
apt update && apt upgrade -y

# Gerekli paketler
apt install -y \
  curl \
  wget \
  git \
  ufw \
  fail2ban \
  htop \
  nano \
  unzip \
  software-properties-common \
  apt-transport-https \
  ca-certificates \
  gnupg \
  lsb-release

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
# Asagidaki satirlari degistir/ekle:
#   PermitRootLogin no
#   PasswordAuthentication no
#   PubkeyAuthentication yes
#   Port 2222                    # (opsiyonel: port degistir)
#   AllowUsers deploy
systemctl restart sshd

# --- Firewall ---
ufw default deny incoming
ufw default allow outgoing
ufw allow 2222/tcp     # SSH (veya 22 eger port degistirmediysen)
ufw allow 80/tcp       # HTTP
ufw allow 443/tcp      # HTTPS
ufw enable

# --- Fail2ban ---
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
nano /etc/fail2ban/jail.local
# [sshd] bolumunu aktifle:
#   enabled = true
#   port = 2222
#   maxretry = 3
#   bantime = 3600
systemctl enable fail2ban
systemctl start fail2ban
```

### 3.4 Docker Kurulumu

```bash
# Docker GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Docker repo ekle
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker kur
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Deploy kullanicisini docker grubuna ekle
usermod -aG docker deploy

# Docker servisini baslat
systemctl enable docker
systemctl start docker

# Dogrula
docker --version
docker compose version
```

### 3.5 Nginx Kurulumu

```bash
apt install -y nginx

# Nginx servisi
systemctl enable nginx
systemctl start nginx
```

### 3.6 Certbot (Let's Encrypt SSL)

```bash
apt install -y certbot python3-certbot-nginx
```

---

## BOLUM 4: UYGULAMA DEPLOY

### 4.1 Dizin Yapisi (Server)

```bash
# Deploy kullanicisina gec
su - deploy

# Uygulama dizini olustur
sudo mkdir -p /opt/emenum
sudo chown deploy:deploy /opt/emenum
cd /opt/emenum

# Alt dizinler
mkdir -p backups logs media
```

### 4.2 Environment Dosyasi

```bash
nano /opt/emenum/.env
```

Icerigi:

```bash
# =============================================================================
# E-Menum Production Environment
# =============================================================================

# --- Django Core ---
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
DJANGO_SECRET_KEY=BURAYA-50-KARAKTER-RANDOM-KEY-URET

# Hostname'leri duzenle (domain veya IP)
ALLOWED_HOSTS=e-menum.com,www.e-menum.com,NETCUP_IP
CSRF_TRUSTED_ORIGINS=https://e-menum.com,https://www.e-menum.com

# --- Database ---
POSTGRES_USER=emenum
POSTGRES_PASSWORD=GUCLU-BIR-SIFRE-BURAYA
POSTGRES_DB=emenum
DATABASE_URL=postgresql://emenum:GUCLU-BIR-SIFRE-BURAYA@db:5432/emenum
DATABASE_SSL_REQUIRE=False

# --- Redis ---
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1

# --- Email (SMTP) ---
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@e-menum.com
EMAIL_HOST_PASSWORD=SMTP-SIFRE
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@e-menum.com

# --- Gunicorn ---
GUNICORN_WORKERS=3
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=120

# --- Sentry (Opsiyonel) ---
SENTRY_DSN=
SENTRY_ENVIRONMENT=production

# --- AI (Opsiyonel) ---
OPENAI_API_KEY=
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini

# --- Genel ---
TZ=Europe/Istanbul
LANGUAGE_CODE=tr
DJANGO_MIGRATE=true
```

**Secret key uret:**

```bash
python3 -c "from secrets import token_urlsafe; print(token_urlsafe(50))"
```

### 4.3 Docker Compose (Production)

```bash
nano /opt/emenum/docker-compose.yml
```

Icerigi:

```yaml
version: "3.9"

services:
  # ---------- PostgreSQL ----------
  db:
    image: postgres:15-alpine
    container_name: emenum_db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - emenum_network

  # ---------- Redis ----------
  redis:
    image: redis:7-alpine
    container_name: emenum_redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - emenum_network

  # ---------- Django Web (Gunicorn) ----------
  web:
    image: ghcr.io/karacaismail/e-menum_v9/web:latest
    # Eger registry kullanmiyorsan:
    # build:
    #   context: .
    #   dockerfile: Dockerfile
    #   target: production
    container_name: emenum_web
    restart: unless-stopped
    env_file: .env
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      CELERY_BROKER_URL: ${CELERY_BROKER_URL}
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./logs:/app/logs
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - emenum_network

  # ---------- Celery Worker ----------
  celery_worker:
    image: ghcr.io/karacaismail/e-menum_v9/web:latest
    container_name: emenum_celery_worker
    restart: unless-stopped
    env_file: .env
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      CELERY_BROKER_URL: ${CELERY_BROKER_URL}
      CELERY_RESULT_BACKEND: ${CELERY_RESULT_BACKEND}
    command: >
      celery -A config worker
      --loglevel=info
      --concurrency=2
      --max-tasks-per-child=50
      --pool=prefork
    volumes:
      - media_volume:/app/media
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - emenum_network

  # ---------- Celery Beat ----------
  celery_beat:
    image: ghcr.io/karacaismail/e-menum_v9/web:latest
    container_name: emenum_celery_beat
    restart: unless-stopped
    env_file: .env
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      CELERY_BROKER_URL: ${CELERY_BROKER_URL}
      CELERY_RESULT_BACKEND: ${CELERY_RESULT_BACKEND}
    command: >
      celery -A config beat
      --loglevel=info
      --scheduler django_celery_beat.schedulers:DatabaseScheduler
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      celery_worker:
        condition: service_started
    networks:
      - emenum_network

networks:
  emenum_network:
    driver: bridge
    name: emenum_network

volumes:
  postgres_data:
    name: emenum_postgres_data
  redis_data:
    name: emenum_redis_data
  static_volume:
    name: emenum_static
  media_volume:
    name: emenum_media
```

### 4.4 init-db.sql Dosyasi

```bash
nano /opt/emenum/init-db.sql
```

Icerigi:

```sql
-- PostgreSQL Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "unaccent";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Timezone
ALTER DATABASE emenum SET timezone TO 'Europe/Istanbul';

DO $$
BEGIN
    RAISE NOTICE 'E-Menum database initialized with required extensions';
END
$$;
```

### 4.5 Nginx Konfigurasyonu

```bash
sudo nano /etc/nginx/sites-available/emenum
```

Icerigi:

```nginx
# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name e-menum.com www.e-menum.com;

    # Certbot challenge icin
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

    # SSL sertifikalari (certbot olusturacak)
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

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;

    # Max upload size (menu fotograflari icin)
    client_max_body_size 10M;

    # Static files (Gunicorn'dan degil, Nginx'den serv et)
    location /static/ {
        alias /opt/emenum/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media files (kullanici yuklemeleri)
    location /media/ {
        alias /opt/emenum/media/;
        expires 7d;
        add_header Cache-Control "public";
        access_log off;
    }

    # Health check (Nginx'den direkt gecir)
    location /health/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
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

        # WebSocket destegi (gelecekte lazim olabilir)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeout
        proxy_connect_timeout 60;
        proxy_send_timeout 120;
        proxy_read_timeout 120;
    }
}
```

```bash
# Nginx aktifle
sudo ln -s /etc/nginx/sites-available/emenum /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 4.6 SSL Sertifikasi

```bash
# Domain DNS'i NetCup IP'ye yonlendirdikten sonra:
sudo certbot --nginx -d e-menum.com -d www.e-menum.com

# Auto-renewal test
sudo certbot renew --dry-run
```

> **NOT:** DNS'in A recordu NetCup server IP'sine yonlendirilmis olmali.

### 4.7 Static/Media Volume Mount

Nginx'in container icindeki static dosyalara erisebilmesi icin:

```bash
# Static dosyalari host'a kopyala
# (Docker compose'daki static_volume'u host dizinine bagla)

# Yontem 1: Named volume'dan host'a kopyala
docker cp emenum_web:/app/staticfiles /opt/emenum/static

# Yontem 2: docker-compose.yml'da volume'u bind mount yap (onerilir):
# web servisinin volumes bolumunu guncelle:
#   - /opt/emenum/static:/app/staticfiles
#   - /opt/emenum/media:/app/media
```

**Onerilir:** `docker-compose.yml`'daki `static_volume` ve `media_volume`'u host dizinlerine bind mount yap:

```yaml
# web servisinde volumes:
volumes:
  - /opt/emenum/static:/app/staticfiles
  - /opt/emenum/media:/app/media
  - ./logs:/app/logs
```

---

## BOLUM 5: ILK DEPLOY (Adim Adim)

### 5.1 Codebase'i Server'a Al

**Yontem A: GitHub Container Registry (Onerilen)**

```bash
# Local'de (gelistirici bilgisayarinda):
cd e-menum_v9/e_menum

# Docker image build & push
docker build -t ghcr.io/karacaismail/e-menum_v9/web:latest --target production .
echo $GITHUB_TOKEN | docker login ghcr.io -u karacaismail --password-stdin
docker push ghcr.io/karacaismail/e-menum_v9/web:latest

# Server'da:
echo $GITHUB_TOKEN | docker login ghcr.io -u karacaismail --password-stdin
cd /opt/emenum
docker compose pull
```

**Yontem B: Server'da Build (Basit)**

```bash
# Server'da:
cd /opt
git clone https://github.com/karacaismail/e-menum_v9.git emenum-src
cd /opt/emenum

# Dockerfile'i kopyala
cp /opt/emenum-src/e_menum/Dockerfile .
cp /opt/emenum-src/e_menum/requirements.txt .
cp /opt/emenum-src/e_menum/requirements-dev.txt .
cp -r /opt/emenum-src/e_menum/apps .
cp -r /opt/emenum-src/e_menum/config .
cp -r /opt/emenum-src/e_menum/shared .
cp -r /opt/emenum-src/e_menum/templates .
cp -r /opt/emenum-src/e_menum/static .
cp -r /opt/emenum-src/e_menum/locale .
cp /opt/emenum-src/e_menum/manage.py .
cp /opt/emenum-src/e_menum/gunicorn.conf.py .
cp /opt/emenum-src/e_menum/conftest.py .
cp /opt/emenum-src/e_menum/pytest.ini .

# docker-compose.yml'da image yerine build kullan:
# web:
#   build:
#     context: .
#     dockerfile: Dockerfile
#     target: production

docker compose build
```

### 5.2 Container'lari Baslat

```bash
cd /opt/emenum

# Ilk calistirma
docker compose up -d

# Log kontrol
docker compose logs -f

# Health check
curl http://localhost:8000/health/
# Beklenen: {"success": true, "data": {"status": "healthy", ...}}
```

### 5.3 Veritabani Kurulumu

```bash
# Migration calistir
docker compose exec web python manage.py migrate --noinput

# Static dosyalari topla
docker compose exec web python manage.py collectstatic --noinput

# Superuser olustur
docker compose exec -it web python manage.py createsuperuser
# Istenecek bilgiler:
#   Email: admin@e-menum.com
#   First name: Admin
#   Last name: User
#   Password: (guclu sifre)
```

### 5.4 Dogrulama

```bash
# Container durumlarini kontrol et
docker compose ps

# Beklenen cikti:
# NAME                   STATUS              PORTS
# emenum_db              Up (healthy)
# emenum_redis           Up (healthy)
# emenum_web             Up (healthy)         127.0.0.1:8000->8000/tcp
# emenum_celery_worker   Up
# emenum_celery_beat     Up

# Web erisim testi
curl -I http://localhost:8000/admin/
# Beklenen: HTTP 302 (login'e yonlendirir)

# Nginx testi (domain ayarlandiktan sonra)
curl -I https://e-menum.com/admin/

# Database baglanti testi
docker compose exec web python manage.py dbshell
# \dt  → tablolari listele
# \q   → cik

# Redis testi
docker compose exec redis redis-cli ping
# Beklenen: PONG
```

---

## BOLUM 6: BAKIM ISLEMLERI

### 6.1 Guncelleme / Yeni Versiyon Deploy

```bash
cd /opt/emenum

# Yeni image cek
docker compose pull

# Container'lari yenile (zero-downtime degil)
docker compose up -d --remove-orphans

# Migration calistir
docker compose exec web python manage.py migrate --noinput

# Static dosyalari guncelle
docker compose exec web python manage.py collectstatic --noinput

# Eski image'lari temizle
docker image prune -f
```

### 6.2 Yedekleme

```bash
# PostgreSQL yedekleme
docker compose exec db pg_dump -U emenum emenum > /opt/emenum/backups/db_$(date +%Y%m%d_%H%M%S).sql

# Gzip ile sikistir
docker compose exec db pg_dump -U emenum emenum | gzip > /opt/emenum/backups/db_$(date +%Y%m%d_%H%M%S).sql.gz

# Media yedekleme
tar -czf /opt/emenum/backups/media_$(date +%Y%m%d_%H%M%S).tar.gz /opt/emenum/media/
```

**Cron ile otomatik yedekleme:**

```bash
crontab -e

# Her gun gece 3'te DB yedekle
0 3 * * * docker compose -f /opt/emenum/docker-compose.yml exec -T db pg_dump -U emenum emenum | gzip > /opt/emenum/backups/db_$(date +\%Y\%m\%d).sql.gz

# 30 gunden eski yedekleri sil
0 4 * * * find /opt/emenum/backups/ -type f -mtime +30 -delete
```

### 6.3 Yedekten Geri Yukleme

```bash
# Container'i durdur
docker compose stop web celery_worker celery_beat

# DB'yi geri yukle
gunzip < /opt/emenum/backups/db_20260222.sql.gz | docker compose exec -T db psql -U emenum emenum

# Container'lari baslat
docker compose start web celery_worker celery_beat
```

### 6.4 Log Izleme

```bash
# Tum log'lar
docker compose logs -f

# Sadece web
docker compose logs -f web

# Sadece hatalar
docker compose logs -f web 2>&1 | grep -i error

# Celery log
docker compose logs -f celery_worker

# Nginx log
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 6.5 Performans Izleme

```bash
# Container kaynak kullanimi
docker stats

# Disk kullanimi
df -h
docker system df

# PostgreSQL aktif baglantilari
docker compose exec db psql -U emenum -c "SELECT count(*) FROM pg_stat_activity;"

# Redis bellek kullanimi
docker compose exec redis redis-cli info memory
```

### 6.6 Sorun Giderme

```bash
# Container restart
docker compose restart web

# Tum servisleri yeniden baslat
docker compose down && docker compose up -d

# Container icine gir (debug)
docker compose exec web bash

# Django shell
docker compose exec web python manage.py shell

# Django check
docker compose exec web python manage.py check --deploy
```

---

## BOLUM 7: ONEMLI BILGILER

### 7.1 Versiyon Matrisi

| Yazilim | Versiyon | Not |
|---------|----------|-----|
| Python | 3.11 | Dockerfile'da sabit |
| Django | 5.0.x | `>=5.0,<6.0` |
| PostgreSQL | 15-alpine | Docker image |
| Redis | 7-alpine | Docker image |
| Gunicorn | 21+ | requirements.txt |
| Celery | 5.4+ | requirements.txt |
| DRF | 3.15+ | REST API framework |
| SimpleJWT | 5.3+ | JWT authentication |
| Nginx | latest | apt package |

### 7.2 Endpoint'ler

| URL | Aciklama |
|-----|----------|
| `/admin/` | Django Admin Panel (Metronic dark theme) |
| `/admin/reports/` | Custom raporlar sayfasi |
| `/admin/settings/` | Platform ayarlari |
| `/admin/permission-matrix/` | Rol-izin matrisi |
| `/api/v1/` | REST API root |
| `/api/v1/auth/login/` | JWT login |
| `/api/v1/auth/refresh/` | Token yenileme |
| `/health/` | Health check |
| `/m/<slug>/` | Public menu sayfasi (QR kod ile erisim) |

### 7.3 Ortam Degiskenleri (Tam Liste)

| Degisken | Zorunlu | Default | Aciklama |
|----------|---------|---------|----------|
| `DJANGO_SECRET_KEY` | **EVET (prod)** | - | 50+ karakter random key |
| `DJANGO_SETTINGS_MODULE` | EVET | `config.settings.development` | Settings dosyasi |
| `DEBUG` | EVET | `False` | Debug modu |
| `ALLOWED_HOSTS` | EVET | `[]` | Izin verilen host'lar |
| `DATABASE_URL` | **EVET (prod)** | SQLite | PostgreSQL connection URL |
| `REDIS_URL` | Hayir | `redis://localhost:6379/0` | Redis URL |
| `CELERY_BROKER_URL` | Hayir | `redis://localhost:6379/0` | Celery broker |
| `CELERY_RESULT_BACKEND` | Hayir | `redis://localhost:6379/0` | Celery result |
| `CSRF_TRUSTED_ORIGINS` | EVET (prod) | `[]` | CSRF trusted URL'ler |
| `SENTRY_DSN` | Hayir | - | Sentry error tracking |
| `GUNICORN_WORKERS` | Hayir | `CPU*2+1` | Worker sayisi |
| `GUNICORN_THREADS` | Hayir | `2` | Thread/worker |
| `GUNICORN_TIMEOUT` | Hayir | `120` | Request timeout (sn) |
| `EMAIL_HOST` | Hayir | `localhost` | SMTP host |
| `EMAIL_PORT` | Hayir | `587` | SMTP port |
| `EMAIL_HOST_USER` | Hayir | - | SMTP kullanici |
| `EMAIL_HOST_PASSWORD` | Hayir | - | SMTP sifre |
| `OPENAI_API_KEY` | Hayir | - | AI icin API key |
| `AI_PROVIDER` | Hayir | `openai` | AI provider |
| `AI_MODEL` | Hayir | `gpt-4o-mini` | AI model |

### 7.4 Dockerfile Stages

```
Stage 1: builder       → Python venv + pip install
Stage 2: production    → Minimal runtime, non-root user, Gunicorn
Stage 3: development   → + dev dependencies, runserver
Stage 4: celery-worker → Celery worker CMD
Stage 5: celery-beat   → Celery beat CMD
```

- Production image: `python:3.11-slim-bookworm`
- Non-root user: `emenum` (UID/GID 1000)
- Entrypoint: `/usr/bin/tini` (signal handling) + `/entrypoint.sh` (DB wait + migrate)
- Health check: `curl http://localhost:8000/health/`
- Static files: build sirasinda `collectstatic` calisir

### 7.5 PostgreSQL Extensions (Otomatik Kurulan)

| Extension | Amac |
|-----------|------|
| `uuid-ossp` | UUID uretimi |
| `unaccent` | Turkce full-text search |
| `pgcrypto` | Kriptografik fonksiyonlar |
| `citext` | Case-insensitive text |
| `pg_trgm` | Fuzzy search (trigram) |

### 7.6 Guvenlik Notlari

- `SECRET_KEY`: Production'da mutlaka environment variable'dan oku, kod icinde olmamali
- `DEBUG=False`: Production'da kesinlikle False
- `DATABASE_SSL_REQUIRE=True`: Production default (managed DB kullaniliyorsa)
- Password: BCrypt SHA256, minimum 12 karakter
- JWT: Access token 15dk, Refresh token 7 gun
- HSTS: 1 yil, preload aktif
- Session cookie: Secure + HttpOnly + SameSite=Lax

---

## HIZLI REFERANS: DEPLOY CHECKLIST

```
[ ] 1. NetCup server'i hazirla (Ubuntu 22/24, Docker, Nginx)
[ ] 2. Guvenlik: SSH hardening, UFW, fail2ban
[ ] 3. /opt/emenum dizinini olustur
[ ] 4. .env dosyasini doldur (SECRET_KEY, DATABASE_URL, vb.)
[ ] 5. docker-compose.yml ve init-db.sql kopyala
[ ] 6. Docker image build veya pull
[ ] 7. docker compose up -d
[ ] 8. docker compose exec web python manage.py migrate
[ ] 9. docker compose exec web python manage.py collectstatic
[ ] 10. docker compose exec -it web python manage.py createsuperuser
[ ] 11. Nginx config yaz ve aktifle
[ ] 12. DNS A record'u NetCup IP'ye yonlendir
[ ] 13. certbot ile SSL sertifikasi al
[ ] 14. https://e-menum.com/admin/ test et
[ ] 15. Cron backup job'u kur
[ ] 16. GitHub Actions CI/CD pipeline kur (opsiyonel)
```

---

> **Sorularin icin:** Ismail'e ulas (Strategic Lead)
> **Repo:** https://github.com/karacaismail/e-menum_v9
