# E-Menum Frontend Architecture

> **Auto-Claude Frontend Architecture Document**
> CSS/JS yaklasimlar, framework kararlari, library secimleri, performans stratejisi.
> Son Guncelleme: 2026-03-16

---

## 1. MIMARI GENEL BAKIS

### 1.1 Frontend Felsefesi

```
PRENSiP: Server-First, Progressive Enhancement

1. HTML ILK
   Server-rendered HTML (Django Templates)
   JavaScript olmadan da calismali (core functionality)

2. CSS IKINCI
   Styling tamamen CSS ile
   CSS-only interaktiflik mumkunse (hover, :checked, details)

3. JS SON
   Enhancement icin, dependency degil
   Minimal, focused, purpose-driven

NEDEN BU YAKLASIM:
  - Erisilebirlik: Screen reader'lar HTML'i okur
  - Performans: Ilk yukleme hizli (no JS bundle wait)
  - SEO: Server-rendered content indekslenebilir
  - Guvenilirlik: JS hata verse de temel islev calisir
  - Mobil: Dusuk bant genisliginde bile calisir
  - Bakim: Daha az karmasiklik, daha az hata

BU YAKLASIM NE DEGIL:
  - SPA (Single Page Application) degil
  - React/Vue/Angular kullanmiyoruz
  - Client-side routing yok
  - Heavy JavaScript framework yok
```

### 1.2 Teknoloji Stack Ozeti

| Katman | Teknoloji | Amac |
|--------|-----------|------|
| Templating | Django Templates | Server-side HTML rendering |
| CSS Framework | Tailwind CSS 3.4.x | Utility-first styling |
| CSS Variables | Native CSS | Theming, runtime customization |
| JS Enhancement | Alpine.js 3.x (CDN) | Declarative interactivity |
| UI Components | Flowbite | Tailwind component library (modals, dropdowns, etc.) |
| Icons | Phosphor Icons (CDN) | Consistent iconography |
| Charts | Chart.js | Dashboard charts |
| Fonts | Google Fonts CDN | Typography (Inter, etc.) |
| CSS Build | PostCSS + Tailwind CLI | Utility compilation, autoprefixer |
| i18n | Django `{% trans %}` / `{% blocktrans %}` | Internationalization |

---

## 2. CSS MIMARISI

### 2.1 Tailwind CSS Yaklasimi

```
NEDEN TAILWIND:
  - Utility-first: Hizli prototipleme ve gelistirme
  - Tutarlilik: Spacing, color, typography scale sabit
  - Purging: Kullanilmayan CSS otomatik temizlenir
  - Responsive: Breakpoint prefix'leri (sm:, md:, lg:, xl:)
  - Dark mode: dark: prefix ile kolay (class-based)
  - JIT: Just-in-time compilation, arbitrary values
  - Ecosystem: Flowbite, plugins, community

KULLANIM KURALLARI:

  DO (Yap):
  - Utility class'lari dogrudan HTML'de kullan
  - Responsive prefix'leri kullan (sm:, md:, lg:, xl:)
  - State prefix'leri kullan (hover:, focus:, active:)
  - Dark mode icin dark: prefix kullan
  - Group/peer modifiers kullan (group-hover:, peer-checked:)
  - @apply sadece tekrar eden pattern'ler icin (component classes)

  DON'T (Yapma):
  - Inline style kullanma (style="...")
  - Custom CSS yazma (istisnalar haric)
  - !important kullanma
  - Arbitrary values'i asiri kullanma [w-137px]
  - Class isimlerini dinamik olusturma (purge sorunu)

CLASS SIRASI CONVENTION:

  Onerilen sira (mantiksal gruplar):

  1. Layout      (display, position, z-index)
  2. Box Model   (width, height, margin, padding)
  3. Typography  (font, text, leading)
  4. Visual      (bg, border, shadow, opacity)
  5. Interactive (cursor, pointer-events)
  6. Transitions/Animations
  7. Responsive  (sm:, md:, lg:, xl:)
  8. State       (hover:, focus:, active:)
  9. Dark mode   (dark:)

  Ornek:
  class="
    flex items-center justify-between
    w-full h-12 px-4 py-2
    text-base font-medium text-gray-900
    bg-white border border-gray-200 rounded-lg shadow-sm
    cursor-pointer
    transition-colors duration-200
    md:h-14 md:px-6
    hover:bg-gray-50 focus:ring-2 focus:ring-blue-500
    dark:bg-gray-800 dark:text-white dark:border-gray-700
  "
```

