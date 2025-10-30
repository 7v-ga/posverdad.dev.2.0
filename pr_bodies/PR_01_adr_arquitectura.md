## Contexto
Necesitamos fijar la arquitectura base y dejar un ADR (Architecture Decision Record) con trade-offs y convenciones.

## Objetivo
Documentar arquitectura objetivo, diagrama de módulos y decisiones clave. Crear carpeta `adr/` con ADR-0001.

## Cambios incluidos
- `docs/adr/ADR-0001-arch-base.md` (Next.js FE, FastAPI BE, Postgres, Redis)
- Diagrama (Mermaid) de flujos FE↔API↔DB↔Redis↔Jobs
- Convenciones de versión de Node/Python y estilo de repo (branches, commit style)
- README actualizado con overview de la arquitectura

## Acceptance Criteria
- ADR claro, versionado, con “Consecuencias”
- Diagrama visible en GitHub
- Enlaces cruzados desde README

## Follow-ups
- ADR-0002 sobre autenticación y RBAC
- ADR-0003 sobre paginación por cursores

Closes #1
