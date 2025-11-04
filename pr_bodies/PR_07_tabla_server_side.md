## Contexto

FE funciona en client-side; hay que mover filtros/paginación/orden al server para escalar.

## Objetivo

Sincronizar UI con `searchParams` y llamar la API con query params para filtrar/paginar/ordenar en server.

## Cambios incluidos

- Adapter FE: construir query (`q,source,from,to,len_min,len_max,pol_min,pol_max,sub_min,sub_max,sort,page,page_size`)
- Hooks de fetch FE para usar `NEXT_PUBLIC_API_BASE_URL`
- Endpoint en API con parsing/validación y SQL/ORM correspondiente

## Alcance

- `/articles` usa datos de API (no mock)
- Server responde `items` y `total` acorde a filtros/paginación

## Acceptance Criteria

- Copiar URL con filtros → recarga mantiene resultados
- Cambiar pageSize/orden refleja resultados del server
- Vacío controlado con CTA “Limpiar filtros”

## Definition of Done

- Typecheck OK FE/BE
- Prueba manual con varias combinaciones de filtros

## Follow-ups

- Cursor-based pagination (#21)
- Índices SQL según uso real

Closes #7