### 2.2 CSS Custom Properties (Design Tokens)

```
NEDEN CSS VARIABLES:
  - Runtime degistirilebilir (JS ile)
  - Cascade/inheritance dogal calisir
  - Marka renkleri dinamik atanabilir
  - Dark mode gecisleri smooth
  - Tailwind ile entegre calisir

VARIABLE KATEGORILERI:

  1. RENK TOKENLERI (--color-*)
     --color-primary:        Marka ana rengi
     --color-primary-light:  Hover state
     --color-primary-dark:   Active state
     --color-primary-subtle: Arka planlar
     --color-secondary:      Ikincil renk
     --color-accent:         Vurgu rengi

  2. YUZEY TOKENLERI (--surface-*)
     --surface-background:   Sayfa arka plani
     --surface-card:         Kart arka plani
     --surface-elevated:     Yukseltilmis elementler
     --surface-overlay:      Modal overlay

  3. METIN TOKENLERI (--text-*)
     --text-primary:         Ana metin
     --text-secondary:       Ikincil metin
     --text-muted:           Soluk metin
     --text-inverse:         Ters renkli metin
     --text-on-primary:      Primary uzerinde metin

  4. KENARLIK TOKENLERI (--border-*)
     --border-color:         Varsayilan kenar rengi
     --border-radius-sm/md/lg/full: Kose yuvarlatma

  5. GOLGE TOKENLERI (--shadow-*)
     --shadow-sm/md/lg/xl:   Golge seviyeleri

  6. TIPOGRAFI TOKENLERI (--font-*)
     --font-family-sans:     Ana font ailesi
     --font-family-heading:  Baslik fontu
     --font-family-mono:     Monospace font

  7. ANIMASYON TOKENLERI (--duration-*, --easing-*)
     --duration-fast:        100ms
     --duration-normal:      200ms
     --duration-slow:        300ms
     --easing-default:       cubic-bezier(0.4, 0, 0.2, 1)

TAILWIND ENTEGRASYONU (tailwind.config.js):

  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'var(--color-primary)',
          light: 'var(--color-primary-light)',
          dark: 'var(--color-primary-dark)',
          subtle: 'var(--color-primary-subtle)',
        },
        surface: {
          bg: 'var(--surface-background)',
          card: 'var(--surface-card)',
        },
      },
      fontFamily: {
        sans: 'var(--font-family-sans)',
        heading: 'var(--font-family-heading)',
      },
    },
  }

  Kullanim: class="bg-primary text-on-primary"
```

### 2.3 Dark Mode

```
YAKLASIM: Class-based toggle on <html> element

  Tailwind config:
    darkMode: 'class'

  HTML root:
    <html class="dark"> ... </html>

  Toggle mechanism (Alpine.js + localStorage):

    <div x-data="{
      dark: localStorage.getItem('darkMode') === 'true'
    }" x-init="
      $watch('dark', val => {
        localStorage.setItem('darkMode', val);
        document.documentElement.classList.toggle('dark', val);
      });
      document.documentElement.classList.toggle('dark', dark);
    ">
      <button @click="dark = !dark">
        <i x-show="!dark" class="ph ph-moon"></i>
        <i x-show="dark" class="ph ph-sun"></i>
      </button>
    </div>

  Template kullanimi:
    class="bg-white dark:bg-gray-900 text-gray-900 dark:text-white"

KURALLAR:
  - Her renk class'ina dark: karsiligi ekle
  - dark: prefix'i Tailwind config'de 'class' mode olmali
  - localStorage ile kullanici tercihi persist et
  - prefers-color-scheme ile ilk yukleme belirle (opsiyonel)
```

### 2.4 Responsive Design

