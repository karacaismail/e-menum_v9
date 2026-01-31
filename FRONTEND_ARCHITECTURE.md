# E-Menum Frontend Architecture

> **Auto-Claude Frontend Architecture Document**  
> CSS/JS yaklaşımları, framework kararları, library seçimleri, performans stratejisi.  
> Son Güncelleme: 2026-01-31

---

## 1. MİMARİ GENEL BAKIŞ

### 1.1 Frontend Felsefesi

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND FELSEFESİ                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRENSİP: Server-First, Progressive Enhancement                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  1. HTML İLK                                                         │ │
│  │     Server-rendered HTML (EJS templates)                             │ │
│  │     JavaScript olmadan da çalışmalı (core functionality)             │ │
│  │                                                                       │ │
│  │  2. CSS İKİNCİ                                                       │ │
│  │     Styling tamamen CSS ile                                          │ │
│  │     CSS-only interaktiflik mümkünse (hover, :checked, details)       │ │
│  │                                                                       │ │
│  │  3. JS SON                                                           │ │
│  │     Enhancement için, dependency değil                               │ │
│  │     Minimal, focused, purpose-driven                                 │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  NEDEN BU YAKLAŞIM:                                                         │
│  ├── Erişilebilirlik: Screen reader'lar HTML'i okur                        │
│  ├── Performans: İlk yükleme hızlı (no JS bundle wait)                     │
│  ├── SEO: Server-rendered content indekslenebilir                          │
│  ├── Güvenilirlik: JS hata verse de temel işlev çalışır                   │
│  ├── Mobil: Düşük bant genişliğinde bile çalışır                          │
│  └── Bakım: Daha az karmaşıklık, daha az hata                             │
│                                                                             │
│  BU YAKLAŞIM NE DEĞİL:                                                      │
│  ├── SPA (Single Page Application) değil                                   │
│  ├── React/Vue/Angular kullanmıyoruz (admin panel hariç potansiyel)       │
│  ├── Client-side routing yok                                               │
│  └── Heavy JavaScript framework yok                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Teknoloji Stack Özeti

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND STACK                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KATMAN            │ TEKNOLOJİ           │ AMAÇ                            │
│  ──────────────────────────────────────────────────────────────────────────│
│  Templating        │ EJS                 │ Server-side HTML rendering      │
│  CSS Framework     │ Tailwind CSS 3.x    │ Utility-first styling           │
│  CSS Variables     │ Native CSS          │ Theming, runtime customization  │
│  JS Enhancement    │ Alpine.js 3.x       │ Declarative interactivity       │
│  AJAX/Partial      │ HTMX (opsiyonel)    │ HTML-over-the-wire              │
│  Icons             │ Phosphor Icons      │ Consistent iconography          │
│  Icons (Fallback)  │ Font Awesome Free   │ Brand icons, fallback           │
│  Fonts             │ Google Fonts CDN    │ Typography (Inter, etc.)        │
│  Build Tool        │ Vite                │ Dev server, production build    │
│  CSS Processing    │ PostCSS             │ Tailwind, autoprefixer          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. CSS MİMARİSİ

