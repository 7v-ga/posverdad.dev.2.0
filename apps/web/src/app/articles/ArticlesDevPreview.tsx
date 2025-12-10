'use client'

import { useEffect } from 'react'
import { useArticlesStore } from '@/store/articles-store'
import { ArticleSchema, type Article } from '@/lib/schemas'
import ArticlesFilters from './components/ArticlesFilters'
import ArticlesTable from './components/ArticlesTable'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

// Datos de ejemplo para probar distintos casos:
// - source como string
// - source como objeto { id, name, domain }
// - fechas distintas (published_at, publication_date, scraped_at, inválida)
// - len_chars ausente (usa default 0 / fallback en UI)
// - entidades normalizadas
// - entidades solo en preprocessed_data.entities
const sampleRawArticles: any[] = [
  {
    id: 1,
    title: 'Artículo con fuente como string y fecha published_at',
    url: 'https://ejemplo.cl/articulo-1',
    source: 'Diario Ejemplo',
    published_at: '2024-10-01T12:00:00Z',
    polarity: 0.12,
    subjectivity: 0.45,
    // sin len_chars ⇒ debería quedar en 0 y la UI mostrará fallback si hay body
    body: 'Este es un cuerpo de prueba para el artículo 1.',
    entities: [
      {
        id: 'e1',
        name: 'Gabriel Boric',
        type: 'PERSON',
        aliases: ['Boric'],
        blocked: false,
      },
    ],
  },
  {
    id: 2,
    title: 'Artículo con fuente como objeto y fecha publication_date',
    url: 'https://otro-medio.cl/noticia-2',
    source: {
      id: 10,
      name: 'Otro Medio',
      domain: 'otro-medio.cl',
    },
    publication_date: '2024-09-15T09:30:00Z',
    polarity: -0.3,
    subjectivity: 0.8,
    len_chars: 1234,
    entities: [
      {
        id: 'e2',
        name: 'Chile',
        type: 'GPE',
        aliases: [],
        blocked: true,
      },
    ],
  },
  {
    id: 3,
    title: 'Artículo con solo scraped_at y entidades crudas',
    url: 'https://tercer-medio.cl/nota-3',
    // source viene solo como dominio
    domain: 'tercer-medio.cl',
    scraped_at: '2024-08-20T18:45:00Z',
    polarity: null,
    subjectivity: null,
    // fecha inválida adicional para probar normalización
    publication_date: 'fecha-invalida',
    preprocessed_data: {
      entities: [
        { text: 'Santiago', label: 'LOC' },
        { text: 'Congreso', label: 'ORG' },
      ],
    },
    body: 'Cuerpo de prueba del artículo 3, con entidades solo en preprocessed_data.',
    // sin entities normalizadas ⇒ EntitiesDialog debería mostrar el bloque de "crudas"
  },
]

export default function ArticlesDevPreview() {
  const { setItems, setLoading, clearFilters, total } = useArticlesStore()

  useEffect(() => {
    // Limpiamos filtros y estado de carga
    clearFilters()
    setLoading(false)

    // Parseamos los datos de ejemplo con ArticleSchema (mismo contrato que la API real)
    const parsed: Article[] = sampleRawArticles.map((raw) =>
      ArticleSchema.parse({
        // replicamos la lógica del mapeo de page.client.tsx
        id: raw.id,
        title: raw.title,
        url: raw.url,
        source: raw.source ?? raw.domain ?? '',
        published_at: raw.published_at ?? raw.publication_date ?? raw.scraped_at ?? null,
        len_chars: raw.len_chars,
        polarity: raw.polarity ?? null,
        subjectivity: raw.subjectivity ?? null,
        entities: raw.entities ?? [],
        body: raw.body,
        preprocessed_data: raw.preprocessed_data,
      }),
    )

    setItems(parsed, parsed.length)
  }, [setItems, setLoading, clearFilters])

  return (
    <div className="space-y-4">
      {/* Header / resumen */}
      <Card className="p-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-lg font-semibold">Artículos — Dev Preview</h1>
          <p className="text-sm text-muted-foreground">
            Vista de prueba local con datos mock para validar filtros, tabla, diálogos y entidades.
          </p>
        </div>
        <div className="flex flex-col gap-2 items-stretch md:items-end">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Total mock</span>
            <Badge variant="secondary">{total}</Badge>
          </div>
        </div>
      </Card>

      {/* Filtros reales */}
      <ArticlesFilters />

      {/* Tabla real + diálogos (detalle, entidades) */}
      <ArticlesTable />
    </div>
  )
}