```
YAKLASIM: Mobile-first with Tailwind breakpoints

  BREAKPOINTS:
  sm:   640px    Kucuk tablet
  md:   768px    Tablet
  lg:   1024px   Desktop
  xl:   1280px   Genis desktop
  2xl:  1536px   Cok genis ekran

  MOBILE-FIRST DEMEK:
  - Varsayilan stiller mobil icindir
  - Breakpoint prefix'leri buyuk ekranlar icin override eder

  Ornek:
    class="
      flex flex-col        <!-- Mobil: dikey -->
      md:flex-row          <!-- Tablet+: yatay -->
      gap-4
      p-4 md:p-6 lg:p-8   <!-- Artan padding -->
    "

  SIDEBAR PATTERN:
    - Mobilde: gizli, hamburger menu ile acilir
    - lg: breakpoint'te: sabit sidebar gorunur
    class="
      fixed inset-y-0 left-0 z-40
      -translate-x-full lg:translate-x-0
      transition-transform duration-300
    "
```

### 2.5 CSS Build Pipeline

```
PIPELINE: PostCSS + Tailwind CLI (no webpack/vite)

  INPUT:
    static/src/css/main.css

  main.css ICERIGI:
    @tailwind base;
    @tailwind components;
    @tailwind utilities;

    /* Design tokens */
    @import './tokens/colors.css';

    /* Component classes (@apply based) */
    @import './components/buttons.css';
    @import './components/forms.css';

  OUTPUT:
    static/css/styles.css

  BUILD COMMAND:
    npm run build:css
    --> npx tailwindcss -i static/src/css/main.css -o static/css/styles.css --minify

  DEV (watch mode):
    npm run watch:css
    --> npx tailwindcss -i static/src/css/main.css -o static/css/styles.css --watch

  DJANGO STATIC COLLECTION:
    python manage.py collectstatic --noinput

  tailwind.config.js CONTENT PATHS:
    content: [
      './templates/**/*.html',
      './apps/**/templates/**/*.html',
      './static/js/**/*.js',
      './node_modules/flowbite/**/*.js',
    ]

  postcss.config.js:
    module.exports = {
      plugins: {
        tailwindcss: {},
        autoprefixer: {},
      },
    }
```

### 2.6 CSS Dosya Yapisi

```
static/
├── src/
│   └── css/
│       ├── main.css              # Ana entry point (Tailwind directives)
│       ├── tokens/
│       │   └── colors.css        # CSS custom property tanimlari
│       └── components/
│           ├── buttons.css       # @apply based button classes
│           ├── forms.css         # Form element overrides
│           └── cards.css         # Card component classes
│
└── css/
    └── styles.css                # COMPILED OUTPUT (git-ignored)
```

---

## 3. JAVASCRIPT MIMARISI

### 3.1 Alpine.js Yaklasimi

```
NEDEN ALPINE.JS:
  - Minimal boyut (~15KB minified, gzipped ~6KB)
  - No build step gerekli (CDN'den dogrudan)
  - HTML icinde deklaratif (framework ogrenme yuku az)
  - SSR uyumlu (Django Templates ile mukemmel calisir)
  - Vue.js benzeri syntax (tanidik)
  - Tailwind ekosisteminde onerilen
  - Progressive enhancement'a uygun

TEMEL DIREKTIFLER:

  STATE:
  x-data="{ open: false }"      Component state tanimla
  x-init="fetchData()"          Component mount'da calistir

  RENDERING:
  x-show="open"                 Conditional display (CSS)
  x-if="condition"              Conditional render (DOM)
  x-for="item in items"         List rendering
  x-text="message"              Text content binding
  x-html="htmlContent"          HTML content binding

  BINDING:
  x-bind:class="{ active: isActive }"   Class binding
  x-bind:disabled="isLoading"           Attribute binding
  :class="..."                          Shorthand

  EVENTS:
  x-on:click="handleClick"      Event listener
  @click="..."                  Shorthand
  @click.prevent="..."          Modifier: preventDefault
  @click.outside="close()"      Click outside
  @keydown.escape="close()"     Keyboard events

  FORMS:
  x-model="formData.email"      Two-way binding
  x-model.lazy="..."            Change event (not input)
  x-model.number="..."          Cast to number

  REFS & MAGIC:
  x-ref="input"                 Element reference
  $refs.input.focus()           Access ref
  $el                           Current element
  $watch('value', callback)     Reactive watcher
  $nextTick(callback)           After DOM update

  TRANSITIONS:
  x-transition                  Default fade
  x-transition:enter="..."      Enter transition classes
  x-transition:leave="..."      Leave transition classes
```

