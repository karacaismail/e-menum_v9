# E-Menum Component Patterns & Design System

> **Auto-Claude UI/UX Document**
> Django Templates, Tailwind CSS, Alpine.js patterns, accessibility, WCAG compliance.
> Son Guncelleme: 2026-03-16

---

## 1. DESIGN PHILOSOPHY

### 1.1 Core Principles

| Principle | Description | Priority |
|-----------|-------------|----------|
| **Inclusive by Default** | Accessible to all: elderly, children, disabled users | P0 |
| **Clarity over Cleverness** | Comprehension always before creativity | P0 |
| **Brand Flexibility** | Each restaurant should reflect its own identity | P1 |
| **Performance First** | Fast loading, smooth interactions | P1 |
| **Delightful Details** | Micro-interactions for a professional feel | P2 |

### 1.2 User Spectrum

| Group | Needs |
|-------|-------|
| Children (8-12) | Touch-friendly, playful, simple navigation |
| Teens (13-19) | Modern, fast, social-ready |
| Adults (20-50) | Efficient, professional, comprehensive |
| Seniors (50+) | Large text, high contrast, clear hierarchy |
| Color blindness | Not relying on color alone, patterns + icons |
| Low vision | High contrast mode, screen reader support |
| Motor impairment | Large touch targets (min 48px), no hover-only actions |

---

## 2. FRONTEND STACK

### 2.1 Technology Overview

```yaml
Templates:      Django Templates ({% extends %}, {% block %}, {% include %})
CSS:            Tailwind CSS 3.4 (dark mode via class strategy)
Interactivity:  Alpine.js 3.x (x-data, x-show, x-on, x-ref)
Components:     Flowbite (modals, dropdowns, tabs, toasts)
Icons:          Phosphor Icons (ph ph-icon-name)
Charts:         Chart.js
i18n:           Django {% trans %} / {% blocktrans %}
```

### 2.2 Template Structure

```
templates/
├── layouts/
│   ├── base.html              # Root layout: Alpine.js, Tailwind, dark mode toggle
│   ├── panel.html             # Restaurant owner portal (sidebar + topbar)
│   └── marketing.html         # Public marketing pages
├── partials/
│   ├── _sidebar.html          # Navigation sidebar
│   ├── _topbar.html           # Top navigation bar
│   └── _notification_widget.html
├── components/                # Reusable UI components ({% include %})
├── accounts/                  # Restaurant owner portal pages
├── admin/                     # Superadmin panel pages
└── public/                    # Public-facing pages (menu viewer)
```

### 2.3 Template Conventions

```html
{# RULE: Always extend a layout #}
{% extends "layouts/panel.html" %}
{% load i18n %}

{% block title %}{% trans "Dashboard" %}{% endblock %}

{% block content %}
  {# RULE: Use {% include %} for reusable components #}
  {% include "components/stat_card.html" with title=total_orders icon="ph-receipt" %}

  {# RULE: Never use hardcoded strings #}
  <h1>{% trans "Siparis Yonetimi" %}</h1>

  {# RULE: Alpine.js for client-side interactivity #}
  <div x-data="{ open: false }">
    <button @click="open = !open">{% trans "Filtrele" %}</button>
    <div x-show="open" x-transition>
      {% include "components/filter_panel.html" %}
    </div>
  </div>
{% endblock %}
```

---

## 3. DESIGN TOKENS

### 3.1 Color Palette

| Token | Value | Usage |
|-------|-------|-------|
| **Primary Teal** | `#1A6B5A` | Buttons, links, active states |
| Primary Light | `#23896F` | Hover states |
| Primary Dark | `#145648` | Active/pressed states |
| Primary Subtle | `#E8F5F1` | Backgrounds, badges |
| **Accent Amber** | `#F5A623` | Highlights, CTAs, warnings |
| Accent Light | `#F7B84E` | Hover |
| Accent Dark | `#D4901A` | Active |

### 3.2 Semantic Colors

| Role | Color | Background | Icon |
|------|-------|------------|------|
| Success | `#059669` | `#D1FAE5` | `ph-check-circle` |
| Warning | `#D97706` | `#FEF3C7` | `ph-warning` |
| Error | `#DC2626` | `#FEE2E2` | `ph-x-circle` |
| Info | `#2563EB` | `#DBEAFE` | `ph-info` |

