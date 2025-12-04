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

// Se resuelve en build/hydration. Si cambias .env.local, reinicia `pnpm dev`.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL

export default function ArticlesPageClient() {
  const { setItems, filters, setFilters } = useArticlesStore()

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const pathname = usePathname()
  const searchParams = useSearchParams()
  const router = useRouter()

  // 1) Hidratar filtros desde la URL en el primer render
  useEffect(() => {
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

  // 2) Reflejar cambios de filtros en la URL (qs) sin recargar
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

  // 3) Cargar datos desde FastAPI siempre al montar
  useEffect(() => {
    let mounted = true

    async function load() {
      setIsLoading(true)
      setError(null)

      try {
        if (!API_BASE) {
          throw new Error(
            'NEXT_PUBLIC_API_BASE_URL no está definida (revisa apps/web/.env.local y reinicia `pnpm dev`).',
          )
        }

        const url = new URL('/articles/', API_BASE)
        url.searchParams.set('limit', '500') // ajusta el límite si quieres

        const res = await fetch(url.toString(), {
          method: 'GET',
          cache: 'no-store',
        })

        if (!res.ok) {
          throw new Error(`Error ${res.status} al cargar artículos (HTTP ${res.status})`)
        }

        // FastAPI devuelve lista simple -> adaptamos al tipo de items
        const raw = (await res.json()) as unknown as ArticlesResponse['items']
        if (!mounted) return

        const total = Array.isArray(raw) ? raw.length : 0
        setItems(raw ?? [], total)
      } catch (e: any) {
        console.error('Error cargando artículos desde API:', e)
        if (mounted) {
          setError(e?.message ?? 'No se pudieron cargar los artículos desde la API')
        }
      } finally {
        if (mounted) {
          setIsLoading(false)
        }
      }
    }

    void load()

    return () => {
      mounted = false
    }
  }, [setItems])

  const content = useMemo(() => {
    if (isLoading) {
      return <Skeleton className="h-64 w-full" data-slot="skeleton" />
    }

    if (error) {
      return (
        <div className="rounded border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          <p className="font-semibold">Error al cargar artículos</p>
          <p className="mt-1 whitespace-pre-line">{error}</p>
        </div>
      )
    }

    return (
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <aside className="lg:col-span-3">
          <div className="sticky top-4 space-y-4">
            <ArticlesFilters />
          </div>
        </aside>
        <section className="lg:col-span-9">
          <ArticlesTable />
        </section>
      </div>
    )
  }, [isLoading, error])

  return content
}