### 3.2 Alpine.js Kullanim Patternleri

```
DROPDOWN MENU:
  <div x-data="{ open: false }" class="relative">
    <button @click="open = !open" :aria-expanded="open">
      Menu
    </button>
    <div x-show="open"
         x-transition
         @click.outside="open = false"
         class="absolute mt-2 ...">
      <!-- Menu items -->
    </div>
  </div>

MODAL (Flowbite pattern):
  <div x-data="{ showModal: false }">
    <button @click="showModal = true">Ac</button>
    <div x-show="showModal"
         x-transition.opacity
         class="fixed inset-0 z-50 bg-black/50"
         @click="showModal = false">
      <div @click.stop class="modal-content bg-white dark:bg-gray-800 ...">
        <!-- Modal content -->
        <button @click="showModal = false">Kapat</button>
      </div>
    </div>
  </div>

TABS:
  <div x-data="{ activeTab: 'tab1' }">
    <div role="tablist" class="flex border-b border-gray-200 dark:border-gray-700">
      <button @click="activeTab = 'tab1'"
              :class="activeTab === 'tab1'
                ? 'border-primary text-primary'
                : 'border-transparent text-gray-500'"
              class="px-4 py-2 border-b-2"
              role="tab"
              :aria-selected="activeTab === 'tab1'">
        Tab 1
      </button>
      <!-- More tabs -->
    </div>
    <div x-show="activeTab === 'tab1'" role="tabpanel">
      Tab 1 content
    </div>
  </div>

TOAST NOTIFICATIONS:
  <div x-data="{ toasts: [] }"
       @toast.window="toasts.push($event.detail);
                      setTimeout(() => toasts.shift(), 3000)">
    <template x-for="toast in toasts" :key="toast.id">
      <div x-text="toast.message"
           class="fixed bottom-4 right-4 bg-green-500 text-white
                  px-4 py-2 rounded-lg shadow-lg">
      </div>
    </template>
  </div>
```

### 3.3 AJAX ve CSRF Token Islemi

```
YAKLASIM: Vanilla JS fetch + Django CSRF token

  CSRF TOKEN OKUMA:
  function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value
      || document.cookie
          .split('; ')
          .find(row => row.startsWith('csrftoken='))
          ?.split('=')[1];
  }

  FETCH WITH CSRF:
  async function fetchWithCsrf(url, options = {}) {
    const defaults = {
      headers: {
        'X-CSRFToken': getCsrfToken(),
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
    };
    const response = await fetch(url, { ...defaults, ...options });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  KULLANIM ORNEKLERI:

  // GET
  const data = await fetchWithCsrf('/api/v1/menus/');

  // POST
  const result = await fetchWithCsrf('/api/v1/menus/', {
    method: 'POST',
    body: JSON.stringify({ name: 'Yeni Menu' }),
  });

  // DELETE (soft delete)
  await fetchWithCsrf(`/api/v1/menus/${id}/`, {
    method: 'DELETE',
  });

  ALPINE.JS ICINDE:
  <div x-data="{
    items: [],
    loading: false,
    async fetchItems() {
      this.loading = true;
      try {
        const res = await fetchWithCsrf('/api/v1/items/');
        this.items = res.data;
      } catch (err) {
        console.error(err);
      } finally {
        this.loading = false;
      }
    }
  }" x-init="fetchItems()">
    <template x-if="loading">
      <div class="animate-spin ...">Loading...</div>
    </template>
    <template x-for="item in items" :key="item.id">
      <div x-text="item.name"></div>
    </template>
  </div>
```

### 3.4 JavaScript Dosya Yapisi

