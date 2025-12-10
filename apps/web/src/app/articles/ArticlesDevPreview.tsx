'use client'

import { useArticlesStore } from '@/store/articles-store'
import type { Article } from '@/lib/schemas'

export default function ArticlesDevPreview() {
  const items = useArticlesStore((s) => s.items)
  const selection = useArticlesStore((s) => s.selection)

  const first: Article | undefined = items[0]

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Articles Dev Preview</h1>
      <section>
        <h2 className="text-sm font-medium">Resumen</h2>
        <pre className="mt-2 rounded bg-muted p-2 text-xs">
          {JSON.stringify(
            {
              count: items.length,
              firstId: first?.id ?? null,
            },
            null,
            2,
          )}
        </pre>
      </section>

      <section>
        <h2 className="text-sm font-medium">Selección actual</h2>
        <pre className="mt-2 rounded bg-muted p-2 text-xs">
          {JSON.stringify(selection, null, 2)}
        </pre>
      </section>
    </div>
  )
}
