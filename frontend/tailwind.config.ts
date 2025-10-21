// frontend/tailwind.config.ts
import type { Config } from 'tailwindcss'

const config = {
  // v4: usa ['class', 'dark'] para modo oscuro por clase
  darkMode: ['class', 'dark'],
  // v4 sigue aceptando 'content' (Next + TS agradecen el tipado explícito)
  content: [
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      container: { center: true, padding: '2rem' },
    },
  },
  // quito plugins para reducir ruido de tipos; si quieres 'tailwindcss-animate', lo reactivamos luego
  plugins: [],
} satisfies Config

export default config
