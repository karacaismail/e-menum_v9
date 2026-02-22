# E-Menum Reporting Features - Gap Analizi & Gelistirme Plani

> Tarih: 2026-02-22
> Hazirlayan: Claude (Otomatik Analiz)
> Kapsam: 142 planlanan reporting feature vs Django codebase mevcut durum

---

## 1. MEVCUT DJANGO CODEBASE OZETI

### 1.1 Kurulu App'ler (9 adet)

| App | Durum | Model Sayisi | API Endpoint |
|-----|-------|-------------|-------------|
| `apps.core` | Tam | 8 (Organization, User, Branch, Role, Permission, Session, UserRole, AuditLog) | Auth, Org, User CRUD |
| `apps.menu` | Tam | 10 (Theme, Menu, Category, Product, Variant, Modifier, Allergen, ProductAllergen, NutritionInfo, QRCode) | Full CRUD |
| `apps.orders` | Tam | 7 (Zone, Table, QRCode, QRScan, Order, OrderItem, ServiceRequest) | Full CRUD + Workflow |
| `apps.customers` | Tam | 4 (Customer, CustomerVisit, Feedback, LoyaltyPoint) | CRUD + Loyalty |
| `apps.subscriptions` | Tam | 6 (Feature, Plan, PlanFeature, Subscription, Invoice, OrganizationUsage) | Plans, Billing |
| `apps.notifications` | Tam | 1 (Notification) | CRUD + Mark Read |
| `apps.ai` | Tam | 2 (AIGeneration, AIProviderConfig) | Generate, Improve, Suggest |
| `apps.media` | Tam | 2 (MediaFolder, Media) | Upload, CRUD |
| `apps.analytics` | **STUB** | 0 (Sadece yorum) | Yok |

### 1.2 Altyapi Durumu

| Bilesken | Durum | Aciklama |
|----------|-------|----------|
| Multi-tenancy | Var | TenantMiddleware + BaseTenantViewSet |
| RBAC/ABAC | Var | django-guardian + custom abilities |
| Soft Delete | Var | SoftDeleteMixin tum modellerde |
| JWT Auth | Var | simplejwt + Session yonetimi |
| Plan Enforcement | Var | PlanEnforcementMixin |
| Celery (async) | Var | celery[redis] kurulu |
| Redis Cache | Var | django-redis kurulu |
| AI Provider | Var | AIProviderConfig (multi-provider, fallback) |
| Audit Log | Var | AuditLog modeli |

---

## 2. GAP ANALIZI - KATEGORI BAZLI

### Durum Kodlari

- **YOK**: Hicbir implementasyon yok, sifirdan yazilmali
- **ALTYAPI VAR**: Veri modeli mevcut ama raporlama/analitik katmani yok
- **KISMI**: Bazi parcalar var ama reporting ozelligi tamamlanmamis

---

### 2.1 ALTYAPI (INFRA) - Kritik Bagimliliklar

| Feature ID | Feature | Durum | Aciklama |
|-----------|---------|-------|----------|
| INFRA-001 | Reporting DB Schema | **YOK** | analytics app STUB, hicbir model yok |
| INFRA-002 | AI Model Integration Layer | **KISMI** | AIProviderConfig + AIGeneration var ama reporting icin NLQ/insight yok |
| INFRA-003 | Credit System | **KISMI** | OrganizationUsage + credits_used tracking var, reporting credit sistemi yok |
| INFRA-004 | Report Generation Engine | **YOK** | Rapor uretme motoru yok |
| INFRA-005 | Real-time Data Pipeline | **YOK** | Celery var ama streaming/aggregation pipeline yok |

### 2.2 PERIYODIK RAPORLAR (12 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-PER-001 | Gunluk Ozet Raporu | YOK |
| RPT-PER-002 | Sabah Brifingi | YOK |
| RPT-PER-003 | Aksam Ozeti | YOK |
| RPT-PER-004 | Vardiya Ozeti | YOK |
| RPT-PER-005 | Haftalik Trend | YOK |
| RPT-PER-006 | Haftalik Performans Karti | YOK |
| RPT-PER-007 | Haftalik Personel Siralamasi | YOK |
| RPT-PER-008 | Aylik Analiz | YOK |
| RPT-PER-009 | Aylik Yonetici Ozeti | YOK |
| RPT-PER-010 | Ceyreklik Degerlendirme | YOK |
| RPT-PER-011 | Yillik Ozet | YOK |
| RPT-PER-012 | Ozel Donem Raporu | YOK |

