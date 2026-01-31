# E-Menum Glossary

> **Auto-Claude Domain Glossary**  
> İş terminolojisi, teknik terimler, sektör kavramları.  
> Son Güncelleme: 2026-01-31

---

## 1. PLATFORM TERİMLERİ

### 1.1 Temel Kavramlar

| Terim | Türkçe | Tanım |
|-------|--------|-------|
| **Tenant** | Kiracı | Platformu kullanan tek bir organizasyon/işletme. Multi-tenant mimaride her müşteri bir tenant'tır. |
| **Organization** | Organizasyon | E-Menum'da bir işletmeyi temsil eden ana varlık. Tüm veriler organization altında izole edilir. |
| **Branch** | Şube | Bir organizasyonun fiziksel lokasyonu. Ana merkez + şubeler şeklinde yapılanır. |
| **Workspace** | Çalışma Alanı | Kullanıcının aktif olarak çalıştığı organization bağlamı. |
| **Module** | Modül | Bağımsız çalışabilen, açılıp kapatılabilen özellik paketi. |
| **Feature** | Özellik | Bir modül içindeki spesifik işlevsellik. |
| **Plan** | Plan | Abonelik paketi (Free, Starter, Professional, Business, Enterprise). |
| **Subscription** | Abonelik | Organizasyonun aktif plan durumu ve ödeme bilgileri. |

### 1.2 Kullanıcı & Yetki Terimleri

| Terim | Türkçe | Tanım |
|-------|--------|-------|
| **Role** | Rol | Kullanıcıya atanan yetki grubu (owner, manager, staff vb.). |
| **Permission** | İzin | Spesifik bir eylem için yetki (menu.create, orders.view vb.). |
| **RBAC** | Rol Tabanlı Erişim | Role-Based Access Control. Rollere dayalı yetkilendirme. |
| **ABAC** | Öznitelik Tabanlı Erişim | Attribute-Based Access Control. Dinamik koşullara dayalı yetkilendirme. |
| **Impersonation** | Kimliğe Bürünme | Admin'in kullanıcı olarak sisteme girmesi (destek amaçlı). |
| **Invitation** | Davet | Yeni kullanıcıyı organizasyona ekleme süreci. |

### 1.3 Menü Terimleri

| Terim | Türkçe | Tanım |
|-------|--------|-------|
| **Menu** | Menü | Yayınlanabilir ürün kataloğu. Bir organizasyonun birden fazla menüsü olabilir. |
| **Category** | Kategori | Menü içindeki ürün grubu (Başlangıçlar, Ana Yemekler vb.). |
| **Product** | Ürün | Satışa sunulan tek bir yiyecek/içecek kalemi. |
| **Variant** | Varyant | Ürünün farklı versiyonu (Küçük/Orta/Büyük boy gibi). |
| **Modifier** | Ek Seçenek | Ürüne eklenebilir opsiyon (Ekstra peynir, Acılı vb.). |
| **Modifier Group** | Seçenek Grubu | İlişkili modifier'ların grubu (Soslar, Ekstralar vb.). |
| **Allergen** | Alerjen | Alerjik reaksiyona sebep olabilecek madde (Gluten, Fıstık vb.). |
| **Nutrition Info** | Besin Değeri | Kalori, protein, karbonhidrat vb. bilgiler. |
| **Theme** | Tema | Menünün görsel tasarım şablonu. |
| **Slug** | URL Kısa Adı | URL-dostu benzersiz tanımlayıcı (ana-menu, yaz-menusu). |

### 1.4 Sipariş Terimleri

| Terim | Türkçe | Tanım |
|-------|--------|-------|
| **Order** | Sipariş | Müşterinin verdiği ürün talebi. |
| **Order Item** | Sipariş Kalemi | Siparişin içindeki tek bir ürün satırı. |
| **Cart** | Sepet | Sipariş verilmeden önceki geçici ürün listesi. |
| **Table** | Masa | Fiziksel oturma birimi. |
| **Zone** | Bölge | Masa gruplarını içeren alan (İç Salon, Bahçe vb.). |
| **Service Request** | Servis Talebi | Garson çağırma, hesap isteme gibi talepler. |
| **Kitchen Display** | Mutfak Ekranı | Siparişlerin mutfakta görüntülendiği sistem. |
| **Waiter App** | Garson Uygulaması | Personelin sipariş yönetimi için kullandığı arayüz. |

### 1.5 QR & Dijital Terimleri

