'use client'

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { formatDate } from '@/lib/utils'
import type { Article, Entity } from '@/lib/schemas'

type RawEntity = {
  text?: string
  label?: string
  name?: string
}

type PreprocessedData = {
  len_chars?: number | null
  body_len?: number | null
  entities?: RawEntity[]
  [key: string]: unknown
}

type ArticleWithExtras = Article & {
  publication_date?: string | null
  scraped_at?: string | null
  preprocessed_data?: PreprocessedData | null
}

type Props = {
  article: ArticleWithExtras | null
  onClose: () => void
}

// Mapea labels crudos (PER, MISC, etc.) al enum de Entity.type
function mapLabelToType(label?: string): Entity['type'] {
  if (!label) return 'OTHER'
  const upper = label.toUpperCase()

  if (upper === 'PER' || upper === 'PERSON') return 'PERSON'
  if (upper === 'ORG') return 'ORG'
  if (upper === 'LOC' || upper === 'GPE') return 'LOC'
  if (upper === 'EVENT') return 'EVENT'
  if (upper === 'WORK_OF_ART') return 'WORK_OF_ART'
  if (upper === 'PRODUCT') return 'PRODUCT'

  // MISC, etc.
  return 'OTHER'
}

export default function ArticleDetailDialog({ article, onClose }: Props) {
  if (!article) return null

  // ---- Fuente ----
  const rawSource = article.source
  let sourceLabel = '[sin fuente]'
  if (typeof rawSource === 'string') {
    sourceLabel = rawSource || '[sin fuente]'
  } else if (rawSource) {
    sourceLabel = rawSource.name ?? rawSource.domain ?? '[sin fuente]'
  }

  // ---- Fecha (varios posibles campos) ----
  const rawDate =
    article.published_at ??
    article.publication_date ?? // típico en DB
    article.scraped_at ?? // por si solo tienes fecha de scrapeo
    null

  const dateLabel = rawDate ? formatDate(rawDate) : '—'

  // ---- Longitud (varios posibles campos) ----
  const lenFromField =
    typeof article.len_chars === 'number' && article.len_chars > 0 ? article.len_chars : null

  const lenFromBody =
    typeof article.body === 'string' && article.body.length > 0 ? article.body.length : null

  const lenFromPreprocessed =
    article.preprocessed_data?.len_chars ?? article.preprocessed_data?.body_len ?? null

  const lenChars = lenFromField ?? lenFromBody ?? lenFromPreprocessed
  const lenLabel = typeof lenChars === 'number' ? lenChars.toString() : '—'

  // ---- Sentimiento ----
  const polarity = typeof article.polarity === 'number' ? article.polarity.toFixed(3) : '—'
  const subjectivity =
    typeof article.subjectivity === 'number' ? article.subjectivity.toFixed(3) : '—'

  // ---- Entidades ----
  const normalizedEntities: Entity[] = Array.isArray(article.entities) ? article.entities : []

  // Si no hay entidades normalizadas, caemos a las crudas del preprocessed_data
  let entitiesToShow: Entity[] = normalizedEntities

  if (entitiesToShow.length === 0) {
    const rawEntities: RawEntity[] = Array.isArray(article.preprocessed_data?.entities)
      ? article.preprocessed_data!.entities!
      : []

    if (rawEntities.length > 0) {
      entitiesToShow = rawEntities.map(
        (re, idx): Entity => ({
          id: `raw-${idx}`,
          name: re.text ?? re.name ?? '(sin texto)',
          type: mapLabelToType(re.label),
          aliases: [],
          blocked: false,
        }),
      )
    }
  }

  const hasEntities = entitiesToShow.length > 0

  return (
    <Dialog
      open={!!article}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>{article.title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Meta */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-xs text-muted-foreground">Fuente</div>
              <div>{sourceLabel}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Fecha</div>
              <div>{dateLabel}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">URL</div>
              <a
                href={article.url}
                target="_blank"
                rel="noreferrer"
                className="underline underline-offset-2 break-all"
              >
                {article.url}
              </a>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Longitud (caracteres)</div>
              <div>{lenLabel}</div>
            </div>
          </div>

          {/* Sentimiento */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-xs text-muted-foreground">Polaridad</div>
              <div>{polarity}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Subjetividad</div>
              <div>{subjectivity}</div>
            </div>
          </div>

          {/* Entidades */}
          <div className="mt-4">
            <div className="font-medium mb-1">Entidades</div>
            {!hasEntities ? (
              <div className="text-xs text-muted-foreground">Sin entidades asociadas.</div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {entitiesToShow.map((e) => (
                  <Badge key={e.id}>
                    {e.type}: {e.name}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
