-- ===============================================
-- Posverdad — schema.sql (modo Alembic)
-- ===============================================
-- Este archivo NO define tablas.
-- La estructura (DDL) se gestiona con Alembic (migrations en ./alembic/versions).
--
-- ¿Para qué queda schema.sql entonces?
--   1) Activar extensiones de Postgres opcionales
--   2) Crear vistas/materialized views que NO estén modeladas en SQLAlchemy
--   3) Ajustes puntuales de configuración (raro; preferir Alembic)

-- =========================
-- Extensiones (opcionales)
-- =========================

-- Búsqueda/fuzzy matching (útil si luego haces sugerencias de alias por similitud)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Si alguna vez necesitas generar UUIDs desde SQL:
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Si vas a usar búsquedas semánticas / vectores en el futuro:
-- CREATE EXTENSION IF NOT EXISTS vector;

-- =========================
-- Vistas (si aplican)
-- =========================
-- Nota: antes existía v_run_summary vinculada a nlp_runs.
-- Si tu modelo nuevo ya NO usa nlp_runs, esta vista debe desaparecer y
-- el código que la consulta debe migrarse a la nueva lógica.
--
-- Si en el futuro quieres una vista para resúmenes de scraping/NLP,
-- créala aquí (o como migration Alembic explícita si prefieres versionarlo).
