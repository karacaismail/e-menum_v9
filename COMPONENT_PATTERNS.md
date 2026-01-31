# E-Menum Component Patterns & Design System

> **Auto-Claude UI/UX Document**  
> Accessibility, estetik standartlar, WCAG uyumluluğu, marka uyarlama, UX akışları.  
> Son Güncelleme: 2026-01-31

---

## 1. DESIGN PHILOSOPHY

### 1.1 Core Principles

| Principle | Description | Priority |
|-----------|-------------|----------|
| **Inclusive by Default** | Herkes için erişilebilir: yaşlılar, çocuklar, engelliler | P0 |
| **Clarity over Cleverness** | Anlaşılırlık her zaman yaratıcılıktan önce gelir | P0 |
| **Brand Flexibility** | Her işletmenin kimliğini yansıtabilmeli | P1 |
| **Performance First** | Hızlı yükleme, akıcı etkileşim | P1 |
| **Delightful Details** | Mikro-etkileşimler ile profesyonel his | P2 |

### 1.2 User Spectrum

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TARGET USER SPECTRUM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AGE GROUPS:                                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Children (8-12)     │  Touch-friendly, playful, simple navigation   │ │
│  │  Teens (13-19)       │  Modern, fast, social-ready                   │ │
│  │  Adults (20-50)      │  Efficient, professional, comprehensive       │ │
│  │  Seniors (50+)       │  Large text, high contrast, clear hierarchy   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  VISUAL ABILITIES:                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Normal vision       │  Standard design baseline                     │ │
│  │  Myopia (Nearsighted)│  Scalable text, zoom support                  │ │
│  │  Hyperopia (Farsighted)│  Larger default text, generous spacing     │ │
│  │  Color blindness     │  Not relying on color alone, patterns        │ │
│  │  Low vision          │  High contrast mode, screen reader support   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  COGNITIVE ABILITIES:                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Dyslexia            │  OpenDyslexic font option, line spacing      │ │
│  │  ADHD                │  Focused UI, minimal distractions            │ │
│  │  Cognitive load      │  Progressive disclosure, chunked info        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  MOTOR ABILITIES:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Limited dexterity   │  Large touch targets (min 48px)              │ │
│  │  Tremors             │  Generous spacing, no hover-only actions     │ │
│  │  One-handed use      │  Thumb-friendly zones                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. ACCESSIBILITY STANDARDS (WCAG 2.1)

### 2.1 Compliance Targets

| Level | Requirement | Status |
|-------|-------------|--------|
| **Level A** | Minimum accessibility | ZORUNLU |
| **Level AA** | Standard compliance | ZORUNLU |
| **Level AAA** | Enhanced accessibility | HEDEFLENİYOR |

### 2.2 WCAG Checklist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WCAG 2.1 COMPLIANCE CHECKLIST                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PERCEIVABLE (Algılanabilir):                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  [x] 1.1.1  Non-text content has text alternatives                   │ │
│  │  [x] 1.2.1  Audio/video has captions or transcripts                  │ │
│  │  [x] 1.3.1  Information conveyed through structure (not just visual) │ │
│  │  [x] 1.3.2  Meaningful sequence preserved                            │ │
│  │  [x] 1.3.3  Instructions don't rely on shape/size/location alone     │ │
│  │  [x] 1.4.1  Color is not only visual means of conveying info         │ │
│  │  [x] 1.4.3  Contrast ratio minimum 4.5:1 (text)                      │ │
│  │  [x] 1.4.4  Text resizable up to 200% without loss                   │ │
│  │  [x] 1.4.5  Images of text avoided (except logos)                    │ │
│  │  [x] 1.4.10 Content reflows at 320px width                           │ │
│  │  [x] 1.4.11 Non-text contrast minimum 3:1                            │ │
│  │  [x] 1.4.12 Text spacing adjustable                                  │ │
│  │  [x] 1.4.13 Hover/focus content dismissible                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  OPERABLE (Kullanılabilir):                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  [x] 2.1.1  All functionality keyboard accessible                    │ │
│  │  [x] 2.1.2  No keyboard trap                                         │ │
│  │  [x] 2.2.1  Timing adjustable                                        │ │
│  │  [x] 2.2.2  Pause/stop/hide for moving content                       │ │
│  │  [x] 2.3.1  No content flashes more than 3 times/second              │ │
│  │  [x] 2.4.1  Skip navigation link provided                            │ │
│  │  [x] 2.4.2  Pages have descriptive titles                            │ │
│  │  [x] 2.4.3  Focus order is logical                                   │ │
│  │  [x] 2.4.4  Link purpose clear from text                             │ │
│  │  [x] 2.4.5  Multiple ways to find pages                              │ │
│  │  [x] 2.4.6  Headings and labels descriptive                          │ │
│  │  [x] 2.4.7  Focus visible                                            │ │
│  │  [x] 2.5.1  Pointer gestures have alternatives                       │ │
│  │  [x] 2.5.2  Pointer actions cancellable                              │ │
│  │  [x] 2.5.3  Label in name matches visible label                      │ │
│  │  [x] 2.5.4  Motion-activated functions have alternatives             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  UNDERSTANDABLE (Anlaşılabilir):                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  [x] 3.1.1  Page language defined                                    │ │
│  │  [x] 3.1.2  Language of parts defined                                │ │
│  │  [x] 3.2.1  Focus doesn't trigger unexpected context change          │ │
│  │  [x] 3.2.2  Input doesn't trigger unexpected context change          │ │
│  │  [x] 3.2.3  Consistent navigation                                    │ │
│  │  [x] 3.2.4  Consistent identification                                │ │
│  │  [x] 3.3.1  Input errors identified                                  │ │
│  │  [x] 3.3.2  Labels or instructions provided                          │ │
│  │  [x] 3.3.3  Error suggestions provided                               │ │
│  │  [x] 3.3.4  Error prevention for legal/financial                     │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ROBUST (Sağlam):                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  [x] 4.1.1  HTML validates                                           │ │
│  │  [x] 4.1.2  Name, role, value for UI components                      │ │
│  │  [x] 4.1.3  Status messages announced                                │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Screen Reader Support

