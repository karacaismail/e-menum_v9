/** @type {import('tailwindcss').Config} */
module.exports = {
  // Scan Django templates and static JS for Tailwind classes
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/**/*.js',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0fdf8',
          100: '#ccfced',
          200: '#9af8db',
          300: '#5aefc5',
          400: '#2adea9',
          500: '#1A6B5A',
          600: '#0f5c4b',
          700: '#0a4a3b',
          800: '#083a2f',
          900: '#062f26',
          950: '#031a15',
        },
        accent: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#F5A623',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
          950: '#451a03',
        },
        secondary: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
          950: '#052e16',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
        heading: ['Plus Jakarta Sans', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      minHeight: {
        'touch': '48px',
      },
      minWidth: {
        'touch': '48px',
      },
    },
  },
  // Safelist: dynamic classes from DB that Tailwind scanner can't detect
  safelist: [
    // Color variants used dynamically in templates
    { pattern: /bg-(red|orange|amber|yellow|green|teal|blue|indigo|purple|pink|rose|cyan)-(50|100|500|900|950)/ },
    { pattern: /text-(red|orange|amber|yellow|green|teal|blue|indigo|purple|pink|rose|cyan)-(400|500|600)/ },
    { pattern: /border-(red|orange|amber|green|blue|purple|teal|pink|rose|cyan)-(100|900)/ },
    { pattern: /dark:bg-(red|orange|green|blue|purple|pink|rose|cyan|teal|amber)-(900|950)/ },
    { pattern: /dark:text-(red|orange|green|blue|purple|pink|rose|cyan|teal|amber)-400/ },
    { pattern: /dark:border-(red|orange|green|blue|purple|rose|cyan|teal|amber)-900/ },
    // Grid columns used dynamically
    { pattern: /lg:grid-cols-(1|2|3|4|5|6)/ },
    // Sidebar responsive utilities (Alpine.js dynamic classes need explicit safelist)
    'lg:translate-x-0',
    'lg:static',
    'lg:inset-auto',
    '-translate-x-full',
    'translate-x-0',
  ],
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
