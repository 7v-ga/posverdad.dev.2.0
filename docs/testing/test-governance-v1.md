# Posverdad v2 — Test Governance v1

**Estado:** propuesta activa  
**Ámbito:** backend (Scrapy pipelines + storage_helpers + API), con foco en DB/NLP best-effort  
**Principio rector:** los tests son el contrato; el contrato debe estar escrito, tipificado y versionado.

---

## 1. Objetivo

Establecer reglas para diseñar, mantener y evolucionar tests de Posverdad v2 de forma que:

- Detecten regresiones reales (transacciones abortadas, ruptura de idempotencia, escrituras destructivas).
- Eviten fragilidad por acoplamiento a implementación (p. ej. `call_count`, `startswith` literal de SQL).
- Permitan convivencia entre:
  - **unit tests** con mocks,
  - **integration tests** con Postgres real (Alembic),
  - y eventualmente **end-to-end** (scrape real controlado).

---

## 2. Principios no negociables

### 2.1 Tests verifican **efectos**, no “cómo”

**Preferir:**

- filas insertadas / relaciones creadas,
- valores finales (fields, invariants),
- commits/rollbacks en fronteras claras.

**Evitar (salvo contrato explícito):**

- `execute.call_count`,
- `sql.startswith(...)` sin normalizar,
- ordenar de queries salvo que sea parte del contrato.

### 2.2 Contratos explícitos por capa

Cada función pública debe declarar su contrato observable:

- Entrada aceptada.
- Qué cambia en DB (tablas/relaciones) y qué no.
- Qué pasa ante error (raise vs best-effort).
- Reglas de no sobrescritura destructiva (COALESCE).

**Si el contrato cambia, se versiona** (v2, v3…).

### 2.3 DB real manda

Los tests con mocks **no** deben imponer un contrato incompatible con Postgres real.

Cuando haya conflicto:

- el contrato de **integration** (Postgres + Alembic) prevalece,
- y los unit tests se ajustan para validar efectos con un mock más realista o con aserciones más semánticas.

### 2.4 Best-effort no debe romper pipelines

Todo componente “derivado” (NLP, entidades, framing, joins opcionales) debe:

- fallar sin abortar transacción principal,
- degradar con elegancia,
- registrar warning, no fatal.

---

## 3. Taxonomía de tests

### 3.1 Unit tests (rápidos, sin Postgres)

**Objetivo:** pureza lógica + branching + normalización.

Se permiten mocks, pero deben:

- simular una interfaz mínima coherente (cursor/conn),
- evitar depender del string exacto del SQL.

Ejemplos válidos:

- normalización de fechas, URLs, body length.
- `_as_nullable_float`, parseos y fallbacks.
- si input vacío → early return sin tocar DB.
- si manage_tx=True → se llama rollback ante excepción.

### 3.2 Contract tests (doble ejecución: mock + real)

**Objetivo:** asegurar que helpers polimórficos se comportan igual bajo cursor real y cursor mock.

Recomendado para:

- `store_article`
- `save_keywords`
- `save_entities`
- `save_framing`
- `save_categories_and_link`

### 3.3 Integration tests (Postgres real + Alembic)

**Objetivo:** validar SQL real y schema real.

Incluyen:

- `alembic upgrade head` antes de suite.
- inserciones reales y verificación de constraints/triggers.
- validación de invariants: NOT NULL, FK, UNIQUE.

### 3.4 E2E / smoke (scrape reducido)

**Objetivo:** correr un spider (limitado) en entorno de test y verificar persistencia mínima.

Reglas:

- muy pocos artículos (2–5),
- dominios controlados,
- se ejecuta en CI solo si el tiempo lo permite.

---

## 4. Reglas de diseño para mocks de DB

### 4.1 No usar “startswith frágil” sin normalización

Si un mock reacciona al SQL, debe normalizar:

- `sql = sql.strip().lower()`
- opcional: colapsar whitespace

Y preferir `in` / `contains` en vez de `startswith`.

### 4.2 Evitar `call_count` como aserción primaria

Se puede usar `call_count` solo si:

- el contrato explícito lo define,
- o la prueba busca detectar loops infinitos o duplicación accidental grave.

En general, preferir:

- inspeccionar parámetros (calls),
- inspeccionar “estado” del mock (p. ej. `db.links`, `db.cat`),
- o usar fixtures de DB real.

### 4.3 Mocks deben reflejar interfaces reales

Si tu código usa `with conn.cursor() as cur:`, el mock debe implementar:

- `cursor()` que devuelva un objeto con `__enter__/__exit__`,
- `execute()`, `fetchone()`.

Si tu código usa `executemany()`, el mock debe:

- implementarlo o el test no debe depender de que se llame.

---

## 5. Contratos recomendados para helpers “conflictivos”

### 5.1 `link_article_categories`

**Contrato recomendado:** dedup a nivel app (menos IO) + `ON CONFLICT DO NOTHING` como safety net.

- Resultado observable: pares únicos insertados.
- No contrato: “1 execute por input”.

### 5.2 `_pg_table_exists`

- En unit tests, puede devolver “unknown=True” si el cursor no soporta `to_regclass`.
- En integration tests, debe comportarse fiel a Postgres.

### 5.3 `save_keywords`

- Si falla una operación DB y manage_tx=True → rollback + raise `RuntimeError`.
- Si manage_tx=False (cursor directo) → propaga error (o raise RuntimeError según contrato), pero **no** debe “silenciar” sin feedback.

---

## 6. Estrategia de evolución (para evitar whack-a-mole)

### 6.1 “Golden path” por funcionalidad crítica

Definir tests de integración para:

- insert/upsert de articles,
- persistencia de `polarity/subjectivity` (fill-only-if-null),
- persistencia de `entity_mentions` (raw),
- dedupe por URL / body_hash.

### 6.2 Ajustar unit tests para no competir con integración

Si un unit test impone implementación, se refactoriza para:

- validar efectos,
- o convertirse en contract test.

### 6.3 Versionado

Cuando se cambia un contrato:

- se actualiza este documento,
- se etiqueta el cambio (Test Governance v2),
- y se deja una nota en el PR.

---

## 7. Checklist de PR (testing)

Antes de merge:

- [ ] Los unit tests no dependen de SQL exacto (o justifican excepción).
- [ ] No hay `call_count` sin contrato explícito.
- [ ] Helpers DB críticos tienen al menos 1 integration test.
- [ ] NLP/derivados son best-effort (no rompen TX principal).
- [ ] No se introducen escrituras destructivas (COALESCE/guardrails).
- [ ] Si se cambia un contrato, se actualiza Test Governance.

---

## 8. Roadmap inmediato (2–3 sesiones)

1. **Inventario**: listar todos los tests por tipo (unit/contract/integration).
2. **Normalización**: crear `tests/helpers/db_mocks.py` con mocks estándar (`DummyConn`, `DummyCursor`, `CaptureDB`).
3. **Integración mínima**: añadir 3 integration tests con DB real + Alembic head.
4. **Refactor**: migrar tests frágiles a validación por efectos.

---

## 9. Anexo: definición de “efectos observables”

Un test es “observable” si afirma sobre:

- filas/relaciones insertadas,
- valores persistidos (select),
- invariants (unique/not null),
- comportamiento de error (raise/rollback),
- métricas o counters (stats), siempre que sean parte del contrato.
