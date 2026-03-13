#!/usr/bin/env bash
# =============================================================================
# E-Menum CI/CD Deploy Script #1
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
#   DEPLOY_BUILD  1 ise Docker image her zaman derlenir; 0 ise sadece ilgili dosya degistiğinde (varsayılan: 0)
#   FORCE_DEPLOY  1 ise degisiklik olmasa da islemler yapilir (varsayılan: 0)
#   DEPLOY_DEBUG  1 ise deploy sonrasi health check ekler (degisiklik/FORCE yoksa calismaz)
#   DEPLOY_GRACEFUL 1 ise graceful (HUP); 0 ise tam restart (varsayilan: 0 = her deploy full restart)
#   DEPLOY_LOG    Log dosyasi yolu (varsayilan: /var/log/deploy.log)
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

# Log: hem ekrana hem dosyaya (timestamp ile)
_log() {
  local level="$1" color="$2" msg="${*:3}"
  local ts
  ts=$(date '+%Y-%m-%d %H:%M:%S')
  echo -e "${color}[$level]${NC} $msg"
  if [[ -n "$LOG_FILE" && -w "$(dirname "$LOG_FILE")" ]]; then
    echo "[$ts] [$level] $msg" >> "$LOG_FILE"
  fi
}
log_info()  { _log "INFO"  "$BLUE"  "$*"; }
log_ok()    { _log "OK"    "$GREEN" "$*"; }
log_warn()  { _log "WARN"  "$YELLOW" "$*"; }
log_err()   { _log "ERROR" "$RED"   "$*"; }

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

# Log dosyasi: DEPLOY_LOG env veya /var/log/deploy.log
LOG_FILE="${DEPLOY_LOG:-/var/log/deploy.log}"

cd "$REPO_ROOT"
log_info "Repo root: $REPO_ROOT"
log_info "App root:  $APP_ROOT"
log_info "Log file:  $LOG_FILE"

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
  git clean -fd
  git reset --hard "origin/$BRANCH" || { log_err "Git reset failed. Aborting."; exit 1; }
  if [[ "$PREV_HEAD" != "$(git rev-parse HEAD)" ]]; then
    NEED_RESTART=1
  fi
  log_ok "Code updated (branch: $BRANCH)"
else
  log_info "SKIP_PULL=1, skipping git pull"
  PREV_HEAD=""
fi

# -----------------------------------------------------------------------------
# Mod tespiti: Docker mı bare metal mi? (NEED_FULL_BUILD karari icin once yapilmali)
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

# -----------------------------------------------------------------------------
# 1b. Commit'e gore akilli karar: full build gerekli mi? (sadece Docker modunda)
#     Dockerfile, requirements*.txt, package.json, docker/ degisti mi?
# -----------------------------------------------------------------------------
NEED_FULL_BUILD=0
if [[ "$DEPLOY_MODE" == "docker" && ("$NEED_RESTART" == "1" || "$FORCE_DEPLOY" == "1") ]]; then
  if [[ "$DEPLOY_BUILD" == "1" ]]; then
    NEED_FULL_BUILD=1
    log_info "DEPLOY_BUILD=1: tam image derlemesi yapilacak."
  elif [[ -n "$PREV_HEAD" ]]; then
    changed_files=$(git diff --name-only "$PREV_HEAD" HEAD 2>/dev/null || true)
    if echo "$changed_files" | grep -qE '^e_menum/(Dockerfile(\.[^/]*)?|requirements(-dev)?\.txt|package(-lock)?\.json|tailwind\.config\.|docker/|docker-compose\.prod\.yml)'; then
      NEED_FULL_BUILD=1
      log_info "Derleme gerektiren dosya degisti (Dockerfile/requirements/package/docker): tam build yapilacak."
    fi
  fi
  if [[ "$NEED_FULL_BUILD" != "1" ]]; then
    log_info "Sadece kod degisti: build atlanacak, minimal kesinti ile guncellenecek."
  fi