### 3.3 Tailwind Configuration (tailwind.config.js)

```javascript
module.exports = {
  darkMode: 'class',  // Toggle via .dark class on <html>
  theme: {
    extend: {
      colors: {
        primary: {
          50:  '#E8F5F1',
          100: '#C5E8DE',
          200: '#9DD8C8',
          300: '#6EC4AE',
          400: '#3DAF92',
          500: '#1A6B5A',  // DEFAULT
          600: '#165C4D',
          700: '#145648',
          800: '#0F4038',
          900: '#0A2B25',
        },
        accent: {
          50:  '#FEF7E8',
          400: '#F7B84E',
          500: '#F5A623',  // DEFAULT
          600: '#D4901A',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        heading: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
      },
    },
  },
};
```

### 3.4 Dark Mode

```html
{# base.html: Dark mode toggle with Alpine.js #}
<html x-data="{ darkMode: localStorage.getItem('darkMode') === 'true' }"
      :class="{ 'dark': darkMode }">
<head>
  <script>
    // Prevent FOUC: apply dark mode before render
    if (localStorage.getItem('darkMode') === 'true') {
      document.documentElement.classList.add('dark');
    }
  </script>
</head>
<body class="bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100">
  {# Toggle button #}
  <button @click="darkMode = !darkMode; localStorage.setItem('darkMode', darkMode)"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          aria-label="{% trans 'Karanlik modu degistir' %}">
    <i class="ph" :class="darkMode ? 'ph-sun' : 'ph-moon'" aria-hidden="true"></i>
  </button>
</body>
</html>
```

---

## 4. TYPOGRAPHY

### 4.1 Font Stack

| Role | Font | Tailwind Class |
|------|------|----------------|
| Body | Inter | `font-sans` |
| Headings | Plus Jakarta Sans | `font-heading` |
| Monospace (prices, codes) | JetBrains Mono | `font-mono` |

### 4.2 Type Scale

| Token | Size | Line Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| `text-xs` | 12px | 1.5 | 400 | Captions, badges |
| `text-sm` | 14px | 1.5 | 400 | Secondary text |
| `text-base` | 16px | 1.6 | 400 | Body text (default) |
| `text-lg` | 18px | 1.6 | 400 | Lead paragraphs |
| `text-xl` | 20px | 1.5 | 500 | Card titles |
| `text-2xl` | 24px | 1.4 | 600 | Section headings |
| `text-3xl` | 30px | 1.3 | 700 | Page titles |
| `text-4xl` | 36px | 1.2 | 700 | Hero headlines |

### 4.3 Readability Rules

```
Line Length:   max-w-prose (65ch optimal)
Line Height:   Body 1.5-1.7, Headings 1.2-1.4
Letter Spacing: Headings -0.02em, ALL CAPS 0.05em
Paragraph Gap:  space-y-4 between paragraphs
```

---

## 5. LAYOUT SYSTEM

### 5.1 Panel Layout (panel.html)

```html
{# layouts/panel.html #}
{% extends "layouts/base.html" %}

<div class="flex h-screen overflow-hidden">
  {# Sidebar: fixed on desktop, drawer on mobile #}
  {% include "partials/_sidebar.html" %}

  {# Main content area #}
  <div class="flex-1 flex flex-col overflow-hidden">
    {% include "partials/_topbar.html" %}

    <main class="flex-1 overflow-y-auto p-4 lg:p-6">
      {% block content %}{% endblock %}
    </main>
  </div>
</div>
```

### 5.2 Responsive Breakpoints (Tailwind defaults)

| Prefix | Min Width | Target |
|--------|-----------|--------|
| (none) | 0px | Mobile (default) |
| `sm:` | 640px | Large phones landscape |
| `md:` | 768px | Tablets |
| `lg:` | 1024px | Desktop |
| `xl:` | 1280px | Large desktop |
| `2xl:` | 1536px | Ultra wide |

### 5.3 Touch Target Requirements

```
Minimum:      44 x 44 px (WCAG 2.5.5)
Recommended:  48 x 48 px
Senior mode:  56 x 56 px
Gap between:  min 8px
```

