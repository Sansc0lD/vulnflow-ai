/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#050507',
        surface: '#08080B',
        'surface-elevated': '#0E0E13',
        border: 'rgba(255, 255, 255, 0.11)',
        muted: '#8A8D96',
        primary: {
          DEFAULT: '#F5F5F3',
          hover: '#ffffff',
          foreground: '#050507',
        },
        accent: {
          DEFAULT: '#F5F5F3',
          emerald: '#34d399',
        },
        cvss: {
          critical: '#ef4444',
          high: '#f97316',
          medium: '#eab308',
          low: '#d4d4d8',
          info: '#71717a',
        },
      },
      fontFamily: {
        display: ['Geist', 'system-ui', 'sans-serif'],
        serif: ['Instrument Serif', 'Georgia', 'serif'],
        sans: ['Geist', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
