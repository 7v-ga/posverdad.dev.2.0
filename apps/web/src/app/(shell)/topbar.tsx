'use client'

import { Input } from '@/components/ui/input'
import { useArticlesStore } from '@/store/articles-store'
import type { ArticlesState, ArticlesActions } from '@/store/articles-store'
import { useState, useEffect } from 'react'
import { useDebounced } from '@/lib/use-debounce'

type Store = ArticlesState & ArticlesActions

const selectSetFilters = (s: Store) => s.setFilters
const selectQ = (s: Store) => s.filters.q

export function Topbar() {
  const setFilters = useArticlesStore(selectSetFilters)
  const qStore = useArticlesStore(selectQ)
  const [q, setQ] = useState(qStore)
  const qDebounced = useDebounced(q, 300)

  useEffect(() => {
    setFilters({ q: qDebounced })
  }, [qDebounced, setFilters])

  useEffect(() => {
    setQ(qStore)
  }, [qStore])

  return (
    <header className="sticky top-0 z-30 bg-background/80 backdrop-blur border-b">
      <div className="container flex items-center gap-4 py-3">
        <div className="text-lg font-semibold">Repositorio de artículos</div>
        <div className="ml-auto w-80">
          <Input
            placeholder="Buscar título o URL…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
      </div>
    </header>
  )
}