```html
<!-- ARIA Landmarks -->
<header role="banner">
  <nav role="navigation" aria-label="Ana menü">
</header>

<main role="main" id="main-content">
  <section aria-labelledby="menu-heading">
    <h1 id="menu-heading">Menümüz</h1>
  </section>
</main>

<footer role="contentinfo">
</footer>

<!-- Skip Link (ilk element) -->
<a href="#main-content" class="skip-link">
  Ana içeriğe geç
</a>

<!-- Live Regions (dinamik içerik) -->
<div aria-live="polite" aria-atomic="true" class="sr-only">
  <!-- Sepete ekleme, hata mesajları buraya -->
</div>

<!-- Form Labels -->
<label for="table-number">Masa Numarası</label>
<input 
  id="table-number" 
  type="text" 
  aria-describedby="table-help"
  aria-required="true"
>
<span id="table-help" class="help-text">Örnek: A5, B12</span>

<!-- Accessible Icons -->
<button aria-label="Sepete ekle">
  <i class="ph-shopping-cart" aria-hidden="true"></i>
  <span class="sr-only">Sepete ekle</span>
</button>
```

---

## 3. COLOR SYSTEM

### 3.1 Base Palette

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COLOR PALETTE                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SEMANTIC COLORS (Fixed - Theme Independent):                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Success      │ #059669 │ bg: #D1FAE5 │ Contrast: 4.5:1+ │ ✓        │ │
│  │  Warning      │ #D97706 │ bg: #FEF3C7 │ Contrast: 4.5:1+ │ ⚠        │ │
│  │  Error        │ #DC2626 │ bg: #FEE2E2 │ Contrast: 4.5:1+ │ ✕        │ │
│  │  Info         │ #2563EB │ bg: #DBEAFE │ Contrast: 4.5:1+ │ ℹ        │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  NEUTRAL SCALE (Light Mode):                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  neutral-50   │ #FAFAFA │ Background (lightest)                      │ │
│  │  neutral-100  │ #F4F4F5 │ Background (cards)                         │ │
│  │  neutral-200  │ #E4E4E7 │ Borders (subtle)                           │ │
│  │  neutral-300  │ #D4D4D8 │ Borders (visible)                          │ │
│  │  neutral-400  │ #A1A1AA │ Placeholder text                           │ │
│  │  neutral-500  │ #71717A │ Secondary text                             │ │
│  │  neutral-600  │ #52525B │ Body text (muted)                          │ │
│  │  neutral-700  │ #3F3F46 │ Body text                                  │ │
│  │  neutral-800  │ #27272A │ Headlines                                  │ │
│  │  neutral-900  │ #18181B │ Headlines (emphasis)                       │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  NEUTRAL SCALE (Dark Mode):                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  neutral-900  │ #18181B │ Background (darkest)                       │ │
│  │  neutral-800  │ #27272A │ Background (cards)                         │ │
│  │  neutral-700  │ #3F3F46 │ Borders (subtle)                           │ │
│  │  neutral-600  │ #52525B │ Borders (visible)                          │ │
│  │  neutral-500  │ #71717A │ Placeholder text                           │ │
│  │  neutral-400  │ #A1A1AA │ Secondary text                             │ │
│  │  neutral-300  │ #D4D4D8 │ Body text (muted)                          │ │
│  │  neutral-200  │ #E4E4E7 │ Body text                                  │ │
│  │  neutral-100  │ #F4F4F5 │ Headlines                                  │ │
│  │  neutral-50   │ #FAFAFA │ Headlines (emphasis)                       │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Contrast Requirements

| Element | Minimum Ratio | Target Ratio | WCAG Level |
|---------|---------------|--------------|------------|
| Body text | 4.5:1 | 7:1 | AA / AAA |
| Large text (18px+) | 3:1 | 4.5:1 | AA / AAA |
| UI components | 3:1 | 4.5:1 | AA |
| Focus indicators | 3:1 | 4.5:1 | AA |
| Icons (informative) | 3:1 | 4.5:1 | AA |
| Disabled elements | No requirement | - | - |

### 3.3 Color Blindness Support

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COLOR BLINDNESS CONSIDERATIONS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NEVER rely on color alone. Always provide:                                 │
│                                                                             │
│  Status Indicators:                                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ✓ Success  │ Green + Checkmark icon + "Başarılı" text               │ │
│  │  ⚠ Warning  │ Orange + Warning icon + "Dikkat" text                  │ │
│  │  ✕ Error    │ Red + X icon + "Hata" text                             │ │
│  │  ℹ Info     │ Blue + Info icon + descriptive text                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Data Visualization:                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • Use patterns in addition to colors                                │ │
│  │  • Provide data labels directly on charts                            │ │
│  │  • Support high contrast mode                                        │ │
│  │  • Test with color blindness simulators                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Interactive Elements:                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • Links: Underline + color change                                   │ │
│  │  • Buttons: Shape + color + text                                     │ │
│  │  • Form validation: Icon + border + message                          │ │
│  │  • Required fields: Asterisk + color + aria-required                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Color Blindness Types to Test:                                             │
│  ├── Protanopia (red-blind) ~1% male                                       │
│  ├── Deuteranopia (green-blind) ~1% male                                   │
│  ├── Tritanopia (blue-blind) ~0.01%                                        │
│  └── Achromatopsia (total) ~0.003%                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 High Contrast Mode

