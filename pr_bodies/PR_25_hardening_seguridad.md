## Contexto

Subir baseline de seguridad para FE y API.

## Objetivo

CSP estricta, rate limit en rutas sensibles y ampliar auditoría.

## Cambios incluidos

- FE: headers CSP (`next.config.ts` + middleware)
- API: rate limit `POST/PATCH` (fastapi-limiter/redis)
- Audit: registrar IP/UA sistemáticamente

## Acceptance Criteria

- Report-Only CSP sin bloqueos, luego Enforce
- Logs muestran límites aplicándose

## Follow-ups

- CSRF según estrategia de auth

Closes #25
