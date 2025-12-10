// apps/web/src/lib/csv.ts
import type { Article } from './schemas'

function escapeCSV(val: string) {
  // Si contiene comillas, comas o saltos de línea → encierra en comillas y duplica comillas internas
  if (/[",\n]/.test(val)) return '"' + val.replace(/"/g, '""') + '"'
  return val
}

function sourceToLabel(source: Article['source']): string {
  if (!source) return ''
  if (typeof source === 'string') return source
  return source.name || source.domain || String(source.id)
}

export function toCSV(rows: Article[]): string {
  const headers = [
    'id',
    'title',
    'url',
    'source',
    'published_at',
    'len_chars',
    'polarity',
    'subjectivity',
    'entities_raw',
  ]
  const lines: string[] = [headers.join(',')]

  for (const r of rows) {
    const sourceLabel = sourceToLabel(r.source)
    const publishedAt = r.published_at ?? ''

    const len =
      typeof r.len_chars === 'number' && Number.isFinite(r.len_chars) ? String(r.len_chars) : ''

    const pol =
      typeof r.polarity === 'number' && Number.isFinite(r.polarity) ? String(r.polarity) : ''

    const sub =
      typeof r.subjectivity === 'number' && Number.isFinite(r.subjectivity)
        ? String(r.subjectivity)
        : ''

    // 👇 Entidades crudas desde preprocessed_data.entities (si existen)
    const rawEntities: any[] =
      (r as any).preprocessed_data &&
      typeof (r as any).preprocessed_data === 'object' &&
      Array.isArray((r as any).preprocessed_data.entities)
        ? (r as any).preprocessed_data.entities
        : []

    const entitiesRaw = rawEntities.length
      ? rawEntities
          .map((e: any) => {
            const label = e.label ?? 'ENT'
            const text = e.text ?? e.name ?? ''
            return text ? `${label}:${text}` : label
          })
          .join(' | ')
      : ''

    lines.push(
      [
        r.id,
        escapeCSV(r.title),
        r.url,
        escapeCSV(sourceLabel),
        publishedAt,
        len,
        pol,
        sub,
        escapeCSV(entitiesRaw),
      ].join(','),
    )
  }

  return lines.join('\n')
}

export function downloadCSV(filename: string, csv: string) {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
