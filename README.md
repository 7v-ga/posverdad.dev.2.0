# Posverdad – Base de datos y migraciones (Alembic)

Este proyecto utiliza **SQLAlchemy + Alembic** para versionar y mantener el esquema de la base de datos.
La base de datos se considera **descartable en desarrollo**, pero las migraciones permiten:

- reconstruirla desde cero en cualquier entorno
- evolucionar el esquema de forma controlada en el futuro

---

## Requisitos

- Python 3.12
- Docker + Docker Compose
- PostgreSQL (vía contenedor)
- `uv` (recomendado) o `pip`

---

## Dependencias relevantes

En `requirements.in` deben existir al menos:

```txt
SQLAlchemy>=2.0,<3.0
alembic>=1.13
psycopg[binary]>=3.2
```

Instalación con `uv`:

```bash
uv pip install -r requirements.txt
```

---

## Variables de entorno

La aplicación y Alembic usan **una sola URL de conexión**.

`.env`:

```env
DATABASE_URL=postgresql+psycopg://posverdad:posverdad@localhost:5432/posverdad
```

> ⚠️ Importante:
>
> - **NO usar `psycopg2`**
> - El driver correcto es `postgresql+psycopg` (psycopg v3)

---

## Arranque de la base de datos (Docker)

```bash
docker compose up -d db
```

Esperar a que PostgreSQL esté listo:

```bash
docker exec posverdad-db-1 pg_isready -U posverdad -d posverdad
```

---

## Alembic – uso básico

### Estado actual

```bash
alembic current
```

### Crear una migración automática

```bash
alembic revision --autogenerate -m "descripcion"
```

### Aplicar migraciones

```bash
alembic upgrade head
```

---

## Flujo recomendado (desarrollo)

Base limpia desde cero:

```bash
docker compose down -v
docker compose up -d db

until docker exec posverdad-db-1 pg_isready -U posverdad -d posverdad; do
  sleep 1
done

alembic upgrade head
```

---

## Esquema controlado por Alembic

Las tablas actuales incluyen:

- articles
- entities
- articles_entities
- entity_mentions
- entity_actions
- categories
- sources
- alembic_version

⚠️ **No modificar el esquema directamente en SQL en producción.**
Toda modificación debe hacerse mediante:

1. cambio en modelos SQLAlchemy
2. nueva migración Alembic

---

## Sobre `nlp_runs`

La tabla `nlp_runs` **ya no forma parte del esquema activo**.

Referencias antiguas deben:

- eliminarse o
- adaptarse a un sistema de auditoría basado en:
  - `entity_actions`
  - timestamps
  - metadata JSON

Alembic es ahora la fuente de verdad del estado del esquema.

---

## Scraping y base de datos

Antes de ejecutar Scrapy:

1. Confirmar que la base existe
2. Confirmar que las migraciones están aplicadas
3. Confirmar que no hay referencias a tablas eliminadas (`nlp_runs`, vistas antiguas, etc.)

Verificación rápida:

```bash
psql "$DATABASE_URL" -c "\dt"
```

---

## Buenas prácticas

- Nunca versionar archivos generados (`tsbuildinfo`, `.eslintcache`, etc.)
- Nunca mezclar `psycopg2` con `psycopg`
- Mantener **una sola fuente de conexión** (`DATABASE_URL`)
- Cada cambio estructural → migración nueva

---

## Estado actual

✔ Alembic operativo  
✔ PostgreSQL en Docker  
✔ Base reconstruible desde cero  
✔ Esquema versionado

El proyecto está listo para continuar con scraping y normalización de entidades.
