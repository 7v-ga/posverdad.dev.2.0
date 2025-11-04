## Contexto

Asegurar navegación por teclado y contraste, evitar errores de hidratación/semántica.

## Objetivo

Arreglos a11y en componentes base y roles ARIA.

## Cambios incluidos

- Revisión de botones vs enlaces; evitar `<button>` anidados
- Focus rings visibles (Tailwind) + `sr-only` en labels
- `aria-label`/`aria-describedby` en controles de tabla y filtros

## Acceptance Criteria

- Navegación por teclado completa
- Lighthouse a11y ≥ 90 en páginas clave

## Follow-ups

- Tests e2e a11y básicos (axe/playwright)

Closes #22