```css
/* High Contrast Mode Variables */
@media (prefers-contrast: high) {
  :root {
    --text-primary: #000000;
    --text-secondary: #1a1a1a;
    --bg-primary: #ffffff;
    --bg-secondary: #f0f0f0;
    --border-color: #000000;
    --border-width: 2px;
    --focus-outline: 3px solid #000000;
    --link-color: #0000EE;
    --link-visited: #551A8B;
  }
}

/* Windows High Contrast Mode */
@media (forced-colors: active) {
  .button {
    border: 2px solid ButtonText;
    background: ButtonFace;
    color: ButtonText;
  }
  
  .button:focus {
    outline: 3px solid Highlight;
  }
}
```

---

## 4. TYPOGRAPHY

### 4.1 Font Stack

```css
/* Primary Font Stack */
--font-sans: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 
             'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;

/* Monospace (for codes, prices) */
--font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', Consolas, monospace;

/* Dyslexia-Friendly Option */
--font-dyslexic: 'OpenDyslexic', 'Comic Sans MS', cursive;
```

### 4.2 Type Scale

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TYPOGRAPHY SCALE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BASE SIZE: 16px (1rem) - WCAG recommends minimum 16px                     │
│                                                                             │
│  Scale (1.25 ratio - Major Third):                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Token      │ Size    │ Line Height │ Weight │ Usage                 │ │
│  │  ─────────────────────────────────────────────────────────────────── │ │
│  │  text-xs    │ 12px    │ 1.5 (18px)  │ 400    │ Captions, badges     │ │
│  │  text-sm    │ 14px    │ 1.5 (21px)  │ 400    │ Secondary text       │ │
│  │  text-base  │ 16px    │ 1.6 (26px)  │ 400    │ Body text (default)  │ │
│  │  text-lg    │ 18px    │ 1.6 (29px)  │ 400    │ Lead paragraphs      │ │
│  │  text-xl    │ 20px    │ 1.5 (30px)  │ 500    │ Card titles          │ │
│  │  text-2xl   │ 24px    │ 1.4 (34px)  │ 600    │ Section headings     │ │
│  │  text-3xl   │ 30px    │ 1.3 (39px)  │ 700    │ Page titles          │ │
│  │  text-4xl   │ 36px    │ 1.2 (43px)  │ 700    │ Hero headlines       │ │
│  │  text-5xl   │ 48px    │ 1.1 (53px)  │ 800    │ Display              │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  SENIOR/ACCESSIBILITY MODE (125% scale):                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  text-base  │ 20px    │ 1.7 (34px)  │ 400    │ Body text            │ │
│  │  text-lg    │ 22px    │ 1.7 (37px)  │ 400    │ Lead paragraphs      │ │
│  │  text-xl    │ 25px    │ 1.6 (40px)  │ 500    │ Card titles          │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Readability Guidelines

```
TEXT READABILITY RULES:

Line Length:
├── Optimal: 50-75 characters per line
├── Maximum: 80 characters
├── Mobile: Full width okay, but larger text
└── Implementation: max-width: 65ch;

Line Height:
├── Body text: 1.5-1.7 (WCAG 1.4.12 requirement)
├── Headings: 1.2-1.4
├── Small text: 1.5+ (more space for readability)
└── Dyslexia mode: 2.0 (double spacing)

Letter Spacing:
├── Body: normal (0)
├── Headings: -0.02em (tighter for large text)
├── All caps: 0.05em (required for readability)
└── Dyslexia mode: 0.12em (increased)

Word Spacing:
├── Normal: default
└── Dyslexia mode: 0.16em (increased)

Paragraph Spacing:
├── Between paragraphs: 1.5em minimum
├── After headings: 0.5em
└── Before headings: 2em
```

### 4.4 Text Accessibility Features

```html
<!-- User Preferences Panel -->
<div class="accessibility-panel" role="region" aria-label="Erişilebilirlik ayarları">
  
  <!-- Font Size -->
  <div class="setting-group">
    <label id="font-size-label">Yazı Boyutu</label>
    <div role="group" aria-labelledby="font-size-label">
      <button aria-label="Yazıyı küçült" data-size="decrease">A-</button>
      <span aria-live="polite">%<span id="current-size">100</span></span>
      <button aria-label="Yazıyı büyüt" data-size="increase">A+</button>
    </div>
  </div>
  
  <!-- Font Family -->
  <div class="setting-group">
    <label for="font-family">Yazı Tipi</label>
    <select id="font-family">
      <option value="default">Varsayılan (Inter)</option>
      <option value="dyslexic">Disleksi Dostu (OpenDyslexic)</option>
      <option value="serif">Serifli (Georgia)</option>
    </select>
  </div>
  
  <!-- Line Spacing -->
  <div class="setting-group">
    <label for="line-spacing">Satır Aralığı</label>
    <select id="line-spacing">
      <option value="normal">Normal</option>
      <option value="relaxed">Geniş</option>
      <option value="loose">Çok Geniş</option>
    </select>
  </div>
  
  <!-- High Contrast -->
  <div class="setting-group">
    <label>
      <input type="checkbox" id="high-contrast">
      Yüksek Kontrast Modu
    </label>
  </div>
  
</div>
```

---

## 5. SPACING & LAYOUT

