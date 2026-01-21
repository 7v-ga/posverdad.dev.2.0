# Posverdad v2 — Plataforma de Scraping, NLP y Análisis Editorial

Posverdad es una plataforma de **recolección, análisis y exploración de noticias** basada en scraping, procesamiento de lenguaje natural (NLP) y persistencia estructurada en PostgreSQL.

Desde la versión **v2**, el proyecto utiliza **SQLAlchemy + Alembic** como **fuente única de verdad del esquema**, permitiendo reconstruir y evolucionar la base de datos de forma controlada.

---

## Componentes principales

- **Scrapy** — ingestión de noticias
- **PostgreSQL** — base de datos principal
- **Alembic** — versionado del esquema
- **FastAPI** — API de consulta
- **Next.js** — frontend
- **NLP híbrido** — spaCy + pysentimiento + heurísticas propias
- **Docker Compose** — entorno de desarrollo reproducible

---

## Requisitos

- Python **3.12**
- Docker + Docker Compose
- PostgreSQL (vía contenedor)
- `uv` (recomendado) o `pip`
- Node.js + `pnpm` (solo para frontend)

---

## Instalación de dependencias Python

### Desarrollo (recomendado)

```bash
make py-install
```

### Producción / mínimo

```bash
make py-install-prod
```

---

## Variables de entorno

La **aplicación completa y Alembic** utilizan **una sola URL de conexión**.

```env
DATABASE_URL=postgresql+psycopg://posverdad:posverdad@localhost:5432/posverdad
```

**Importante**

- NO usar `psycopg2`
- Usar `postgresql+psycopg` (psycopg v3)

---

## Base de datos

```bash
make db-up
make db-wait
```

Reset destructivo:

```bash
make db-reset
```

---

## Migraciones (Alembic)

```bash
make migrate-current
make migrate
make migrate-revision MSG="descripcion"
```

---

## Flujo recomendado (desde cero)

```bash
make reset-all
```

---

## Scraping

```bash
make scrape SPIDER=el_mostrador COUNT=5
```

Verificar tablas:

```bash
psql "$DATABASE_URL" -c "\dt"
```

---

## API

```bash
make api-dev
```

Disponible en http://127.0.0.1:8000

---

## Frontend

```bash
make web-dev
```

---

## Tests

```bash
make test
make test-nocov
```

---

## Estado actual

- Alembic operativo
- Base reconstruible
- Scraping funcional con ajustes pendientes
- NLP en fase de estabilización (polarity, subjectivity, entities)

---

## Próximos focos

1. Estabilizar polarity / subjectivity
2. Consolidar entidades
3. Robustecer transacciones Scrapy
4. Ampliar tests reales