---

## 6. COMPONENT PATTERNS

### 6.1 Buttons

```html
{# components/button.html #}
{# Usage: {% include "components/button.html" with variant="primary" label="Kaydet" %} #}

{# PRIMARY #}
<button class="inline-flex items-center gap-2 px-5 py-2.5
               bg-primary-500 text-white rounded-lg
               hover:bg-primary-600 focus:ring-4 focus:ring-primary-200
               dark:focus:ring-primary-800
               disabled:opacity-50 disabled:cursor-not-allowed
               transition-colors duration-150">
  <i class="ph ph-floppy-disk" aria-hidden="true"></i>
  {% trans "Kaydet" %}
</button>

{# SECONDARY (outlined) #}
<button class="inline-flex items-center gap-2 px-5 py-2.5
               border border-primary-500 text-primary-500 rounded-lg
               hover:bg-primary-50 dark:hover:bg-primary-900
               focus:ring-4 focus:ring-primary-200">
  {% trans "Iptal" %}
</button>

{# DANGER #}
<button class="inline-flex items-center gap-2 px-5 py-2.5
               bg-red-600 text-white rounded-lg
               hover:bg-red-700 focus:ring-4 focus:ring-red-200">
  <i class="ph ph-trash" aria-hidden="true"></i>
  {% trans "Sil" %}
</button>

{# LOADING STATE with Alpine.js #}
<button x-data="{ loading: false }"
        @click="loading = true"
        :disabled="loading"
        class="inline-flex items-center gap-2 px-5 py-2.5
               bg-primary-500 text-white rounded-lg">
  <svg x-show="loading" class="animate-spin h-4 w-4" viewBox="0 0 24 24"
       aria-hidden="true">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
            stroke-width="4" fill="none"/>
    <path class="opacity-75" fill="currentColor"
          d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
  </svg>
  <span x-text="loading ? '{% trans "Yukleniyor..." %}' : '{% trans "Kaydet" %}'"></span>
</button>
```

**Button Sizes:**

| Size | Height | Padding | Font | Tailwind |
|------|--------|---------|------|----------|
| xs | 28px | `px-3 py-1` | `text-xs` | Small inline actions |
| sm | 36px | `px-4 py-2` | `text-sm` | Compact UI |
| md | 44px | `px-5 py-2.5` | `text-sm` | Default |
| lg | 52px | `px-6 py-3` | `text-base` | Prominent actions |

### 6.2 Form Inputs

```html
{# components/form_input.html #}
{# Usage: {% include "components/form_input.html" with field=form.email %} #}

<div class="mb-4">
  <label for="{{ field.id_for_label }}"
         class="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
    {{ field.label }}
    {% if field.field.required %}
      <span class="text-red-500" aria-hidden="true">*</span>
    {% endif %}
  </label>

  <input type="{{ field.field.widget.input_type }}"
         id="{{ field.id_for_label }}"
         name="{{ field.html_name }}"
         value="{{ field.value|default:'' }}"
         {% if field.field.required %}aria-required="true"{% endif %}
         {% if field.errors %}aria-invalid="true" aria-describedby="{{ field.id_for_label }}-error"{% endif %}
         class="block w-full px-4 py-2.5 rounded-lg border
                text-gray-900 dark:text-white
                bg-white dark:bg-gray-700
                border-gray-300 dark:border-gray-600
                focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                {% if field.errors %}border-red-500 focus:ring-red-500{% endif %}
                placeholder-gray-400 dark:placeholder-gray-500">

  {% if field.help_text %}
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ field.help_text }}</p>
  {% endif %}

  {% if field.errors %}
    <p id="{{ field.id_for_label }}-error"
       class="mt-1 text-sm text-red-600 dark:text-red-400 flex items-center gap-1"
       role="alert">
      <i class="ph ph-warning-circle" aria-hidden="true"></i>
      {{ field.errors.0 }}
    </p>
  {% endif %}
</div>
```

**Validation States:**