| Terim | Türkçe | Tanım |
|-------|--------|-------|
| **QR Code** | QR Kod | Menüye erişim sağlayan kare barkod. |
| **QR Scan** | QR Tarama | Müşterinin QR kodu okuması eylemi. |
| **Public Menu** | Herkese Açık Menü | Giriş yapmadan görüntülenebilen menü. |
| **Session** | Oturum | Müşterinin menüdeki aktif ziyareti. |
| **Conversion** | Dönüşüm | QR taramadan siparişe geçiş. |

---

## 2. TEKNİK TERİMLER

### 2.1 Mimari Terimler

| Terim | Tanım |
|-------|-------|
| **Multi-Tenant** | Tek uygulama, çoklu müşteri mimarisi. Veriler organizationId ile izole edilir. |
| **SSR** | Server-Side Rendering. Sayfanın sunucuda oluşturulması. |
| **SPA** | Single Page Application. Tek sayfa uygulama (E-Menum'da kullanılmıyor). |
| **MPA** | Multi Page Application. Geleneksel çoklu sayfa yapısı. |
| **API** | Application Programming Interface. Programatik erişim arayüzü. |
| **REST** | Representational State Transfer. API tasarım prensibi. |
| **JWT** | JSON Web Token. Kimlik doğrulama token formatı. |
| **Middleware** | Ara Katman. Request/response işleme zincirindeki fonksiyon. |
| **ORM** | Object-Relational Mapping. Veritabanı soyutlama katmanı (Prisma). |

### 2.2 Veritabanı Terimleri

| Terim | Tanım |
|-------|-------|
| **Schema** | Veritabanı yapı tanımı. |
| **Migration** | Şema değişikliği betiği. |
| **Soft Delete** | Silme işaretleme (deletedAt). Veri silinmez, işaretlenir. |
| **Hard Delete** | Kalıcı silme. Veri tamamen kaldırılır. |
| **FK** | Foreign Key. Tablolar arası ilişki anahtarı. |
| **Index** | Sorgu performansı için veri indeksi. |
| **CUID** | Collision-resistant Unique ID. Benzersiz ID formatı. |
| **Cascade** | İlişkili kayıtların otomatik güncellenmesi/silinmesi. |

### 2.3 Frontend Terimleri

| Terim | Tanım |
|-------|-------|
| **Component** | Yeniden kullanılabilir UI birimi. |
| **Template** | EJS şablon dosyası. |
| **Partial** | Alt şablon, include edilebilir parça. |
| **Layout** | Sayfa iskelet şablonu. |
| **Slot** | Layout içinde içerik yerleştirme alanı. |
| **CSS Variable** | CSS Custom Property. Dinamik stil değişkeni. |
| **Design Token** | Tasarım sistemi değeri (renk, spacing vb.). |
| **Breakpoint** | Responsive tasarım kırılım noktası. |
| **Utility Class** | Tek amaçlı CSS sınıfı (Tailwind yaklaşımı). |

### 2.4 Güvenlik Terimleri

| Terim | Tanım |
|-------|-------|
| **Authentication** | Kimlik Doğrulama. Kim olduğunu kanıtlama. |
| **Authorization** | Yetkilendirme. Ne yapabileceğini belirleme. |
| **HSTS** | HTTP Strict Transport Security. Zorunlu HTTPS. |
| **CSRF** | Cross-Site Request Forgery. Siteler arası istek sahteciliği. |
| **XSS** | Cross-Site Scripting. Zararlı script enjeksiyonu. |
| **Rate Limiting** | İstek sayısı sınırlama. |
| **Brute Force** | Deneme yanılma saldırısı. |
| **Salt** | Şifre hashleme için rastgele ek. |
| **Hash** | Tek yönlü şifreleme (bcrypt). |

---

## 3. İŞ TERİMLERİ

### 3.1 Finans & Abonelik

| Terim | Türkçe | Tanım |
|-------|--------|-------|
| **MRR** | Aylık Tekrar Eden Gelir | Monthly Recurring Revenue. Aboneliklerden aylık gelir. |
| **ARR** | Yıllık Tekrar Eden Gelir | Annual Recurring Revenue. MRR × 12. |
| **LTV** | Müşteri Yaşam Boyu Değeri | Lifetime Value. Müşterinin toplam getirisi. |
| **CAC** | Müşteri Edinme Maliyeti | Customer Acquisition Cost. Bir müşteri kazanma maliyeti. |
| **Churn** | Kayıp Oranı | Abonelik iptali oranı. |
| **ARPU** | Kullanıcı Başı Gelir | Average Revenue Per User. |
| **Upgrade** | Yükseltme | Üst plana geçiş. |
| **Downgrade** | Düşürme | Alt plana geçiş. |
| **Proration** | Orantılı Hesaplama | Dönem ortası plan değişikliği faturalaması. |
| **Dunning** | Ödeme Takibi | Başarısız ödeme takip süreci. |
| **Grace Period** | Ek Süre | Ödeme için tanınan tolerans süresi. |

### 3.2 Metrikler & Analitik

| Terim | Türkçe | Tanım |
|-------|--------|-------|
| **Conversion Rate** | Dönüşüm Oranı | Ziyaretçinin müşteriye dönüşme yüzdesi. |
| **Bounce Rate** | Hemen Çıkış Oranı | Tek sayfa görüntüleyip çıkma oranı. |
| **Session Duration** | Oturum Süresi | Kullanıcının sitede geçirdiği süre. |
| **DAU** | Günlük Aktif Kullanıcı | Daily Active Users. |
| **MAU** | Aylık Aktif Kullanıcı | Monthly Active Users. |
| **NPS** | Net Tavsiye Skoru | Net Promoter Score. Müşteri memnuniyeti ölçütü. |
| **PMF** | Ürün-Pazar Uyumu | Product-Market Fit. |
| **KPI** | Anahtar Performans Göstergesi | Key Performance Indicator. |
| **OKR** | Hedef ve Sonuçlar | Objectives and Key Results. |

### 3.3 AI & Otomasyon

| Terim | Türkçe | Tanım |
|-------|--------|-------|
| **AI Credit** | AI Kredisi | AI özelliklerini kullanmak için gereken birim. |
| **Token** | Jeton | AI modellerinin metin işleme birimi. |
| **Prompt** | İstem | AI'ya verilen talimat/soru. |
| **Generation** | Üretim | AI'nın içerik oluşturması. |
| **Completion** | Tamamlama | AI'nın metin tamamlaması. |
| **Embedding** | Gömme | Metin'in vektör temsiline dönüştürülmesi. |
| **Fine-tuning** | İnce Ayar | Model'in özel veriyle eğitilmesi. |
| **RAG** | Retrieval-Augmented Generation. Bilgi getirme destekli üretim. |
| **Hallucination** | Halüsinasyon | AI'nın gerçek dışı bilgi üretmesi. |

---

## 4. SEKTÖR TERİMLERİ

### 4.1 Restoran & Cafe

| Terim | Türkçe | Açıklama |
|-------|--------|----------|
| **F&B** | Yiyecek & İçecek | Food & Beverage sektörü. |
| **PoS** | Satış Noktası | Point of Sale. Kasa/ödeme sistemi. |
| **Cover** | Kuvert | Bir masadaki misafir sayısı. |
| **Turn** | Devir | Bir masanın tekrar dolu olma sıklığı. |
| **Ticket** | Fiş/Adisyon | Sipariş fişi. |
| **Check** | Hesap | Müşteriye sunulan toplam tutar. |
| **Comp** | İkram | Ücretsiz verilen ürün. |
| **86** | Tükendi | Mutfak jargonunda "ürün bitti" anlamı. |
| **Mise en Place** | Hazırlık | Servis öncesi hazırlık. |
| **BOH** | Arka Alan | Back of House. Mutfak, depo vb. |
| **FOH** | Ön Alan | Front of House. Servis alanı. |

### 4.2 Türk Mutfağı Spesifik

| Terim | Açıklama |
|-------|----------|
| **Porsiyon** | Standart servis miktarı. |
| **Yarım Porsiyon** | Standartın yarısı miktar. |
| **Kumanya** | Paket servis. |
| **Gel-Al** | Take-away. Paket alım. |
| **Self Servis** | Müşterinin kendine servis yapması. |
| **Açık Büfe** | Sınırsız seçim imkanı. |
| **Fix Menü** | Sabit içerikli set menü. |
| **Alakart** | Tek tek seçim yapılan menü. |
| **Dürüm** | Lavaşa sarılı servis. |
| **Pide** | Kapalı/açık hamur servis. |
| **Lahmacun** | İnce hamur servis. |
| **Kahvaltı Tabağı** | Kahvaltı seti. |
| **Serpme Kahvaltı** | Zengin kahvaltı servisi. |

---

## 5. KISALTMALAR

### 5.1 Teknik Kısaltmalar

| Kısaltma | Açılım | Anlamı |
|----------|--------|--------|
| **API** | Application Programming Interface | Programatik arayüz |
| **JWT** | JSON Web Token | Kimlik token'ı |
| **CRUD** | Create, Read, Update, Delete | Temel veri işlemleri |
| **REST** | Representational State Transfer | API mimarisi |
| **ORM** | Object-Relational Mapping | Veritabanı soyutlaması |
| **SSR** | Server-Side Rendering | Sunucu taraflı render |
| **CDN** | Content Delivery Network | İçerik dağıtım ağı |
| **SSL/TLS** | Secure Sockets Layer / Transport Layer Security | Şifreli bağlantı |
| **DNS** | Domain Name System | Alan adı sistemi |
| **CORS** | Cross-Origin Resource Sharing | Çapraz kaynak paylaşımı |

### 5.2 İş Kısaltmaları

| Kısaltma | Açılım | Anlamı |
|----------|--------|--------|
| **SaaS** | Software as a Service | Hizmet olarak yazılım |
| **B2B** | Business to Business | İşletmeden işletmeye |
| **B2C** | Business to Consumer | İşletmeden tüketiciye |
| **GTM** | Go-to-Market | Pazara giriş stratejisi |
| **TAM** | Total Addressable Market | Toplam erişilebilir pazar |
| **SAM** | Serviceable Addressable Market | Hizmet verilebilir pazar |
| **SOM** | Serviceable Obtainable Market | Elde edilebilir pazar |
| **ROI** | Return on Investment | Yatırım getirisi |
| **MVP** | Minimum Viable Product | Minimum uygulanabilir ürün |
| **PMF** | Product-Market Fit | Ürün-pazar uyumu |

### 5.3 E-Menum Spesifik

| Kısaltma | Açılım | Anlamı |
|----------|--------|--------|
| **QR** | Quick Response | Hızlı yanıt kodu |
| **KDS** | Kitchen Display System | Mutfak ekran sistemi |
| **OMS** | Order Management System | Sipariş yönetim sistemi |
| **CRM** | Customer Relationship Management | Müşteri ilişkileri yönetimi |
| **AI** | Artificial Intelligence | Yapay zeka |
| **ML** | Machine Learning | Makine öğrenmesi |
| **NLQ** | Natural Language Query | Doğal dil sorgusu |

---

## 6. DURUM & ENUM DEĞERLERİ

### 6.1 Organization Status

| Değer | Türkçe | Açıklama |
|-------|--------|----------|
| `active` | Aktif | Normal çalışma durumu |
| `suspended` | Askıya Alınmış | Geçici erişim engeli |
| `pending` | Beklemede | Onay bekleniyor |
| `deleted` | Silindi | Soft delete durumu |

### 6.2 User Status

| Değer | Türkçe | Açıklama |
|-------|--------|----------|
| `active` | Aktif | Giriş yapabilir |
| `pending` | Davet Bekliyor | Davet kabul edilmedi |
| `inactive` | Pasif | Devre dışı bırakıldı |

### 6.3 Order Status

| Değer | Türkçe | Açıklama |
|-------|--------|----------|
| `pending` | Beklemede | Onay bekleniyor |
| `confirmed` | Onaylandı | İşletme kabul etti |
| `preparing` | Hazırlanıyor | Mutfakta hazırlanıyor |
| `ready` | Hazır | Servis için hazır |
| `delivered` | Teslim Edildi | Müşteriye verildi |
| `completed` | Tamamlandı | İşlem sonlandı |
| `cancelled` | İptal | Sipariş iptal edildi |

### 6.4 Subscription Status

| Değer | Türkçe | Açıklama |
|-------|--------|----------|
| `trialing` | Deneme | Ücretsiz deneme süreci |
| `active` | Aktif | Ödeme yapılıyor |
| `past_due` | Gecikmiş | Ödeme başarısız |
| `cancelled` | İptal Edildi | Kullanıcı iptal etti |
| `expired` | Süresi Doldu | Abonelik sona erdi |
| `suspended` | Askıda | Admin müdahalesi |

---

## 7. KULLANIM REHBERİ

### 7.1 Dökümanlarda Tutarlılık

```
TERİM KULLANIM KURALLARI:

1. Teknik dökümanlarda İngilizce terimler tercih edilir
   Örnek: "Organization" (not "Organizasyon")

2. Kullanıcı arayüzünde Türkçe kullanılır
   Örnek: "Menü Yönetimi" (not "Menu Management")

3. Kod içinde İngilizce kullanılır
   Örnek: organizationId, createMenu()

4. Hata mesajlarında Türkçe kullanılır
   Örnek: "Menü bulunamadı"

5. Kısaltmalar ilk kullanımda açılır
   Örnek: "QR (Quick Response) kodu..."
```

### 7.2 Yeni Terim Ekleme

```
YENİ TERİM EKLENİRKEN:

1. Var olan terimleri kontrol et
2. Tutarlı kategori altına ekle
3. Türkçe karşılık belirt
4. Net ve kısa tanım yaz
5. Gerekirse örnek ver
6. İlgili diğer terimlere referans ver
```

---

*Bu sözlük, E-Menum ekosistemindeki tüm terimlerin referansıdır. Yeni terimler eklendikçe güncellenir.*