**Durum: 0/12 mevcut. Tamamen sifirdan yazilmali.**

### 2.3 SATIS RAPORLARI (14 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-SAL-001 | Ciro Raporu | ALTYAPI VAR (Order modeli var, aggregation yok) |
| RPT-SAL-002 | Satis Dagilim | ALTYAPI VAR |
| RPT-SAL-003 | Satis Karsilastirma | YOK |
| RPT-SAL-004 | Kar Marji | YOK (cost_data modeli yok) |
| RPT-SAL-005 | Odeme Analizi | ALTYAPI VAR (Order.payment_method var) |
| RPT-SAL-006 | Indirim Analizi | YOK (discount modeli yok) |
| RPT-SAL-007 | Saatlik Satis | ALTYAPI VAR |
| RPT-SAL-008 | Gunluk Satis | ALTYAPI VAR |
| RPT-SAL-009 | En Cok Satanlar | ALTYAPI VAR |
| RPT-SAL-010 | En Az Satanlar | ALTYAPI VAR |
| RPT-SAL-011 | Satis Hedef Takip | YOK (hedef modeli yok) |
| RPT-SAL-012 | Satis Kanali | ALTYAPI VAR (Order.channel var) |
| RPT-SAL-013 | KDV Ozet | ALTYAPI VAR |
| RPT-SAL-014 | Nakit Akis | YOK (expense modeli yok) |

**Durum: 0/14 rapor mevcut. 8 tanesinde veri altyapisi var, 6 tanesi icin ek modeller gerekli.**

### 2.4 MENU RAPORLARI (12 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-MNU-001 | Performans Matrisi (BCG) | YOK |
| RPT-MNU-002 | Urun Performans | ALTYAPI VAR |
| RPT-MNU-003 | Kategori Analiz | ALTYAPI VAR |
| RPT-MNU-004 | Fiyat Analiz | YOK |
| RPT-MNU-005 | Populerlik Trend | YOK |
| RPT-MNU-006 | Urun Eslestirme | YOK |
| RPT-MNU-007 | Menu Optimizasyon | YOK |
| RPT-MNU-008 | Menu Muhendisligi | YOK |
| RPT-MNU-009 | Degerlendirme Analizi | KISMI (Feedback modeli var, sentiment yok) |
| RPT-MNU-010 | Maliyet Analizi | YOK (recipe_data yok) |
| RPT-MNU-011 | Modifier Analizi | ALTYAPI VAR |
| RPT-MNU-012 | Menu Uygunluk | YOK |

**Durum: 0/12 rapor mevcut. 3 tanesinde veri altyapisi var.**

### 2.5 SIPARIS RAPORLARI (10 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-ORD-001 | Siparis Analiz | ALTYAPI VAR (Order + OrderItem modelleri tam) |
| RPT-ORD-002 | Siparis Zaman Analizi | ALTYAPI VAR |
| RPT-ORD-003 | Yogun Saat | ALTYAPI VAR |
| RPT-ORD-004 | Siparis Kanal Analizi | ALTYAPI VAR |
| RPT-ORD-005 | Siparis Iptal | ALTYAPI VAR (status workflow var) |
| RPT-ORD-006 | Siparis Degisiklik | YOK |
| RPT-ORD-007 | Void/Refund | YOK (refund modeli yok) |
| RPT-ORD-008 | Siparis Karsilama | ALTYAPI VAR |
| RPT-ORD-009 | Ozel Istek | ALTYAPI VAR (ServiceRequest modeli var) |
| RPT-ORD-010 | Sepet Analizi | ALTYAPI VAR |

**Durum: 0/10 rapor mevcut. 8 tanesinde veri altyapisi var.**