### 5.1 Spacing Scale

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SPACING SCALE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Base Unit: 4px (0.25rem)                                                   │
│                                                                             │
│  Token      │ Value   │ Usage                                               │
│  ────────────────────────────────────────────────────────────────────────── │
│  space-0    │ 0       │ Reset                                               │
│  space-1    │ 4px     │ Inline spacing, icon gaps                           │
│  space-2    │ 8px     │ Tight spacing, form elements                        │
│  space-3    │ 12px    │ Default gap                                         │
│  space-4    │ 16px    │ Card padding, section gap                           │
│  space-5    │ 20px    │ Component spacing                                   │
│  space-6    │ 24px    │ Section padding                                     │
│  space-8    │ 32px    │ Large section gaps                                  │
│  space-10   │ 40px    │ Page sections                                       │
│  space-12   │ 48px    │ Major sections                                      │
│  space-16   │ 64px    │ Page margins                                        │
│  space-20   │ 80px    │ Hero sections                                       │
│  space-24   │ 96px    │ Major breaks                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Touch Target Guidelines

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TOUCH TARGET REQUIREMENTS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WCAG 2.5.5 Target Size (Level AAA):                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Minimum touch target: 44 × 44 px                                    │ │
│  │  Recommended:          48 × 48 px                                    │ │
│  │  Senior/Accessibility: 56 × 56 px                                    │ │
│  │                                                                       │ │
│  │  Spacing between targets: minimum 8px                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  IMPLEMENTATION:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  /* Even small icons get large tap area */                           │ │
│  │  .icon-button {                                                      │ │
│  │    min-width: 48px;                                                  │ │
│  │    min-height: 48px;                                                 │ │
│  │    display: flex;                                                    │ │
│  │    align-items: center;                                              │ │
│  │    justify-content: center;                                          │ │
│  │  }                                                                   │ │
│  │                                                                       │ │
│  │  /* Extend tap area beyond visual bounds */                          │ │
│  │  .link-with-extended-area {                                          │ │
│  │    position: relative;                                               │ │
│  │  }                                                                   │ │
│  │  .link-with-extended-area::before {                                  │ │
│  │    content: '';                                                      │ │
│  │    position: absolute;                                               │ │
│  │    inset: -8px; /* Extends clickable area */                        │ │
│  │  }                                                                   │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  THUMB ZONE (Mobile):                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ┌─────────────────────────┐                                         │ │
│  │  │     HARD TO REACH       │  Top corners                            │ │
│  │  │                         │                                         │ │
│  │  │    OKAY (stretch)       │  Upper middle                           │ │
│  │  │                         │                                         │ │
│  │  │   NATURAL (easy)        │  Bottom 2/3                             │ │
│  │  │                         │                                         │ │
│  │  │ ████ SWEET SPOT ████    │  Bottom center/right                    │ │
│  │  └─────────────────────────┘                                         │ │
│  │                                                                       │ │
│  │  Place primary actions in thumb-friendly zones                       │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Responsive Breakpoints

```css
/* Breakpoint System */
--breakpoint-sm: 640px;   /* Large phones landscape */
--breakpoint-md: 768px;   /* Tablets */
--breakpoint-lg: 1024px;  /* Desktop */
--breakpoint-xl: 1280px;  /* Large desktop */
--breakpoint-2xl: 1536px; /* Ultra wide */

/* Mobile-First Media Queries */
/* Default: < 640px (mobile) */

@media (min-width: 640px) { /* sm: Tablets & up */ }
@media (min-width: 768px) { /* md: Small desktop */ }
@media (min-width: 1024px) { /* lg: Desktop */ }
@media (min-width: 1280px) { /* xl: Large desktop */ }

/* Container Widths */
.container {
  width: 100%;
  margin: 0 auto;
  padding: 0 16px;
}
@media (min-width: 640px) { .container { max-width: 640px; } }
@media (min-width: 768px) { .container { max-width: 768px; } }
@media (min-width: 1024px) { .container { max-width: 1024px; } }
@media (min-width: 1280px) { .container { max-width: 1280px; } }
```

---

## 6. BRAND CUSTOMIZATION SYSTEM

### 6.1 Theming Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BRAND CUSTOMIZATION LAYERS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LAYER 1: Platform Defaults (E-Menum Base)                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • Default colors, typography, spacing                               │ │
│  │  • WCAG-compliant baseline                                           │ │
│  │  • Cannot be broken by customization                                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  LAYER 2: Theme Presets (Restaurant Chooses)                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • Modern Minimal     │ Clean, white, minimal shadows                │ │
│  │  • Classic Elegant    │ Serif fonts, warm tones, refined             │ │
│  │  • Bold Contemporary  │ Strong colors, geometric, energetic          │ │
│  │  • Rustic Natural     │ Earth tones, organic shapes, textured        │ │
│  │  • Dark Luxe          │ Dark backgrounds, gold accents, premium      │ │
│  │  • Playful Casual     │ Rounded, colorful, friendly                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  LAYER 3: Brand Customization (Deep Customization)                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • Primary brand color (auto-generates palette)                      │ │
│  │  • Secondary color                                                   │ │
│  │  • Logo upload (light/dark variants)                                 │ │
│  │  • Custom font (from approved list)                                  │ │
│  │  • Border radius preference                                          │ │
│  │  • Button style preference                                           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  LAYER 4: Advanced (Enterprise Only)                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • Custom CSS injection (validated)                                  │ │
│  │  • Custom favicon                                                    │ │
│  │  • White-label domain                                                │ │
│  │  • Complete color palette override                                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 CSS Custom Properties for Theming

