import { Suspense } from 'react'
import ArticlesPageClient from './page.client'

export default function Page() {
  return (
    <div className="container mx-auto px-4 py-6">
      <Suspense fallback={<div className="h-64 w-full rounded-xl animate-pulse bg-muted" />}>
        <ArticlesPageClient />
      </Suspense>
    </div>
  )
}
