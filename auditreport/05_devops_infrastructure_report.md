# DevOps & Infrastructure Audit Report

**Project:** E-Menum Enterprise QR Menu SaaS
**Date:** 2026-03-17
**SAFe Role:** Release Train Engineer / DevOps Lead
**Auditor:** E-Menum Engineering Team -- Automated Audit System
**Report Version:** 1.1.1

---

## Executive Summary

| Metric | Score |
|--------|-------|
| **Overall Operational Readiness** | **76 / 100** |
| CI/CD Pipeline | 82 / 100 |
| Docker Architecture | 85 / 100 |
| Infrastructure Topology | 72 / 100 |
| Production Readiness | 70 / 100 |
| Monitoring & Observability | 65 / 100 |
| Disaster Recovery | 55 / 100 |

The project has a well-designed CI/CD pipeline with lint, test, security, and Tailwind build stages. The Docker architecture uses a 5-stage multi-stage build with proper non-root user execution and health checks. The deployment model uses webhook-triggered git-pull deploys on a Hetzner VPS. Sentry error tracking is configured in production.py (needs SENTRY_DSN env var). Key gaps include database backup automation (simple pg_dump cronjob recommended) and basic uptime monitoring. Full ELK/Prometheus/Grafana stack and CDN are not needed for current regional scale.

---

## 1. CI/CD Pipeline Analysis

### 1.1 GitHub Actions Workflow Overview

**File:** `.github/workflows/ci.yml`

| Job | Name | Depends On | Duration (Est.) |
|-----|------|-----------|----------------|
| lint | Lint & Format | - | ~1 min |
| test | Tests | lint | ~3-5 min |
| security | Security Audit | lint | ~1-2 min |
| tailwind | Tailwind Build | - | ~1 min |

**Total estimated pipeline time: 5-7 minutes** (test and security run in parallel after lint).

### 1.2 Job Details

#### Lint Job
```yaml
- ruff check . --output-format=github
- ruff format --check .
```
- Python 3.13, pip cache on requirements-dev.txt
- Pinned: `ruff==0.15.6`
- **Assessment: GREEN** -- Fast, deterministic, version-pinned

#### Test Job
```yaml
- Django system check (--fail-level WARNING)
- Migration check (makemigrations --check --dry-run)
- pytest -x -q --tb=short --cov=apps --cov=shared --cov-fail-under=55
```
- PostgreSQL 15-alpine service with health check
- Full `requirements-dev.txt` install
- Coverage threshold: 55%
- **Assessment: GREEN** -- Comprehensive test pipeline with coverage gate

#### Security Job
```yaml
- pip-audit --strict --desc on 2>&1 || true
```
- **Assessment: YELLOW** -- `|| true` makes this non-blocking. Known vulnerabilities will not fail the pipeline.

**Finding OPS-01 (MEDIUM):** The `|| true` on pip-audit (ci.yml line 131) means the security audit is informational only. Set a timeline to make this a hard failure.

#### Tailwind Job
```yaml
- npm install --no-audit --no-fund
- npm run css:build
```
- Node.js 20, independent of other jobs
- **Assessment: GREEN** -- Validates CSS build succeeds

### 1.3 Deployment Workflow

**File:** `.github/workflows/deploy.yml`

```
CI (success) + push to main
    --> deploy job
        --> curl POST $DEPLOY_WEBHOOK_URL
```

| Aspect | Details | Assessment |
|--------|---------|-----------|
| Trigger | workflow_run (CI success + push event) | GREEN |
| Method | Webhook POST to server | GREEN |
| Secret | DEPLOY_WEBHOOK_URL in GitHub Secrets | GREEN |
| Graceful fail | Warns if secret not set, exits 0 | GREEN |
| Error handling | `|| exit 1` on curl failure | GREEN |

**Finding OPS-02 (MEDIUM):** The deployment is a simple webhook trigger. There is no rollback mechanism, deployment validation, or smoke test after deployment. If the webhook succeeds but the application fails to start, there is no automated detection.

---

## 2. Docker Architecture