```
static/
└── js/
    ├── utils/
    │   ├── csrf.js               # fetchWithCsrf utility
    │   ├── formatting.js         # Number/date formatting
    │   └── storage.js            # LocalStorage wrapper
    │
    ├── components/
    │   ├── darkModeToggle.js     # Dark mode Alpine component
    │   ├── toast.js              # Toast notification system
    │   └── charts.js             # Chart.js initialization helpers
    │
    ├── pages/
    │   ├── dashboard.js          # Admin dashboard charts
    │   └── menu-editor.js        # Menu CRUD page logic
    │
    └── app.js                    # Global init (dark mode, etc.)

YUKLEME STRATEJISI:
  - Alpine.js: CDN <script defer>
  - Flowbite: CDN <script defer>
  - Chart.js: CDN, sadece dashboard sayfalarinda
  - Phosphor Icons: CDN <link>
  - Utility scripts: Django {% static %} tag ile

  NO BUILD STEP for JS:
  - Tum JS dosyalari dogrudan static/ dizininden servis edilir
  - ES module kullanilmaz (CDN + script tag yaklasimi)
  - Bundler/minifier yok (dosyalar zaten kucuk)
```

---

## 4. IKON SISTEMI

### 4.1 Phosphor Icons (Birincil)

```
NEDEN PHOSPHOR:
  - 6 agirlik: Thin, Light, Regular, Bold, Fill, Duotone
  - 6000+ ikon
  - MIT lisansi (ticari kullanim serbest)
  - Tutarli 24x24 grid
  - Pixel-perfect design
  - Aktif gelistirme ve topluluk

KURULUM (CDN):
  <link rel="stylesheet"
        href="https://unpkg.com/@phosphor-icons/web@2.x/src/css/icons.css">

KULLANIM:
  <i class="ph ph-house"></i>              Regular
  <i class="ph-fill ph-house"></i>         Fill
  <i class="ph-bold ph-user"></i>          Bold
  <i class="ph-light ph-gear"></i>         Light
  <i class="ph-duotone ph-chart-bar"></i>  Duotone

AGIRLIK SECIMI:
  Thin      - Cok minimal tasarimlar, buyuk boyutlar
  Light     - Zarif, modern, genis alanlar
  Regular   - Genel kullanim (varsayilan)
  Bold      - Vurgu, dikkat cekme, kucuk boyutlar
  Fill      - Aktif state, selected, toggle on
  Duotone   - Dekoratif, marketing, hero sections

  Tutarlilik: Bir sayfada max 2 agirlik kullan
  Ornek: Regular (default) + Fill (active state)

BOYUTLANDIRMA (Tailwind ile):
  <i class="ph ph-house text-base"></i>     16px
  <i class="ph ph-house text-lg"></i>       18px
  <i class="ph ph-house text-xl"></i>       20px
  <i class="ph ph-house text-2xl"></i>      24px
  <i class="ph ph-house text-4xl"></i>      36px

SIK KULLANILAN IKONLAR:
  Navigation: ph-house, ph-list, ph-gear, ph-sign-out
  Actions:    ph-plus, ph-pencil, ph-trash, ph-eye
  Menu:       ph-fork-knife, ph-coffee, ph-bowl-food
  Dashboard:  ph-chart-bar, ph-chart-line, ph-users
  Status:     ph-check-circle, ph-warning, ph-x-circle
  UI:         ph-caret-down, ph-magnifying-glass, ph-bell
```

---

## 5. TEMPLATE SISTEMI (Django)

### 5.1 Template Inheritance

