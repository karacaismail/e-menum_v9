# E-Menum Scripts

## deploy.sh – CI/CD Deploy

GitHub’a commit atıldığında sunucuda güncel kodu çekip migration, build ve restart işlemlerini yapan script.

### Sunucuda kullanım

```bash
# Repo kökünde (e-menum_v9)
./scripts/deploy.sh
```

- **Docker kullanıyorsanız:** `docker-compose.prod.yml` ile build + up yapar. Migrate ve collectstatic container entrypoint’te zaten çalışır.
- **Bare metal (Gunicorn):** venv, `pip install`, `migrate`, Tailwind `css:build`, `collectstatic`, ardından Gunicorn restart (systemctl veya HUP).

### Ortam değişkenleri

| Değişken       | Açıklama |
|----------------|----------|
| `DEPLOY_MODE`  | `docker` veya `bare` (boşsa otomatik tespit) |
| `GIT_BRANCH`   | Çekilecek branch (varsayılan: mevcut branch) |
| `SKIP_PULL`    | `1` ise `git pull` atlanır |
| `VENV_PATH`    | Bare metal’de venv yolu (varsayılan: repo kökünde `.venv`) |

### Örnekler

```bash
# Sadece Docker deploy
DEPLOY_MODE=docker ./scripts/deploy.sh

# Belirli branch
GIT_BRANCH=main ./scripts/deploy.sh

# Pull yapmadan (zaten güncel kodu çektiniz)
SKIP_PULL=1 ./scripts/deploy.sh
```

### GitHub ile otomatik tetikleme

1. **GitHub Actions:** `.github/workflows/deploy.yml` push (main) sonrası isteğe bağlı webhook çağırır.
2. **Secret:** Repo → Settings → Secrets → `DEPLOY_WEBHOOK_URL` (Coolify veya kendi webhook URL’iniz).
3. **Sunucuda:** Webhook geldiğinde `./scripts/deploy.sh` çalıştırılacak şekilde ayarlayın (Coolify “Deploy” webhook’u veya küçük bir webhook sunucusu).

Webhook kullanmıyorsanız: sunucuda elle `git pull && ./scripts/deploy.sh` veya SSH ile tek komut çalıştırabilirsiniz.