| State | Border | Ring | Icon |
|-------|--------|------|------|
| Default | `border-gray-300` | none | none |
| Focus | `border-primary-500` | `ring-primary-500` | none |
| Valid | `border-green-500` | `ring-green-500` | `ph-check-circle` |
| Invalid | `border-red-500` | `ring-red-500` | `ph-warning-circle` |
| Disabled | `border-gray-200 bg-gray-100` | none | none |

### 6.3 Cards

```html
{# components/stat_card.html #}
{# Usage: {% include "components/stat_card.html" with title="Siparisler" value="142" icon="ph-receipt" %} #}

<div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200
            dark:border-gray-700 p-5 hover:shadow-md transition-shadow">
  <div class="flex items-center justify-between mb-3">
    <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ title }}</span>
    <div class="w-10 h-10 rounded-lg bg-primary-50 dark:bg-primary-900/30
                flex items-center justify-center">
      <i class="ph {{ icon }} text-xl text-primary-500" aria-hidden="true"></i>
    </div>
  </div>
  <p class="text-2xl font-bold font-heading text-gray-900 dark:text-white">{{ value }}</p>
  {% if change %}
    <p class="mt-1 text-sm {% if change > 0 %}text-green-600{% else %}text-red-600{% endif %}">
      <i class="ph {% if change > 0 %}ph-arrow-up{% else %}ph-arrow-down{% endif %}"
         aria-hidden="true"></i>
      {{ change }}% {% trans "gecen haftaya gore" %}
    </p>
  {% endif %}
</div>

{# PRODUCT CARD (Menu Item) #}
<div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200
            dark:border-gray-700 overflow-hidden group">
  <div class="relative aspect-[4/3] overflow-hidden">
    <img src="{{ product.image_url }}" alt="{{ product.name }}"
         class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
         loading="lazy">
    {% if product.badges %}
      <div class="absolute top-2 right-2 flex gap-1">
        {% for badge in product.badges %}
          <span class="px-2 py-0.5 text-xs font-medium rounded-full
                       bg-primary-500 text-white">{{ badge }}</span>
        {% endfor %}
      </div>
    {% endif %}
  </div>
  <div class="p-4">
    <div class="flex justify-between items-start mb-2">
      <h3 class="font-heading font-semibold text-gray-900 dark:text-white">{{ product.name }}</h3>
      <span class="font-mono font-bold text-primary-500">{{ product.price }}</span>
    </div>
    <p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">{{ product.description }}</p>
  </div>
</div>
```

### 6.4 Modals (Flowbite + Alpine.js)

```html
{# components/modal.html #}
<div x-data="{ open: false }" @open-modal.window="open = true">
  {# Trigger #}
  <button @click="open = true" class="btn-primary">
    {% trans "Yeni Ekle" %}
  </button>

  {# Modal backdrop + content #}
  <div x-show="open"
       x-transition:enter="transition ease-out duration-300"
       x-transition:enter-start="opacity-0"
       x-transition:enter-end="opacity-100"
       x-transition:leave="transition ease-in duration-200"
       x-transition:leave-start="opacity-100"
       x-transition:leave-end="opacity-0"
       class="fixed inset-0 z-50 flex items-center justify-center p-4"
       @keydown.escape.window="open = false"
       role="dialog" aria-modal="true" aria-labelledby="modal-title">

    {# Overlay #}
    <div class="fixed inset-0 bg-black/50" @click="open = false" aria-hidden="true"></div>

    {# Panel #}
    <div x-show="open"
         x-transition:enter="transition ease-out duration-300"
         x-transition:enter-start="opacity-0 scale-95"
         x-transition:enter-end="opacity-100 scale-100"
         class="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl
                w-full max-w-lg max-h-[90vh] overflow-y-auto">

      {# Header #}
      <div class="flex items-center justify-between p-5 border-b dark:border-gray-700">
        <h3 id="modal-title" class="text-lg font-heading font-semibold
                                     text-gray-900 dark:text-white">
          {% trans "Kategori Ekle" %}
        </h3>
        <button @click="open = false"
                class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                aria-label="{% trans 'Kapat' %}">
          <i class="ph ph-x text-lg" aria-hidden="true"></i>
        </button>
      </div>

      {# Body #}
      <div class="p-5">
        {% block modal_body %}{% endblock %}
      </div>

      {# Footer #}
      <div class="flex justify-end gap-3 p-5 border-t dark:border-gray-700">
        <button @click="open = false"
                class="px-5 py-2.5 text-sm text-gray-700 dark:text-gray-300
                       border border-gray-300 dark:border-gray-600 rounded-lg
                       hover:bg-gray-50 dark:hover:bg-gray-700">
          {% trans "Iptal" %}
        </button>
        <button class="px-5 py-2.5 text-sm text-white bg-primary-500
                       rounded-lg hover:bg-primary-600 focus:ring-4 focus:ring-primary-200">
          {% trans "Kaydet" %}
        </button>
      </div>
    </div>
  </div>
</div>
```