```
LAYOUT HIERARCHY:

  templates/
  ├── layouts/
  │   ├── base.html              # Root layout (HTML head, body wrapper)
  │   ├── auth.html              # Login/register pages
  │   ├── admin.html             # Admin panel (sidebar + topbar)
  │   ├── restaurant.html        # Restaurant panel
  │   └── public.html            # Public-facing pages
  │
  ├── partials/
  │   ├── _sidebar.html          # Admin sidebar navigation
  │   ├── _topbar.html           # Top navigation bar
  │   ├── _breadcrumbs.html      # Breadcrumb navigation
  │   ├── _flash_messages.html   # Toast/alert messages
  │   ├── _pagination.html       # Reusable pagination
  │   └── _dark_mode_toggle.html # Dark mode switch
  │
  └── [app_name]/
      ├── list.html              # CRUD list page
      ├── detail.html            # CRUD detail/edit page
      └── form.html              # Create/edit form

BASE LAYOUT PATTERN (base.html):

  <!DOCTYPE html>
  <html lang="{{ LANGUAGE_CODE }}" class="{% block html_class %}{% endblock %}">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}E-Menum{% endblock %}</title>

    <!-- Tailwind compiled CSS -->
    <link rel="stylesheet" href="{% static 'css/styles.css' %}">

    <!-- Phosphor Icons -->
    <link rel="stylesheet"
          href="https://unpkg.com/@phosphor-icons/web@2.x/src/css/icons.css">

    {% block extra_head %}{% endblock %}
  </head>
  <body class="bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white">
    {% block body %}{% endblock %}

    <!-- Alpine.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x/dist/cdn.min.js"></script>
    <!-- Flowbite -->
    <script defer src="https://cdn.jsdelivr.net/npm/flowbite@2.x/dist/flowbite.min.js"></script>

    {% block extra_scripts %}{% endblock %}
  </body>
  </html>

PAGE TEMPLATE PATTERN:

  {% extends "layouts/admin.html" %}
  {% load static i18n %}

  {% block title %}{% trans "Menu Yonetimi" %} - E-Menum{% endblock %}

  {% block breadcrumbs %}
    {% include "partials/_breadcrumbs.html" with items=breadcrumbs %}
  {% endblock %}

  {% block content %}
    <div class="p-4 lg:p-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        {% trans "Menu Yonetimi" %}
      </h1>
      <!-- Page content -->
    </div>
  {% endblock %}

  {% block extra_scripts %}
    <script src="{% static 'js/pages/menu-editor.js' %}"></script>
  {% endblock %}
```

### 5.2 Template Tags ve Filters

```
DJANGO TEMPLATE TAGS:

  i18n (Ceviri):
    {% load i18n %}
    {% trans "Menu Olustur" %}
    {% blocktrans with name=menu.name %}
      {{ name }} menusu basariyla olusturuldu.
    {% endblocktrans %}

  Static Files:
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/styles.css' %}">
    <img src="{% static 'images/logo.svg' %}" alt="E-Menum">

  URL Routing:
    <a href="{% url 'menu:list' %}">Menuler</a>
    <a href="{% url 'menu:detail' pk=menu.pk %}">{{ menu.name }}</a>
    <form action="{% url 'menu:delete' pk=menu.pk %}" method="post">

  CSRF Protection:
    <form method="post">
      {% csrf_token %}
      <!-- Form fields -->
    </form>

  Conditionals:
    {% if user.is_authenticated %}
      {% trans "Hosgeldiniz" %}, {{ user.first_name }}
    {% else %}
      <a href="{% url 'auth:login' %}">{% trans "Giris Yap" %}</a>
    {% endif %}

  Loops:
    {% for item in menu_items %}
      <div class="{% cycle 'bg-white' 'bg-gray-50' %} dark:bg-gray-800 p-4">
        {{ item.name }} - {{ item.price|floatformat:2 }} TL
      </div>
    {% empty %}
      <p>{% trans "Henuz urun eklenmemis." %}</p>
    {% endfor %}

  Custom Filters:
    {{ price|floatformat:2 }}           Ondalik format
    {{ description|truncatewords:20 }}  Kelime sinirla
    {{ created_at|date:"d.m.Y" }}       Tarih format
    {{ name|title }}                     Baslik formati
    {{ text|linebreaksbr }}             Satir sonlari
```

### 5.3 Partial ve Include Patternleri

```
REUSABLE PARTIALS:

  Sidebar:
    {% include "partials/_sidebar.html" with active="menus" %}

  Flash Messages:
    {% include "partials/_flash_messages.html" %}

  Pagination:
    {% include "partials/_pagination.html" with page_obj=page_obj %}

  Form Fields (component-like):
    {% include "partials/form/_text_input.html" with
       name="menu_name"
       label=_("Menu Adi")
       value=form.name.value
       error=form.name.errors
       required=True
    %}

PARTIAL NAMING CONVENTION:
  - Underscore prefix: _partial_name.html
  - Partials dizini altinda gruplanir
  - Her partial kendi x-data scope'unda olabilir
```

---