### 2.1 Tailwind CSS Yaklaşımı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TAILWIND CSS KULLANIM REHBERİ                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NEDEN TAILWIND:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ├── Utility-first: Hızlı prototipleme ve geliştirme                │ │
│  │  ├── Tutarlılık: Spacing, color, typography scale sabit             │ │
│  │  ├── Purging: Kullanılmayan CSS otomatik temizlenir                 │ │
│  │  ├── Responsive: Breakpoint prefix'leri (sm:, md:, lg:)             │ │
│  │  ├── Dark mode: dark: prefix ile kolay                              │ │
│  │  ├── JIT: Just-in-time compilation, arbitrary values                │ │
│  │  └── Ecosystem: Headless UI, plugins, community                     │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  KULLANIM KURALLARI:                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  DO (Yap):                                                           │ │
│  │  ├── Utility class'ları doğrudan HTML'de kullan                     │ │
│  │  ├── Responsive prefix'leri kullan (sm:, md:, lg:)                  │ │
│  │  ├── State prefix'leri kullan (hover:, focus:, active:)             │ │
│  │  ├── Dark mode için dark: prefix kullan                             │ │
│  │  ├── Group/peer modifiers kullan (group-hover:, peer-checked:)      │ │
│  │  └── @apply sadece tekrar eden pattern'ler için (component classes) │ │
│  │                                                                       │ │
│  │  DON'T (Yapma):                                                      │ │
│  │  ├── Inline style kullanma (style="...")                            │ │
│  │  ├── Custom CSS yazma (istisnalar hariç)                            │ │
│  │  ├── !important kullanma                                            │ │
│  │  ├── Arbitrary values'ı aşırı kullanma [w-137px]                   │ │
│  │  └── Class isimlerini dinamik oluşturma (purge sorunu)             │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CLASS SIRASI CONVENTION:                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Önerilen sıra (mantıksal gruplar):                                 │ │
│  │                                                                       │ │
│  │  1. Layout (display, position, z-index)                             │ │
│  │  2. Box Model (width, height, margin, padding)                      │ │
│  │  3. Typography (font, text, leading)                                │ │
│  │  4. Visual (bg, border, shadow, opacity)                            │ │
│  │  5. Interactive (cursor, pointer-events)                            │ │
│  │  6. Transitions/Animations                                          │ │
│  │  7. Responsive modifiers (sm:, md:, lg:)                           │ │
│  │  8. State modifiers (hover:, focus:, active:)                      │ │
│  │  9. Dark mode (dark:)                                               │ │
│  │                                                                       │ │
│  │  Örnek:                                                              │ │
│  │  class="                                                            │ │
│  │    flex items-center justify-between                                │ │
│  │    w-full h-12 px-4 py-2                                           │ │
│  │    text-base font-medium text-gray-900                             │ │
│  │    bg-white border border-gray-200 rounded-lg shadow-sm            │ │
│  │    cursor-pointer                                                   │ │
│  │    transition-colors duration-200                                   │ │
│  │    md:h-14 md:px-6                                                 │ │
│  │    hover:bg-gray-50 focus:ring-2 focus:ring-blue-500               │ │
│  │    dark:bg-gray-800 dark:text-white dark:border-gray-700           │ │
│  │  "                                                                  │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 CSS Custom Properties (Theming)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CSS CUSTOM PROPERTIES SİSTEMİ                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NEDEN CSS VARIABLES:                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ├── Runtime değiştirilebilir (JS ile)                              │ │
│  │  ├── Cascade/inheritance doğal çalışır                              │ │
│  │  ├── Marka renkleri dinamik atanabilir                              │ │
│  │  ├── Erişilebilirlik modları anlık değişir                          │ │
│  │  ├── Dark mode geçişleri smooth                                     │ │
│  │  └── Tailwind ile entegre çalışır                                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  VARIABLE KATEGORİLERİ:                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  1. RENK TOKENLERİ (--color-*)                                      │ │
│  │     --color-primary: Marka ana rengi                                │ │
│  │     --color-primary-light: Hover state                              │ │
│  │     --color-primary-dark: Active state                              │ │
│  │     --color-primary-subtle: Arka planlar                            │ │
│  │     --color-secondary: İkincil renk                                 │ │
│  │     --color-accent: Vurgu rengi                                     │ │
│  │                                                                       │ │
│  │  2. YÜZEY TOKENLERİ (--surface-*)                                   │ │
│  │     --surface-background: Sayfa arka planı                          │ │
│  │     --surface-card: Kart arka planı                                 │ │
│  │     --surface-elevated: Yükseltilmiş elementler                     │ │
│  │     --surface-overlay: Modal overlay                                │ │
│  │                                                                       │ │
│  │  3. METİN TOKENLERİ (--text-*)                                      │ │
│  │     --text-primary: Ana metin                                       │ │
│  │     --text-secondary: İkincil metin                                 │ │
│  │     --text-muted: Soluk metin                                       │ │
│  │     --text-inverse: Ters renkli metin                               │ │
│  │     --text-on-primary: Primary üzerinde metin                       │ │
│  │                                                                       │ │
│  │  4. KENARLIK TOKENLERİ (--border-*)                                 │ │
│  │     --border-color: Varsayılan kenar rengi                          │ │
│  │     --border-radius-sm/md/lg/full: Köşe yuvarlatma                 │ │
│  │                                                                       │ │
│  │  5. GÖLGE TOKENLERİ (--shadow-*)                                    │ │
│  │     --shadow-sm/md/lg/xl: Gölge seviyeleri                         │ │
│  │                                                                       │ │
│  │  6. TİPOGRAFİ TOKENLERİ (--font-*)                                  │ │
│  │     --font-family-sans: Ana font ailesi                             │ │
│  │     --font-family-heading: Başlık fontu                             │ │
│  │     --font-family-mono: Monospace font                              │ │
│  │                                                                       │ │
│  │  7. SPACING TOKENLERİ (--space-*)                                   │ │
│  │     --space-unit: Temel birim (4px)                                 │ │
│  │     --space-1 through --space-24                                    │ │
│  │                                                                       │ │
│  │  8. ANİMASYON TOKENLERİ (--duration-*, --easing-*)                  │ │
│  │     --duration-fast: 100ms                                          │ │
│  │     --duration-normal: 200ms                                        │ │
│  │     --duration-slow: 300ms                                          │ │
│  │     --easing-default: cubic-bezier(0.4, 0, 0.2, 1)                 │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  TAİLWIND ENTEGRASYONU:                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  tailwind.config.js içinde:                                         │ │
│  │                                                                       │ │
│  │  theme: {                                                           │ │
│  │    extend: {                                                        │ │
│  │      colors: {                                                      │ │
│  │        primary: {                                                   │ │
│  │          DEFAULT: 'var(--color-primary)',                           │ │
│  │          light: 'var(--color-primary-light)',                       │ │
│  │          dark: 'var(--color-primary-dark)',                         │ │
│  │          subtle: 'var(--color-primary-subtle)',                     │ │
│  │        },                                                           │ │
│  │        surface: {                                                   │ │
│  │          bg: 'var(--surface-background)',                           │ │
│  │          card: 'var(--surface-card)',                               │ │
│  │        },                                                           │ │
│  │      },                                                             │ │
│  │      fontFamily: {                                                  │ │
│  │        sans: 'var(--font-family-sans)',                             │ │
│  │        heading: 'var(--font-family-heading)',                       │ │
│  │      },                                                             │ │
│  │    },                                                               │ │
│  │  }                                                                  │ │
│  │                                                                       │ │
│  │  Kullanım: class="bg-primary text-on-primary"                       │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 CSS Dosya Yapısı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CSS DOSYA YAPISI                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  src/                                                                       │
│  └── styles/                                                               │
│      │                                                                      │
│      ├── main.css                 # Ana entry point                        │
│      │                                                                      │
│      ├── base/                    # Temel stiller                          │
│      │   ├── reset.css            # CSS reset/normalize                    │
│      │   ├── typography.css       # Font face tanımları                    │
│      │   └── accessibility.css    # A11y utility classes                   │
│      │                                                                      │
│      ├── tokens/                  # Design tokens                          │
│      │   ├── colors.css           # Renk değişkenleri                      │
│      │   ├── spacing.css          # Spacing scale                          │
│      │   ├── typography.css       # Type scale                             │
│      │   ├── shadows.css          # Shadow tokens                          │
│      │   └── animations.css       # Animation/transition tokens            │
│      │                                                                      │
│      ├── themes/                  # Tema dosyaları                         │
│      │   ├── default.css          # Varsayılan (light) tema               │
│      │   ├── dark.css             # Dark mode overrides                    │
│      │   ├── high-contrast.css    # Yüksek kontrast mod                   │
│      │   └── presets/             # Marka preset'leri                      │
│      │       ├── modern-minimal.css                                        │
│      │       ├── classic-elegant.css                                       │
│      │       ├── bold-contemporary.css                                     │
│      │       ├── rustic-natural.css                                        │
│      │       ├── dark-luxe.css                                             │
│      │       └── turkish-classic.css                                       │
│      │                                                                      │
│      ├── components/              # Component-specific (minimal)           │
│      │   ├── buttons.css          # @apply based button classes           │
│      │   ├── forms.css            # Form element overrides                │
│      │   ├── cards.css            # Card component classes                │
│      │   └── navigation.css       # Nav component classes                 │
│      │                                                                      │
│      └── utilities/               # Custom utilities                       │
│          ├── layout.css           # Layout helpers                        │
│          └── print.css            # Print styles                          │
│                                                                             │
│  main.css İÇERİĞİ:                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  /* Tailwind Directives */                                           │ │
│  │  @tailwind base;                                                     │ │
│  │  @tailwind components;                                               │ │
│  │  @tailwind utilities;                                                │ │
│  │                                                                       │ │
│  │  /* Base */                                                          │ │
│  │  @import './base/reset.css';                                         │ │
│  │  @import './base/typography.css';                                    │ │
│  │  @import './base/accessibility.css';                                 │ │
│  │                                                                       │ │
│  │  /* Tokens */                                                        │ │
│  │  @import './tokens/colors.css';                                      │ │
│  │  @import './tokens/spacing.css';                                     │ │
│  │  @import './tokens/typography.css';                                  │ │
│  │  @import './tokens/shadows.css';                                     │ │
│  │  @import './tokens/animations.css';                                  │ │
│  │                                                                       │ │
│  │  /* Default Theme */                                                 │ │
│  │  @import './themes/default.css';                                     │ │
│  │                                                                       │ │
│  │  /* Components (minimal, @apply based) */                            │ │
│  │  @import './components/buttons.css';                                 │ │
│  │  @import './components/forms.css';                                   │ │
│  │  @import './components/cards.css';                                   │ │
│  │  @import './components/navigation.css';                              │ │
│  │                                                                       │ │
│  │  /* Utilities */                                                     │ │
│  │  @import './utilities/layout.css';                                   │ │
│  │  @import './utilities/print.css';                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. JAVASCRIPT MİMARİSİ

