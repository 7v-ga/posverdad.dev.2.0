'use client'

import { useEffect, useMemo, useState } from 'react'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import type { Route } from 'next'

import { useArticlesStore } from '@/store/articles-store'
import type { ArticlesResponse } from '@/lib/schemas'
import { fromQS, toQS } from '@/lib/querystring'

import { Skeleton } from '@/components/ui/skeleton'
import ArticlesTable from './components/ArticlesTable'
import ArticlesFilters from './components/ArticlesFilters'

export default function ArticlesPage() {
  const { items, setItems, setLoading, loading, filters, setFilters } = useArticlesStore()
  const [error, setError] = useState<string | null>(null)

  const pathname = usePathname()
  const searchParams = useSearchParams()
  const router = useRouter()

  // Hidratar filtros desde la URL en el primer render
  useEffect(() => {
    // ReadonlyURLSearchParams -> URLSearchParams para reutilizar utilidades
    const sp = new URLSearchParams(searchParams.toString())
    const qs = fromQS(sp)

    setFilters({
      q: qs.str('q'),
      sources: qs.arr('source'),
      dateFrom: qs.iso('from'),
      dateTo: qs.iso('to'),
      lenMin: qs.num('lenMin') ?? undefined,
      lenMax: qs.num('lenMax') ?? undefined,
      polMin: qs.num('polMin') ?? undefined,
      polMax: qs.num('polMax') ?? undefined,
      subMin: qs.num('subMin') ?? undefined,
      subMax: qs.num('subMax') ?? undefined,
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Empujar cambios de filtros a la URL (sin recargar página)
useEffect(() => {
  const qs = toQS({
    q: filters.q,
    source: filters.sources,
    from: filters.dateFrom ?? undefined,
    to: filters.dateTo ?? undefined,
    lenMin: filters.lenMin ?? undefined,
    lenMax: filters.lenMax ?? undefined,
    polMin: filters.polMin ?? undefined,
    polMax: filters.polMax ?? undefined,
    subMin: filters.subMin ?? undefined,
    subMax: filters.subMax ?? undefined,
  })

  const href = (qs ? `${pathname}${qs}` : pathname) as Route
  router.replace(href, { scroll: false })
}, [filters, pathname, router])

  // Cargar datos mock (una vez)
  useEffect(() => {
    let mounted = true
    async function load() {
      setLoading(true)
      try {
        const res = await fetch('/api/articles')
        const data = (await res.json()) as ArticlesResponse
        if (!mounted) return
        setItems(data.items, data.total)
      } catch (_e) {
        setError('No se pudieron cargar los artículos')
      } finally {
        setLoading(false)
      }
    }
    if (items.length === 0) load()
    return () => {
      mounted = false
    }
  }, [items.length, setItems, setLoading])

  const content = useMemo(() => {
    if (loading) return <Skeleton className="h-64 w-full" />
    if (error) return <div className="text-red-600">{error}</div>
    return (
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <aside className="lg:col-span-1">
          <ArticlesFilters />
        </aside>
        <section className="lg:col-span-3">
          <ArticlesTable />
        </section>
      </div>
    )
  }, [loading, error])

  return content
}
