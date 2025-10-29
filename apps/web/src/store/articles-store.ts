'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { type Article, type Entity, type Filters, FiltersSchema } from '@/lib/schemas'

export type ArticlesState = {
  items: Article[]
  total: number
  loading: boolean
  filters: Filters
  selection: Article | null
}

export type ArticlesActions = {
  setItems: (a: Article[], total?: number) => void
  setLoading: (v: boolean) => void
  setFilters: (f: Partial<Filters>) => void
  clearFilters: () => void
  select: (a: Article | null) => void
  updateEntity: (articleId: string, entityId: string, data: Partial<Entity>) => void
  addAlias: (articleId: string, entityId: string, alias: string) => void
  removeAlias: (articleId: string, entityId: string, alias: string) => void
}

const initialFilters: Filters = FiltersSchema.parse({})

export const useArticlesStore = create<ArticlesState & ArticlesActions>()(
  persist(
    (set, get) => ({
      items: [],
      total: 0,
      loading: false,
      filters: initialFilters,
      selection: null,

      setItems: (a, total) => set({ items: a, total: total ?? a.length }),
      setLoading: (v) => set({ loading: v }),
      setFilters: (f) => set({ filters: { ...get().filters, ...f } }),
      clearFilters: () => set({ filters: initialFilters }),
      select: (a) => set({ selection: a }),

      updateEntity: (articleId, entityId, data) => {
        const items = get().items.map((art) => {
          if (art.id !== articleId) return art
          return {
            ...art,
            entities: art.entities.map((e) => (e.id === entityId ? { ...e, ...data } : e)),
          }
        })
        set({ items })
      },

      addAlias: (articleId, entityId, alias) => {
        const items = get().items.map((art) => {
          if (art.id !== articleId) return art
          return {
            ...art,
            entities: art.entities.map((e) =>
              e.id === entityId && !e.aliases.includes(alias)
                ? { ...e, aliases: [...e.aliases, alias] }
                : e
            ),
          }
        })
        set({ items })
      },

      removeAlias: (articleId, entityId, alias) => {
        const items = get().items.map((art) => {
          if (art.id !== articleId) return art
          return {
            ...art,
            entities: art.entities.map((e) =>
              e.id === entityId ? { ...e, aliases: e.aliases.filter((a) => a !== alias) } : e
            ),
          }
        })
        set({ items })
      },
    }),
    { name: 'postverdad-articles' }
  )
)

// Solo para QA manual; no afecta producción
if (typeof window !== 'undefined') {
  // @ts-expect-error
  window.__articlesStore = useArticlesStore
}
