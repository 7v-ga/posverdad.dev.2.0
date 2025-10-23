import { NextResponse } from 'next/server'

export async function GET() {
  const now = new Date().toISOString()
  const items = [
    {
      id: 'a-1',
      title: 'Prueba 1: polaridad media',
      url: 'https://ejemplo.cl/nota/1',
      source: 'Fuente X',
      published_at: now,
      len_chars: 1200,
      polarity: 0.1,
      subjectivity: 0.3,
      entities: [
        { id: 'e-1', name: 'Gabriel', type: 'PERSON', aliases: [], blocked: false },
        { id: 'e-2', name: 'SieteV', type: 'ORG', aliases: [], blocked: false },
      ],
    },
    {
      id: 'a-2',
      title: 'Prueba 2: negativa',
      url: 'https://ejemplo.cl/nota/2',
      source: 'Fuente Y',
      published_at: now,
      len_chars: 800,
      polarity: -0.4,
      subjectivity: 0.6,
      entities: [
        { id: 'e-3', name: 'Chile', type: 'LOC', aliases: [], blocked: false },
      ],
    },
  ]
  return NextResponse.json({ items, total: items.length })
}
