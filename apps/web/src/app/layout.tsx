// apps/web/src/app/layout.tsx
import "../styles/globals.css";
import type { ReactNode } from "react"
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Posverdad FE',
  description: 'UI administrativa de Posverdad',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-background text-foreground">
        {children}
      </body>
    </html>
  )
}