### 3.1 Alpine.js Yaklaşımı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ALPINE.JS KULLANIM REHBERİ                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NEDEN ALPINE.JS:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ├── Minimal boyut (~15KB minified, gzipped ~6KB)                   │ │
│  │  ├── No build step gerekli (CDN'den doğrudan)                       │ │
│  │  ├── HTML içinde deklaratif (framework öğrenme yükü az)             │ │
│  │  ├── SSR uyumlu (EJS templates ile mükemmel çalışır)                │ │
│  │  ├── Vue.js benzeri syntax (tanıdık)                                │ │
│  │  ├── Tailwind ekosisteminde önerilen                                │ │
│  │  └── Progressive enhancement'a uygun                                │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  TEMEL DİREKTİFLER:                                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  STATE:                                                              │ │
│  │  x-data="{ open: false }"      Component state tanımla              │ │
│  │  x-init="fetchData()"          Component mount'da çalıştır          │ │
│  │                                                                       │ │
│  │  RENDERING:                                                          │ │
│  │  x-show="open"                 Conditional display (CSS)            │ │
│  │  x-if="condition"              Conditional render (DOM)             │ │
│  │  x-for="item in items"         List rendering                       │ │
│  │  x-text="message"              Text content binding                 │ │
│  │  x-html="htmlContent"          HTML content binding                 │ │
│  │                                                                       │ │
│  │  BINDING:                                                            │ │
│  │  x-bind:class="{ active: isActive }"   Class binding                │ │
│  │  x-bind:disabled="isLoading"           Attribute binding            │ │
│  │  :class="..."                          Shorthand                    │ │
│  │                                                                       │ │
│  │  EVENTS:                                                             │ │
│  │  x-on:click="handleClick"      Event listener                       │ │
│  │  @click="..."                  Shorthand                            │ │
│  │  @click.prevent="..."          Modifier: preventDefault             │ │
│  │  @click.stop="..."             Modifier: stopPropagation            │ │
│  │  @click.outside="close()"      Click outside                        │ │
│  │  @keydown.escape="close()"     Keyboard events                      │ │
│  │                                                                       │ │
│  │  FORMS:                                                              │ │
│  │  x-model="formData.email"      Two-way binding                      │ │
│  │  x-model.lazy="..."            Change event (not input)             │ │
│  │  x-model.number="..."          Cast to number                       │ │
│  │                                                                       │ │
│  │  REFS & MAGIC:                                                       │ │
│  │  x-ref="input"                 Element reference                    │ │
│  │  $refs.input.focus()           Access ref                           │ │
│  │  $el                           Current element                      │ │
│  │  $watch('value', callback)     Reactive watcher                     │ │
│  │  $nextTick(callback)           After DOM update                     │ │
│  │                                                                       │ │
│  │  TRANSITIONS:                                                        │ │
│  │  x-transition                  Default fade                         │ │
│  │  x-transition:enter="..."      Enter transition classes             │ │
│  │  x-transition:leave="..."      Leave transition classes             │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  KULLANIM PATTERNLERI:                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  DROPDOWN MENU:                                                      │ │
│  │  <div x-data="{ open: false }" class="relative">                    │ │
│  │    <button @click="open = !open" :aria-expanded="open">             │ │
│  │      Menü                                                           │ │
│  │    </button>                                                        │ │
│  │    <div x-show="open"                                               │ │
│  │         x-transition                                                │ │
│  │         @click.outside="open = false"                               │ │
│  │         class="absolute mt-2 ...">                                  │ │
│  │      <!-- Menu items -->                                            │ │
│  │    </div>                                                           │ │
│  │  </div>                                                             │ │
│  │                                                                       │ │
│  │  MODAL:                                                              │ │
│  │  <div x-data="{ showModal: false }">                                │ │
│  │    <button @click="showModal = true">Aç</button>                    │ │
│  │    <template x-teleport="body">                                     │ │
│  │      <div x-show="showModal"                                        │ │
│  │           x-transition.opacity                                      │ │
│  │           class="fixed inset-0 bg-black/50"                        │ │
│  │           @click="showModal = false">                               │ │
│  │        <div @click.stop class="modal-content">                     │ │
│  │          <!-- Modal content -->                                     │ │
│  │          <button @click="showModal = false">Kapat</button>         │ │
│  │        </div>                                                       │ │
│  │      </div>                                                         │ │
│  │    </template>                                                      │ │
│  │  </div>                                                             │ │
│  │                                                                       │ │
│  │  TABS:                                                               │ │
│  │  <div x-data="{ activeTab: 'tab1' }">                               │ │
│  │    <div role="tablist">                                             │ │
│  │      <button @click="activeTab = 'tab1'"                            │ │
│  │              :class="{ 'active': activeTab === 'tab1' }"            │ │
│  │              role="tab"                                             │ │
│  │              :aria-selected="activeTab === 'tab1'">                 │ │
│  │        Tab 1                                                        │ │
│  │      </button>                                                      │ │
│  │      <!-- More tabs -->                                             │ │
│  │    </div>                                                           │ │
│  │    <div x-show="activeTab === 'tab1'" role="tabpanel">              │ │
│  │      Tab 1 content                                                  │ │
│  │    </div>                                                           │ │
│  │  </div>                                                             │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Alpine.js Global Store & Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                ALPINE.JS STORE VE COMPONENT YAPISI                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GLOBAL STORE (Alpine.store):                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  // stores/cart.js                                                   │ │
│  │  document.addEventListener('alpine:init', () => {                    │ │
│  │    Alpine.store('cart', {                                           │ │
│  │      items: [],                                                     │ │
│  │      total: 0,                                                      │ │
│  │                                                                       │ │
│  │      add(product, quantity = 1) {                                   │ │
│  │        const existing = this.items.find(i => i.id === product.id); │ │
│  │        if (existing) {                                              │ │
│  │          existing.quantity += quantity;                             │ │
│  │        } else {                                                     │ │
│  │          this.items.push({ ...product, quantity });                │ │
│  │        }                                                            │ │
│  │        this.calculateTotal();                                       │ │
│  │        this.persist();                                              │ │
│  │      },                                                             │ │
│  │                                                                       │ │
│  │      remove(productId) {                                            │ │
│  │        this.items = this.items.filter(i => i.id !== productId);    │ │
│  │        this.calculateTotal();                                       │ │
│  │        this.persist();                                              │ │
│  │      },                                                             │ │
│  │                                                                       │ │
│  │      calculateTotal() {                                             │ │
│  │        this.total = this.items.reduce((sum, item) =>               │ │
│  │          sum + (item.price * item.quantity), 0                     │ │
│  │        );                                                           │ │
│  │      },                                                             │ │
│  │                                                                       │ │
│  │      persist() {                                                    │ │
│  │        localStorage.setItem('cart', JSON.stringify(this.items));   │ │
│  │      },                                                             │ │
│  │                                                                       │ │
│  │      init() {                                                       │ │
│  │        const saved = localStorage.getItem('cart');                 │ │
│  │        if (saved) {                                                 │ │
│  │          this.items = JSON.parse(saved);                           │ │
│  │          this.calculateTotal();                                     │ │
│  │        }                                                            │ │
│  │      }                                                              │ │
│  │    });                                                              │ │
│  │  });                                                                │ │
│  │                                                                       │ │
│  │  // Kullanım:                                                       │ │
│  │  <span x-text="$store.cart.items.length"></span>                    │ │
│  │  <button @click="$store.cart.add(product)">Sepete Ekle</button>    │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  REUSABLE COMPONENT (Alpine.data):                                          │ │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  // components/productCard.js                                       │ │
│  │  document.addEventListener('alpine:init', () => {                    │ │
│  │    Alpine.data('productCard', (product) => ({                       │ │
│  │      product,                                                       │ │
│  │      quantity: 1,                                                   │ │
│  │      selectedVariant: null,                                         │ │
│  │      showDetails: false,                                            │ │
│  │                                                                       │ │
│  │      get currentPrice() {                                           │ │
│  │        if (this.selectedVariant) {                                  │ │
│  │          return this.selectedVariant.price;                         │ │
│  │        }                                                            │ │
│  │        return this.product.price;                                   │ │
│  │      },                                                             │ │
│  │                                                                       │ │
│  │      get totalPrice() {                                             │ │
│  │        return this.currentPrice * this.quantity;                    │ │
│  │      },                                                             │ │
│  │                                                                       │ │
│  │      addToCart() {                                                  │ │
│  │        this.$store.cart.add({                                       │ │
│  │          ...this.product,                                           │ │
│  │          variant: this.selectedVariant,                             │ │
│  │          price: this.currentPrice                                   │ │
│  │        }, this.quantity);                                           │ │
│  │        this.quantity = 1;                                           │ │
│  │        this.showToast('Ürün sepete eklendi');                       │ │
│  │      },                                                             │ │
│  │                                                                       │ │
│  │      showToast(message) {                                           │ │
│  │        this.$dispatch('toast', { message });                        │ │
│  │      }                                                              │ │
│  │    }));                                                             │ │
│  │  });                                                                │ │
│  │                                                                       │ │
│  │  // Kullanım:                                                       │ │
│  │  <div x-data="productCard(<%= JSON.stringify(product) %>)">        │ │
│  │    <h3 x-text="product.name"></h3>                                  │ │
│  │    <span x-text="totalPrice"></span>                                │ │
│  │    <button @click="addToCart">Sepete Ekle</button>                 │ │
│  │  </div>                                                             │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 HTMX (Opsiyonel Eklenti)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HTMX KULLANIM REHBERİ                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HTMX NEDİR:                                                                │
│  HTML-over-the-wire yaklaşımı. Server'dan HTML partial alıp DOM'a ekler.   │
│  AJAX işlemleri için JavaScript yazmaya gerek kalmaz.                       │
│                                                                             │
│  NE ZAMAN KULLAN:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ├── Form submission (sayfa yenilemeden)                            │ │
│  │  ├── Infinite scroll / Load more                                    │ │
│  │  ├── Search autocomplete                                            │ │
│  │  ├── Partial page updates (sidebar, notification)                   │ │
│  │  ├── Real-time updates (polling based)                              │ │
│  │  └── Server-driven UI updates                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  TEMEL ATRIBUTLER:                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  REQUEST:                                                            │ │
│  │  hx-get="/api/items"           GET request                          │ │
│  │  hx-post="/api/items"          POST request                         │ │
│  │  hx-put="/api/items/1"         PUT request                          │ │
│  │  hx-delete="/api/items/1"      DELETE request                       │ │
│  │                                                                       │ │
│  │  TRIGGER:                                                            │ │
│  │  hx-trigger="click"            On click (default for buttons)       │ │
│  │  hx-trigger="submit"           On form submit                       │ │
│  │  hx-trigger="change"           On input change                      │ │
│  │  hx-trigger="keyup delay:500ms" Debounced keyup                    │ │
│  │  hx-trigger="load"             On element load                      │ │
│  │  hx-trigger="revealed"         When scrolled into view              │ │
│  │                                                                       │ │
│  │  TARGET:                                                             │ │
│  │  hx-target="#result"           Insert into #result                  │ │
│  │  hx-target="this"              Replace this element                 │ │
│  │  hx-target="closest tr"        Closest ancestor                     │ │
│  │                                                                       │ │
│  │  SWAP:                                                               │ │
│  │  hx-swap="innerHTML"           Replace inner HTML (default)         │ │
│  │  hx-swap="outerHTML"           Replace entire element               │ │
│  │  hx-swap="beforeend"           Append inside                        │ │
│  │  hx-swap="afterend"            Insert after                         │ │
│  │                                                                       │ │
│  │  MISC:                                                               │ │
│  │  hx-indicator=".spinner"       Show during request                  │ │
│  │  hx-confirm="Emin misiniz?"    Confirmation dialog                  │ │
│  │  hx-push-url="true"            Update browser URL                   │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ÖRNEK KULLANIM:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  SEARCH (Debounced):                                                 │ │
│  │  <input type="search"                                               │ │
│  │         name="q"                                                    │ │
│  │         hx-get="/api/search"                                        │ │
│  │         hx-trigger="keyup changed delay:300ms"                     │ │
│  │         hx-target="#results"                                        │ │
│  │         hx-indicator=".search-spinner">                             │ │
│  │  <span class="search-spinner htmx-indicator">...</span>             │ │
│  │  <div id="results"></div>                                           │ │
│  │                                                                       │ │
│  │  INFINITE SCROLL:                                                    │ │
│  │  <div hx-get="/api/items?page=2"                                    │ │
│  │       hx-trigger="revealed"                                         │ │
│  │       hx-swap="afterend">                                           │ │
│  │    Loading more...                                                  │ │
│  │  </div>                                                             │ │
│  │                                                                       │ │
│  │  DELETE WITH CONFIRM:                                                │ │
│  │  <button hx-delete="/api/items/<%= item.id %>"                      │ │
│  │          hx-target="closest tr"                                     │ │
│  │          hx-swap="outerHTML"                                        │ │
│  │          hx-confirm="Bu öğeyi silmek istediğinize emin misiniz?">  │ │
│  │    Sil                                                              │ │
│  │  </button>                                                          │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  SERVER RESPONSE:                                                           │
│  HTMX, server'dan HTML bekler. API endpoint'leri HTML partial döner.       │
│                                                                             │
│  // Express route                                                          │
│  router.get('/api/search', (req, res) => {                                 │
│    const results = searchItems(req.query.q);                               │
│    res.render('partials/search-results', { results }); // HTML döner      │
│  });                                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 JavaScript Dosya Yapısı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    JAVASCRIPT DOSYA YAPISI                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  public/                                                                    │
│  └── js/                                                                   │
│      │                                                                      │
│      ├── vendor/                   # Third-party (CDN fallback)            │
│      │   ├── alpine.min.js         # Alpine.js                            │
│      │   └── htmx.min.js           # HTMX (opsiyonel)                     │
│      │                                                                      │
│      ├── stores/                   # Alpine global stores                  │
│      │   ├── cart.js               # Sepet store                          │
│      │   ├── user.js               # Kullanıcı store                      │
│      │   ├── theme.js              # Tema store                           │
│      │   └── notifications.js      # Bildirim store                       │
│      │                                                                      │
│      ├── components/               # Alpine reusable components            │
│      │   ├── productCard.js                                               │
│      │   ├── modal.js                                                     │
│      │   ├── dropdown.js                                                  │
│      │   ├── tabs.js                                                      │
│      │   ├── accordion.js                                                 │
│      │   ├── toast.js                                                     │
│      │   └── imageGallery.js                                              │
│      │                                                                      │
│      ├── utils/                    # Utility fonksiyonlar                  │
│      │   ├── accessibility.js      # A11y helpers (focus trap, etc.)      │
│      │   ├── storage.js            # LocalStorage wrapper                 │
│      │   ├── validation.js         # Client-side validation               │
│      │   ├── formatting.js         # Number/date formatting               │
│      │   └── api.js                # Fetch wrapper                        │
│      │                                                                      │
│      ├── pages/                    # Page-specific scripts                 │
│      │   ├── menu.js               # Public menu page                     │
│      │   ├── cart.js               # Cart page                            │
│      │   ├── checkout.js           # Checkout page                        │
│      │   └── dashboard.js          # Admin dashboard                      │
│      │                                                                      │
│      └── app.js                    # Main entry point                      │
│                                                                             │
│  app.js İÇERİĞİ:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  // Import stores                                                    │ │
│  │  import './stores/cart.js';                                          │ │
│  │  import './stores/user.js';                                          │ │
│  │  import './stores/theme.js';                                         │ │
│  │  import './stores/notifications.js';                                 │ │
│  │                                                                       │ │
│  │  // Import components                                                │ │
│  │  import './components/productCard.js';                               │ │
│  │  import './components/modal.js';                                     │ │
│  │  import './components/dropdown.js';                                  │ │
│  │  import './components/tabs.js';                                      │ │
│  │  import './components/accordion.js';                                 │ │
│  │  import './components/toast.js';                                     │ │
│  │                                                                       │ │
│  │  // Initialize Alpine                                                │ │
│  │  import Alpine from 'alpinejs';                                      │ │
│  │  window.Alpine = Alpine;                                             │ │
│  │  Alpine.start();                                                     │ │
│  │                                                                       │ │
│  │  // Global utilities                                                 │ │
│  │  import { initAccessibility } from './utils/accessibility.js';       │ │
│  │  initAccessibility();                                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ES MODULES VS IIFE:                                                        │
│  ├── Modern browsers: ES Modules (type="module")                           │
│  ├── Legacy support: Bundle to IIFE if needed                              │
│  └── CDN alternative: Script tags in order                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. İKON SİSTEMİ

### 4.1 Phosphor Icons (Birincil)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHOSPHOR ICONS REHBERİ                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NEDEN PHOSPHOR:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ├── 6 ağırlık: Thin, Light, Regular, Bold, Fill, Duotone           │ │
│  │  ├── 6000+ ikon (ve artıyor)                                        │ │
│  │  ├── MIT lisansı (ticari kullanım serbest)                          │ │
│  │  ├── Tutarlı 24x24 grid                                             │ │
│  │  ├── Pixel-perfect design                                           │ │
│  │  ├── Web component, SVG, React, Vue desteği                         │ │
│  │  └── Aktif geliştirme ve topluluk                                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  KURULUM SEÇENEKLERİ:                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  1. CDN (Önerilen - Web Components):                                 │ │
│  │  <script src="https://unpkg.com/@phosphor-icons/web"></script>      │ │
│  │                                                                       │ │
│  │  Kullanım:                                                           │ │
│  │  <ph-icon name="shopping-cart" size="24" weight="regular"></ph-icon>│ │
│  │  <ph-icon name="house" size="32" weight="fill"></ph-icon>           │ │
│  │                                                                       │ │
│  │  2. CSS/Font (Icon font):                                            │ │
│  │  <link href="https://unpkg.com/@phosphor-icons/web@2.x/            │ │
│  │        src/css/icons.css" rel="stylesheet">                         │ │
│  │                                                                       │ │
│  │  Kullanım:                                                           │ │
│  │  <i class="ph ph-shopping-cart"></i>                                │ │
│  │  <i class="ph-fill ph-house"></i>                                   │ │
│  │  <i class="ph-bold ph-user"></i>                                    │ │
│  │                                                                       │ │
│  │  3. SVG Sprite (Performance):                                        │ │
│  │  İhtiyaç duyulan ikonları SVG sprite olarak bundle et               │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  AĞIRLIK SEÇİMİ:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Thin      │ Çok minimal tasarımlar, büyük boyutlar                 │ │
│  │  Light     │ Zarif, modern, geniş alanlar                           │ │
│  │  Regular   │ Genel kullanım (varsayılan)                            │ │
│  │  Bold      │ Vurgu, dikkat çekme, küçük boyutlar                    │ │
│  │  Fill      │ Aktif state, selected, toggle on                       │ │
│  │  Duotone   │ Dekoratif, marketing, hero sections                    │ │
│  │                                                                       │ │
│  │  Tutarlılık: Bir sayfada max 2 ağırlık kullan                       │ │
│  │  Örnek: Regular (default) + Fill (active state)                     │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  BOYUTLANDIRMA:                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Context          │ Boyut    │ Örnek Kullanım                       │ │
│  │  ─────────────────────────────────────────────────────────────────  │ │
│  │  Inline text      │ 1em      │ Metin içi, badge                     │ │
│  │  Button icon      │ 20px     │ Buton içi ikon                       │ │
│  │  Nav item         │ 24px     │ Navigasyon öğesi                     │ │
│  │  Card action      │ 24px     │ Kart aksiyonları                     │ │
│  │  Empty state      │ 48-64px  │ Boş durum illüstrasyonu             │ │
│  │  Hero             │ 64-96px  │ Hero section                         │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Font Awesome (Yedek)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FONT AWESOME KULLANIMI                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NE ZAMAN KULLAN:                                                           │
│  ├── Phosphor'da olmayan spesifik ikonlar                                  │
│  ├── Brand ikonları (sosyal medya, ödeme sistemleri)                       │
│  └── Legacy uyumluluk                                                       │
│                                                                             │
│  KURULUM:                                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  CDN (Free):                                                         │ │
│  │  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/    │ │
│  │        libs/font-awesome/6.x/css/all.min.css">                      │ │
│  │                                                                       │ │
│  │  Veya sadece brands:                                                 │ │
│  │  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/    │ │
│  │        libs/font-awesome/6.x/css/brands.min.css">                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  BRAND İKONLARI ÖRNEKLERİ:                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  <i class="fa-brands fa-facebook"></i>                               │ │
│  │  <i class="fa-brands fa-instagram"></i>                              │ │
│  │  <i class="fa-brands fa-twitter"></i>                                │ │
│  │  <i class="fa-brands fa-whatsapp"></i>                               │ │
│  │  <i class="fa-brands fa-cc-visa"></i>                                │ │
│  │  <i class="fa-brands fa-cc-mastercard"></i>                          │ │
│  │  <i class="fa-brands fa-google"></i>                                 │ │
│  │  <i class="fa-brands fa-apple"></i>                                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 İkon Erişilebilirliği

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    İKON ERİŞİLEBİLİRLİK KURALLARI                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEKORATİF İKON (bilgi taşımıyor):                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  <i class="ph ph-star" aria-hidden="true"></i>                       │ │
│  │  <span>Favoriler</span>                                              │ │
│  │                                                                       │ │
│  │  veya:                                                               │ │
│  │  <ph-icon name="star" aria-hidden="true"></ph-icon>                 │ │
│  │  <span>Favoriler</span>                                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ANLAMLI İKON (tek başına anlam taşıyor):                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  <button aria-label="Sepete ekle">                                   │ │
│  │    <i class="ph ph-shopping-cart" aria-hidden="true"></i>           │ │
│  │  </button>                                                           │ │
│  │                                                                       │ │
│  │  veya sr-only ile:                                                   │ │
│  │  <button>                                                            │ │
│  │    <i class="ph ph-shopping-cart" aria-hidden="true"></i>           │ │
│  │    <span class="sr-only">Sepete ekle</span>                         │ │
│  │  </button>                                                           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  STATUS İKON (durumu gösteren):                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  <!-- Sadece renk değil, ikon + metin de göster -->                 │ │
│  │  <span class="text-green-600">                                      │ │
│  │    <i class="ph-fill ph-check-circle" aria-hidden="true"></i>       │ │
│  │    <span>Başarılı</span>                                            │ │
│  │  </span>                                                             │ │
│  │                                                                       │ │
│  │  <span class="text-red-600">                                        │ │
│  │    <i class="ph-fill ph-x-circle" aria-hidden="true"></i>          │ │
│  │    <span>Hata</span>                                                │ │
│  │  </span>                                                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  FONKSİYONEL İKON (etkileşimli):                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  <!-- Toggle -->                                                     │ │
│  │  <button :aria-pressed="isBookmarked"                               │ │
│  │          :aria-label="isBookmarked ? 'Favorilerden kaldır'          │ │
│  │                                    : 'Favorilere ekle'"             │ │
│  │          @click="toggleBookmark">                                   │ │
│  │    <i :class="isBookmarked ? 'ph-fill' : 'ph'"                     │ │
│  │       class="ph-bookmark"                                           │ │
│  │       aria-hidden="true"></i>                                       │ │
│  │  </button>                                                           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. BUILD & TOOLING

### 5.1 Vite Konfigürasyonu

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VITE YAPILANDIRMASI                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NEDEN VITE:                                                                │
│  ├── Hızlı dev server (ESM tabanlı)                                        │
│  ├── Hot Module Replacement (HMR)                                          │
│  ├── Optimized production builds (Rollup)                                  │
│  ├── Native TypeScript desteği                                             │
│  ├── PostCSS entegrasyonu (Tailwind için)                                  │
│  └── Minimal konfigürasyon                                                  │
│                                                                             │
│  PROJE YAPISI:                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  project/                                                            │ │
│  │  ├── src/                                                           │ │
│  │  │   ├── styles/           # CSS kaynak dosyaları                   │ │
│  │  │   │   └── main.css                                               │ │
│  │  │   └── scripts/          # JS kaynak dosyaları                    │ │
│  │  │       └── app.js                                                 │ │
│  │  │                                                                   │ │
│  │  ├── public/               # Static assets (kopyalanır)             │ │
│  │  │   ├── images/                                                    │ │
│  │  │   ├── fonts/                                                     │ │
│  │  │   └── favicon.ico                                                │ │
│  │  │                                                                   │ │
│  │  ├── dist/                 # Build output                           │ │
│  │  │                                                                   │ │
│  │  ├── vite.config.js                                                 │ │
│  │  ├── tailwind.config.js                                             │ │
│  │  ├── postcss.config.js                                              │ │
│  │  └── package.json                                                   │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  vite.config.js:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  import { defineConfig } from 'vite';                                │ │
│  │  import { resolve } from 'path';                                     │ │
│  │                                                                       │ │
│  │  export default defineConfig({                                       │ │
│  │    root: 'src',                                                     │ │
│  │    publicDir: '../public',                                          │ │
│  │                                                                       │ │
│  │    build: {                                                         │ │
│  │      outDir: '../dist',                                             │ │
│  │      emptyOutDir: true,                                             │ │
│  │      manifest: true,        // Asset manifest for SSR               │ │
│  │      rollupOptions: {                                               │ │
│  │        input: {                                                     │ │
│  │          main: resolve(__dirname, 'src/scripts/app.js'),           │ │
│  │          styles: resolve(__dirname, 'src/styles/main.css'),        │ │
│  │        },                                                           │ │
│  │        output: {                                                    │ │
│  │          entryFileNames: 'js/[name]-[hash].js',                    │ │
│  │          chunkFileNames: 'js/[name]-[hash].js',                    │ │
│  │          assetFileNames: (assetInfo) => {                          │ │
│  │            if (assetInfo.name.endsWith('.css')) {                  │ │
│  │              return 'css/[name]-[hash][extname]';                  │ │
│  │            }                                                        │ │
│  │            return 'assets/[name]-[hash][extname]';                 │ │
│  │          },                                                         │ │
│  │        },                                                           │ │
│  │      },                                                             │ │
│  │    },                                                               │ │
│  │                                                                       │ │
│  │    server: {                                                        │ │
│  │      port: 3001,                                                    │ │
│  │      proxy: {                                                       │ │
│  │        '/api': 'http://localhost:3000',  // Backend proxy          │ │
│  │      },                                                             │ │
│  │    },                                                               │ │
│  │  });                                                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  tailwind.config.js:                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  /** @type {import('tailwindcss').Config} */                         │ │
│  │  module.exports = {                                                  │ │
│  │    content: [                                                       │ │
│  │      './src/**/*.{html,js,ts,ejs}',                                │ │
│  │      './views/**/*.ejs',                                            │ │
│  │    ],                                                               │ │
│  │    darkMode: 'class',       // or 'media'                          │ │
│  │    theme: {                                                         │ │
│  │      extend: {                                                      │ │
│  │        colors: {                                                    │ │
│  │          primary: {                                                 │ │
│  │            DEFAULT: 'var(--color-primary)',                         │ │
│  │            light: 'var(--color-primary-light)',                     │ │
│  │            dark: 'var(--color-primary-dark)',                       │ │
│  │            subtle: 'var(--color-primary-subtle)',                   │ │
│  │          },                                                         │ │
│  │          // ... more custom colors                                  │ │
│  │        },                                                           │ │
│  │        fontFamily: {                                                │ │
│  │          sans: ['var(--font-family-sans)', 'sans-serif'],          │ │
│  │          heading: ['var(--font-family-heading)', 'sans-serif'],    │ │
│  │        },                                                           │ │
│  │      },                                                             │ │
│  │    },                                                               │ │
│  │    plugins: [                                                       │ │
│  │      require('@tailwindcss/forms'),                                │ │
│  │      require('@tailwindcss/typography'),                           │ │
│  │    ],                                                               │ │
│  │  };                                                                 │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  postcss.config.js:                                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  module.exports = {                                                  │ │
│  │    plugins: {                                                       │ │
│  │      'tailwindcss': {},                                             │ │
│  │      'autoprefixer': {},                                            │ │
│  │      'cssnano': process.env.NODE_ENV === 'production'              │ │
│  │        ? { preset: 'default' }                                     │ │
│  │        : false,                                                     │ │
│  │    },                                                               │ │
│  │  };                                                                 │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Package.json Scripts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NPM SCRIPTS                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  {                                                                          │
│    "scripts": {                                                            │
│      // Development                                                        │
│      "dev": "vite",                                                        │
│      "dev:server": "nodemon src/server.js",                               │
│      "dev:all": "concurrently \"npm:dev\" \"npm:dev:server\"",            │
│                                                                             │
│      // Build                                                              │
│      "build": "vite build",                                                │
│      "build:analyze": "vite build --mode analyze",                        │
│                                                                             │
│      // Preview                                                            │
│      "preview": "vite preview",                                            │
│                                                                             │
│      // Linting                                                            │
│      "lint": "eslint src --ext .js,.ts",                                  │
│      "lint:fix": "eslint src --ext .js,.ts --fix",                        │
│      "lint:css": "stylelint \"src/**/*.css\"",                            │
│                                                                             │
│      // Type checking                                                      │
│      "typecheck": "tsc --noEmit",                                         │
│                                                                             │
│      // Testing                                                            │
│      "test": "vitest",                                                     │
│      "test:coverage": "vitest --coverage"                                 │
│    }                                                                       │
│  }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. PERFORMANS STRATEJİSİ

### 6.1 Frontend Performans Hedefleri

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PERFORMANS HEDEFLERİ                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CORE WEB VITALS HEDEFLERI:                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Metrik                │ Hedef      │ Açıklama                       │ │
│  │  ─────────────────────────────────────────────────────────────────── │ │
│  │  LCP (Largest          │ < 2.5s     │ En büyük içerik görünme süresi│ │
│  │   Contentful Paint)    │            │                                │ │
│  │                                                                       │ │
│  │  FID (First Input      │ < 100ms    │ İlk etkileşim gecikmesi       │ │
│  │   Delay)               │            │                                │ │
│  │                                                                       │ │
│  │  CLS (Cumulative       │ < 0.1      │ Görsel stabilite              │ │
│  │   Layout Shift)        │            │                                │ │
│  │                                                                       │ │
│  │  TTFB (Time to First   │ < 600ms    │ İlk byte süresi               │ │
│  │   Byte)                │            │                                │ │
│  │                                                                       │ │
│  │  FCP (First Contentful │ < 1.8s     │ İlk içerik görünme            │ │
│  │   Paint)               │            │                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  BUNDLE SIZE HEDEFLERI:                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Asset           │ Hedef (gzipped) │ Notlar                         │ │
│  │  ─────────────────────────────────────────────────────────────────── │ │
│  │  CSS (main)      │ < 30KB          │ Tailwind purged                │ │
│  │  JS (main)       │ < 50KB          │ Alpine + app code              │ │
│  │  Fonts           │ < 100KB         │ Subset, woff2                  │ │
│  │  Initial HTML    │ < 50KB          │ Server-rendered                │ │
│  │                                                                       │ │
│  │  Total initial   │ < 250KB         │ First meaningful load          │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Optimizasyon Teknikleri

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OPTİMİZASYON TEKNİKLERİ                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CSS OPTİMİZASYONU:                                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ├── Tailwind PurgeCSS: Kullanılmayan class'ları sil                │ │
│  │  ├── Critical CSS: Above-the-fold CSS inline                        │ │
│  │  ├── CSS minification: cssnano ile                                  │ │
│  │  ├── Preload: <link rel="preload" as="style">                      │ │
│  │  └── Font-display: swap (FOUT tercih)                               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  JS OPTİMİZASYONU:                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ├── Minimal JS: Alpine.js (~6KB gzip)                              │ │
│  │  ├── Defer loading: <script defer>                                  │ │
│  │  ├── Code splitting: Page-specific bundles                          │ │
│  │  ├── Tree shaking: Unused exports eliminated                        │ │
│  │  └── Minification: Terser ile                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  IMAGE OPTİMİZASYONU:                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ├── Format: WebP/AVIF with fallback                                │ │
│  │  ├── Lazy loading: loading="lazy"                                   │ │
│  │  ├── Responsive: srcset + sizes                                     │ │
│  │  ├── Aspect ratio: width/height attributes (CLS önleme)            │ │
│  │  ├── Placeholder: LQIP (Low Quality Image Placeholder)              │ │
│  │  └── CDN: Cloudflare/Bunny image optimization                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  FONT OPTİMİZASYONU:                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ├── Format: WOFF2 only (modern browsers)                           │ │
│  │  ├── Subset: Latin + Turkish chars only                             │ │
│  │  ├── Preload: <link rel="preload" as="font">                       │ │
│  │  ├── font-display: swap                                             │ │
│  │  └── Variable fonts: Tek dosyada tüm ağırlıklar                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CACHING STRATEJİSİ:                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Asset Type       │ Cache-Control                │ Strategy          │ │
│  │  ─────────────────────────────────────────────────────────────────── │ │
│  │  HTML             │ no-cache                     │ Always validate   │ │
│  │  CSS/JS (hashed)  │ max-age=31536000, immutable  │ Long-term cache   │ │
│  │  Images (static)  │ max-age=2592000              │ 30 days           │ │
│  │  Fonts            │ max-age=31536000             │ 1 year            │ │
│  │  API responses    │ no-store                     │ No caching        │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. BROWSER SUPPORT

### 7.1 Desteklenen Browserlar

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BROWSER SUPPORT MATRİSİ                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HEDEF: Modern browsers, son 2 major version                               │
│                                                                             │
│  DESTEKLENEN:                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Browser            │ Minimum │ Notlar                               │ │
│  │  ─────────────────────────────────────────────────────────────────── │ │
│  │  Chrome             │ 90+     │ Auto-update, evergreen               │ │
│  │  Firefox            │ 90+     │ Auto-update, evergreen               │ │
│  │  Safari             │ 14+     │ iOS 14+, macOS Big Sur+              │ │
│  │  Edge (Chromium)    │ 90+     │ Auto-update                          │ │
│  │  Samsung Internet   │ 14+     │ Android cihazlar                     │ │
│  │  Opera              │ 76+     │ Chromium-based                       │ │
│  │                                                                       │ │
│  │  Mobile:                                                             │ │
│  │  iOS Safari         │ 14+     │ iPhone 6s ve sonrası                 │ │
│  │  Chrome Android     │ 90+     │ Android 5.0+                         │ │
│  │  WebView Android    │ 90+     │ In-app browsers                      │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  DESTEKLENMEYEN:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ├── Internet Explorer (tüm versiyonlar)                            │ │
│  │  ├── Legacy Edge (EdgeHTML)                                         │ │
│  │  ├── Safari < 14                                                    │ │
│  │  └── Opera Mini                                                     │ │
│  │                                                                       │ │
│  │  Degradation: Temel HTML/CSS çalışır, JS özellikleri eksik          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  BROWSERSLIST (package.json):                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  "browserslist": [                                                   │ │
│  │    "> 1%",                                                          │ │
│  │    "last 2 versions",                                               │ │
│  │    "not dead",                                                      │ │
│  │    "not IE 11",                                                     │ │
│  │    "not op_mini all"                                                │ │
│  │  ]                                                                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. TEST STRATEJİSİ (Frontend)

### 8.1 Frontend Test Yaklaşımı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND TEST STRATEJİSİ                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TEST TÜRLERİ:                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  1. VISUAL REGRESSION                                                │ │
│  │     Tool: Playwright visual comparisons                              │ │
│  │     Scope: Kritik sayfalar, component snapshots                     │ │
│  │     Frequency: PR'larda                                             │ │
│  │                                                                       │ │
│  │  2. ACCESSIBILITY TESTING                                            │ │
│  │     Tool: axe-core, Lighthouse CI                                   │ │
│  │     Scope: Tüm public sayfalar                                      │ │
│  │     Frequency: Her deploy'da                                        │ │
│  │                                                                       │ │
│  │  3. CROSS-BROWSER TESTING                                            │ │
│  │     Tool: Playwright (Chrome, Firefox, Safari)                      │ │
│  │     Scope: Kritik user flows                                        │ │
│  │     Frequency: Release öncesi                                       │ │
│  │                                                                       │ │
│  │  4. PERFORMANCE TESTING                                              │ │
│  │     Tool: Lighthouse CI, Web Vitals                                 │ │
│  │     Scope: LCP, FID, CLS metrikleri                                │ │
│  │     Frequency: Her deploy'da                                        │ │
│  │                                                                       │ │
│  │  5. E2E (User Flows)                                                 │ │
│  │     Tool: Playwright                                                │ │
│  │     Scope: QR scan → Order akışı                                    │ │
│  │     Frequency: Nightly, release öncesi                              │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ACCESSIBILITY AUDIT CHECKLIST:                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  [ ] axe-core scan: 0 violations                                    │ │
│  │  [ ] Lighthouse accessibility: > 90                                 │ │
│  │  [ ] Keyboard navigation: Complete                                  │ │
│  │  [ ] Screen reader: NVDA/VoiceOver tested                          │ │
│  │  [ ] Color contrast: All text passes                               │ │
│  │  [ ] Focus indicators: Visible                                     │ │
│  │  [ ] Touch targets: 48px minimum                                   │ │
│  │  [ ] Zoom: 200% without horizontal scroll                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Bu döküman, E-Menum frontend mimarisini tanımlar. Tüm frontend geliştirmeleri bu kurallara uygun olmalıdır.*