### 2.1 Multi-Stage Dockerfile Analysis

**File:** `e_menum/Dockerfile` (165+ lines)

| Stage | Base Image | Size Impact | Purpose |
|-------|-----------|-------------|---------|
| 1. css-builder | node:20-slim | NOT in final | Tailwind CSS compilation |
| 2. builder | python:3.13-slim-bookworm | NOT in final | pip install + venv |
| 3. production | python:3.13-slim-bookworm | ~300-400MB est. | Runtime image |
| 4. development | extends production | +dev dependencies | Local dev |
| 5. celery-worker | extends production | Same as production | Background tasks |
| 6. celery-beat | extends production | Same as production | Periodic tasks |

### 2.2 Production Stage Security Features

| Feature | Implementation | Status |
|---------|----------------|--------|
| Non-root user | `emenum` (UID/GID 1000) | GREEN |
| Init system | tini | GREEN -- Proper signal handling |
| Health check | curl /health/ every 30s | GREEN |
| No build tools | Separate builder stage | GREEN |
| Minimal packages | Only runtime dependencies | GREEN |
| Read-only FS potential | Not enforced | YELLOW |

### 2.3 Gunicorn Configuration

| Parameter | Value | Assessment |
|-----------|-------|-----------|
| Workers | 3 | GREEN -- (2 * CPU + 1) for CX21 |
| Threads | 2 | GREEN -- gthread worker class |
| Timeout | 120s | YELLOW -- Long for API calls |
| Graceful timeout | 30s | GREEN |
| Keep-alive | 5s | GREEN |
| Worker class | gthread | GREEN -- Better than sync for I/O |
| Worker tmp dir | /dev/shm | GREEN -- RAM-backed temp dir |
| Forwarded allow IPs | * | YELLOW -- Should be proxy IP only |
| Access log | stdout | GREEN |
| Error log | stderr | GREEN |

**Finding OPS-03 (LOW):** `--forwarded-allow-ips "*"` (Dockerfile line 165) trusts X-Forwarded-For from any source. In production behind a known reverse proxy, this should be restricted to the proxy's IP address to prevent header spoofing.

### 2.4 Entrypoint Script

The entrypoint is at `docker/entrypoint.sh` (referenced in Dockerfile line 128). It handles:
- Environment variable-driven migrations (`DJANGO_MIGRATE=true`)
- Static file collection (`DJANGO_COLLECTSTATIC=true`)
- Superuser creation (`DJANGO_CREATE_SUPERUSER`)
- Seed data loading (`DJANGO_SEED_DATA=true`)

### 2.5 AMD64/EPYC Compatibility

A separate `Dockerfile.amd64linux` exists for production deployment on Hetzner (AMD EPYC processors). The production docker-compose references this file:
```yaml
web:
  build:
    dockerfile: Dockerfile.amd64linux
    target: production
```

---

## 3. Docker Compose Topology

### 3.1 Service Inventory

| Service | Image | Ports | Health Check | Restart |
|---------|-------|-------|-------------|---------|
| db | postgres:15-alpine | 127.0.0.1:5432 (prod) | pg_isready | unless-stopped |
| redis | redis:7-alpine | 127.0.0.1:6379 (prod) | redis-cli ping | unless-stopped |
| web | Dockerfile (production) | 8000:8000 | curl /health/ | unless-stopped |
| celery_worker | Dockerfile (celery-worker) | none | none | unless-stopped |
| celery_beat | Dockerfile (celery-beat) | none | none | unless-stopped |

### 3.2 Volume Management

| Volume | Purpose | Persistence |
|--------|---------|------------|
| postgres_data | PostgreSQL data directory | Named volume |
| redis_data | Redis AOF persistence | Named volume |
| media_volume | User-uploaded files | Named volume |
| staticfiles_volume | collectstatic output (prod) | Named volume |
| pip_cache | pip cache (dev only) | Named volume |

### 3.3 Network Topology

- Single bridge network: `emenum_network`
- All services communicate over internal Docker DNS
- External access only through web:8000

### 3.4 Production vs Development Differences

