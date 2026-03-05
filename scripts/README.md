# E-Menum Scripts

## deploy.sh – CI/CD Deploy

GitHub’a commit atıldığında sunucuda güncel kodu çekip migration, build ve restart işlemlerini yapan script.

### Sunucuda kullanım

```bash
# Repo kökünde (e-menum_v9)
./scripts/deploy.sh
```

- **Docker (varsayilan: build yok, sadece up + migrate):** Kod host'tan mount; deploy: git pull, host'ta Tailwind, up -d, migrate, collectstatic, restart. Image her seferinde derlenmez. Migrate ve collectstatic container entrypoint’te zaten çalışır.
- **Bare metal (Gunicorn):** venv, `pip install`, `migrate`, Tailwind `css:build`, `collectstatic`, ardından Gunicorn restart (systemctl veya HUP).

### Ortam değişkenleri

| Değişken       | Açıklama |
|----------------|----------|
| `DEPLOY_MODE`  | `docker` veya `bare` (boşsa otomatik tespit) |
| `GIT_BRANCH`   | Çekilecek branch (varsayılan: mevcut branch) |
| `SKIP_PULL`    | `1` ise `git pull` atlanır |
| `LOCK_FILE`    | Kilit dosyası (varsayılan: `/tmp/emenum-deploy.lock`) |
| `DEPLOY_BUILD` | `1` ise Docker image derlenir (varsayılan: atlanır) |
| `VENV_PATH`    | Bare metal’de venv yolu (varsayılan: repo kökünde `.venv`) |

**Lock:** Script `flock` ile aynı anda yalnızca bir deploy calisir. Dakikada bir tetikleseniz bile, onceki deploy bitene kadar yeni cagri kilit alinamadigi icin sessizce cikar (exit 0).

### Örnekler

```bash
# Sadece Docker deploy
DEPLOY_MODE=docker ./scripts/deploy.sh

# Belirli branch
GIT_BRANCH=main ./scripts/deploy.sh

# Pull yapmadan (zaten güncel kodu çektiniz)
SKIP_PULL=1 ./scripts/deploy.sh

# Kod/Dockerfile degisikligi sonrasi tam image build
DEPLOY_BUILD=1 ./scripts/deploy.sh
```

### GitHub ile otomatik tetikleme

1. **GitHub Actions:** `.github/workflows/deploy.yml` push (main) sonrası isteğe bağlı webhook çağırır.
2. **Secret:** Repo → Settings → Secrets → `DEPLOY_WEBHOOK_URL` (Coolify veya kendi webhook URL’iniz).
3. **Sunucuda:** Webhook geldiğinde `./scripts/deploy.sh` çalıştırılacak şekilde ayarlayın (Coolify “Deploy” webhook’u veya küçük bir webhook sunucusu).

Webhook kullanmıyorsanız: sunucuda elle `git pull && ./scripts/deploy.sh` veya SSH ile tek komut çalıştırabilirsiniz.

**Docker + volume:** Sunucuda Node.js kurulu olmali (Tailwind host'ta derlenir). Kod `e_menum` -> container `/app` mount edilir; media ve staticfiles named volume'da kalir.
