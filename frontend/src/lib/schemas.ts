// src/lib/schemas.ts
import { z } from 'zod'

/* =========================
 * Entidades detectadas
 * ========================= */
export const EntitySchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum([
    'PERSON',
    'ORG',
    'LOC',
    'GPE',
    'EVENT',
    'WORK_OF_ART',
    'PRODUCT',
    'OTHER',
  ]).default('OTHER'),
  aliases: z.array(z.string()).default([]),
  blocked: z.boolean().default(false),
})
export type Entity = z.infer<typeof EntitySchema>

/* =========================
 * Artículo
 * ========================= */
export const ArticleSchema = z.object({
  id: z.string(),
  title: z.string(),
  url: z.string().url(),
  source: z.string(),
  published_at: z.string().datetime(),
  len_chars: z.number().int().nonnegative(),
  polarity: z.number().gte(-1).lte(1),
  subjectivity: z.number().gte(0).lte(1),
  entities: z.array(EntitySchema).default([]),
})
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
 * Esto encaja bien con:
 *   if (filters.lenMin != null) { ... }
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
