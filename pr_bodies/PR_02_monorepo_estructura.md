## Contexto
Hoy frontend convive con scraping y scripts. Queremos un layout claro para escalar (FE/BE/infra/docs).

## Objetivo
Reorganizar en monorepo liviano con carpetas top-level.

## Cambios incluidos
- Estructura:
  ```
  /apps/web
  /api
  /db
  /jobs
  /scripts
  /docs
  ```
- Root `.editorconfig`, `.gitattributes`, `.gitignore`
- Root `Makefile` con phony targets (`frontend-dev`, `api-dev`, `db-apply`)
- Ajustes de paths en documentación

## Acceptance Criteria
- `pnpm -C apps/web dev` y `uvicorn api.main:app --reload` funcionan
- DB scripts siguen operando desde `/db`

## Follow-ups
- CI matrix por subproyecto

Closes #2
