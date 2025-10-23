// next.config.ts
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  typedRoutes: true,
  turbopack: {
    // Fuerza que /apps/web sea la raíz del workspace para Turbopack
    root: process.cwd(),
  },
}

export default nextConfig
