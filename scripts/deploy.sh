#!/usr/bin/env bash
# =============================================================================
# E-Menum CI/CD Deploy Script
# =============================================================================
# Sunucuda çalıştırılır: GitHub'a commit atıldıktan sonra bu script tetiklenir.
# - Git pull ile güncel kodu çeker
# - DB migration (Django migrate) çalıştırır
# - Build (Tailwind CSS, static, gerekirse image) yapar
# - Uygulamayı yeniden başlatır (Docker veya Gunicorn)
#
# Kullanım:
#   ./scripts/deploy.sh              # Otomatik mod tespiti (Docker öncelikli)
#   DEPLOY_MODE=docker ./scripts/deploy.sh
#   DEPLOY_MODE=bare   ./scripts/deploy.sh
#   GIT_BRANCH=main    ./scripts/deploy.sh
#
# Ortam değişkenleri:
#   DEPLOY_MODE   docker | bare  (boşsa otomatik tespit)
#   GIT_BRANCH    Çekilecek branch (varsayılan: mevcut branch)
#   SKIP_PULL     1 ise git pull yapılmaz
#   LOCK_FILE     Kilit dosyasi (varsayılan: /tmp/emenum-deploy.lock)
#   DEPLOY_BUILD  1 ise Docker image yeniden derlenir (varsayılan: 0)
#   FORCE_DEPLOY  1 ise degisiklik olmasa da islemler yapilir (varsayılan: 0)
#   DEPLOY_DEBUG  1 ise deploy sonrasi health check ekler (degisiklik/FORCE yoksa calismaz)
#
# Kesinti: Restart sirasinda web/celery ~2-5 sn kesinti olur. Migrate once uygulanir,
#         hata verirse script durur, restart yapilmaz (proje bozulmaz).
# Yetkiler: Container emenum (UID 1000). Media/static volume'da; kod host mount.
# Cift calisma: flock ile ayni anda tek deploy.
# =============================================================================

set -e

# Renkler
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# -----------------------------------------------------------------------------
# Lock: Dakikada bir tetiklenince ust uste calismayı engeller (flock)
# -----------------------------------------------------------------------------
LOCK_FILE="${LOCK_FILE:-/tmp/emenum-deploy.lock}"
DEPLOY_LOCK_FD=200
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
  log_warn "Deploy zaten calisiyor (lock: $LOCK_FILE). Cikiliyor."
  exit 0
fi

# -----------------------------------------------------------------------------
# Proje yolları: script repo kökünden veya e_menum içinden çalıştırılabilir
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/../e_menum/manage.py" ]]; then
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
  APP_ROOT="$REPO_ROOT/e_menum"
else
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
  APP_ROOT="$REPO_ROOT"
fi

if [[ ! -f "$APP_ROOT/manage.py" ]]; then
  log_err "manage.py bulunamadı: $APP_ROOT"
  exit 1
fi

cd "$REPO_ROOT"
log_info "Repo root: $REPO_ROOT"
log_info "App root:  $APP_ROOT"

# -----------------------------------------------------------------------------
# 1. Git pull: fetch + reset --hard (local degisiklikleri atar, remote ile senkron)
#    Yeni commit geldiyse NEED_RESTART=1
# -----------------------------------------------------------------------------
NEED_RESTART=0
if [[ "$SKIP_PULL" != "1" ]]; then
  PREV_HEAD="$(git rev-parse HEAD 2>/dev/null)"
  log_info "Git pull (reset --hard ile remote senkron)..."
  BRANCH="${GIT_BRANCH:-$(git branch --show-current)}"
  git fetch origin
  git checkout "$BRANCH"
  git reset --hard "origin/$BRANCH" || { log_err "Git reset failed. Aborting."; exit 1; }
  if [[ "$PREV_HEAD" != "$(git rev-parse HEAD)" ]]; then
    NEED_RESTART=1
  fi
  log_ok "Code updated (branch: $BRANCH)"
else
  log_info "SKIP_PULL=1, skipping git pull"
fi

# -----------------------------------------------------------------------------
# Mod tespiti: Docker mı bare metal mi?
# -----------------------------------------------------------------------------
detect_deploy_mode() {
  if [[ -n "$DEPLOY_MODE" ]]; then
    echo "$DEPLOY_MODE"
    return
  fi
  if command -v docker &>/dev/null && [[ -f "$APP_ROOT/docker-compose.prod.yml" ]]; then
    echo "docker"
  else
    echo "bare"
  fi
}

