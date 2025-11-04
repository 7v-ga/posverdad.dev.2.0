## Contexto

Necesitamos datos de arranque para flujos FE/API sin depender del scraper.

## Objetivo

Seed idempotente de 2 fuentes demo.

## Cambios incluidos

- `db/seed_dev.sql` (UPSERT por name)
- Target de Make: `db-seed-dev` (si aplica en `makefiles/db.mk`)

## Alcance

- Insertar/actualizar:
  - `('Fuente Demo 1', 'demo1.cl')`
  - `('Fuente Demo 2', 'demo2.cl')`

## Acceptance Criteria

- `make db-seed-dev` corre sin error
- Las 2 fuentes existen tras ejecutar el seed

## Definition of Done

- Script idempotente (re-ejecutable)
- README-dev con instrucción del comando

## Cómo probar

```bash
make db-seed-dev
psql "$POSTGRES_URI" -c "SELECT id,name,domain FROM sources WHERE name LIKE 'Fuente Demo%';"
```

## Follow-ups

- Extender con usuarios cuando se defina Auth/RBAC

Closes #31
