# E-Menum Project Context

> **Auto-Claude Context Document**  
> Bu dosya, projenin iş bağlamını ve stratejik yönelimini detaylandırır.  
> Son Güncelleme: 2026-01-31

---

## 1. STRATEGIC CONTEXT

### 1.1 Vizyon

**2030 Vizyonu:** Türkiye'nin önde gelen restoran teknoloji ekosistemi olmak.

**Misyon:** Restoran ve kafelere yapay zeka destekli araçlar sunarak operasyonel verimliliği artırmak, müşteri deneyimini iyileştirmek ve veri odaklı kararlar almalarını sağlamak.

### 1.2 Değer Önerisi (Value Proposition)

| Segment | Problem | E-Menum Çözümü |
|---------|---------|----------------|
| Küçük Kafe | Menü güncelleme zor, pahalı | Anında dijital güncelleme, ücretsiz başlangıç |
| Orta Restoran | Müşteri verisi yok | Analitik dashboard, müşteri segmentasyonu |
| Zincir İşletme | Şubeler arası tutarsızlık | Merkezi menü yönetimi, senkronizasyon |
| Tümü | AI erişimi yok | Entegre AI: içerik, görsel, tahminleme |

### 1.3 Rekabet Avantajları

| Avantaj | Detay |
|---------|-------|
| **AI-First** | 9 farklı AI modeli entegrasyonu (Claude, GPT, Prophet) |
| **Uygun Fiyat** | Rakiplere göre %30-50 daha uygun |
| **Yerel Odak** | Türk pazarına özel özellikler, TL fatulama |
| **Modüler Yapı** | İhtiyaca göre özellik seçimi |
| **Self-serve** | Teknik destek gerektirmez |

---

## 2. MARKET CONTEXT

### 2.1 Pazar Büyüklüğü (TAM-SAM-SOM)

| Metrik | Değer | Açıklama |
|--------|-------|----------|
| **TAM** | 350.000 işletme | Türkiye F&B toplam |
| **SAM** | 87.500 işletme | Teknoloji adopte eden segment |
| **SOM Y1** | 500 işletme | İlk yıl hedef |
| **SOM Y3** | 5.000 işletme | 3 yıl hedef |
| **SOM Y5** | 50.000 işletme | 5 yıl hedef (₺100M ARR) |

### 2.2 Hedef Müşteri Profili (ICP)

**Birincil Segment: Orta Ölçekli Kafeler**
- Konum: İstanbul (başlangıç), A/A+ lokasyonlar
- Büyüklük: 20-100 kişi kapasiteli
- Ürün sayısı: 30-150 menü kalemi
- Dijital hazırlık: Sosyal medya aktif
- Pain point: Menü güncelleme zorluğu, veri eksikliği

**İkincil Segment: Butik Restoranlar**
- Fine dining veya konsept mekanlar
- Premium görsel ihtiyacı
- Alerjen/beslenme bilgisi zorunluluğu

**Üçüncül Segment: Zincir İşletmeler**
- 3+ şube
- Merkezi yönetim ihtiyacı
- Franchise standardizasyon

### 2.3 Rakip Haritası

| Rakip | Güçlü Yönü | Zayıf Yönü | E-Menum Avantajı |
|-------|------------|------------|------------------|
| Menulux | Pazar lideri | Pahalı, eski UI | Fiyat, modern UX |
| QRall | Kolay kullanım | Limited özellik | AI, modüler yapı |
| Getir Menü | Entegrasyon | Bağımlılık yaratır | Bağımsızlık |
| Paper menu | Tanıdıklık | Güncelleme zor | Anında güncelleme |

---

## 3. PRODUCT CONTEXT

### 3.1 Feature Kategorileri

| Kategori | Özellik Sayısı | Durum |
|----------|----------------|-------|
| Core (Menü, QR, Tema) | 45 | MVP |
| Sipariş & Operasyon | 38 | Growth |
| AI Features | 42 | Diferansiyatör |
| Analytics & Reporting | 67 | Enterprise |
| Gamification | 25 | Engagement |
| Entegrasyonlar | 15 | Ecosystem |
| **TOPLAM** | **272** | - |

### 3.2 Pricing Tiers

| Plan | Fiyat/Ay | Hedef | Temel Özellikler |
|------|----------|-------|------------------|
| **Free** | ₺0 | Lead gen | 1 menü, 3 kategori, 15 ürün, watermark |
| **Starter** | ₺2.000 | Küçük kafe | Unlimited menü, 5.000 QR scan, basic analytics |
| **Professional** | ₺4.000 | Orta işletme | AI content, advanced analytics, 1 şube |
| **Business** | ₺6.000 | Büyük restoran | Multi-branch (3), kampanyalar, API |
| **Enterprise** | ₺8.000+ | Zincir | Unlimited şube, SLA, dedicated support |

