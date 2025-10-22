#!/usr/bin/env bash
set -euo pipefail

# === Prechequeos ===
if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI 'gh' no está instalado."
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: No estás autenticado en gh. Corre: gh auth login"
  exit 1
fi

# Detecta owner/repo actual
OWNER_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)
if [[ -z "${OWNER_REPO}" ]]; then
  echo "ERROR: No pude detectar el repo con 'gh repo view'. Ubícate dentro del repo git."
  exit 1
fi
echo "Repo detectado: ${OWNER_REPO}"

mkdir -p pr_bodies

# === #1 ADR arquitectura ===
cat > pr_bodies/PR_01_adr_arquitectura.md <<'MD'
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
MD

# === #2 Monorepo / estructura ===
cat > pr_bodies/PR_02_monorepo_estructura.md <<'MD'
## Contexto
Hoy frontend convive con scraping y scripts. Queremos un layout claro para escalar (FE/BE/infra/docs).

## Objetivo
Reorganizar en monorepo liviano con carpetas top-level.

## Cambios incluidos
- Estructura:
  ```
  /frontend
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
- `pnpm -C frontend dev` y `uvicorn api.main:app --reload` funcionan
- DB scripts siguen operando desde `/db`

## Follow-ups
- CI matrix por subproyecto

Closes #2
MD

# === #4 Normalización DB + vistas ===
cat > pr_bodies/PR_04_db_normalizado_vistas.md <<'MD'
## Contexto
Tenemos `schema.sql` y vistas `v_run_*`. Queremos normalizar nombres, tipos y ofrecer vistas UX-friendly.

## Objetivo
Pulir esquema y añadir `v_fe_articles` consumible por FE.

## Cambios incluidos
- `db/schema.sql`: consistencia de tipos `NUMERIC` vs `REAL`, `NOT NULL` donde aplique
- `v_fe_articles` con columnas: `id,title,url,source,published_at,len_chars,polarity,subjectivity`
- Índices recomendados para filtros y cursores (`published_at`, `(source_id, published_at)`)

## Acceptance Criteria
- `psql -f db/schema.sql` aplica sin errores
- `SELECT * FROM v_fe_articles LIMIT 10` retorna columnas esperadas

## Follow-ups
- Triggers para mantener `articles.len_chars` y hashes

Closes #4
MD

# === #15 Slack notificaciones ===
cat > pr_bodies/PR_15_slack_notificaciones.md <<'MD'
## Contexto
Ya existe `notify_summary.py`. Formalizarlo con payload consistente y manejo de errores.

## Objetivo
Estandarizar bloques Slack (KPIs + Top fuentes + entidades) y capturar fallos.

## Cambios incluidos
- `scripts/notify_summary.py`: bloqueado por vista `v_run_*`, try/except con fallback
- Formato de mensaje (blocks) estable; enlace a dashboard futuro
- README sección “Notificaciones” (scopes, canal, tokens)

## Acceptance Criteria
- Mensaje con KPIs básicos y top fuentes/entidades
- Manejo de error no rompe pipeline (loggea y continúa)

## Follow-ups
- Adjuntar CSV opcional (gated por token de usuario)

Closes #15
MD

# === #16 Dashboard básico ===
cat > pr_bodies/PR_16_dashboard_basico.md <<'MD'
## Contexto
Necesitamos una vista rápida para stakeholders.

## Objetivo
Vista `/dashboard` en FE con métricas base desde `v_run_summary` y `v_run_top_sources`.

## Cambios incluidos
- `frontend/src/app/dashboard/page.tsx`: tarjetas KPIs + gráfico simple (Chart.js o Recharts)
- Hook `useDashboardData` con fetch a `/api/runs/summary`
- Skeletons y estados vacíos

## Acceptance Criteria
- KPIs: insertados, descartados, duración, artículos por minuto
- Top fuentes (barra) del último run

## Follow-ups
- Tendencias 30 días y bins de sentimiento

Closes #16
MD

# === #18 Full-text search tsvector ===
cat > pr_bodies/PR_18_fulltext_tsvector.md <<'MD'
## Contexto
El filtro `q` ahora hace substring. Migrar a full-text para relevancia.

## Objetivo
Agregar `tsvector` + índice GIN + consulta `plainto_tsquery`/`to_tsquery`.

## Cambios incluidos
- `ALTER TABLE articles ADD COLUMN tsv tsvector;`
- Trigger para mantener `tsv` desde `title` + `body` (config `spanish`)
- Índice GIN sobre `tsv`
- Endpoint API adapta `q` → `WHERE tsv @@ plainto_tsquery('spanish', :q)`

## Acceptance Criteria
- Búsquedas más relevantes
- Explain muestra uso de índice

## Follow-ups
- Rank con `ts_rank_cd` y ordenar por score

Closes #18
MD

# === #20 Data quality pre-insert ===
cat > pr_bodies/PR_20_data_quality_preinsert.md <<'MD'
## Contexto
Evitar basura en DB: URL vacías, títulos nulos, fechas inconsistentes.

## Objetivo
Validar antes de persistir en pipeline y, opcionalmente, constraints suaves.

## Cambios incluidos
- Validaciones en `pipelines.py`/storage layer (Python)
- Reglas: URL no vacía, título no vacío, `published_at` razonable, idioma conocido
- Métrica `discarded_invalid` incrementada

## Acceptance Criteria
- Inserts inválidos se registran como descartados
- Logs apuntan motivo concreto

## Follow-ups
- Reporte de calidad por run

Closes #20
MD

# === #22 Accesibilidad (a11y) ===
cat > pr_bodies/PR_22_accesibilidad_a11y.md <<'MD'
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
MD

# === #23 Dashboards avanzados ===
cat > pr_bodies/PR_23_dashboards_avanzados.md <<'MD'
## Contexto
Extender el dashboard básico con vistas analíticas.

## Objetivo
3 paneles: cohortes por semana, histograma de polaridad/subjectividad, NER por fuente.

## Cambios incluidos
- Endpoints: `/api/runs/series`, `/api/runs/sentiment_bins`, `/api/runs/entities_top`
- FE: `/dashboard/analytics` con 3 charts y filtros (fecha/fuente)
- Caching leve (in-memory) para endpoints

## Acceptance Criteria
- Visualizaciones interactivas
- Tooltips + leyendas claras

## Follow-ups
- Exportar gráficos a PNG/CSV

Closes #23
MD

# === #24 Caching Redis ===
cat > pr_bodies/PR_24_cache_redis.md <<'MD'
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
MD

# === #25 Hardening seguridad ===
cat > pr_bodies/PR_25_hardening_seguridad.md <<'MD'
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
MD

# === #26 Infra-as-code ===
cat > pr_bodies/PR_26_infra_as_code.md <<'MD'
## Contexto
Simplificar setup local y preparar futuro despliegue.

## Objetivo
Docker Compose para FE, API, DB, Redis. Manifiestos K8s opcionales.

## Cambios incluidos
- `docker-compose.yml` con servicios `frontend`, `api`, `db`, `redis`
- `.env`/`.env.example` variables mínimas
- (Opcional) `/k8s` con manifests base (Deployment/Service)

## Acceptance Criteria
- `docker compose up` levanta stack local
- README con instrucciones

## Follow-ups
- CI/CD docker build/push

Closes #26
MD

# === #27 Observabilidad ===
cat > pr_bodies/PR_27_observabilidad.md <<'MD'
## Contexto
Necesitamos entender performance y fallos.

## Objetivo
Logging JSON, métricas Prometheus y tracing básico (OTel).

## Cambios incluidos
- Logging estructurado en API y jobs (uvicorn/structlog)
- Endpoint `/metrics` (Prometheus)
- OpenTelemetry SDK con exporter sencillo (stdout u OTLP)

## Acceptance Criteria
- Logs parseables (fields: level, msg, path, duration)
- `/metrics` expone contadores/latencias

## Follow-ups
- Jaeger/Tempo para tracing en dev

Closes #27
MD

# === #28 Documentación y runbooks ===
cat > pr_bodies/PR_28_docs_runbooks.md <<'MD'
## Contexto
Hay que facilitar operación y onboarding.

## Objetivo
Manual de usuario (UI) y runbooks (operación, incidentes).

## Cambios incluidos
- `docs/user-guide.md` (uso de tabla, filtros, bulk)
- `docs/runbooks/operacion.md`, `docs/runbooks/incidentes.md`
- Índice en README

## Acceptance Criteria
- Guía reproducible de punta a punta
- Incluye troubleshooting básico

## Follow-ups
- Vídeos/gifs (opcional)

Closes #28
MD

# === #29 QA E2E smoke ===
cat > pr_bodies/PR_29_qa_e2e_smoke.md <<'MD'
## Contexto
Asegurar que lo principal no se rompa entre merges.

## Objetivo
Añadir **smoke e2e** con Playwright: carga `/articles`, aplica filtro, exporta CSV.

## Cambios incluidos
- `frontend/e2e/playwright.config.ts`
- Test `articles.smoke.spec.ts` con:
  - Carga página
  - Escribe en búsqueda (debounce)
  - Verifica tabla con ≥1 fila (cuando haya datos)
  - Exporta CSV y verifica descarga (mock)
- Script `pnpm e2e`

## Acceptance Criteria
- Test corre en local y CI (headless)
- Report básico en artifacts

## Follow-ups
- Añadir casos a11y (#22) y flujo de bulk

Closes #29
MD

echo "Archivos de PR body (Sprint 3–4 + backlog) generados en ./pr_bodies"

# Publica cada archivo como comentario en su issue para dejarlo guardado/visible
declare -A ISSUE_FILE_MAP=(
  [1]="pr_bodies/PR_01_adr_arquitectura.md"
  [2]="pr_bodies/PR_02_monorepo_estructura.md"
  [4]="pr_bodies/PR_04_db_normalizado_vistas.md"
  [15]="pr_bodies/PR_15_slack_notificaciones.md"
  [16]="pr_bodies/PR_16_dashboard_basico.md"
  [18]="pr_bodies/PR_18_fulltext_tsvector.md"
  [20]="pr_bodies/PR_20_data_quality_preinsert.md"
  [22]="pr_bodies/PR_22_accesibilidad_a11y.md"
  [23]="pr_bodies/PR_23_dashboards_avanzados.md"
  [24]="pr_bodies/PR_24_cache_redis.md"
  [25]="pr_bodies/PR_25_hardening_seguridad.md"
  [26]="pr_bodies/PR_26_infra_as_code.md"
  [27]="pr_bodies/PR_27_observabilidad.md"
  [28]="pr_bodies/PR_28_docs_runbooks.md"
  [29]="pr_bodies/PR_29_qa_e2e_smoke.md"
)

for ISSUE in "${!ISSUE_FILE_MAP[@]}"; do
  FILE="${ISSUE_FILE_MAP[$ISSUE]}"
  if [[ -s "$FILE" ]]; then
    echo "Comentando en issue #$ISSUE con $FILE ..."
    gh issue comment "$ISSUE" -F "$FILE"
  else
    echo "WARN: No encontré contenido para issue #$ISSUE ($FILE)"
  fi
done

echo "Listo. Revisa los comentarios en cada issue y usa los .md como cuerpo de PR al crear cada Pull Request."