DEPLOY_MODE="$(detect_deploy_mode)"
log_info "Deploy mode: $DEPLOY_MODE"

# Degisiklik yoksa hicbir islem yapma (Tailwind, migrate, collectstatic, restart yok)
# Sadece NEED_RESTART veya FORCE_DEPLOY varsa deploy calisir. DEPLOY_DEBUG sadece health check ekler.
if [[ "$NEED_RESTART" != "1" && "$FORCE_DEPLOY" != "1" ]]; then
  log_ok "Degisiklik yok, hicbir islem yapilmiyor."
  exit 0
fi

# -----------------------------------------------------------------------------
# 2a. Docker deploy: kod host'tan mount (./e_menum -> /app), rebuild her seferinde YOK
#     Host'ta Tailwind derlenir, migrate/collectstatic container'da, servis restart.
#     DEPLOY_BUILD=1 ise image derlenir (Dockerfile/requirements degisince).
# -----------------------------------------------------------------------------
run_docker_deploy() {
  cd "$APP_ROOT"

  if [[ "$DEPLOY_BUILD" == "1" ]]; then
    log_info "Docker image derleniyor (web, celery_worker, celery_beat)..."
    docker compose -f docker-compose.prod.yml build web celery_worker celery_beat
  else
    log_info "Docker build atlaniyor (kod volume'dan, tam build icin DEPLOY_BUILD=1)"
  fi

  # Tailwind container icinde derlenir (host'ta Node gerekmez)
  if [[ -f package.json ]] && [[ -f static/css/input.css ]]; then
    log_info "Tailwind CSS (Node container icinde) derleniyor..."
    docker run --rm \
      -v "$(pwd):/app" -w /app \
      node:20-slim \
      sh -c "npm install --no-audit --no-fund && npx tailwindcss -i ./static/css/input.css -o ./static/css/tailwind.min.css --minify"
    log_ok "Tailwind tamamlandi."
  fi

  log_info "Containers ayakta (up -d)..."
  docker compose -f docker-compose.prod.yml up -d

  log_info "Migrate ve collectstatic (container icinde)..."
  sleep 3
  MIGRATE_OK=0
  for _ in 1 2 3 4 5; do
    if docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput; then
      MIGRATE_OK=1
      break
    fi
    log_warn "Migrate bekleniyor (container/DB hazir olabilir), 5 sn sonra tekrar..."
    sleep 5
  done
  if [[ "$MIGRATE_OK" != "1" ]]; then
    log_err "Migrate basarisiz. Deploy durduruldu."
    exit 1
  fi
  docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput 2>/dev/null || true

  if [[ "$NEED_RESTART" == "1" || "$DEPLOY_BUILD" == "1" || "$FORCE_DEPLOY" == "1" || "$DEPLOY_DEBUG" == "1" ]]; then
    log_info "Servisler yeniden baslatiliyor (kod/image/force/debug)..."
    docker compose -f docker-compose.prod.yml restart web celery_worker celery_beat
  else
    log_info "Restart atlaniyor."
  fi

  # Her basarili deploy'da deploy_info.json yaz (footer'da build bilgisi)
  cd "$REPO_ROOT"
  GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "")
  GIT_BRANCH_NAME=$(git branch --show-current 2>/dev/null || echo "")
  cd "$APP_ROOT"
  DEPLOY_AT=$(date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
  BUILD_NUM=$(date '+%Y%m%d-%H%M' 2>/dev/null || echo "")
  echo "{\"at\":\"$DEPLOY_AT\",\"status\":\"ok\",\"mode\":\"docker\",\"commit\":\"$GIT_COMMIT\",\"branch\":\"$GIT_BRANCH_NAME\",\"build\":\"$BUILD_NUM\"}" > "$APP_ROOT/deploy_info.json"
  log_info "deploy_info.json yazildi (footer build bilgisi)"

  if [[ "$DEPLOY_DEBUG" == "1" ]]; then
    sleep 5
    if curl -sf "http://localhost:${WEB_PORT:-8000}/health/" >/dev/null 2>&1; then
      log_ok "Health check: OK"
    else
      log_warn "Health check: /health/ ulasilamadi (nginx/proxy kullaniliyor olabilir)"
    fi
  fi

  log_ok "Docker deploy tamamlandi."
}