### 6.5 Toast Notifications

```html
{# components/toast.html - include in base.html #}
<div x-data="toastManager()" class="fixed top-4 right-4 z-50 space-y-2">
  <template x-for="toast in toasts" :key="toast.id">
    <div x-show="toast.visible"
         x-transition:enter="transition ease-out duration-300"
         x-transition:enter-start="opacity-0 translate-x-8"
         x-transition:enter-end="opacity-100 translate-x-0"
         x-transition:leave="transition ease-in duration-200"
         x-transition:leave-start="opacity-100"
         x-transition:leave-end="opacity-0"
         :class="{
           'bg-green-50 dark:bg-green-900/30 border-green-500': toast.type === 'success',
           'bg-red-50 dark:bg-red-900/30 border-red-500': toast.type === 'error',
           'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-500': toast.type === 'warning',
           'bg-blue-50 dark:bg-blue-900/30 border-blue-500': toast.type === 'info'
         }"
         class="flex items-center gap-3 px-4 py-3 rounded-lg border-l-4 shadow-lg
                bg-white dark:bg-gray-800 min-w-[320px] max-w-md"
         role="alert" aria-live="polite">
      <i class="ph text-xl"
         :class="{
           'ph-check-circle text-green-600': toast.type === 'success',
           'ph-x-circle text-red-600': toast.type === 'error',
           'ph-warning text-yellow-600': toast.type === 'warning',
           'ph-info text-blue-600': toast.type === 'info'
         }" aria-hidden="true"></i>
      <p class="flex-1 text-sm text-gray-700 dark:text-gray-200" x-text="toast.message"></p>
      <button @click="dismiss(toast.id)"
              class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
              aria-label="{% trans 'Kapat' %}">
        <i class="ph ph-x text-sm" aria-hidden="true"></i>
      </button>
    </div>
  </template>
</div>

<script>
function toastManager() {
  return {
    toasts: [],
    add(type, message, duration = 5000) {
      const id = Date.now();
      this.toasts.push({ id, type, message, visible: true });
      if (type !== 'error') {
        setTimeout(() => this.dismiss(id), duration);
      }
    },
    dismiss(id) {
      const toast = this.toasts.find(t => t.id === id);
      if (toast) toast.visible = false;
      setTimeout(() => { this.toasts = this.toasts.filter(t => t.id !== id); }, 300);
    }
  };
}
</script>
```

### 6.6 Data Tables

```html
{# components/data_table.html #}
<div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border
            border-gray-200 dark:border-gray-700 overflow-hidden">

  {# Table toolbar #}
  <div class="flex flex-col sm:flex-row items-start sm:items-center
              justify-between gap-3 p-4 border-b dark:border-gray-700">
    <div class="relative w-full sm:w-72">
      <i class="ph ph-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2
                text-gray-400" aria-hidden="true"></i>
      <input type="search" placeholder="{% trans 'Ara...' %}"
             class="w-full pl-10 pr-4 py-2 text-sm border border-gray-300
                    dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700
                    focus:ring-2 focus:ring-primary-500">
    </div>
    <div class="flex gap-2">
      <button class="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600
                     rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
        <i class="ph ph-funnel mr-1" aria-hidden="true"></i>
        {% trans "Filtrele" %}
      </button>
      <button class="px-4 py-2 text-sm bg-primary-500 text-white rounded-lg
                     hover:bg-primary-600">
        <i class="ph ph-plus mr-1" aria-hidden="true"></i>
        {% trans "Yeni Ekle" %}
      </button>
    </div>
  </div>

  {# Table #}
  <div class="overflow-x-auto">
    <table class="w-full text-sm text-left">
      <thead class="text-xs uppercase text-gray-500 dark:text-gray-400
                    bg-gray-50 dark:bg-gray-700/50">
        <tr>
          <th scope="col" class="px-4 py-3">{% trans "Isim" %}</th>
          <th scope="col" class="px-4 py-3">{% trans "Durum" %}</th>
          <th scope="col" class="px-4 py-3 text-right">{% trans "Islemler" %}</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
        {% for item in items %}
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
          <td class="px-4 py-3 font-medium text-gray-900 dark:text-white">{{ item.name }}</td>
          <td class="px-4 py-3">
            {% include "components/badge.html" with status=item.status %}
          </td>
          <td class="px-4 py-3 text-right">
            {% include "components/row_actions.html" with item=item %}
          </td>
        </tr>
        {% empty %}
        <tr>
          <td colspan="3" class="px-4 py-12 text-center text-gray-500">
            {% include "components/empty_state.html" with message="Henuz kayit yok" %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  {# Pagination #}
  {% if is_paginated %}
    {% include "components/pagination.html" with page_obj=page_obj %}
  {% endif %}
</div>
```

