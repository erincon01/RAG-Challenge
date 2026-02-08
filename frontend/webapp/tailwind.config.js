/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: '#0f1722',
        panel: '#182437',
        accent: '#2dd4bf',
        accentWarm: '#fb923c',
        ink: '#e2e8f0',
        mute: '#94a3b8',
      },
      fontFamily: {
        sans: ['"Space Grotesk"', '"IBM Plex Sans"', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 40px rgba(45, 212, 191, 0.25)',
      },
    },
  },
  plugins: [],
}
