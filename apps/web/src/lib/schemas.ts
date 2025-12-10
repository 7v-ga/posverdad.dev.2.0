// apps/web/src/lib/schemas.ts
import { z } from 'zod'

/* =========================
 * Entidades detectadas
 * ========================= */
export const EntitySchema = z.object({
  // La API puede devolver id numérico; aquí lo normalizamos a string
  id: z.union([z.string(), z.number()]).transform((v) => String(v)),
  name: z.string(),
  type: z
    .enum(['PERSON', 'ORG', 'LOC', 'GPE', 'EVENT', 'WORK_OF_ART', 'PRODUCT', 'OTHER'])
    .default('OTHER'),
  aliases: z.array(z.string()).default([]),
  blocked: z.boolean().default(false),
})
export type Entity = z.infer<typeof EntitySchema>

/* =========================
 * Fuente (API o string normalizada)
 * ========================= */
export const SourceSchema = z.object({
  id: z.number().int(),
  name: z.string(),
  domain: z.string().nullable().optional(),
})
export type Source = z.infer<typeof SourceSchema>

/* Helper fecha flexible -> ISO string o null */
const DateTimeFlexible = z
  .union([z.string().datetime(), z.string(), z.null()])
  .transform((value) => {
    if (!value) return null
    const d = new Date(value)
    if (Number.isNaN(d.getTime())) return null
    return d.toISOString()
  })

/* =========================
 * Artículo (tipo usado en el FE)
 * ========================= */
export const ArticleSchema = z
  .object({
    // La API usa id numérico; en el FE lo normalizamos a string
    id: z.union([z.string(), z.number()]).transform((v) => String(v)),
    title: z.string(),
    url: z.string().url(),

    // Puede venir ya normalizada como string o como objeto SourceOut
    source: z.union([z.string(), SourceSchema]),

    // Fecha principal que usa la UI (normalizada a ISO o null)
    published_at: DateTimeFlexible,

    // Longitud:
    // - La API puede devolver number, null o no mandarla.
    // - En el FE la normalizamos siempre a number (>= 0), usando 0 como "sin dato".
    len_chars: z
      .number()
      .int()
      .nonnegative()
      .nullable()
      .optional()
      .transform((v) => (typeof v === 'number' && Number.isFinite(v) && v >= 0 ? v : 0)),

    // Pueden ser null/undefined si la API no los calcula para todos
    polarity: z.number().gte(-1).lte(1).nullable().optional(),
    subjectivity: z.number().gte(0).lte(1).nullable().optional(),

    // Entidades ya normalizadas
    entities: z.array(EntitySchema).default([]),

    // Body del artículo (solo detalle; útil como fallback para len_chars)
    body: z.string().optional(),
  })
  // MUY IMPORTANTE: no perder campos extra como preprocessed_data
  .passthrough()

export type Article = z.infer<typeof ArticleSchema>

/* =========================
 * Respuesta de artículos
 * ========================= */
export const ArticlesResponseSchema = z.object({
  items: z.array(ArticleSchema),
  total: z.number().int().nonnegative(),
})
export type ArticlesResponse = z.infer<typeof ArticlesResponseSchema>

/* =========================
 * Filtros (UI)
 * =========================
 * Nota: usamos `null` para "sin valor" porque en la UI comprobamos con `!= null`.
 */
export const FiltersSchema = z.object({
  q: z.string().default(''),
  sources: z.array(z.string()).default([]),

  // Fechas en ISO (o null si no aplica)
  dateFrom: z.string().datetime().nullable().default(null),
  dateTo: z.string().datetime().nullable().default(null),

  // Rangos numéricos (o null si no aplica)
  lenMin: z.number().nullable().default(null),
  lenMax: z.number().nullable().default(null),
  polMin: z.number().nullable().default(null),
  polMax: z.number().nullable().default(null),
  subMin: z.number().nullable().default(null),
  subMax: z.number().nullable().default(null),
})
export type Filters = z.infer<typeof FiltersSchema>