### 6.7 Sidebar Navigation

```html
{# partials/_sidebar.html #}
<aside x-data="{ collapsed: window.innerWidth < 1024, mobileOpen: false }"
       @toggle-sidebar.window="mobileOpen = !mobileOpen"
       :class="collapsed ? 'w-16' : 'w-64'"
       class="hidden lg:flex flex-col h-screen bg-white dark:bg-gray-800
              border-r border-gray-200 dark:border-gray-700 transition-all duration-300">

  {# Logo #}
  <div class="flex items-center h-16 px-4 border-b dark:border-gray-700">
    <img src="{% static 'images/logo.svg' %}" alt="E-Menum" class="h-8">
    <span x-show="!collapsed" class="ml-3 font-heading font-bold text-primary-500">
      E-Menum
    </span>
  </div>

  {# Navigation items #}
  <nav class="flex-1 overflow-y-auto py-4" aria-label="{% trans 'Ana navigasyon' %}">
    {% for item in nav_items %}
    <a href="{{ item.url }}"
       class="flex items-center gap-3 px-4 py-2.5 mx-2 rounded-lg
              text-sm font-medium transition-colors
              {% if item.active %}
                bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400
              {% else %}
                text-gray-600 dark:text-gray-400
                hover:bg-gray-100 dark:hover:bg-gray-700
              {% endif %}"
       {% if item.active %}aria-current="page"{% endif %}>
      <i class="ph {{ item.icon }} text-xl" aria-hidden="true"></i>
      <span x-show="!collapsed">{{ item.label }}</span>
      {% if item.badge %}
        <span x-show="!collapsed"
              class="ml-auto px-2 py-0.5 text-xs rounded-full
                     bg-red-100 text-red-600 dark:bg-red-900/50 dark:text-red-400">
          {{ item.badge }}
        </span>
      {% endif %}
    </a>
    {% endfor %}
  </nav>

  {# Collapse toggle #}
  <button @click="collapsed = !collapsed"
          class="hidden lg:flex items-center justify-center h-12 border-t
                 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
          aria-label="{% trans 'Kenar cubugunu daralt' %}">
    <i class="ph text-lg" :class="collapsed ? 'ph-caret-right' : 'ph-caret-left'"
       aria-hidden="true"></i>
  </button>
</aside>
```

---

## 7. CHARTS (Chart.js)

### 7.1 Chart Container Pattern

