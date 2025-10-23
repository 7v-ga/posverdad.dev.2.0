## Contexto
Dashboards y listados pueden ser costosos.

## Objetivo
Cachear lecturas con Redis y claves deterministas por query.

## Cambios incluidos
- Cliente Redis (URL env), TTL por endpoint
- Decorador `@cache(ttl=60)` en endpoints de analytics
- Invalida caché por `run_id` reciente

## Acceptance Criteria
- Hits de caché medibles en logs
- Caídas de latencia en endpoints con tráfico

## Follow-ups
- Cache warming post-scrape

Closes #24