```css
:root {
  /* === BRAND COLORS (Customizable) === */
  --brand-primary: #2563eb;        /* Main brand color */
  --brand-primary-light: #3b82f6;  /* Hover state */
  --brand-primary-dark: #1d4ed8;   /* Active state */
  --brand-primary-subtle: #dbeafe; /* Backgrounds */
  
  --brand-secondary: #7c3aed;
  --brand-accent: #f59e0b;
  
  /* === AUTO-GENERATED FROM PRIMARY === */
  --brand-text-on-primary: #ffffff; /* Calculated for contrast */
  
  /* === SURFACE COLORS === */
  --surface-background: #ffffff;
  --surface-card: #ffffff;
  --surface-elevated: #ffffff;
  --surface-overlay: rgba(0, 0, 0, 0.5);
  
  /* === TEXT COLORS === */
  --text-primary: #18181b;
  --text-secondary: #52525b;
  --text-muted: #a1a1aa;
  --text-inverse: #ffffff;
  
  /* === BORDER & SHADOWS === */
  --border-color: #e4e4e7;
  --border-radius-sm: 4px;
  --border-radius-md: 8px;
  --border-radius-lg: 12px;
  --border-radius-full: 9999px;
  
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  
  /* === TYPOGRAPHY === */
  --font-family-primary: 'Inter', sans-serif;
  --font-family-heading: var(--font-family-primary);
  
  /* === COMPONENT SPECIFIC === */
  --button-radius: var(--border-radius-md);
  --card-radius: var(--border-radius-lg);
  --input-radius: var(--border-radius-md);
}

/* Dark Mode Override */
[data-theme="dark"] {
  --surface-background: #18181b;
  --surface-card: #27272a;
  --surface-elevated: #3f3f46;
  
  --text-primary: #fafafa;
  --text-secondary: #a1a1aa;
  --text-muted: #71717a;
  
  --border-color: #3f3f46;
}

/* High Contrast Override */
[data-contrast="high"] {
  --text-primary: #000000;
  --text-secondary: #1a1a1a;
  --border-color: #000000;
  --border-width: 2px;
}
```

### 6.3 Theme Generator Logic

```
AUTO-PALETTE GENERATION:

Input: Brand Primary Color (#2563eb)

Algorithm:
1. Extract HSL values
2. Generate complementary shades:
   - Light: Increase L by 10%, decrease S by 5%
   - Dark: Decrease L by 10%, increase S by 5%
   - Subtle: L at 95%, S at 30%
   
3. Calculate text color for contrast:
   - If luminance > 0.5: use dark text
   - If luminance < 0.5: use white text

4. Validate WCAG contrast:
   - If fails, adjust until passes
   - Notify user if impossible

5. Generate success/warning/error variants:
   - Blend with semantic colors
   - Maintain recognizability
```

---

## 7. COMPONENT LIBRARY

