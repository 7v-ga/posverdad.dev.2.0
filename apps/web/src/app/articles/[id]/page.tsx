// apps/web/src/app/articles/[id]/page.tsx

import { getArticle } from '@/lib/api'

export default async function ArticleDetailPage({ params }: { params: { id: string } }) {
  const id = Number(params.id)
  const article = await getArticle(id)

  return (
    <div className="mx-auto max-w-3xl p-6 space-y-6">
      <header>
        <h1 className="text-3xl font-bold">{article.title}</h1>
        {article.subtitle && (
          <p className="mt-2 text-lg text-muted-foreground">{article.subtitle}</p>
        )}

        <div className="mt-3 text-sm text-muted-foreground space-y-1">
          <div>Fuente: {article.source?.name ?? article.domain ?? 'Desconocida'}</div>
          <div>Fecha: {article.publication_date ?? '—'}</div>
          {article.polarity !== null && article.polarity !== undefined && (
            <div>Polaridad: {article.polarity.toFixed(3)}</div>
          )}
          {article.subjectivity !== null && article.subjectivity !== undefined && (
            <div>Subjetividad: {article.subjectivity.toFixed(3)}</div>
          )}
        </div>
      </header>

      {article.image && (
        <div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={article.image} alt="" className="max-h-96 w-full rounded object-cover" />
        </div>
      )}

      <article className="prose dark:prose-invert max-w-none">{article.body}</article>
    </div>
  )
}
