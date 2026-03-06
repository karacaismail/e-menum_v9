# E-Menum Scripts

## deploy.sh – CI/CD Deploy  #1

GitHub'a commit atıldığında sunucuda güncel kodu çekip migration, build ve restart işlemlerini yapan script.

### Sunucuda kullanım

```bash
# Repo kökünde (e-menum_v9)
./scripts/deploy.sh
```

- **Docker (akıllı mod):** Commit'e göre karar verir:
  - **Sadece kod değiştiyse:** Image derlenmez, Tailwind + up -d + migrate + collectstatic + **seed (roles, plans, allergens --force)** + **tam restart** (web, celery).
  - **Dockerfile, requirements*.txt, package.json, docker/, docker-compose.prod.yml değiştiyse:** **Tam image build** + up -d + migrate + collectstatic + seed + restart.
  - **DEPLOY_GRACEFUL=1** verirseniz: Graceful reload (HUP) yerine tam restart.
- **Bare metal (Gunicorn):** venv, `pip install`, `migrate`, Tailwind `css:build`, `collectstatic`, ardından Gunicorn restart (systemctl veya HUP).

### Ortam değişkenleri

| Değişken       | Açıklama |
|----------------|----------|
| `DEPLOY_MODE`  | `docker` veya `bare` (boşsa otomatik tespit) |
| `GIT_BRANCH`   | Çekilecek branch (varsayılan: mevcut branch) |
| `SKIP_PULL`    | `1` ise `git pull` atlanır |
| `LOCK_FILE`    | Kilit dosyası (varsayılan: `/tmp/emenum-deploy.lock`) |
| `DEPLOY_BUILD` | `1` ise her deploy'da Docker image derlenir; `0` ise sadece ilgili dosya değiştiğinde (varsayılan: 0) |
| `FORCE_DEPLOY`   | `1` ise degisiklik olmasa da islemler yapilir |
| `DEPLOY_GRACEFUL`| `1` ise graceful (HUP); `0` ise her deploy tam restart (varsayilan: 0) |
| `DEPLOY_LOG`     | Log dosyasi (varsayilan: `/var/log/deploy.log`) |
| `DEPLOY_DEBUG` | `1` ise test modu: tum adimlar + deploy_test.json + health check (footer badge) |
| `VENV_PATH`    | Bare metal'de venv yolu (varsayılan: repo kökünde `.venv`) |

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

# Degisiklik olmasa da islemleri zorla calistir (migrate/collectstatic vb.)
FORCE_DEPLOY=1 ./scripts/deploy.sh

# Test modu: tum CI/CD adimlari + deploy_test.json (footer'da badge) + health check
DEPLOY_DEBUG=1 ./scripts/deploy.sh
```

### GitHub ile otomatik tetikleme

1. **Sunucuda:** `./scripts/webhook.sh` ile kurulum (detay: asagidaki webhook.sh bolumu).
2. **GitHub Actions:** `.github/workflows/deploy.yml` push (main) sonrasi webhook URL'ine POST atar.
3. **Secret:** Repo → Settings → Secrets and variables → Actions → `DEPLOY_WEBHOOK_URL` = script ciktisindaki tam URL.

Webhook kullanmıyorsanız: sunucuda elle `git pull && ./scripts/deploy.sh` veya SSH ile tek komut çalıştırabilirsiniz.

**Docker + volume:** Tailwind, gecici Node container icinde derlenir (sunucuda Node gerekmez). Kod `e_menum` -> container `/app` mount; media ve staticfiles volume'da.

---

## webhook.sh – Webhook Kurulum

GitHub push sonrasi deploy tetikleyen webhook servisini kurar (adnanh/webhook).

### Kurulum

```bash
cd /opt/emenum-src   # veya repo kokunuz

# Ilk kurulum: secret verilmezse rasgele uretilir, ciktisini kaydedin
./scripts/webhook.sh

# Guncelleme (hooks.json, servis): once servisi durdurun, secret ile tekrar calistirin
sudo systemctl stop emenum-webhook
sudo env WEBHOOK_SECRET=GIZLI_ANAHTARINIZ bash /opt/emenum-src/scripts/webhook.sh
```

### Neden stop + env?

- **stop:** Webhook binary calisirken uzerine yazilamaz (`Text file busy`). Servisi once durdurmak gerekir.
- **env:** `sudo` ortam degiskenlerini tasimaz. `sudo env WEBHOOK_SECRET=xxx` ile secret gecirilir; aksi halde yeni secret uretilir, GitHub'daki URL gecersiz olur.

### GitHub Webhook Ayarı

1. Script ciktisindaki URL'yi kopyalayin (orn. `http://SUNUCU_IP:9000/hooks/emenum-deploy-XXX`).
2. Repo → Settings → Secrets and variables → Actions → `DEPLOY_WEBHOOK_URL` secret'ına yapistirin.
3. `.github/workflows/deploy.yml` push (main) sonrasi bu URL'ye POST atar.

### Log ve servis

| Dosya/Komut | Aciklama |
|-------------|----------|
| `/var/log/webhook.log` | Webhook servis logu |
| `/var/log/deploy.log` | deploy.sh ciktisi |
| `tail -f /var/log/webhook.log` | Canli izleme |
| `sudo systemctl status emenum-webhook` | Servis durumu |
| `sudo systemctl restart emenum-webhook` | Servis yeniden baslat |

### Ortam degiskenleri

| Degisken | Varsayilan | Aciklama |
|----------|------------|----------|
| `WEBHOOK_SECRET` | (rasgele) | URL path'e eklenen gizli anahtar |
| `WEBHOOK_PORT` | 9000 | Dinleme portu |
| `WEBHOOK_LOG` | /var/log/webhook.log | Log dosyasi |
| `REPO_PATH` | script ust dizini | Proje kökü |

### Test

```bash
curl -X POST "http://SUNUCU_IP:9000/hooks/emenum-deploy-SECRET"
```

---

### Kesinti ve guvenlik

- **Kesinti:** Varsayilan graceful modda web ve Celery worker kesintisiz (HUP/pool_restart). Celery beat ~2 sn restart. Migrate once calistirilir; migrate hata verirse script durur, restart yapilmaz (proje tutarli kalir).
- **Yetkiler:** Container kullanici emenum (UID 1000). Media ve staticfiles named volume'da; kod host mount (okunabilir olmali).
- **Cift deploy:** `flock` ile ayni anda yalnizca bir deploy calisir; ust uste tetikleme projeyi bozmaz.
