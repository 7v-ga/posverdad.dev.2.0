// Tipado inline sin importar nada en runtime
const config = {
  // Next 15: usar 'typedRoutes' a nivel raíz (si lo usas)
  typedRoutes: true,

  // Si usas Turbopack por defecto en dev
  // future: { webpack5: true }, // (opcional según tu setup)
} satisfies import('next').NextConfig

export default config
