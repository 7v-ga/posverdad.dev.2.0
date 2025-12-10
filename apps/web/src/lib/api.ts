// apps/web/src/lib/api.ts

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL

if (!API_BASE) {
  throw new Error('NEXT_PUBLIC_API_BASE_URL no está definida')
}

// -----------------------------
// Helper genérico GET
// -----------------------------
async function get<T>(
  path: string,
  params?: Record<string, string | number | undefined | null>,
): Promise<T> {
  const url = new URL(path, API_BASE)

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value))
      }
    }
  }

  const res = await fetch(url.toString(), {
    method: 'GET',
    cache: 'no-store',
  })

  if (!res.ok) {
    throw new Error(`GET ${url} -> ${res.status}`)
  }

  return res.json() as Promise<T>
}

// -----------------------------
// Tipos (alineados con FastAPI)
// -----------------------------

export interface SourceOut {
  id: number
  name: string
  domain?: string | null
}

export interface ArticleSummary {
  id: number
  title: string
  url: string
  domain?: string | null
  source?: SourceOut | null
  publication_date?: string | null
  published_at?: string | null
  scraped_at?: string | null
  polarity?: number | null
  subjectivity?: number | null
  language?: string | null
  // longitud calculada por el backend
  len_chars?: number | null
}

export interface ArticleDetail extends ArticleSummary {
  subtitle?: string | null
  body: string
  meta_description?: string | null
  meta_keywords?: string | null
  image?: string | null
  run_id?: string | null
}

// -----------------------------
// Funciones de API
// -----------------------------

export async function listArticles(params: {
  q?: string
  source_id?: number
  entity_id?: number
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}): Promise<ArticleSummary[]> {
  return get<ArticleSummary[]>('/articles/', params)
}

export async function getArticle(id: number): Promise<ArticleDetail> {
  return get<ArticleDetail>(`/articles/${id}`)
}