| Aspect | Development | Production |
|--------|-------------|-----------|
| Dockerfile | target: development | target: production |
| Ports (db, redis) | 0.0.0.0 exposed | 127.0.0.1 only |
| Debug | True | False |
| Code mount | Volume mount (.:/app) | Volume mount (.:/app) |
| Beat replicas | Not specified | replicas: 1 (enforced) |
| Static volume | static_volume | staticfiles_volume |

**Finding OPS-04 (MEDIUM):** Production docker-compose.prod.yml mounts the host code directory (`.:/app`). This enables git-pull-based deploys but means the container's code can change without rebuilding. This is acceptable for the current deployment model but should be documented as a deliberate choice.

---

## 4. Infrastructure Topology

### 4.1 Target Deployment

| Component | Specification |
|-----------|--------------|
| Provider | Hetzner |
| Server | VPS CX21+ |
| CPU | 2+ vCPUs (AMD EPYC) |
| RAM | 4+ GB |
| Storage | 40+ GB SSD |
| OS | Linux (Debian/Ubuntu) |
| PaaS | Coolify (self-hosted) |

### 4.2 Service Mesh

```
Internet
   |
   +-- DNS (e-menum.net)
   |
   +-- Hetzner VPS
       |
       +-- Nginx/Traefik (reverse proxy, SSL termination)
       |     |
       |     +-- Let's Encrypt (auto-renewal)
       |
       +-- Docker Engine
             |
             +-- emenum_network (bridge)
                   |
                   +-- web:8000 (Gunicorn, 3 workers)
                   |     |
                   |     +-- db:5432 (PostgreSQL 15)
                   |     +-- redis:6379 (Redis 7)
                   |
                   +-- celery_worker (prefork, 2 concurrent)
                   |     |
                   |     +-- db:5432
                   |     +-- redis:6379
                   |
                   +-- celery_beat (single instance)
                         |
                         +-- db:5432
                         +-- redis:6379
```

---

## 5. Production Readiness Checklist

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | DEBUG=False enforced | GREEN | production.py line 21 |
| 2 | SECRET_KEY from env (required) | GREEN | ValueError if missing |
| 3 | DATABASE_URL from env (required) | GREEN | ValueError if missing |
| 4 | ALLOWED_HOSTS configured | GREEN | Domain + wildcard + localhost |
| 5 | CSRF_TRUSTED_ORIGINS | GREEN | All domain variants |
| 6 | Gunicorn with gthread | GREEN | 3 workers, 2 threads |
| 7 | PostgreSQL with connection pooling | YELLOW | conn_max_age=600, no PgBouncer |
| 8 | Redis maxmemory policy | GREEN | allkeys-lru, 256MB |
| 9 | Static files (WhiteNoise) | GREEN | CompressedManifestStaticFilesStorage |
| 10 | Health check endpoint | GREEN | /health/ in Docker |
| 11 | Non-root container user | GREEN | emenum (UID 1000) |
| 12 | tini init system | GREEN | Proper PID 1 handling |
| 13 | Celery beat single instance | GREEN | replicas: 1 in prod compose |
| 14 | JSON logging in production | GREEN | production.py logging config |
| 15 | Sentry error tracking | YELLOW | Configured but optional (SENTRY_DSN) |
| 16 | Template caching | GREEN | production.py:436-445 |
| 17 | Browsable API disabled | GREEN | production.py:411-413 |
| 18 | Stricter throttle rates | GREEN | anon: 50/hr in production |
| 19 | Database backup automation | RED | Not configured |
| 20 | CDN for static/media | RED | Not configured |
| 21 | Monitoring/alerting | YELLOW | Sentry configured (needs SENTRY_DSN env var); full stack not needed for current scale |
| 22 | Log aggregation | YELLOW | JSON logging to stdout/stderr; ELK/Loki not needed for current scale |
| 23 | Rollback mechanism | RED | No automated rollback |
| 24 | SSL certificate monitoring | YELLOW | Let's Encrypt auto-renewal assumed |

**Production Readiness: 16/24 items GREEN (67%)**