## 6. FLOWBITE ENTEGRASYONU

### 6.1 Flowbite Kullanimi

```
NEDEN FLOWBITE:
  - Tailwind CSS uzerine kurulu (ek CSS yok)
  - Hazir UI component'leri (modal, dropdown, tooltip, etc.)
  - Dark mode destegi built-in
  - Erisilebilirlik (a11y) uyumlu
  - CDN ile yuklenebilir

KURULUM:
  <!-- CSS (Tailwind zaten var, ek CSS gerekmez) -->
  <!-- JS (CDN) -->
  <script src="https://cdn.jsdelivr.net/npm/flowbite@2.x/dist/flowbite.min.js"></script>

TAILWIND CONFIG ENTEGRASYONU:
  // tailwind.config.js
  module.exports = {
    content: [
      './node_modules/flowbite/**/*.js',
      // ... diger content paths
    ],
    plugins: [
      require('flowbite/plugin'),
    ],
  }

SIK KULLANILAN COMPONENTLER:

  Modal:
    data-modal-target="myModal"
    data-modal-toggle="myModal"

  Dropdown:
    data-dropdown-toggle="myDropdown"

  Tooltip:
    data-tooltip-target="myTooltip"

  Tabs:
    data-tabs-toggle="#myTabs"

  Accordion:
    data-accordion="collapse"

NOT: Flowbite ve Alpine.js birlikte kullanilabilir.
  - Basit UI interactions: Flowbite data attributes
  - Complex state management: Alpine.js x-data
  - Secim kriteri: State paylasilmiyorsa Flowbite, paylasiliyorsa Alpine
```

---

## 7. CHART.JS (Dashboard)

### 7.1 Chart.js Kullanimi

```
YUKLEME:
  <!-- Sadece dashboard sayfalarinda -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.x"></script>

DARK MODE UYUMU:
  Chart.js renkleri dark mode'a gore degismeli.
  CSS variable veya Alpine.js watch ile guncelle.

ORNEK (Django template icinde):

  {% block extra_scripts %}
  <script>
    const ctx = document.getElementById('revenueChart').getContext('2d');
    const isDark = document.documentElement.classList.contains('dark');

    new Chart(ctx, {
      type: 'line',
      data: {
        labels: {{ chart_labels|safe }},
        datasets: [{
          label: '{% trans "Gelir" %}',
          data: {{ chart_data|safe }},
          borderColor: isDark ? '#60a5fa' : '#3b82f6',
          backgroundColor: isDark ? 'rgba(96,165,250,0.1)' : 'rgba(59,130,246,0.1)',
          fill: true,
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            labels: {
              color: isDark ? '#e5e7eb' : '#374151'
            }
          }
        },
        scales: {
          x: { ticks: { color: isDark ? '#9ca3af' : '#6b7280' } },
          y: { ticks: { color: isDark ? '#9ca3af' : '#6b7280' } }
        }
      }
    });
  </script>
  {% endblock %}

HATA YONETIMI:
  - Chart data bos olabilir: {% if chart_data %} kontrolu yap
  - Canvas element bulunamazsa: null check
  - JSON serialization: |safe filter kullan, XSS'e dikkat
```

---

## 8. PERFORMANS STRATEJISI

### 8.1 CSS Performans

```
  - Tailwind JIT: Sadece kullanilan class'lar build edilir
  - Purge: Production build'de kullanilmayan CSS temizlenir
  - Minification: --minify flag ile build
  - Tek CSS dosyasi: Tum stiller styles.css'de birlesir
  - Cache: Django staticfiles hash ile cache-busting
```

### 8.2 JavaScript Performans

```
  - defer attribute: Tum script tag'lerinde
  - CDN: Alpine.js, Flowbite, Chart.js CDN'den
  - No bundle: Bundle olusturma yuku yok
  - Lazy load: Chart.js sadece ihtiyac olan sayfalarda
  - Minimal JS: Cogu interaksiyon Flowbite data-attributes ile
```

### 8.3 Genel Performans

