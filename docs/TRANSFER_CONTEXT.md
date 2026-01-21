Posverdad v2 — Documento de Traspaso de Contexto

Estado post-migración Alembic (enero 2026)

1. Contexto general del proyecto

Posverdad es una plataforma de scraping + NLP + análisis editorial con:

Scrapy para ingestión de noticias

PostgreSQL como DB principal

FastAPI como API

Next.js como frontend

NLP híbrido (spaCy + pysentimiento + heurísticas)

Persistencia estructurada de artículos, entidades, menciones, framing y métricas

El proyecto se encuentra en una migración mayor de esquema hacia Alembic (v2), abandonando SQL “manual” como fuente de verdad.

2. Estado actual del repositorio
   Rama activa
   migration/alembic-v2

Últimos commits relevantes

alembic: v2 schema baseline and migrations

alembic v2: align app models + storage with schema

docs(ai): add AI Protocol v2 and formalize NLP governance

Tests

✅ make test y make test-nocov pasan

⚠️ Los tests no cubren completamente el scrape real

3. Base de datos y migraciones
   Alembic

Alembic ya está integrado

alembic heads → único head

alembic upgrade head aplicado correctamente

Migraciones existentes incluyen:

articles

entities

entity_mentions

entity_actions

triggers (updated_at)

defaults y constraints

Problemas detectados

Autogenerate no siempre da no-op

Diferencias entre:

modelos Python (apps/api/models.py)

helpers SQL (storage_helpers.py)

schema real en DB

4. Scraping: estado funcional real
   Lo que sí funciona

Scrapy corre

Artículos sí se insertan en articles

URLs canónicas funcionan

Deduplicación básica funciona

Tests pasan

Lo que no está funcionando correctamente

polarity / subjectivity

Campos existen

No siempre se persisten

NLP se ejecuta, pero el flujo DB es inconsistente

entities / entity_mentions

Tablas existen

Inserciones no ocurren o quedan vacías

Falta o inconsistencia en:

\_ensure_entity

normalización de entidades

vínculo artículo ↔ entidad

preprocessed_data

A veces NULL

A veces no se guarda aunque NLP devuelve datos

5. Pipelines (Scrapy)
   Archivo clave
   scrapy_project/pipelines.py

Situación

process_item() fue refactorizado varias veces

Se intentó compatibilidad con tests usando:

try:
store_article(cur, item, return_created=True)
except TypeError:
store_article(cur, item)

Esto introdujo fragilidad transaccional

Problemas actuales

Errores tipo:

current transaction is aborted

Conexiones cerradas en scrape largo

Rollbacks implícitos no controlados

👉 Necesario: revisar límites claros de transacción:

Qué abre / cierra la transacción

Qué función puede fallar sin abortar todo

6. storage_helpers.py
   Archivo clave
   scrapy_project/storage_helpers.py

Situación

Refactor fuerte para:

soportar cursor o conexión

tests con mocks

\_ensure_source() funciona (aunque largo)

NO existen aún:

\_ensure_entity()

\_ensure_category()

Esto explica:

entidades vacías

categorías vacías (esperable para El Mostrador)

7. API (FastAPI)
   Estado

FastAPI levanta correctamente tras:

make py-install
uvicorn apps.api.main:app --reload

Error previo de ModuleNotFoundError: fastapi fue por entorno mal instalado

Modelos alineados parcialmente con Alembic

8. Frontend
   Estado

Cambios locales no commiteados

ESLint / Prettier funcionan

Visualización depende de:

articles

entities

entity_mentions (actualmente vacías)

Frontend no es el foco inmediato hasta estabilizar DB + NLP.

9. Protocolo de IA (AI Protocol)

Existe AI Protocol v2

Formaliza:

qué es NLP “oficial”

qué campos son derivados

qué puede sobrescribirse

Ya está integrado en docs

Sirve como contrato técnico para lo que sigue

10. Problemas prioritarios a resolver (orden recomendado)
    Fase 1 — Estabilidad DB / Scrape

Verificar esquema real (psql \dt, \d articles)

Asegurar search_path = public

Revisar transacciones en pipeline

Asegurar store_article() nunca deje la transacción en estado abortado

Fase 2 — NLP core

Arreglar persistencia de:

polarity

subjectivity

Definir un solo punto donde se actualizan

Fase 3 — Entidades

Implementar \_ensure_entity()

Implementar inserción en:

entities

entity_mentions

Validar con 2–3 artículos reales

11. Próximo paso en el chat nuevo

En el nuevo chat, conviene empezar con:

Compartir estos archivos:

scrapy_project/pipelines.py

scrapy_project/storage_helpers.py

apps/api/models.py

última migración Alembic

Pregunta inicial recomendada:

“Ayúdame a estabilizar primero la persistencia de polarity/subjectivity sin romper tests ni scrape.”

12. Nota final

El estado actual no es un desastre:
es exactamente el punto típico de una migración estructural real.

Lo importante es que ahora:

hay Alembic

hay tests

hay protocolo de IA

hay visibilidad clara de los problemas

Eso nos permite continuar de forma mucho más controlada en el siguiente chat.