### 3.3 AI Credit System

| Model | Credit/İstek | Kullanım |
|-------|--------------|----------|
| Claude Haiku | 1 | Hızlı içerik |
| Claude Sonnet | 3 | Detaylı içerik |
| GPT-4o-mini | 2 | Alternatif |
| GPT-4o | 5 | Premium |
| Image Gen (DALL-E) | 10 | Görsel üretimi |
| Image Gen (Midjourney) | 15 | Premium görsel |
| Prophet Forecast | 5 | Tahminleme |
| Anomaly Detection | 3 | Anomali tespiti |
| NL Query | 2 | Doğal dil sorgu |

**Plan Bazlı Aylık Credit:**
- Starter: 500
- Professional: 2.000
- Business: 5.000
- Enterprise: Unlimited

---

## 4. TECHNICAL CONTEXT

### 4.1 Sistem Gereksinimleri

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| Node.js | 20.x LTS | 22.x LTS |
| PostgreSQL | 14 | 15+ |
| Redis | 6.x | 7.x |
| RAM | 2GB | 4GB |
| Storage | 20GB | 50GB+ |

### 4.2 Performance Hedefleri

| Metrik | Hedef | Kritik |
|--------|-------|--------|
| API Response (P95) | <200ms | <500ms |
| Page Load (TTI) | <2s | <4s |
| Database Query | <50ms | <100ms |
| Uptime | 99.9% | 99.5% |
| Error Rate | <0.1% | <1% |

### 4.3 Scalability Projections

| Metrik | MVP | Y1 | Y3 | Y5 |
|--------|-----|----|----|----|-
| Organizations | 100 | 500 | 5.000 | 50.000 |
| Products | 10K | 50K | 500K | 5M |
| QR Scans/day | 1K | 10K | 100K | 1M |
| Concurrent Users | 100 | 500 | 5.000 | 50.000 |
| Database Size | 1GB | 10GB | 100GB | 1TB |

---

## 5. TEAM CONTEXT

### 5.1 Ekip Yapısı

| İsim | Rol | Sorumluluk | Haftalık Saat |
|------|-----|------------|---------------|
| İsmail | Stratejik Danışman | Mimari, ürün stratejisi | Değişken |
| Pınar | Sales & Support | Müşteri edinimi, destek | 20 |
| Ali | Jr. Developer | Istanbul bölge, frontend | 20 |
| Bora | Jr. Developer | Diğer bölge, backend | 20 |
| Ahmet | Jr. Developer | GTM, Mautic, DevOps | 20 |

### 5.2 Kaynak Kısıtları

| Kaynak | Limit | Not |
|--------|-------|-----|
| Aylık Bütçe | ₺10.000 | İşgücü + infra |
| Dev Kapasitesi | 60 saat/hafta | 3 dev × 20 saat |
| Infra Budget | ~₺500/ay | Hetzner VPS |

### 5.3 Communication Channels

| Kanal | Kullanım |
|-------|----------|
| GitHub Issues | Task tracking, bug reports |
| GitHub Discussions | Technical decisions |
| Slack/Discord | Günlük iletişim |
| Weekly Call | Sprint planning |

---

## 6. BUSINESS RULES CONTEXT

### 6.1 Multi-Tenancy Rules

```yaml
Tenant Isolation:
  - Her organization tamamen izole
  - Cross-tenant data access YASAK
  - Shared resources: plans, system configs only
  
Data Ownership:
  - Tüm içerik organization'a ait
  - Export her zaman mümkün (GDPR)
  - Hesap silme = 30 gün soft delete, sonra purge
```

### 6.2 Permission Inheritance

```yaml
Hierarchy:
  Platform Level:
    - super_admin > admin > sales > support
  
  Organization Level:
    - owner > manager > staff > viewer
  
  Inheritance Rules:
    - owner: organization içinde tam yetki
    - manager: billing hariç tam yetki
    - staff: assigned modules only
    - viewer: read-only everywhere
```

### 6.3 Plan Feature Gating

```yaml
Feature Access Rules:
  - Free: Watermark zorunlu, limited everything
  - Starter: Base features, no AI
  - Professional: AI content, advanced analytics
  - Business: Multi-branch, API access
  - Enterprise: Custom features, SLA

Override System:
  - Admin can grant/revoke specific features
  - Trial periods possible
  - Grandfathering for existing customers
```

---

## 7. INTEGRATION CONTEXT

### 7.1 External Services