### 2.6 MUSTERI RAPORLARI (12 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-CUS-001 | Musteri Genel Bakis | ALTYAPI VAR (Customer + CustomerVisit) |
| RPT-CUS-002 | Segmentasyon (RFM) | YOK (ML pipeline yok) |
| RPT-CUS-003 | CLV | YOK (ML pipeline yok) |
| RPT-CUS-004 | Tutundurma | ALTYAPI VAR |
| RPT-CUS-005 | Churn Risk | YOK (ML pipeline yok) |
| RPT-CUS-006 | Geri Bildirim | ALTYAPI VAR (Feedback modeli var) |
| RPT-CUS-007 | Musteri Yolculugu | YOK |
| RPT-CUS-008 | Musteri Kazanim | ALTYAPI VAR |
| RPT-CUS-009 | Ziyaret Sikligi | ALTYAPI VAR (CustomerVisit var) |
| RPT-CUS-010 | Tercihleri | YOK |
| RPT-CUS-011 | Bireysel Profil | ALTYAPI VAR |
| RPT-CUS-012 | NPS Analiz | YOK (NPS modeli yok) |

**Durum: 0/12 rapor mevcut. 6 tanesinde veri altyapisi var, ML pipeline tamamen yok.**

### 2.7 PERSONEL RAPORLARI (10 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-STF-001 | Personel Genel Bakis | KISMI (User modeli var, performans metrikleri yok) |
| RPT-STF-002 | Performans Karti | YOK |
| RPT-STF-003 | Verimlilik | YOK |
| RPT-STF-004 | Vardiya Analiz | YOK (shift modeli yok) |
| RPT-STF-005 | Siralamaasi | YOK |
| RPT-STF-006 | Egitim Ihtiyac | YOK |
| RPT-STF-007 | Devam Raporu | YOK (attendance modeli yok) |
| RPT-STF-008 | Isgcu Maliyet | YOK |
| RPT-STF-009 | Kisisel Dashboard | YOK |
| RPT-STF-010 | Bahsis Raporu | YOK (tips modeli yok) |

**Durum: 0/10 rapor mevcut. Neredeyse tamamen sifirdan, cok sayida ek model gerekli.**

### 2.8 ENVANTER RAPORLARI (8 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-INV-001 | Stok Durum | YOK (inventory modeli yok) |
| RPT-INV-002 | Stok Tahmin | YOK |
| RPT-INV-003 | Fire/Kayip | YOK |
| RPT-INV-004 | Stok Devir Hizi | YOK |
| RPT-INV-005 | Malzeme Maliyet | YOK |
| RPT-INV-006 | Tedarikci Performans | YOK |
| RPT-INV-007 | Satin Alma Gecmisi | YOK |
| RPT-INV-008 | Son Kullanma Tarihi | YOK |

**Durum: 0/8. Inventory modulu tamamen yok. Tum modeller + raporlar sifirdan.**

### 2.9 KAMPANYA RAPORLARI (8 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-CMP-001 | Kampanya Genel Bakis | YOK (campaign modeli yok) |
| RPT-CMP-002 | Kampanya ROI | YOK |
| RPT-CMP-003 | Kampanya Karsilastirma | YOK |
| RPT-CMP-004 | Attribution | YOK |
| RPT-CMP-005 | Sadakat Ozeti | ALTYAPI VAR (LoyaltyPoint var) |
| RPT-CMP-006 | Uye Analiz | ALTYAPI VAR |
| RPT-CMP-007 | Kupon Analiz | YOK (coupon modeli yok) |
| RPT-CMP-008 | Referans Program | YOK (referral modeli yok) |

**Durum: 0/8 rapor mevcut. Campaign modulu yok, sadece loyalty altyapisi var.**

### 2.10 OPERASYON RAPORLARI (10 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-OPR-001 | Masa Kullanim | ALTYAPI VAR (Table + Zone modelleri var) |
| RPT-OPR-002 | Masa Devir Hizi | ALTYAPI VAR |
| RPT-OPR-003 | Mutfak Performans | YOK |
| RPT-OPR-004 | Servis Sure | ALTYAPI VAR (OrderItem status workflow var) |
| RPT-OPR-005 | Bekleme Suresi | YOK |
| RPT-OPR-006 | Rezervasyon Analizi | YOK (reservation modeli yok) |
| RPT-OPR-007 | Teslimat Performans | YOK |
| RPT-OPR-008 | Paket Servis Analizi | YOK |
| RPT-OPR-009 | Operasyonel Sorun | ALTYAPI VAR (ServiceRequest var) |
| RPT-OPR-010 | Ekipman Durum | YOK (equipment modeli yok) |