---

## 6. Monitoring & Observability Gaps

### 6.1 Current State

| Capability | Status | Tool |
|-----------|--------|------|
| Error tracking | OPTIONAL | Sentry (if SENTRY_DSN set) |
| Application logging | CONFIGURED | JSON to stdout/stderr |
| Container health checks | CONFIGURED | Docker HEALTHCHECK |
| Uptime monitoring | NOT CONFIGURED | No Uptime Kuma/Pingdom |
| APM (Application Performance) | NOT CONFIGURED | No New Relic/Datadog |
| Infrastructure metrics | NOT CONFIGURED | No Prometheus/node-exporter |
| Database metrics | NOT CONFIGURED | No pg_stat_statements |
| Redis metrics | NOT CONFIGURED | No Redis INFO monitoring |
| Celery monitoring | NOT CONFIGURED | No Flower/Celery Events |
| Log aggregation | NOT CONFIGURED | No ELK/Grafana Loki |
| Alerting | NOT CONFIGURED | No PagerDuty/Slack alerts |

**Finding OPS-05 (MEDIUM):** Sentry error tracking already configured in production.py (needs SENTRY_DSN env var). Full ELK/Prometheus/Grafana stack not needed for current scale. Recommended additions: make Sentry mandatory, add basic uptime monitoring (Uptime Kuma).

### 6.2 Recommended Monitoring Stack (Right-Sized for Current Scale)

| Component | Tool | Effort |
|-----------|------|--------|
| Error tracking | Sentry (make SENTRY_DSN mandatory) | 1h |
| Uptime monitoring | Uptime Kuma (self-hosted) | 2h |
| Celery monitoring | Flower (celery-flower container) | 2h |

**Note:** Full Prometheus/Grafana/ELK stack is not needed for current scale. Sentry provides error tracking, alerting, and performance monitoring. Revisit when scaling beyond 500+ organizations.

---

## 7. Disaster Recovery Assessment

### 7.1 Current Capabilities

| Scenario | Recovery Plan | Status |
|----------|-------------|--------|
| Application crash | Docker `restart: unless-stopped` | GREEN |
| Database corruption | No backup, volume only | RED |
| Full server failure | No documented recovery procedure | RED |
| Media data loss | No backup for media volume | RED |
| Redis data loss | AOF persistence on volume | YELLOW |
| DNS failure | No secondary DNS | YELLOW |
| DDoS attack | SEO Shield rate limiting | YELLOW |
| Secret compromise | No rotation procedure documented | RED |

### 7.2 Recovery Time Objectives

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| RTO (Recovery Time Objective) | Unknown (hours?) | < 30 min | HIGH |
| RPO (Recovery Point Objective) | Unknown (volume snapshot?) | < 1 hour | HIGH |
| MTTR (Mean Time To Recovery) | Not measured | < 15 min | HIGH |

**Finding OPS-07 (RESOLVED):** Admin CSS layout conflict fixed - `grid-column` on `#toolbar` replaced with proper `display: flex` layout.

**Finding OPS-08 (RESOLVED):** Sitemap.xml 500 error fixed with graceful error handling in `apps/seo/sitemaps.py`.

**Finding OPS-06 (MEDIUM):** Recommend simple pg_dump daily cronjob on Hetzner server. Enterprise-level DR not needed for current scale. Example: `0 3 * * * pg_dump -Fc $DATABASE_URL > /backups/emenum_$(date +%Y%m%d).dump`

---

## 8. Scalability Roadmap

### 8.1 Current Capacity Estimation

| Resource | Capacity | Bottleneck At |
|----------|----------|--------------|
| Web (Gunicorn 3w x 2t) | ~100 concurrent requests | 500+ concurrent users |
| Database (PostgreSQL, no pooler) | ~100 connections | Multiple workers saturating |
| Redis (256MB) | ~500K cached keys | Unlikely bottleneck |
| Celery (2 workers) | ~10 tasks/sec | High async task volume |
| Disk (40GB) | ~30GB usable | 10K+ media uploads |