# -----------------------------------------------------------------------------
# 2b. Bare metal deploy: venv, pip, migrate, npm, collectstatic, restart gunicorn
# -----------------------------------------------------------------------------
run_bare_deploy() {
  cd "$APP_ROOT"

  VENV_PATH="${VENV_PATH:-$REPO_ROOT/.venv}"
  if [[ -d "$VENV_PATH" ]]; then
    log_info "Virtual environment: $VENV_PATH"
    source "$VENV_PATH/bin/activate"
  else
    log_warn "VENV not found at $VENV_PATH; using system Python"
  fi

  log_info "Python bağımlılıkları güncelleniyor..."
  pip install -q -r requirements.txt

  log_info "Veritabanı migration..."
  python manage.py migrate --noinput
  log_ok "Migration tamamlandı."

  if [[ -f package.json ]] && grep -q '"css:build"' package.json 2>/dev/null; then
    log_info "Tailwind CSS build..."
    npm ci --no-audit --no-fund 2>/dev/null || npm install --no-audit --no-fund
    npm run css:build
    log_ok "CSS build tamamlandı."
  fi

  log_info "Static dosyalar toplanıyor..."
  python manage.py collectstatic --noinput
  log_ok "Collectstatic tamamlandı."

  log_info "Django check..."
  python manage.py check || true

  if [[ "$NEED_RESTART" == "1" || "$FORCE_DEPLOY" == "1" || "$DEPLOY_DEBUG" == "1" ]]; then
    log_info "Gunicorn yeniden baslatiliyor..."
    if systemctl is-active --quiet gunicorn 2>/dev/null || systemctl is-active --quiet emenum 2>/dev/null; then
      sudo systemctl restart gunicorn 2>/dev/null || sudo systemctl restart emenum 2>/dev/null || true
      log_ok "systemctl restart yapildi."
    elif pgrep -f "gunicorn.*config.wsgi" >/dev/null; then
      GUNICORN_PID=$(pgrep -f "gunicorn.*config.wsgi" | head -1)
      kill -HUP "$GUNICORN_PID" 2>/dev/null && log_ok "Gunicorn HUP gonderildi (PID $GUNICORN_PID)" || log_warn "Gunicorn restart manuel yapilmalı."
    else
      log_warn "Gunicorn process bulunamadi. Manuel baslatin: gunicorn -c gunicorn.conf.py config.wsgi:application"
    fi
  else
    log_info "Kod degismedi, Gunicorn restart atlaniyor."
  fi

  # Her basarili deploy'da deploy_info.json yaz (footer'da build bilgisi)
  cd "$REPO_ROOT"
  GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "")
  GIT_BRANCH_NAME=$(git branch --show-current 2>/dev/null || echo "")
  cd "$APP_ROOT"
  DEPLOY_AT=$(date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
  BUILD_NUM=$(date '+%Y%m%d-%H%M' 2>/dev/null || echo "")
  echo "{\"at\":\"$DEPLOY_AT\",\"status\":\"ok\",\"mode\":\"bare\",\"commit\":\"$GIT_COMMIT\",\"branch\":\"$GIT_BRANCH_NAME\",\"build\":\"$BUILD_NUM\"}" > "$APP_ROOT/deploy_info.json"
  log_info "deploy_info.json yazildi (footer build bilgisi)"

  if [[ "$DEPLOY_DEBUG" == "1" ]]; then
    sleep 2
    if curl -sf "http://127.0.0.1:8000/health/" >/dev/null 2>&1; then
      log_ok "Health check: OK"
    else
      log_warn "Health check: /health/ ulasilamadi"
    fi
  fi

  log_ok "Bare metal deploy tamamlandi."
}

# -----------------------------------------------------------------------------
# Çalıştır
# -----------------------------------------------------------------------------
echo ""
echo "========================================"
echo "  E-Menum Deploy"
echo "========================================"

if [[ "$DEPLOY_MODE" == "docker" ]]; then
  run_docker_deploy
else
  run_bare_deploy
fi

echo ""
log_ok "Deploy bitti."
echo "========================================"
