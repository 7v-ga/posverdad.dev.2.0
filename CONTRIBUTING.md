# CONTRIBUTING.md

¡Gracias por contribuir a **Posverdad**! Este documento describe cómo trabajar en el proyecto (flujo de trabajo, estilos de código, tests, PRs, entorno local, etc.). Si algo no está claro, abre un issue etiquetado como `question`.

---

## 1) Visión rápida del repo

Monorepo con frontend y backend:

```
.
├─ apps/
│  ├─ web/                # Next.js 14 (App Router, TS), UI (Tailwind + shadcn/ui)
│  └─ api/                # FastAPI, SQLAlchemy 2.0, Pydantic v2
├─ packages/
│  ├─ shared/             # Tipos/DTOs compartidos (Zod/Pydantic JSON schemas, utils)
│  └─ ui/                 # (opcional) componentes UI compartidos FE
├─ infra/                 # Docker, compose, despliegue, CI helpers, Alembic (si aplica)
├─ scripts/               # scripts utilitarios (migraciones, seed, limpieza)
├─ makefiles/             # make targets por dominio (db, api, web, etc.)
├─ .env.example           # variables de entorno de ejemplo (NUNCA subir .env reales)
└─ README.md
```

**Stack principal**

- **Frontend**: Next.js 14 (App Router) + TypeScript estricto + Tailwind + shadcn/ui + TanStack Table + Zustand + Zod.
- **Backend**: FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Uvicorn + Alembic (migraciones).
- **DB**: PostgreSQL (vistas `v_run_*`).
- **Scraping**: Scrapy (vive en este repo, carpeta `scrapy_project/`).
- **Calidad**: ESLint + Prettier (FE), Ruff + Black + MyPy (BE), pre-commit hooks.
- **Commits/PRs**: Conventional Commits, PR checks obligatorios.

---

## 2) Requisitos previos

- **Node.js** ≥ 20.x y **pnpm** ≥ 9.x
- **Python** ≥ 3.12 y **pipx** o **pip** + **virtualenv**
- **PostgreSQL** ≥ 14
- **Redis** (si usas workers/colas)
- **Make** (recomendado)

---

## 3) Setup local (primer uso)

1. Clona el repo y copia variables:

   ```bash
   cp .env.example .env
   # Edita valores (DB, Slack, etc.). Nunca subas tokens reales.
   ```

2. **Backend**:

   ```bash
   cd apps/api
   python -m venv .venv && source .venv/bin/activate
   pip install -U pip wheel
   pip install -r requirements.txt
   # DB: crear y migrar si aplica
   make db-up           # opcional: docker compose up -d postgres
   make db-migrate      # alembic upgrade head (si usamos Alembic)
   make dev             # uvicorn app.main:app --reload
   ```

3. **Frontend**:

   ```bash
   cd apps/web
   pnpm install
   pnpm dev
   # App corre en http://localhost:3000
   ```

4. **Scraping** (opcional, si vas a tocarlo):

   ```bash
   cd scrapy_project
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   make scrape
   ```

---

## 4) Flujo de trabajo (Git)

- **Branching**:
  - `main`: estable, protegido.
  - `develop` (si existe): integración.
  - Feature branches: `feat/<slug>`, `fix/<slug>`, `chore/<slug>`.

- **Conventional Commits**:
  - `feat: añade tabla de artículos`
  - `fix: corrige paginación`
  - `chore: bump deps`
  - `docs: actualiza README`
  - `refactor: desacopla servicio`
  - `test: añade tests`

- **PRs**:
  - Pequeños y enfocados.
  - Incluye descripción (qué/por qué/cómo).
  - Checklist: tests pasan, linter ok, sin secretos.
  - Solicita review a 1–2 personas.
  - **No** merges directos a `main`.

---

## 5) Estándares de código

### Frontend (apps/web)

- **TypeScript estricto**: sin `any` implícitos.
- **Next.js 14 App Router** (Server Components por defecto, Client Components solo si hay estado/efectos).
- **UI**: Tailwind + shadcn/ui (consistencia visual, tokens).
- **Estado**: Zustand para filtros/estado local; evita over-engineering.
- **Tablas**: TanStack Table (sorting, paginación, column visibility).
- **Validación**: Zod para DTOs en FE (y adaptar schemas a/from BE).
- **Fetch**:
  - En server (RSC) cuando sea posible.
  - Usa `NEXT_PUBLIC_API_BASE_URL` para apuntar a la API.
  - Maneja errores con toasts/modals y estados vacíos (`EmptyState`).