```html
{# components/chart_card.html #}
<div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border
            border-gray-200 dark:border-gray-700 p-5">
  <div class="flex items-center justify-between mb-4">
    <h3 class="font-heading font-semibold text-gray-900 dark:text-white">
      {% trans "Haftalik Satis" %}
    </h3>
    <div x-data="{ period: '7d' }" class="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5">
      <button @click="period = '7d'" :class="period === '7d' ? 'bg-white dark:bg-gray-600 shadow-sm' : ''"
              class="px-3 py-1 text-xs rounded-md transition-colors">7G</button>
      <button @click="period = '30d'" :class="period === '30d' ? 'bg-white dark:bg-gray-600 shadow-sm' : ''"
              class="px-3 py-1 text-xs rounded-md transition-colors">30G</button>
    </div>
  </div>
  <div class="relative h-64">
    <canvas id="salesChart" role="img" aria-label="{% trans 'Haftalik satis grafigi' %}"></canvas>
  </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
  const isDark = document.documentElement.classList.contains('dark');
  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
  const textColor = isDark ? '#9CA3AF' : '#6B7280';

  new Chart(document.getElementById('salesChart'), {
    type: 'line',
    data: {
      labels: {{ chart_labels|safe }},
      datasets: [{
        label: '{% trans "Satis" %}',
        data: {{ chart_data|safe }},
        borderColor: '#1A6B5A',
        backgroundColor: 'rgba(26, 107, 90, 0.1)',
        fill: true,
        tension: 0.3,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: textColor } },
        y: { grid: { color: gridColor }, ticks: { color: textColor } }
      }
    }
  });
});
</script>
```

### 7.2 Chart Color Palette

| Use | Color | Hex |
|-----|-------|-----|
| Primary series | Teal | `#1A6B5A` |
| Secondary series | Amber | `#F5A623` |
| Tertiary series | Blue | `#3B82F6` |
| Quaternary series | Purple | `#8B5CF6` |
| Grid lines (light) | Gray | `rgba(0,0,0,0.06)` |
| Grid lines (dark) | Gray | `rgba(255,255,255,0.06)` |

---

## 8. FEEDBACK & STATES

### 8.1 Loading States

```html
{# Skeleton loader #}
<div class="animate-pulse space-y-3">
  <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
  <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
  <div class="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
</div>

{# Inline spinner #}
<div role="status" aria-live="polite" class="flex items-center gap-2">
  <svg class="animate-spin h-5 w-5 text-primary-500" viewBox="0 0 24 24" aria-hidden="true">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
            stroke-width="4" fill="none"/>
    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
  </svg>
  <span class="text-sm text-gray-500">{% trans "Yukleniyor..." %}</span>
</div>
```

### 8.2 Empty States

```html
{# components/empty_state.html #}
<div class="flex flex-col items-center justify-center py-12 px-4 text-center">
  <div class="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-700
              flex items-center justify-center mb-4">
    <i class="ph {{ icon|default:'ph-tray' }} text-3xl text-gray-400" aria-hidden="true"></i>
  </div>
  <h3 class="text-lg font-heading font-semibold text-gray-900 dark:text-white mb-1">
    {{ title|default:"Henuz kayit yok" }}
  </h3>
  <p class="text-sm text-gray-500 dark:text-gray-400 max-w-sm mb-4">
    {{ message|default:"Yeni bir kayit ekleyerek baslayabilirsiniz." }}
  </p>
  {% if action_url %}
    <a href="{{ action_url }}"
       class="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-500 text-white
              rounded-lg hover:bg-primary-600 text-sm">
      <i class="ph ph-plus" aria-hidden="true"></i>
      {{ action_label|default:"Yeni Ekle" }}
    </a>
  {% endif %}
</div>
```

### 8.3 Error Pages

```html
{# templates/errors/404.html #}
{% extends "layouts/base.html" %}
{% load i18n %}

{% block content %}
<div class="min-h-screen flex items-center justify-center px-4">
  <div class="text-center">
    <p class="text-6xl font-heading font-bold text-primary-500 mb-4">404</p>
    <h1 class="text-2xl font-heading font-bold text-gray-900 dark:text-white mb-2">
      {% trans "Sayfa Bulunamadi" %}
    </h1>
    <p class="text-gray-500 dark:text-gray-400 mb-8">
      {% trans "Aradiginiz sayfa mevcut degil veya tasindi." %}
    </p>
    <a href="{% url 'home' %}"
       class="inline-flex items-center gap-2 px-6 py-3 bg-primary-500
              text-white rounded-lg hover:bg-primary-600">
      <i class="ph ph-house" aria-hidden="true"></i>
      {% trans "Ana Sayfaya Don" %}
    </a>
  </div>
</div>
{% endblock %}
```

---

## 9. ACCESSIBILITY (WCAG 2.1 AA)

