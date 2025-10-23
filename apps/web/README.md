# 🧭 Posverdad Frontend

Frontend del sistema **Posverdad**, proyecto de análisis automatizado de medios chilenos.  
Basado en **Next.js 14 (App Router)** con **TypeScript**, **Tailwind**, **shadcn/ui**, **TanStack Table**, **Zustand** y **Zod**.

---

## 📦 Stack técnico

| Componente | Tecnología |
|-------------|-------------|
| Framework | Next.js 14 (App Router) |
| Lenguaje | TypeScript estricto |
| UI | TailwindCSS + shadcn/ui |
| Estado global | Zustand + persistencia localStorage |
| Validación | Zod |
| Tabla / Filtros | TanStack Table v8 |
| Build Tool | pnpm + corepack (Node 20 LTS) |

---

## 🚀 Instalación y entorno

### 1️⃣ Requisitos previos
- Node.js **v20.x**  
- pnpm (**corepack habilitado**)  
- nvm (opcional, recomendado)  
- Ubuntu/Linux user-space (sin sudo global)

### 2️⃣ Setup

```bash
# Instalar y activar Node 20
nvm install 20
nvm use 20
corepack enable
corepack prepare pnpm@latest --activate

# Instalar dependencias
cd apps/web
pnpm install
```

### 3️⃣ Variables de entorno

Archivo `.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000   # backend FastAPI (lectura/escritura)
NEXT_PUBLIC_FEATURE_BULK=1                       # activa barra de selección masiva (modo beta)
```

> Si `NEXT_PUBLIC_FEATURE_BULK` ≠ `1`, la barra de selección y las acciones masivas se ocultan.

---

## 🧱 Estructura del proyecto

```
apps/web/
 ├── app/
 │   ├── (shell)/
 │   │    ├── layout.tsx
 │   │    └── topbar.tsx
 │   └── articles/
 │        ├── page.tsx
 │        └── components/
 │             ├── ArticlesTable.tsx
 │             ├── ArticlesFilters.tsx
 │             ├── ArticleDetailDialog.tsx
 │             └── EntitiesDialog.tsx
 ├── api/
 │   └── articles/route.ts          # mock local (se sustituirá por FastAPI)
 ├── lib/
 │   ├── csv.ts                     # exportar CSV (UTF-8, comillas escapadas)
 │   ├── utils.ts                   # utilidades varias
 │   └── schemas.ts                 # Zod schemas: Article, ArticlesResponse, etc.
 ├── store/
 │   └── articles-store.ts          # Zustand store + acciones locales (mock)
 ├── public/
 ├── styles/
 │   └── globals.css
 └── package.json
```

---

## ⚙️ Scripts útiles

| Comando | Descripción |
|----------|-------------|
| `pnpm dev` | Ejecuta el servidor Next.js con Turbopack |
| `pnpm build` | Compila para producción |
| `pnpm start` | Sirve la build compilada |
| `pnpm lint` | Linter |
| `pnpm typecheck` | Verificación TypeScript (`tsc --noEmit`) |
| `pnpm format` | Formatea con Prettier |

---

## 🧩 Features implementadas

### 🧠 **A. UX Polish**
- Búsqueda con debounce (300 ms)
- Estado vacío con CTA “Limpiar filtros”
- Exportar CSV filtrado (UTF-8)
- Toggle de columnas (persistente en `localStorage`)
- Selector de pageSize (10/20/50) persistente

### 🔗 **B. URL-Driven Filters**
- Filtros ↔ `searchParams` sincronizados (shareable links)
- Estado rehidratable desde la URL
- Persistencia combinada (`localStorage` + URL)

### 🧩 **C. Bulk Entities (Mock + Flag)**
- Visible si `NEXT_PUBLIC_FEATURE_BULK=1`
- Selección por fila y “Seleccionar todo (página)”
- Acciones:  
  - **Bloquear / Desbloquear** entidades  
  - **Agregar alias** masivamente
- Estado local mock (sin API real)
- Feedback básico (`alert`, puede migrar a `toast()`)

---

## 📡 Integración API real (pendiente)

**Próxima fase (P1.5):**

1. Reemplazar `app/api/articles/route.ts` (mock) por fetch real:
   ```ts
   const base = process.env['NEXT_PUBLIC_API_BASE_URL']
   const res = await fetch(`${base}/api/articles?...`)
   ```
2. Validar con `ArticlesResponse` (Zod).
3. Sincronizar paginación (server-side o híbrida).
4. Conectar acciones `addAlias` / `blockEntity` al backend FastAPI.

---

## 🔒 Seguridad y control

- `main` y `develop` protegidas (1 review, checks automáticos).
- Workflows CI:  
  - `Auto label PRs / label (pull_request)`  
  - `Auto label by title / label-by-title (pull_request)`
- Script CLI para (des)activar protecciones:
  `scripts/protect-branches.sh`

---

## 🧪 QA y testing manual

**Flujo recomendado:**

| Caso | Qué validar |
|------|--------------|
| Filtros | Cambios en UI reflejados en la URL, recarga conserva estado |
| CSV | Exporta correctamente los artículos visibles |
| Persistencia | pageSize y columnas sobreviven al refresh |
| Bulk (flag on) | Seleccionar todo, bloquear/desbloquear, agregar alias |
| Estado vacío | “No hay resultados con estos filtros” + botón “Limpiar filtros” |
| Layout | Sin errores de hidratación, sin botones anidados |

---

## 🧭 Próximos pasos

1. **Integrar API FastAPI real** (`NEXT_PUBLIC_API_BASE_URL`)
2. **Persistir cambios de entidades** (`blocked`, `aliases`) vía backend
3. **Agregar Auth/RBAC** con NextAuth y roles
4. **Dashboards BI** con vistas SQL (`v_run_*`)
5. **Toasts e internacionalización (es-CL)**

---

## 👥 Contacto / roles

| Rol | Persona / Función |
|-----|--------------------|
| Owner / Dev principal | Gabriel (7v-ga) |
| Asistente técnico | ChatGPT (Postverdad Context) |
| Estado del proyecto | En desarrollo activo – Fase P1 finalizada |

---

### 📄 Licencia
Software en desarrollo, uso interno de investigación (no redistribuido públicamente).

---

**Última actualización:** 2025-10-21  
**Versión:** P1 (Frontend UX + Filtros + Bulk Mock)