- **Accesibilidad**: roles ARIA, focus visible, teclas.

### Backend (apps/api)

- **FastAPI** con **Pydantic v2** (DTOs) y **SQLAlchemy 2.0** (ORM/SQL expressions).
- **Rutas** versionadas: `/api/v1/...`.
- **Validación**: query params con Pydantic; sanitizar entradas.
- **DB**:
  - Consultas a tablas y vistas `v_run_*`.
  - Indices donde aplique; evitar N+1 (use `selectinload`/`joinedload`).

- **Migrations**: Alembic (scripts claros, reversibles).
- **Errores**: HTTPException con códigos precisos; logs con contexto.

### Scraping

- Mantener reglas de deduplicación y límites (consecutivos/in-a-row) claros.
- No bloquear pipeline si Slack falla.
- Logs con `run_id`.

---

## 6) Linting, formateo y hooks

- **Frontend**:

  ```bash
  pnpm lint
  pnpm format
  ```

  ESLint + Prettier integrados. Fija reglas en `.eslintrc.*`.

- **Backend**:

  ```bash
  ruff check apps/api
  ruff format apps/api
  mypy apps/api
  pytest
  ```

- **pre-commit**:
  - Instala una vez: `pre-commit install`
  - Hook: ruff, black, prettier, eslint, detect-secrets.

---

## 7) Tests

- **FE**: Vitest/Playwright (smoke + e2e básicos para flujos críticos).
- **BE**: Pytest (fixtures de DB, test de endpoints con `TestClient`).
- **Datos**: mocks/stubs para no depender de scrape vivo.

---

## 8) Base de datos y migraciones

- `.env` define credenciales (usa `.env.example` de guía).
- **Alembic** para cambios de esquema.
- **Vistas**:
  - Mantener `schema.sql` fuente de verdad de vistas/materializadas.
  - Si cambian columnas consumidas por FE, coordina PRs FE/BE.

---

## 9) Seguridad, secretos y permisos

- **Nunca** subas `.env` reales.
- Usa `.env`, variables en CI (GitHub Actions), y `doppler`/`sops`/`1Password` si aplica.
- **Slack**:
  - No pegues tokens ni URLs de webhook en issues/PRs.
  - Prueba scopes en un canal de pruebas.

- **RBAC** (cuando esté): respeta roles `admin` / `read_only` en endpoints y UI.
- **Auditoría**: registra cambios (quién, qué, antes/después) en bitácora.

---

## 10) Issues, labels y milestones

- **Labels**: `P0`, `P1`, `P2`, `bug`, `feat`, `chore`, `docs`, `security`, `infra`, `api`, `frontend`, `scraping`.
- **Milestones**: usa fases del roadmap (MVP → P1 → P2…).
- **Checklist**: desglosa tareas grandes en subtareas/tickets atómicos.

---

## 11) Rendimiento & UX

- **FE**: SSR/streaming para vistas grandes; paginación server-side a partir de X registros; memoización en Client Components.
- **BE**: indexado, límites, `LIMIT/OFFSET` o `keyset pagination` según caso.
- **CDN**: estáticos y caching de respuestas de solo lectura (cuando se permita).

---

## 12) Releases y versionado

- **SemVer** (MAJOR.MINOR.PATCH).
- Changelog generado de Conventional Commits (ej. `release-please`).

---

## 13) Cómo proponer cambios (resumen)

1. Abre un **issue** con contexto y criterio de aceptación.
2. Crea branch `feat/...` y desarrolla con tests y linters verdes.
3. Abre **PR** con descripción, screenshots (si UI), y pasos de prueba.
4. Pide review; atiende comentarios.
5. Merge (squash) cuando CI apruebe.
6. Actualiza documentación si aplica.

---

## 14) Contacto

- Dudas o bloqueos → abre issue `question` o menciona al maintainer en el PR.
- Propuestas mayores de arquitectura → crea un ADR (`/docs/adr/`) y discútelo en un issue antes de implementar.

---

**Gracias por ayudar a que Posverdad sea más útil, robusto y agradable de usar.**