### 9.1 Screen Reader Support

```html
{# Skip link (first element in base.html) #}
<a href="#main-content"
   class="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2
          focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-500 focus:text-white
          focus:rounded-lg">
  {% trans "Ana iceriğe gec" %}
</a>

{# ARIA landmarks #}
<header role="banner">
  <nav role="navigation" aria-label="{% trans 'Ana menu' %}"></nav>
</header>
<main id="main-content" role="main"></main>
<footer role="contentinfo"></footer>

{# Live region for dynamic updates #}
<div aria-live="polite" aria-atomic="true" class="sr-only" id="live-region"></div>

{# Accessible icon buttons #}
<button aria-label="{% trans 'Sepete ekle' %}"
        class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
  <i class="ph ph-shopping-cart text-xl" aria-hidden="true"></i>
</button>
```

### 9.2 Color Contrast Requirements

| Element | Minimum Ratio | WCAG Level |
|---------|---------------|------------|
| Body text | 4.5:1 | AA |
| Large text (18px+) | 3:1 | AA |
| UI components | 3:1 | AA |
| Focus indicators | 3:1 | AA |

### 9.3 Focus Management

```css
/* Visible focus rings via Tailwind */
/* All interactive elements must use focus:ring-2 or focus:outline */
.focus-ring {
  @apply focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
         dark:focus:ring-offset-gray-900;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 10. ANIMATION & MOTION

### 10.1 Transition Durations

| Duration | Use Case | Tailwind |
|----------|----------|----------|
| 100ms | Button hover, focus ring | `duration-100` |
| 150ms | Toggle switches, checkboxes | `duration-150` |
| 200ms | Tooltips, small reveals | `duration-200` |
| 300ms | Modals, dropdowns, menus | `duration-300` |
| 500ms | Page transitions | `duration-500` |

### 10.2 Alpine.js Transitions

```html
{# Standard fade + slide pattern #}
<div x-show="open"
     x-transition:enter="transition ease-out duration-200"
     x-transition:enter-start="opacity-0 -translate-y-1"
     x-transition:enter-end="opacity-100 translate-y-0"
     x-transition:leave="transition ease-in duration-150"
     x-transition:leave-start="opacity-100 translate-y-0"
     x-transition:leave-end="opacity-0 -translate-y-1">
  {# Content #}
</div>
```

---

## 11. IMPLEMENTATION CHECKLIST

### 11.1 New Component Checklist

```
TEMPLATE:
[ ] Uses {% extends %} or {% include %} properly
[ ] All strings wrapped in {% trans %}
[ ] Follows naming: components/component_name.html
[ ] Context variables documented in comment header

STYLING:
[ ] Uses Tailwind utility classes (no custom CSS unless necessary)
[ ] Dark mode classes (dark:) applied
[ ] Responsive breakpoints (sm:, md:, lg:) tested
[ ] Uses design tokens (primary-500, accent-500, font-heading)

ACCESSIBILITY:
[ ] Keyboard navigable (tab order, enter/space activation)
[ ] ARIA attributes correct (aria-label, aria-describedby, role)
[ ] Focus ring visible (focus:ring-2)
[ ] Color contrast >= 4.5:1
[ ] Screen reader tested

INTERACTIVITY:
[ ] Alpine.js for client state (x-data, x-show, x-on)
[ ] Transitions use x-transition
[ ] Loading states handled
[ ] Error states handled

STATES:
[ ] Default, hover, focus, active, disabled
[ ] Loading state with spinner/skeleton
[ ] Error state with message
[ ] Empty state with CTA
```

### 11.2 Pre-Launch Audit

```
AUTOMATED:
[ ] Lighthouse accessibility score > 90
[ ] HTML validation passes
[ ] No console errors in production build

MANUAL:
[ ] Keyboard-only navigation complete
[ ] Screen reader testing (VoiceOver)
[ ] Zoom to 200% without horizontal scroll
[ ] Dark mode all pages verified
[ ] Mobile, tablet, desktop tested
[ ] Touch targets >= 48px measured
```

---

*Bu dokuman, E-Menum UI/UX standartlarini tanimlar. Tum arayuz gelistirmeleri bu kurallara uygun olmalidir.*