### 7.1 Button Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BUTTON VARIANTS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HIERARCHY:                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Primary    │ Main CTA, filled, brand color                          │ │
│  │             │ Usage: 1 per screen ideally                            │ │
│  │                                                                       │ │
│  │  Secondary  │ Supporting action, outlined                            │ │
│  │             │ Usage: Secondary options                               │ │
│  │                                                                       │ │
│  │  Tertiary   │ Minimal action, text only                              │ │
│  │             │ Usage: Cancel, less important                          │ │
│  │                                                                       │ │
│  │  Ghost      │ Subtle, transparent                                    │ │
│  │             │ Usage: Toolbars, inline actions                        │ │
│  │                                                                       │ │
│  │  Danger     │ Destructive action, red                                │ │
│  │             │ Usage: Delete, cancel subscription                     │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  SIZES:                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Size   │ Height │ Padding     │ Font Size │ Touch Target           │ │
│  │  ────────────────────────────────────────────────────────────────── │ │
│  │  xs     │ 28px   │ 8px 12px    │ 12px      │ 44px (extended)        │ │
│  │  sm     │ 36px   │ 8px 16px    │ 14px      │ 44px (extended)        │ │
│  │  md     │ 44px   │ 12px 20px   │ 16px      │ 44px (native)          │ │
│  │  lg     │ 52px   │ 16px 24px   │ 18px      │ 52px                   │ │
│  │  xl     │ 60px   │ 20px 32px   │ 20px      │ 60px                   │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  STATES:                                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Default  → Hover → Focus → Active → Disabled                        │ │
│  │                                                                       │ │
│  │  Focus: 2px outline, 2px offset, brand color                         │ │
│  │  Disabled: 50% opacity, cursor: not-allowed                          │ │
│  │  Loading: Spinner + "Yükleniyor..." text                             │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Form Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FORM PATTERNS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT FIELD ANATOMY:                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Label *                                            (Optional)  │ │ │
│  │  │  ─────────────────────────────────────────────────  indicator   │ │ │
│  │  │  ┌───────────────────────────────────────────────────────────┐ │ │ │
│  │  │  │ [icon]  Placeholder text...                      [action] │ │ │ │
│  │  │  └───────────────────────────────────────────────────────────┘ │ │ │
│  │  │  Helper text or error message                                  │ │ │
│  │  │  Character count: 0/100                                        │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  VALIDATION STATES:                                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Default   │ Gray border                                             │ │
│  │  Focus     │ Brand color border + shadow                             │ │
│  │  Valid     │ Green border + checkmark icon                           │ │
│  │  Invalid   │ Red border + error icon + message                       │ │
│  │  Disabled  │ Gray bg, lower opacity                                  │ │
│  │  Read-only │ No border, subtle bg                                    │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ACCESSIBILITY REQUIREMENTS:                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  • Label always visible (no placeholder-only)                        │ │
│  │  • Error messages linked via aria-describedby                        │ │
│  │  • Required fields: aria-required="true" + visual indicator          │ │
│  │  • Error announced: aria-live="polite"                               │ │
│  │  • Input purpose: autocomplete attribute                             │ │
│  │  • Minimum height: 44px                                              │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Card Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CARD PATTERNS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRODUCT CARD (Menu Item):                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │                                                                 │ │ │
│  │  │  [IMAGE - 16:9 or 1:1 ratio]                                   │ │ │
│  │  │                                                                 │ │ │
│  │  │  [Badges: Vegan, Spicy, Chef's Pick - top right]               │ │ │
│  │  │                                                                 │ │ │
│  │  ├─────────────────────────────────────────────────────────────────┤ │ │
│  │  │                                                                 │ │ │
│  │  │  Product Name                                        ₺XX.XX    │ │ │
│  │  │  Short description (max 2 lines)...                            │ │ │
│  │  │                                                                 │ │ │
│  │  │  [Allergen icons] [Prep time: ~15 min]                         │ │ │
│  │  │                                                                 │ │ │
│  │  │                                     [Add to Cart Button]       │ │ │
│  │  │                                                                 │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  │  Accessibility:                                                       │ │
│  │  • Entire card clickable (for details)                               │ │
│  │  • Add button separate focusable element                             │ │
│  │  • Image alt text describes dish                                     │ │
│  │  • Price announced clearly                                           │ │
│  │  • Allergen icons have text alternatives                             │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CARD VARIANTS:                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Elevated   │ Shadow, white background                               │ │
│  │  Outlined   │ Border, no shadow                                      │ │
│  │  Filled     │ Subtle background color                                │ │
│  │  Interactive│ Hover effect, cursor pointer                           │ │
│  │  Compact    │ Horizontal layout, less padding                        │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.4 Navigation Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       NAVIGATION PATTERNS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MOBILE BOTTOM NAVIGATION:                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Position: Fixed bottom                                              │ │
│  │  Height: 64px (safe area aware)                                      │ │
│  │  Max items: 5                                                        │ │
│  │  Touch target: Full width/5                                          │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  [Home]    [Menu]    [Cart(3)]   [Orders]   [Account]          │ │ │
│  │  │   🏠        📋         🛒          📦          👤              │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  │  Active state: Brand color, bold label                               │ │
│  │  Badge: Cart count, notification dot                                 │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CATEGORY TABS (Horizontal Scroll):                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ← [Tümü] [Başlangıçlar] [Ana Yemekler] [Tatlılar] [İçecekler] →     │ │
│  │                                                                       │ │
│  │  • Horizontally scrollable                                           │ │
│  │  • Active tab visually distinct                                      │ │
│  │  • Scroll indicators on edges                                        │ │
│  │  • Keyboard navigable (arrow keys)                                   │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  BREADCRUMBS:                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Ana Sayfa > Menü > Yemekler > Köfte                                 │ │
│  │                                                                       │ │
│  │  • aria-label="Breadcrumb"                                           │ │
│  │  • Current page: aria-current="page"                                 │ │
│  │  • Separator: aria-hidden="true"                                     │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. FEEDBACK & STATES

### 8.1 Loading States

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LOADING PATTERNS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SKELETON SCREENS (Preferred):                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ │ │
│  │  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ │ │
│  │  │                                                                 │ │ │
│  │  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░                        ░░░░░░░░░ │ │ │
│  │  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                     │ │ │
│  │  │                                                                 │ │ │
│  │  │  ░░░░░░░░░░░░░░░░░  ░░░░░░░░░░░░░                              │ │ │
│  │  │                                                                 │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  │  • Matches content layout                                            │ │
│  │  • Subtle pulse animation                                            │ │
│  │  • Reduces perceived wait time                                       │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  SPINNERS (For actions):                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  • Button loading: Replace text with spinner + "Yükleniyor..."       │ │
│  │  • Modal loading: Center spinner with message                        │ │
│  │  • Page transition: Top progress bar                                 │ │
│  │                                                                       │ │
│  │  Accessibility:                                                       │ │
│  │  • role="status"                                                     │ │
│  │  • aria-live="polite"                                                │ │
│  │  • aria-label="Yükleniyor"                                           │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  PROGRESS INDICATORS:                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Determinate:  [████████░░░░░░░░░░] 60%                              │ │
│  │  Indeterminate: [▓▓▓░░░░░░▓▓▓░░░░] (animated)                        │ │
│  │                                                                       │ │
│  │  • role="progressbar"                                                │ │
│  │  • aria-valuenow, aria-valuemin, aria-valuemax                       │ │
│  │  • aria-label describing the process                                 │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Empty States

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EMPTY STATE PATTERNS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STRUCTURE:                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │                         [Illustration]                                │ │
│  │                                                                       │ │
│  │                    Başlık (What's empty)                             │ │
│  │                                                                       │ │
│  │           Açıklama - neden boş, ne yapılabilir                       │ │
│  │                                                                       │ │
│  │                    [Primary Action Button]                            │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  EXAMPLES:                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Empty Cart:                                                         │ │
│  │  • Icon: Shopping cart with dash                                     │ │
│  │  • Title: "Sepetiniz boş"                                           │ │
│  │  • Desc: "Lezzetli yemeklerimizi keşfedin"                          │ │
│  │  • Action: "Menüyü İncele"                                          │ │
│  │                                                                       │ │
│  │  No Search Results:                                                  │ │
│  │  • Icon: Magnifying glass with X                                     │ │
│  │  • Title: "'pizza' için sonuç bulunamadı"                           │ │
│  │  • Desc: "Farklı kelimelerle aramayı deneyin"                       │ │
│  │  • Action: "Filtreleri Temizle"                                     │ │
│  │                                                                       │ │
│  │  No Orders Yet:                                                      │ │
│  │  • Icon: Receipt/order slip                                          │ │
│  │  • Title: "Henüz siparişiniz yok"                                   │ │
│  │  • Desc: "İlk siparişinizi şimdi verin!"                            │ │
│  │  • Action: "Sipariş Ver"                                            │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.3 Error States

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ERROR HANDLING UI                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INLINE ERRORS (Forms):                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  • Appear below field immediately after blur/submit                  │ │
│  │  • Red border + error icon + message                                 │ │
│  │  • Connected via aria-describedby                                    │ │
│  │  • Clear when user starts fixing                                     │ │
│  │                                                                       │ │
│  │  Example:                                                            │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  E-posta *                                                      │ │ │
│  │  │  ┌───────────────────────────────────────────────────────────┐ │ │ │
│  │  │  │ invalid@email                                      [!]   │ │ │ │
│  │  │  └───────────────────────────────────────────────────────────┘ │ │ │
│  │  │  ⚠ Geçerli bir e-posta adresi girin                           │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  TOAST NOTIFICATIONS:                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Position: Top-center (mobile), top-right (desktop)                  │ │
│  │  Duration: 5 seconds (errors persist until dismissed)                │ │
│  │  Max visible: 3 stacked                                              │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  [✕] ⚠ İşlem başarısız                                   [X]  │ │ │
│  │  │      Lütfen daha sonra tekrar deneyin.                         │ │ │
│  │  │      [Tekrar Dene]                                             │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  │  • role="alert" for errors                                           │ │
│  │  • Focus management for dismiss                                      │ │
│  │  • Swipe to dismiss on mobile                                        │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  FULL PAGE ERRORS:                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  404 - Sayfa Bulunamadı                                              │ │
│  │  • Friendly illustration                                             │ │
│  │  • Clear message                                                     │ │
│  │  • Navigation options (home, back, search)                           │ │
│  │                                                                       │ │
│  │  500 - Sunucu Hatası                                                 │ │
│  │  • Apologetic tone                                                   │ │
│  │  • Retry option                                                      │ │
│  │  • Contact support link                                              │ │
│  │                                                                       │ │
│  │  Offline                                                             │ │
│  │  • Clear offline indicator                                           │ │
│  │  • What's available offline                                          │ │
│  │  • Auto-retry when online                                            │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. ANIMATION & MOTION

### 9.1 Motion Principles

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MOTION GUIDELINES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRINCIPLES:                                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Purposeful    │ Every animation serves a function                   │ │
│  │  Subtle        │ Enhance, don't distract                             │ │
│  │  Quick         │ 200-300ms for micro, 300-500ms for page             │ │
│  │  Respectful    │ Honor reduced-motion preferences                    │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  TIMING:                                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Duration      │ Use Case                                            │ │
│  │  ───────────────────────────────────────────────────────────────     │ │
│  │  100ms         │ Button hover, focus ring                            │ │
│  │  150ms         │ Toggle switches, checkboxes                         │ │
│  │  200ms         │ Micro-interactions, tooltips                        │ │
│  │  300ms         │ Modals, dropdowns, menus                            │ │
│  │  500ms         │ Page transitions, large reveals                     │ │
│  │                                                                       │ │
│  │  Easing: ease-out for enter, ease-in for exit                       │ │
│  │  Default: cubic-bezier(0.4, 0, 0.2, 1)                              │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  REDUCED MOTION:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  @media (prefers-reduced-motion: reduce) {                           │ │
│  │    *, *::before, *::after {                                          │ │
│  │      animation-duration: 0.01ms !important;                          │ │
│  │      animation-iteration-count: 1 !important;                        │ │
│  │      transition-duration: 0.01ms !important;                         │ │
│  │    }                                                                 │ │
│  │  }                                                                   │ │
│  │                                                                       │ │
│  │  Essential animations (loading spinners) can use:                    │ │
│  │  @media (prefers-reduced-motion: no-preference) { }                  │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Common Animations

```css
/* Fade In */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Slide Up (for modals, toasts) */
@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(16px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

/* Scale In (for dialogs) */
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Skeleton Pulse */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Spinner */
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Usage */
.modal-enter {
  animation: scaleIn 300ms ease-out;
}

.toast-enter {
  animation: slideUp 200ms ease-out;
}

.skeleton {
  animation: pulse 1.5s ease-in-out infinite;
}
```

---

## 10. UX FLOW PATTERNS

### 10.1 Menu Browsing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MENU BROWSING UX FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ENTRY POINTS:                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  1. QR Code Scan → Landing page with menu                            │ │
│  │  2. Direct URL → /m/{restaurant-slug}                                │ │
│  │  3. Search Engine → SEO landing + menu                               │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  USER JOURNEY:                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐           │ │
│  │  │  Land   │───►│ Browse  │───►│ Select  │───►│ Detail  │           │ │
│  │  │         │    │Categories│    │ Product │    │  View   │           │ │
│  │  └─────────┘    └─────────┘    └─────────┘    └────┬────┘           │ │
│  │                                                     │                │ │
│  │                                    ┌────────────────┘                │ │
│  │                                    │                                 │ │
│  │                                    ▼                                 │ │
│  │                              ┌─────────┐                             │ │
│  │                              │Add Cart │                             │ │
│  │                              └────┬────┘                             │ │
│  │                                   │                                  │ │
│  │                      ┌────────────┼────────────┐                    │ │
│  │                      │            │            │                    │ │
│  │                      ▼            ▼            ▼                    │ │
│  │                 ┌─────────┐ ┌─────────┐ ┌─────────┐                │ │
│  │                 │Continue │ │  View   │ │ Submit  │                │ │
│  │                 │Browsing │ │  Cart   │ │  Order  │                │ │
│  │                 └─────────┘ └─────────┘ └─────────┘                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  KEY UX CONSIDERATIONS:                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  • Instant category switching (no page reload)                       │ │
│  │  • Sticky header with search and cart                                │ │
│  │  • Quick add without leaving list view                               │ │
│  │  • Persistent cart indicator                                         │ │
│  │  • Back gesture/button returns to previous position                  │ │
│  │  • Scroll position preserved on return                               │ │
│  │  • Filter/sort options easily accessible                             │ │
│  │  • Price and availability always visible                             │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Order Placement Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ORDER PLACEMENT UX FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP INDICATOR:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │   (1)────────(2)────────(3)────────(4)                               │ │
│  │  Sepet     Detaylar    Onay     Tamamlandı                           │ │
│  │   ●──────────○──────────○──────────○                                 │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  STEP 1 - CART REVIEW:                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  • List all items with quantity controls                             │ │
│  │  • Show item customizations                                          │ │
│  │  • Allow item removal                                                │ │
│  │  • Show running total                                                │ │
│  │  • "Alışverişe Devam Et" + "Siparişi Tamamla"                       │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  STEP 2 - ORDER DETAILS:                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  • Table number (required for dine-in)                               │ │
│  │  • Special instructions (optional)                                   │ │
│  │  • Contact number (optional, for updates)                            │ │
│  │  • Pre-fill if returning customer                                    │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  STEP 3 - CONFIRMATION:                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  • Order summary                                                     │ │
│  │  • Total breakdown (subtotal, tax, discounts)                       │ │
│  │  • Estimated wait time                                               │ │
│  │  • "Siparişi Onayla" (prominent CTA)                                │ │
│  │  • "Düzenle" option to go back                                      │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  STEP 4 - SUCCESS:                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  • Order number prominently displayed                                │ │
│  │  • Estimated time                                                    │ │
│  │  • "Track Order" button                                              │ │
│  │  • Share/save receipt option                                         │ │
│  │  • Celebration animation (subtle)                                    │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ERROR PREVENTION:                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  • Confirm before removing items                                     │ │
│  │  • Warn if cart abandoned                                            │ │
│  │  • Validate table number format                                      │ │
│  │  • Double-confirm on final submit                                    │ │
│  │  • Handle network errors gracefully                                  │ │
│  │  • Prevent double submission                                         │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.3 Admin Dashboard UX

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ADMIN DASHBOARD UX                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INFORMATION HIERARCHY:                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Level 1: Critical Alerts (top banner if any)                        │ │
│  │  Level 2: Key Metrics (today's sales, orders, etc.)                  │ │
│  │  Level 3: Action Items (pending orders, low stock)                   │ │
│  │  Level 4: Trends & Insights (charts, comparisons)                    │ │
│  │  Level 5: Secondary Info (recent activity, tips)                     │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  QUICK ACTIONS:                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  • Floating action button (mobile): Most common action               │ │
│  │  • Command palette (Ctrl+K): Power user quick access                 │ │
│  │  • Contextual actions: Right-click/long-press menus                  │ │
│  │  • Batch operations: Multi-select + bulk actions                     │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  NAVIGATION PATTERNS:                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Desktop: Persistent left sidebar                                    │ │
│  │  ├── Collapsed by default (icons only)                              │ │
│  │  ├── Expand on hover or pin                                         │ │
│  │  └── Grouped by function                                            │ │
│  │                                                                       │ │
│  │  Mobile: Bottom navigation + hamburger for secondary                 │ │
│  │  ├── 4-5 primary items in bottom nav                                │ │
│  │  ├── Full menu in slide-out drawer                                  │ │
│  │  └── Swipe gestures for common actions                              │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. IMPLEMENTATION CHECKLIST

### 11.1 Accessibility Audit Checklist

```
Before Launch:

AUTOMATED TESTING:
[ ] axe-core scan passes (0 violations)
[ ] Lighthouse accessibility score > 90
[ ] WAVE tool scan clean
[ ] HTML validation passes

MANUAL TESTING:
[ ] Keyboard-only navigation complete
[ ] Screen reader testing (NVDA/VoiceOver)
[ ] Zoom to 200% without horizontal scroll
[ ] Color contrast verified (all text)
[ ] Focus indicators visible
[ ] Form error handling tested
[ ] Touch targets measured (48px min)

ASSISTIVE TECHNOLOGY:
[ ] NVDA (Windows)
[ ] VoiceOver (macOS/iOS)
[ ] TalkBack (Android)
[ ] Dragon NaturallySpeaking (voice)

DEVICE TESTING:
[ ] Mobile portrait
[ ] Mobile landscape
[ ] Tablet
[ ] Desktop
[ ] Large desktop
```

### 11.2 Component Development Checklist

```
For Each New Component:

ACCESSIBILITY:
[ ] Keyboard accessible
[ ] Screen reader friendly
[ ] ARIA attributes correct
[ ] Focus management proper
[ ] Color contrast passing

RESPONSIVENESS:
[ ] Mobile layout works
[ ] Touch targets adequate
[ ] No horizontal overflow

STATES:
[ ] Default state
[ ] Hover state
[ ] Focus state
[ ] Active state
[ ] Disabled state
[ ] Loading state
[ ] Error state
[ ] Empty state

THEMING:
[ ] Uses CSS variables
[ ] Dark mode works
[ ] High contrast works
[ ] Brand colors applied correctly

TESTING:
[ ] Unit tests written
[ ] Visual regression test
[ ] Cross-browser tested
```

---

*Bu döküman, E-Menum UI/UX standartlarını tanımlar. Tüm arayüz geliştirmeleri bu kurallara uygun olmalıdır.*