| Servis | Amaç | Kritiklik |
|--------|------|-----------|
| Anthropic (Claude) | AI text generation | Yüksek |
| OpenAI (GPT) | AI fallback | Orta |
| Unsplash | Stock photos | Düşük |
| DALL-E/Midjourney | Image generation | Orta |
| Stripe/Iyzico | Payment processing | Kritik |
| SendGrid/AWS SES | Email delivery | Yüksek |
| Google Analytics | User analytics | Orta |

### 7.2 Webhook Events

| Event | Payload | Use Case |
|-------|---------|----------|
| `menu.published` | Menu ID, org ID | Sync to POS |
| `order.created` | Order details | Kitchen display |
| `qr.scanned` | QR ID, timestamp | Analytics |
| `subscription.changed` | Plan, status | Billing sync |

---

## 8. COMPLIANCE CONTEXT

### 8.1 KVKK (Turkish GDPR)

| Gereksinim | Uygulama |
|------------|----------|
| Açık Rıza | Cookie consent, signup consent |
| Veri Minimizasyonu | Only essential data collection |
| Silme Hakkı | Self-service account deletion |
| Taşınabilirlik | JSON export feature |
| DPO | İsmail (designated) |

### 8.2 Accessibility (WCAG 2.1)

| Level | Hedef | Öncelik |
|-------|-------|---------|
| A | Zorunlu | MVP |
| AA | Önerilen | V2 |
| AAA | İdeal | Future |

---

## 9. RISK CONTEXT

### 9.1 Technical Risks

| Risk | Olasılık | Etki | Mitigasyon |
|------|----------|------|------------|
| AI API downtime | Orta | Yüksek | Multi-provider fallback |
| Database scaling | Düşük | Yüksek | Read replicas, caching |
| Security breach | Düşük | Kritik | Regular audits, encryption |

### 9.2 Business Risks

| Risk | Olasılık | Etki | Mitigasyon |
|------|----------|------|------------|
| Low market traction | Yüksek | Kritik | Aggressive sales, pivot |
| Competitor response | Orta | Orta | Differentiation (AI) |
| Team capacity | Yüksek | Yüksek | Prioritization, automation |

---

## 10. SUCCESS METRICS

### 10.1 North Star Metric

**Monthly Active Organizations (MAO)** - Ay içinde en az 1 menü görüntüleme/güncelleme yapan organization sayısı.

### 10.2 Key Performance Indicators

| KPI | Target (Y1) | Current |
|-----|-------------|---------|
| MAO | 300 | 0 |
| MRR | ₺600K | ₺0 |
| Churn Rate | <5% | N/A |
| NPS | >40 | N/A |
| CAC | <₺500 | TBD |
| LTV | >₺36K | Projected |
| LTV:CAC | >72:1 | Projected |

### 10.3 Product-Market Fit Indicators

| Indicator | Target | Current |
|-----------|--------|---------|
| 40% "Very Disappointed" | 40%+ | 20% |
| Organic Growth | 30%+ | 0% |
| NPS | >40 | N/A |
| Retention (M3) | >80% | N/A |

---

## 11. ROADMAP CONTEXT

### 11.1 Phase Overview

| Phase | Timeline | Focus | Key Deliverables |
|-------|----------|-------|------------------|
| **1: MVP Core** | Ay 1-3 | Foundation | Auth, Menu, QR, Basic UI |
| **2: Growth** | Ay 4-6 | Engagement | Orders, AI Features, Analytics |
| **3: Enterprise** | Ay 7-10 | Scale | Multi-branch, Campaigns, Advanced AI |
| **4: Innovation** | Ay 11+ | Differentiation | Voice, AR, Chatbot |

### 11.2 Current Sprint Focus

**Sprint Goal:** Core infrastructure + MVP features

**Active Specs:**
- SPEC-001: Core Kernel
- SPEC-002: Database Setup
- SPEC-003: Auth Module
- SPEC-004: Multi-tenant Infrastructure
- SPEC-005: AI Gateway

---

## 12. DOCUMENTATION STANDARDS

### 12.1 Spec Writing Rules

| Kural | Detay |
|-------|-------|
| Language | Türkçe tercih, teknik terimler İngilizce |
| Format | Markdown, consistent headers |
| Numbering | XXX (001, 002...) prefix |
| Status | draft → ready → in-progress → done |

### 12.2 Code Documentation

| Tür | Zorunluluk |
|-----|------------|
| JSDoc on public methods | Zorunlu |
| README per module | Zorunlu |
| Inline comments | Kompleks logic için |
| CHANGELOG | Her release |

---

*Bu döküman, E-Menum projesinin iş ve stratejik bağlamını tanımlar. Tüm spec'ler ve implementasyonlar bu bağlamla tutarlı olmalıdır.*
