#!/usr/bin/env bash
# =============================================================================
# E-Menum Webhook Kurulum Scripti
# =============================================================================
# GitHub push -> webhook URL -> deploy.sh tetiklenir.
#
# Kullanım:
#   WEBHOOK_SECRET=gizli_anahtar_32 ./scripts/webhook.sh
#   ./scripts/webhook.sh
#     (script SECRET sorar veya rasgele uretir)
#
# Parametreler (ortam degiskenleri):
#   WEBHOOK_SECRET   Guvenlik icin gizli anahtar (URL path'e eklenir)
#   WEBHOOK_PORT     Dinlenecek port (varsayilan: 9000)
#   REPO_PATH        Proje kokunu (varsayilan: script'in 1 ust dizini)
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_err()   { echo -e "${RED}[ERROR]${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_PATH="${REPO_PATH:-$(cd "$SCRIPT_DIR/.." && pwd)}"
DEPLOY_SCRIPT="$REPO_PATH/scripts/deploy.sh"
WEBHOOK_PORT="${WEBHOOK_PORT:-9000}"

# -----------------------------------------------------------------------------
# SECRET kontrol
# -----------------------------------------------------------------------------
if [[ -z "$WEBHOOK_SECRET" ]]; then
  WEBHOOK_SECRET=$(openssl rand -hex 16 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -1)
  log_info "WEBHOOK_SECRET verilmedi, uretildi: $WEBHOOK_SECRET"
  log_warn "Bu degeri kaydedin! GitHub DEPLOY_WEBHOOK_URL'de kullanacaksiniz."
fi

# Guvenlik: sadece alfanumerik
WEBHOOK_SECRET=$(echo "$WEBHOOK_SECRET" | tr -cd 'a-zA-Z0-9_-' | head -c 64)
HOOK_ID="emenum-deploy-$WEBHOOK_SECRET"
WEBHOOK_URL_PATH="/hooks/$HOOK_ID"

# -----------------------------------------------------------------------------
# Onkosullar
# -----------------------------------------------------------------------------
if [[ ! -x "$DEPLOY_SCRIPT" ]]; then
  log_err "deploy.sh bulunamadi veya calistirilabilir degil: $DEPLOY_SCRIPT"
  exit 1
fi

# -----------------------------------------------------------------------------
# webhook binary indir
# -----------------------------------------------------------------------------
log_info "webhook binary indiriliyor..."
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

ARCH=$(uname -m)
case "$ARCH" in
  x86_64)  ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  armv7l)  ARCH="arm" ;;
  *)       ARCH="amd64"; log_warn "Bilinmeyen arch $ARCH, amd64 deneniyor" ;;
esac

WEBHOOK_VERSION="2.8.3"
DOWNLOAD_URL="https://github.com/adnanh/webhook/releases/download/${WEBHOOK_VERSION}/webhook-linux-${ARCH}.tar.gz"

if ! curl -sSLf "$DOWNLOAD_URL" -o "$TMP_DIR/webhook.tar.gz"; then
  log_err "webhook indirilemedi: $DOWNLOAD_URL"
  exit 1
fi

tar xzf "$TMP_DIR/webhook.tar.gz" -C "$TMP_DIR"
WEBHOOK_BIN=$(find "$TMP_DIR" -name "webhook" -type f | head -1)
sudo cp "$WEBHOOK_BIN" /usr/local/bin/webhook
sudo chmod +x /usr/local/bin/webhook
log_ok "webhook /usr/local/bin/webhook yerlestirildi"

# -----------------------------------------------------------------------------
# hooks.json olustur
# -----------------------------------------------------------------------------
sudo mkdir -p /etc/emenum-webhook
HOOKS_JSON="/etc/emenum-webhook/hooks.json"

sudo tee "$HOOKS_JSON" > /dev/null << HOOKSEOF
[
  {
    "id": "$HOOK_ID",
    "execute-command": "$DEPLOY_SCRIPT",
    "command-working-directory": "$REPO_PATH",
    "response-message": "Deploy tetiklendi.",
    "pass-arguments-to-command": [
      {"source": "payload", "name": "ref"}
    ]
  }
]
HOOKSEOF

log_ok "hooks.json olusturuldu: $HOOKS_JSON"

# -----------------------------------------------------------------------------
# systemd service
# -----------------------------------------------------------------------------
sudo tee /etc/systemd/system/emenum-webhook.service > /dev/null << SERVICEEOF
[Unit]
Description=E-Menum deploy webhook
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/webhook -hooks $HOOKS_JSON -port $WEBHOOK_PORT -verbose
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

sudo systemctl daemon-reload
sudo systemctl enable emenum-webhook
sudo systemctl restart emenum-webhook
log_ok "systemd servisi: emenum-webhook (port $WEBHOOK_PORT)"

# -----------------------------------------------------------------------------
# Firewall (ufw varsa)
# -----------------------------------------------------------------------------
if command -v ufw &>/dev/null && sudo ufw status 2>/dev/null | grep -q "Status: active"; then
  if sudo ufw status | grep -q " $WEBHOOK_PORT "; then
    log_info "Port $WEBHOOK_PORT zaten acik"
  else
    sudo ufw allow "$WEBHOOK_PORT"/tcp
    log_ok "ufw: port $WEBHOOK_PORT acildi"
  fi
else
  log_info "ufw aktif degil, firewall atlandi"
fi

# -----------------------------------------------------------------------------
# Sonuc
# -----------------------------------------------------------------------------
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "SUNUCU_IP")
echo ""
echo "========================================"
echo -e "  ${GREEN}Webhook kuruldu${NC}"
echo "========================================"
echo ""
echo "GitHub Actions icin DEPLOY_WEBHOOK_URL secret'ina su URL'yi ekleyin:"
echo ""
echo -e "  ${BLUE}http://${SERVER_IP}:${WEBHOOK_PORT}${WEBHOOK_URL_PATH}${NC}"
echo ""
echo "Domain kullaniyorsaniz (https):"
echo "  https://domain.com/deploy  (nginx proxy gerekli)"
echo ""
echo "Test:"
echo "  curl -X POST http://${SERVER_IP}:${WEBHOOK_PORT}${WEBHOOK_URL_PATH}"
echo ""
echo "Servis:"
echo "  sudo systemctl status emenum-webhook"
echo "  sudo systemctl restart emenum-webhook"
echo ""
