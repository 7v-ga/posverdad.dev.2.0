## Contexto

Frontend P1 listo. Se requiere API real para lectura de artículos, con contrato claro (OpenAPI).

## Objetivo

Exponer `GET /api/articles` (read-only) con DTO alineado al Zod del FE: `ArticlesResponse`.

## Cambios incluidos

- `/api/main.py` (FastAPI mínimo, CORS)
- `/api/requirements.txt`
- Endpoint `GET /api/articles` (lectura desde DB/vista)
- `README-api.md` con instrucciones

## Alcance

- `GET /api/articles`: `{ items: Article[], total }`
- Campos: `id,title,url,source,published_at,len_chars,polarity,subjectivity,entities?[]`

## Acceptance Criteria

- `/docs` (Swagger) expone el contrato correcto
- FE valida respuesta con Zod sin errores

## Definition of Done

- `uvicorn main:app --reload` levanta bien
- `GET /api/articles` responde 200 con shape esperado

## Cómo probar

- `curl http://localhost:8000/api/articles`
- En FE: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` y abrir `/articles`

## Follow-ups

- Paginación/orden server-side (#7, #21)
- Entidades por artículo (endpoint dedicado)

Closes #3