```
  - Server-side rendering: Ilk paint hizli
  - Django template cache: {% cache %} tag ile fragment caching
  - Static file hashing: ManifestStaticFilesStorage
  - Image optimization: WebP format, lazy loading
  - Gzip: Nginx'te gzip compression

  HEDEF METRIKLER:
  LCP (Largest Contentful Paint):  < 2.5s
  FID (First Input Delay):        < 100ms
  CLS (Cumulative Layout Shift):  < 0.1
  TTFB (Time to First Byte):      < 200ms
```

---

## 9. ERISILEBILIRLIK (A11Y)

### 9.1 Temel Kurallar

```
  - Semantic HTML: <nav>, <main>, <article>, <button> vs <div>
  - ARIA attributes: aria-label, aria-expanded, aria-hidden
  - Keyboard navigation: Tab order, focus visible, escape to close
  - Color contrast: WCAG 2.1 AA minimum (4.5:1 text, 3:1 large text)
  - Alt text: Tum gorsellerde anlamli alt text
  - Focus trap: Modal acikken focus modal icinde kalmali
  - Skip link: "Ana icerige atla" linki

ALPINE.JS A11Y PATTERN:

  <div x-data="{ open: false }">
    <button @click="open = !open"
            :aria-expanded="open"
            aria-controls="menu-panel">
      {% trans "Menu" %}
    </button>
    <div id="menu-panel"
         x-show="open"
         role="menu"
         @keydown.escape="open = false">
      <a role="menuitem" href="#">{% trans "Ayarlar" %}</a>
    </div>
  </div>
```

---

## 10. i18n (INTERNATIONALIZATION)

### 10.1 Django i18n Yaklasimi

```
KURAL: UI'da hardcoded string YASAK

  Template:
    {% load i18n %}
    {% trans "Menu Olustur" %}
    {% blocktrans %}Bu islem geri alinamaz.{% endblocktrans %}

  Python:
    from django.utils.translation import gettext_lazy as _
    label = _("Menu Adi")

  JavaScript (template icinde):
    const msg = '{% trans "Basariyla kaydedildi" %}';

  CEVIRI DOSYALARI:
    locale/
    ├── tr/LC_MESSAGES/django.po
    └── en/LC_MESSAGES/django.po

  KOMUTLAR:
    python manage.py makemessages -l tr
    python manage.py compilemessages
```

---

## 11. GELISTIRME WORKFLOW

### 11.1 Gunluk Gelistirme

```
TERMINAL 1 - Django dev server:
  python manage.py runserver

TERMINAL 2 - Tailwind watch:
  npm run watch:css

DEPLOYMENT:
  1. npm run build:css            # Tailwind CSS compile + minify
  2. python manage.py collectstatic --noinput
  3. Deploy (Coolify / PM2 / Gunicorn)

YENI SAYFA EKLEME ADIMLARI:
  1. Django view olustur (views.py)
  2. URL tanimla (urls.py)
  3. Template olustur ({% extends "layouts/admin.html" %})
  4. Gerekiyorsa Alpine.js x-data ekle
  5. i18n string'leri {% trans %} ile sar
  6. Dark mode class'larini ekle (dark:bg-*, dark:text-*)
  7. Responsive breakpoint'leri test et (sm, md, lg)
```

### 11.2 Sik Yapilan Hatalar

```
HATA: Tailwind class'lari calismyor
COZUM: tailwind.config.js content paths'i kontrol et, template path dahil mi?

HATA: Dark mode calismyor
COZUM: darkMode: 'class' ayari var mi? <html> element'e 'dark' class ekleniyor mu?

HATA: Flowbite component'leri calismyor
COZUM: flowbite.min.js yukleniyor mu? Plugin tailwind config'e eklendi mi?

HATA: CSRF token hatasi (403 Forbidden)
COZUM: fetchWithCsrf utility kullan, X-CSRFToken header ekle

HATA: Alpine.js x-data calismyor
COZUM: Alpine CDN script'i defer ile yukleniyor mu? Script sirasi dogru mu?

HATA: Static dosyalar guncellenmiyor
COZUM: python manage.py collectstatic calistir, browser cache temizle
```

---

*Bu dokuman, Auto-Claude agent'in E-Menum projesinin frontend mimarisini anlamasi icin referanstir. Tum frontend implementasyonlari bu dokumanla tutarli olmalidir.*
