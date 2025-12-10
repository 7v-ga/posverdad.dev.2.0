// apps/web/src/app/articles/ArticleDetailDialog.tsx
'use client'

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { formatDate } from '@/lib/utils'
import type { Article } from '@/lib/schemas'

type Props = {
  article: Article | null
  onClose: () => void
}

export default function ArticleDetailDialog({ article, onClose }: Props) {
  if (!article) return null

  const a: any = article

  // ---- Fuente ----
  const rawSource = a.source
  const sourceLabel =
    typeof rawSource === 'string'
      ? rawSource
      : rawSource && typeof rawSource === 'object'
        ? (rawSource.name ?? rawSource.domain ?? '[sin fuente]')
        : '[sin fuente]'

  // ---- Fecha (varios posibles campos) ----
  const rawDate =
    a.published_at ??
    a.publication_date ?? // típico en DB
    a.scraped_at ?? // por si solo tienes fecha de scrapeo
    null

  const dateLabel = rawDate ? formatDate(rawDate) : '—'

  // ---- Longitud (varios posibles campos, más defensivo) ----
  const lenFromField =
    typeof a.len_chars === 'number' && Number.isFinite(a.len_chars) && a.len_chars >= 0
      ? a.len_chars
      : typeof a.length === 'number' && Number.isFinite(a.length) && a.length >= 0
        ? a.length
        : null

  const lenFromBody = typeof a.body === 'string' && a.body.length > 0 ? a.body.length : null

  const lenFromPreprocessed =
    a.preprocessed_data && typeof a.preprocessed_data === 'object'
      ? (() => {
          const pp = a.preprocessed_data as any
          if (
            typeof pp.len_chars === 'number' &&
            Number.isFinite(pp.len_chars) &&
            pp.len_chars >= 0
          ) {
            return pp.len_chars
          }
          if (typeof pp.body_len === 'number' && Number.isFinite(pp.body_len) && pp.body_len >= 0) {
            return pp.body_len
          }
          return null
        })()
      : null

  const lenChars = lenFromField ?? lenFromBody ?? lenFromPreprocessed
  const lenLabel = typeof lenChars === 'number' ? lenChars.toString() : '—'

  // ---- Sentimiento ----
  const polarity =
    typeof a.polarity === 'number' && Number.isFinite(a.polarity) ? a.polarity.toFixed(3) : '—'
  const subjectivity =
    typeof a.subjectivity === 'number' && Number.isFinite(a.subjectivity)
      ? a.subjectivity.toFixed(3)
      : '—'

  // ---- Entidades ----
  const entities: any[] = Array.isArray(a.entities) ? a.entities : []
  const rawEntities: any[] =
    a.preprocessed_data &&
    typeof a.preprocessed_data === 'object' &&
    Array.isArray(a.preprocessed_data.entities)
      ? a.preprocessed_data.entities
      : []

  const hasNormalized = entities.length > 0
  const hasRaw = rawEntities.length > 0

  return (
    <Dialog
      open={!!article}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>{a.title}</DialogTitle>
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
                href={a.url}
                target="_blank"
                rel="noreferrer"
                className="underline underline-offset-2 break-all"
              >
                {a.url}
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

            {hasNormalized ? (
              <div className="flex flex-wrap gap-2">
                {entities.map((e) => (
                  <Badge key={e.id ?? `${e.type}-${e.name}`}>
                    {e.type}: {e.name}
                  </Badge>
                ))}
              </div>
            ) : hasRaw ? (
              <div className="flex flex-wrap gap-2">
                {rawEntities.map((e, idx) => (
                  <Badge key={`${e.label ?? 'ENT'}-${idx}`}>
                    {e.label ?? 'ENT'}: {e.text ?? e.name}
                  </Badge>
                ))}
              </div>
            ) : (
              <div className="text-xs text-muted-foreground">Sin entidades asociadas.</div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