**Durum: 0/10 rapor mevcut. 4 tanesinde veri altyapisi var.**

### 2.11 DIJITAL RAPORLAR (6 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-DIG-001 | QR Tarama Analizi | ALTYAPI VAR (QRScan modeli var) |
| RPT-DIG-002 | Menu Goruntuleme | YOK |
| RPT-DIG-003 | Dijital Etkilesim | YOK |
| RPT-DIG-004 | Web Sitesi Analitigi | YOK |
| RPT-DIG-005 | Siparis Donusum Hunisi | YOK |
| RPT-DIG-006 | Dijital Odeme | YOK |

**Durum: 0/6 rapor mevcut. Sadece QRScan verisi mevcut.**

### 2.12 SUBE RAPORLARI (8 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-BRN-001 | Sube Karsilastirma | ALTYAPI VAR (Branch modeli var) |
| RPT-BRN-002 | Sube Siralamasi | ALTYAPI VAR |
| RPT-BRN-003 | Konsolide Rapor | YOK |
| RPT-BRN-004 | Best Practice | YOK |
| RPT-BRN-005 | Tekil Sube Raporu | ALTYAPI VAR |
| RPT-BRN-006 | Cografi Analiz | YOK |
| RPT-BRN-007 | Standart Uyumluluk | YOK |
| RPT-BRN-008 | Franchise Performans | YOK |

**Durum: 0/8 rapor mevcut. Branch modeli var ama raporlama katmani yok.**

### 2.13 AI SORGU (10 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-AIQ-001 | Temel NL Sorgu | YOK |
| RPT-AIQ-002 | Karsilastirmali Sorgu | YOK |
| RPT-AIQ-003 | Analitik Sorgu | YOK |
| RPT-AIQ-004 | Oneri Sorgusu | YOK |
| RPT-AIQ-005 | Kompleks Sorgu | YOK |
| RPT-AIQ-006 | Trend Sorgusu | YOK |
| RPT-AIQ-007 | Anomali Sorgusu | YOK |
| RPT-AIQ-008 | Ozet Sorgusu | YOK |
| RPT-AIQ-009 | Konusmaya Dayali | YOK |
| RPT-AIQ-010 | Sesli Sorgu | YOK |

**Durum: 0/10. AI content generation var ama NLQ (Natural Language Query) tamamen yok.**

### 2.14 AI ICGORULER (8 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-AII-001 | Otomatik Icgoruler | YOK |
| RPT-AII-002 | Anomali Tespiti | YOK |
| RPT-AII-003 | Trend Tespiti | YOK |
| RPT-AII-004 | Aksiyon Onerileri | YOK |
| RPT-AII-005 | Akilli Uyarilar | YOK |
| RPT-AII-006 | Firsat Bulucu | YOK |
| RPT-AII-007 | Rekabet Istihbarati | YOK |
| RPT-AII-008 | Sektor Benchmark | YOK |

**Durum: 0/8. Tamamen sifirdan.**

### 2.15 TAHMINLEME (8 feature)

| Feature ID | Feature | Durum |
|-----------|---------|-------|
| RPT-FOR-001 | Kisa Vade Tahmin (7g) | YOK |
| RPT-FOR-002 | Orta Vade Tahmin (30g) | YOK |
| RPT-FOR-003 | Uzun Vade Tahmin (90g) | YOK |
| RPT-FOR-004 | Gelir Tahmini | YOK |
| RPT-FOR-005 | Stok Tahmini | YOK |
| RPT-FOR-006 | Personel Ihtiyac | YOK |
| RPT-FOR-007 | Musteri Kaybi Tahmini | YOK |
| RPT-FOR-008 | Mevsimsel Tahmin | YOK |

**Durum: 0/8. Prophet/ML pipeline tamamen yok.**

### 2.16 WHAT-IF ANALIZ (6 feature)

Tumu **YOK**. ML simulation altyapisi gerekli.

### 2.17 PLATFORM RAPORLARI (16 feature)