### 8.2 Scaling Steps

| Phase | Trigger | Action | Effort |
|-------|---------|--------|--------|
| Phase 1 | 100+ orgs | Add PgBouncer, increase Gunicorn workers to 4 | 4h |
| Phase 2 | 500+ orgs | Add CDN (CloudFlare/BunnyCDN), S3 for media | 16h |
| Phase 3 | 1000+ orgs | Horizontal scaling: multiple web containers, load balancer | 24h |
| Phase 4 | 5000+ orgs | Database read replicas, Redis Cluster, dedicated Celery workers | 40h |
| Phase 5 | 10000+ orgs | Consider Kubernetes migration, database sharding evaluation | 80h+ |

---

## 9. Cost Optimization

### 9.1 Current Estimated Costs

| Component | Monthly Cost (Est.) | Notes |
|-----------|-------------------|-------|
| Hetzner CX21 VPS | ~10 EUR | 2 vCPU, 4GB RAM, 40GB SSD |
| Domain (e-menum.net) | ~1 EUR/mo amortized | Annual registration |
| Let's Encrypt SSL | Free | Auto-renewal |
| GitHub (public/private) | Free tier | Actions minutes included |
| Coolify (self-hosted) | Free | Open source |
| **Total** | **~11 EUR/mo** | |

### 9.2 Optimization Opportunities

| Item | Potential Saving | Trade-off |
|------|-----------------|-----------|
| Switch to CX22 (newer gen) | Same price, better perf | Migration effort |
| Hetzner Object Storage for media | ~3 EUR/mo vs S3 | Vendor lock-in |
| Hetzner Volume for backups | ~5 EUR/mo (20GB) | Additional management |
| CloudFlare free tier for CDN | Free | DNS delegation |

---

## 10. Recommendations

### Critical (This Week)

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| OPS-R01 | Set up automated PostgreSQL backups (pg_dump + cron) | 4h | CRITICAL |
| OPS-R02 | Make Sentry DSN mandatory in production | 1h | HIGH |
| OPS-R03 | Set up basic uptime monitoring (Uptime Kuma or external) | 2h | HIGH |

### High (Next Sprint)

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| OPS-R04 | Remove `|| true` from pip-audit CI step | 1h | MEDIUM |
| OPS-R05 | Add deployment smoke test (curl /health/ after deploy) | 2h | HIGH |
| OPS-R06 | Restrict --forwarded-allow-ips to proxy IP | 1h | MEDIUM |
| OPS-R07 | Add Celery Flower for task monitoring | 2h | MEDIUM |

### Medium (Next PI)

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| OPS-R08 | ~~Set up Prometheus + Grafana~~ Not needed -- Sentry sufficient for current scale | N/A | N/A |
| OPS-R09 | ~~Configure CDN~~ BY DESIGN -- local serving via Traefik sufficient for regional SaaS | N/A | N/A |
| OPS-R10 | ~~Add PgBouncer~~ NOT APPLICABLE -- conn_max_age=600 sufficient for current scale | N/A | N/A |
| OPS-R11 | Create disaster recovery runbook | 8h | HIGH |
| OPS-R12 | Implement automated rollback on health check failure | 8h | HIGH |
| OPS-R13 | Enable pytest-xdist in CI for parallel tests | 1h | LOW |

### Long-Term (Backlog)

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| OPS-R14 | Set up log aggregation (Grafana Loki) | 8h | MEDIUM |
| OPS-R15 | Document and test full server recovery procedure | 16h | HIGH |
| OPS-R16 | Evaluate Kubernetes migration path for horizontal scaling | 40h | MEDIUM |

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-17 | Automated Audit System | Initial DevOps & infrastructure audit |
| 1.1.0 | 2026-03-17 | Automated Audit System | Updated with post-deploy fixes and accurate metrics |
| 1.1.1 | 2026-03-17 | Automated Audit System | Business context corrections: OPS-05 severity HIGH->MEDIUM (Sentry already configured), OPS-06 severity CRITICAL->MEDIUM (simple pg_dump cronjob recommended) |
