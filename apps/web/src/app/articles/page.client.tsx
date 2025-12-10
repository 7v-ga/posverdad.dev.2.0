'use client'

import { useEffect, useState } from 'react'
import { useArticlesStore } from '@/store/articles-store'
import { listArticles } from '@/lib/api'
import { useDebounced } from '@/lib/use-debounce'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArticleSchema, type Article } from '@/lib/schemas'
import ArticlesFilters from './components/ArticlesFilters'
import ArticlesTable from './components/ArticlesTable'

export default function ArticlesPageClient() {
  const { items, total, loading, filters, setFilters, setItems, setLoading } = useArticlesStore()

  const [error, setError] = useState<string | null>(null)

  // Campo de búsqueda local, sincronizado con filters.q
  const [search, setSearch] = useState<string>(filters.q)
  const debouncedSearch = useDebounced(search, 400)

  // Mantener filters.q alineado con el input debounced
  useEffect(() => {
    if (filters.q !== debouncedSearch) {
      setFilters({ q: debouncedSearch })
    }
  }, [debouncedSearch, filters.q, setFilters])

  // Carga de artículos desde la API
  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await listArticles({
          q: debouncedSearch || undefined,
          // Fechas: si tu backend las soporta, las pasamos tal cual (ISO)
          date_from: filters.dateFrom ?? undefined,
          date_to: filters.dateTo ?? undefined,
          // De momento traemos un "batch" completo y paginamos en cliente
          limit: 500,
          offset: 0,
        })

        if (cancelled) return

        const parsed: Article[] = data.map((item) =>
          ArticleSchema.parse({
            // spread primero para conservar cualquier campo extra
            ...item,
            // y luego normalizamos los que nos interesan
            id: item.id,
            title: item.title,
            url: item.url,
            source: item.source ?? item.domain ?? '',
            published_at: item.published_at ?? item.publication_date ?? item.scraped_at ?? null,
          }),
        )

        setItems(parsed, parsed.length)
      } catch (e) {
        if (cancelled) return
        console.error(e)
        setError(e instanceof Error ? e.message : 'Error al cargar artículos')
        setItems([], 0)
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    load()

    return () => {
      cancelled = true
    }
  }, [debouncedSearch, filters.dateFrom, filters.dateTo, setItems, setLoading])

  return (
    <div className="space-y-4">
      {/* Header / resumen */}
      <Card className="p-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-lg font-semibold">Artículos</h1>
          <p className="text-sm text-muted-foreground">
            Exploración de artículos analizados por Posverdad.
          </p>
        </div>
        <div className="flex flex-col gap-2 items-stretch md:items-end">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Total cargado</span>
            <Badge variant="secondary">{total}</Badge>
          </div>
          <Input
            className="w-full md:w-64"
            placeholder="Buscar por título o URL…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </Card>

      {/* Filtros */}
      <ArticlesFilters />

      {/* Estado de error / loading */}
      {error && <div className="text-sm text-red-600">Error al cargar artículos: {error}</div>}
      {loading && !items.length && (
        <div className="text-sm text-muted-foreground">Cargando artículos…</div>
      )}

      {/* Tabla principal */}
      <ArticlesTable />
    </div>
  )
}