Tumu **YOK**. Super admin dashboard yok.

### 2.18 EXPORT / DASHBOARD / SCHEDULING

Tumu **YOK**. PDF/Excel export, dashboard widget, scheduling sistemi yok.

---

## 3. OZET TABLO

| Kategori | Toplam | Var | Altyapi Var | Yok | Oran |
|----------|--------|-----|-------------|-----|------|
| Altyapi (INFRA) | 5 | 0 | 2 | 3 | %0 |
| Periyodik Raporlar | 12 | 0 | 0 | 12 | %0 |
| Satis Raporlari | 14 | 0 | 8 | 6 | %0 |
| Menu Raporlari | 12 | 0 | 3 | 9 | %0 |
| Siparis Raporlari | 10 | 0 | 8 | 2 | %0 |
| Musteri Raporlari | 12 | 0 | 6 | 6 | %0 |
| Personel Raporlari | 10 | 0 | 0 | 10 | %0 |
| Envanter Raporlari | 8 | 0 | 0 | 8 | %0 |
| Kampanya Raporlari | 8 | 0 | 2 | 6 | %0 |
| Operasyon Raporlari | 10 | 0 | 4 | 6 | %0 |
| Dijital Raporlar | 6 | 0 | 1 | 5 | %0 |
| Sube Raporlari | 8 | 0 | 3 | 5 | %0 |
| AI Sorgu | 10 | 0 | 0 | 10 | %0 |
| AI Icgoruler | 8 | 0 | 0 | 8 | %0 |
| Tahminleme | 8 | 0 | 0 | 8 | %0 |
| What-If | 6 | 0 | 0 | 6 | %0 |
| Platform | 16 | 0 | 0 | 16 | %0 |
| Export/Dashboard | 7 | 0 | 0 | 7 | %0 |
| **TOPLAM** | **170** | **0** | **37** | **133** | **%0** |

**Sonuc: 142 reporting feature'dan HICBIRI implement edilmemis. analytics app tamamen STUB.**

---

## 4. GELISTIRME PLANI

### 4.1 Oncelik: Eksik Veri Modelleri

Raporlama baslamadan once su modullerin veri modelleri olusturulmali:

**Yeni Django App'ler (olusturulmali):**

1. `apps.inventory` - Stok, malzeme, tedarikci, satin alma
2. `apps.campaigns` - Kampanya, kupon, referral
3. `apps.reporting` - Report engine, scheduled reports, export

**Mevcut App'lere Eklenecek Modeller:**

- `apps.orders`: Discount, Refund, Reservation modelleri
- `apps.core`: Shift, Attendance, StaffMetric modelleri
- `apps.customers`: NPS, CustomerPreference modelleri
- `apps.analytics`: DashboardMetric, ReportCache, Aggregation modelleri

### 4.2 Faz 1 - Altyapi & MVP (Ay 1-3, ~180 gun-efor)

**Sprint 1-2: Reporting Altyapisi**
- `apps.analytics` modellerini implement et (DashboardMetric, SalesAggregation, ProductPerformance)
- Report Generation Engine (Celery task-based)
- Pre-aggregation pipeline (gunluk/haftalik/aylik)
- Credit consumption tracking for reports

**Sprint 3-4: Temel Raporlar (P0)**
- RPT-SAL-001: Ciro Raporu (Order aggregation var, view/serializer yazilmali)
- RPT-SAL-009: En Cok Satanlar (OrderItem aggregation)
- RPT-ORD-001: Siparis Analiz (Order status distribution)
- RPT-CUS-001: Musteri Genel Bakis (Customer + Visit aggregation)
- RPT-DIG-001: QR Tarama (QRScan aggregation)

**Sprint 5-6: AI Query Temeli + Periyodik Raporlar**
- AI NLQ Engine (Claude/GPT entegrasyonu ile sorgu yorumlama)
- RPT-PER-001: Gunluk Ozet (Celery periodic task)
- RPT-PER-005: Haftalik Trend
- RPT-MNU-001: Menu Performans Matrisi (BCG)

### 4.3 Faz 2 - Buyume (Ay 4-6, ~220 gun-efor)