fi

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

  # Tam build: Dockerfile/requirements/package/docker degisti veya DEPLOY_BUILD=1
  if [[ "$NEED_FULL_BUILD" == "1" ]]; then
    log_info "Docker image derleniyor (web, celery_worker, celery_beat)..."
    docker compose -f docker-compose.prod.yml build web celery_worker celery_beat
    log_ok "Image derleme tamamlandi."
  else
    log_info "Docker build atlaniyor (sadece kod degisti, volume'dan guncel)."
  fi

  # Tailwind: her deploy'da (kod/static degisti mi bilmiyoruz, guvenli olsun)
  if [[ -f package.json ]] && [[ -f static/css/input.css ]]; then
    log_info "Tailwind CSS derleniyor..."
    docker run --rm \
      -v "$(pwd):/app" -w /app \
      node:20-slim \
      sh -c "npm install --no-audit --no-fund && npx tailwindcss -i ./static/css/input.css -o ./static/css/tailwind.min.css --minify"
    log_ok "Tailwind tamamlandi."
  fi

  # Full build yaptiysak up -d container'lari yeni image ile acar; yapmadiysak mevcut container'lar ayakta kalir
  log_info "Containers ayakta (up -d)..."
  docker compose -f docker-compose.prod.yml up -d

  # Web container restart loop'taysa exec calismaz; once "running" olmasini bekle
  log_info "Web container'in ayaga kalkmasini bekleniyor..."
  WEB_READY=0
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
    status=$(docker compose -f docker-compose.prod.yml ps web -q 2>/dev/null | xargs -I{} docker inspect -f '{{.State.Status}}' {} 2>/dev/null || echo "unknown")
    if [[ "$status" == "running" ]]; then
      WEB_READY=1
      log_ok "Web container calisiyor."
      break
    fi
    if [[ "$status" == "restarting" ]]; then
      log_warn "Web container yeniden baslatiliyor (restart loop olabilir), bekleniyor..."
    else
      log_warn "Web container durumu: $status, bekleniyor..."
    fi
    sleep 5
  done
  if [[ "$WEB_READY" != "1" ]]; then
    log_err "Web container 100 sn icinde ayaga kalkmadi (muhtemelen restart loop)."
    log_err "Loglari kontrol edin: docker compose -f docker-compose.prod.yml logs web"
    exit 1
  fi

  log_info "Migrate ve collectstatic (container icinde)..."
  sleep 2
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
    log_err "Web loglari: docker compose -f docker-compose.prod.yml logs web"
    exit 1
  fi
  docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput 2>/dev/null || true

  # Seed data: core seeds with --force (kod degisikliklerini DB'ye yansitir)
  log_info "Seed data (roles, plans, allergens --force)..."
  for cmd in seed_roles seed_plans seed_allergens; do
    if docker compose -f docker-compose.prod.yml exec -T web python manage.py "$cmd" --force; then
      log_ok "  $cmd tamamlandi."
    else
      log_warn "  $cmd atlandi veya hata (devam ediliyor)."
    fi
  done

  # CMS & SEO seeds: footer links, navigation, sitemap data (update_or_create, no --force needed)
  log_info "Seed data (cms_content, seo_data)..."
  for cmd in seed_cms_content seed_seo_data; do
    if docker compose -f docker-compose.prod.yml exec -T web python manage.py "$cmd"; then
      log_ok "  $cmd tamamlandi."
    else
      log_warn "  $cmd atlandi veya hata (devam ediliyor)."
    fi
  done

  # Restart: her deploy'da web/celery tam restart (migration + seed sonrasi guvenli)
  if [[ "$NEED_FULL_BUILD" == "1" ]]; then
    log_info "Tam build yapildi, container'lar up -d ile zaten guncel."
  fi
  if [[ "${DEPLOY_GRACEFUL:-0}" == "1" ]]; then
    log_info "DEPLOY_GRACEFUL=1, graceful reload..."
    docker compose -f docker-compose.prod.yml exec -T web python -c "import os,signal; os.kill(1, signal.SIGHUP)" 2>/dev/null && log_ok "Web: Gunicorn HUP (graceful)" || docker compose -f docker-compose.prod.yml restart web
    docker compose -f docker-compose.prod.yml exec -T celery_worker celery -A config control pool_restart 2>/dev/null && log_ok "Celery worker: pool_restart" || docker compose -f docker-compose.prod.yml restart celery_worker
    docker compose -f docker-compose.prod.yml restart celery_beat
  else
    log_info "Web, celery tam restart (varsayilan)..."
    docker compose -f docker-compose.prod.yml restart web celery_worker celery_beat
    log_ok "Restart tamamlandi."
  fi

  # Her basarili deploy'da deploy_info.json yaz (footer'da build bilgisi)
  cd "$REPO_ROOT"
  GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "")
  GIT_BRANCH_NAME=$(git branch --show-current 2>/dev/null || echo "")
  cd "$APP_ROOT"
  DEPLOY_AT=$(date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
  BUILD_NUM=$(date '+%Y%m%d-%H%M' 2>/dev/null || echo "")
  echo "{\"at\":\"$DEPLOY_AT\",\"status\":\"ok\",\"mode\":\"docker\",\"commit\":\"$GIT_COMMIT\",\"branch\":\"$GIT_BRANCH_NAME\",\"build\":\"$BUILD_NUM\"}" > "$APP_ROOT/deploy_info.json"
  # Container icinde /app image'dan; dosyayi container'a kopyala ki footer okuyabilsin
  if docker compose -f docker-compose.prod.yml cp "$APP_ROOT/deploy_info.json" web:/app/deploy_info.json 2>/dev/null; then
    docker compose -f docker-compose.prod.yml exec -T web chown emenum:emenum /app/deploy_info.json 2>/dev/null || true
    log_ok "deploy_info.json container'a kopyalandi (footer build bilgisi)"
  else
    log_info "deploy_info.json host'ta yazildi (container'a kopya atlandi)"
  fi

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
log_info "Deploy basladi (mode=$DEPLOY_MODE)"

if [[ "$DEPLOY_MODE" == "docker" ]]; then
  run_docker_deploy
else
  run_bare_deploy
fi

echo ""
log_ok "Deploy bitti."
echo "========================================"
if [[ -n "$LOG_FILE" ]]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [DONE] Deploy tamamlandi" >> "$LOG_FILE"
  echo "" >> "$LOG_FILE"
fi