/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0a0a0f',
        card: '#13131a',
        border: '#1e1e2e',
        uluka: '#38bdf8',
        ds: '#fb923c',
        confirmed: '#22c55e',
        partial: '#eab308',
        inconclusive: '#6b7280',
        falsified: '#ef4444',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