- Forecasting engine (Prophet/XGBoost)
- Gelismis AI sorgu tipleri (karsilastirma, analitik, oneri)
- Musteri segmentasyonu (RFM)
- Staff performance tracking (yeni modeller)
- PDF/Excel export
- Real-time dashboard (WebSocket)

### 4.4 Faz 3 - Enterprise (Ay 7-10, ~280 gun-efor)

- ML pipeline (CLV, Churn prediction)
- What-if analiz motoru
- Inventory modulu (tamamen yeni)
- Campaign modulu (tamamen yeni)
- Branch karsilastirma raporlari
- Custom dashboard builder

### 4.5 Faz 4 - Inovasyon (Ay 11+, ~165 gun-efor)

- Sesli sorgu
- Conversational analytics
- Competitive intelligence
- BI tool entegrasyonu
- Expansion what-if

---

## 5. TEKNIK MIMARI ONERILERI

### 5.1 apps.reporting Yapisii

```
apps/reporting/
    models/
        report_definition.py    # Rapor tanimlari (feature catalog)
        report_execution.py     # Rapor calisma gecmisi
        report_schedule.py      # Zamanlanmis raporlar
        aggregation.py          # Pre-computed aggregation'lar
    services/
        report_engine.py        # Ana rapor uretim motoru
        aggregation_service.py  # Veri toplama/onisleme
        export_service.py       # PDF/Excel/CSV export
        scheduler_service.py    # Celery periodic task yonetimi
    ai/
        nlq_service.py          # Natural Language Query
        insight_service.py      # Otomatik icgoru uretimi
        forecast_service.py     # Prophet/ML tahminleme
    views/
        report_views.py         # REST API endpoints
        dashboard_views.py      # Dashboard widget API
        ai_query_views.py       # NLQ API
    serializers/
    urls.py
    tasks.py                    # Celery tasks
    manifest.json
```

### 5.2 Aggregation Stratejisi

Pre-computed aggregation tablolari:

- `daily_sales_summary` - Gunluk satis ozeti (cron: her gece)
- `hourly_metrics` - Saatlik metrikler (cron: her saat)
- `product_performance` - Urun performans snapshot (cron: gunluk)
- `customer_metrics` - Musteri metrikleri (cron: gunluk)

### 5.3 AI Integration

- NLQ: Kullanici sorusu -> LLM -> SQL/ORM query -> Sonuc -> LLM -> Rapor
- Insights: Aggregated data -> LLM -> Anomali/Trend/Oneri
- Forecast: Historical data -> Prophet/XGBoost -> Prediction -> LLM -> Yorum

---

## 6. KRITIK BAGIMLILIKLAR

```
INFRA-001 (DB Schema) -> Tum raporlar
INFRA-002 (AI Layer) -> Tum AI ozellikler
INFRA-004 (Report Engine) -> Tum rapor uretimi
Order + OrderItem modelleri -> Satis/Siparis raporlari (MEVCUT)
Customer + Visit modelleri -> Musteri raporlari (MEVCUT)
QRScan modeli -> Dijital raporlar (MEVCUT)
Inventory modulu -> Envanter raporlari (YOK - OLUSTURULMALI)
Campaign modulu -> Kampanya raporlari (YOK - OLUSTURULMALI)
Shift/Attendance -> Personel raporlari (YOK - OLUSTURULMALI)
```

---

## 7. TAHMINI EFOR

| Faz | Sure | Gun-Efor | Gerekli Takim |
|-----|------|----------|---------------|
| Faz 1 (MVP) | 3 ay | 180 | 2 Backend + 1 AI + 1 Frontend |
| Faz 2 (Growth) | 3 ay | 220 | 2 Backend + 2 AI + 1 Data Sci + 2 Frontend |
| Faz 3 (Enterprise) | 4 ay | 280 | 2 Backend + 2 AI + 1 Data Sci + 2 Frontend |
| Faz 4 (Innovation) | 3+ ay | 165 | TBD |
| **Toplam** | **~14 ay** | **845 gun** | |

---

*Bu analiz, Django codebase'in mevcut durumuna dayanmaktadir. Reporting feature'larin %0'i implement edilmis, ancak siparis, musteri, menu gibi core modullerin veri altyapisi mevcuttur.*
