# AI Protocol v2 — Posverdad

## 1. Propósito

Este protocolo define **cómo se integra Inteligencia Artificial (IA / NLP)** en el proyecto **Posverdad**, estableciendo límites claros entre:

- recolección de datos,
- persistencia en base de datos,
- análisis automatizado,
- y revisión humana.

La IA es **asistiva**, nunca decisional.

---

## 2. Principios rectores

### 2.1 IA como señal débil (weak signal)

- Ningún resultado de IA se considera verdad.
- Todo output es **provisional**, **probabilístico** y **revisable**.

### 2.2 Persistencia tolerante a fallos

- Fallos de IA **jamás** deben abortar:
  - scrapes,
  - transacciones DB,
  - ni pipelines completos.
- El sistema debe degradar con elegancia.

### 2.3 No sobrescritura destructiva

- La IA **no puede sobrescribir datos existentes** con valores nulos o vacíos.
- Toda actualización usa lógica `COALESCE` o equivalente.

### 2.4 Separación estricta de responsabilidades

| Capa            | Responsabilidad                |
| --------------- | ------------------------------ |
| Scraping        | Extraer datos crudos           |
| Storage         | Persistir sin lógica semántica |
| NLP / IA        | Analizar y sugerir             |
| Revisión humana | Validar, corregir, decidir     |

---

## 3. Contrato de datos NLP

### 3.1 Campos NLP soportados

Todos son **opcionales** y **nullable**:

- `polarity`
- `subjectivity`
- `entities`
- `framing`
- `preprocessed_data`

### 3.2 Reglas de escritura

- Si un campo ya tiene valor → **NO se borra**
- Si NLP no produce resultado → **no se escribe**
- El almacenamiento es **best-effort**

---

## 4. Entidades y menciones

### 4.1 entity_mentions

- Representan detecciones automáticas.
- No implican existencia canónica.
- Son revisables y versionables.

### 4.2 entities

- Son entidades consolidadas.
- Requieren revisión humana o reglas explícitas.

> Nunca se crean entidades canónicas solo por NLP.

---

## 5. Framing

- `framing` es interpretativo.
- Se almacena como:
  - texto,
  - JSON,
  - o estructura flexible.
- Su ausencia **no es error**.

---

## 6. Transacciones y errores

### 6.1 Regla de oro

> **La IA no puede romper una transacción.**

Ejemplos prohibidos:

- rollback por error NLP
- excepción IA que bloquee `store_article`
- dependencia fuerte entre scrape y análisis

### 6.2 Logging

- Los errores NLP se registran como `warning`
- Nunca como `error` fatal

---

## 7. Tests

Los tests deben asumir que:

- NLP puede no existir
- NLP puede fallar
- NLP puede devolver estructuras parciales

Un test que falla porque la IA no respondió **está mal diseñado**.

---

## 8. Gobernanza

- Este protocolo es **fuente de verdad**
- Cambios requieren:
  - justificación escrita,
  - versión nueva (`v3`, `v4`, …)

---

## 9. Resumen operativo

✔ IA ayuda  
✔ IA sugiere  
✔ IA falla sin romper  
✖ IA no decide  
✖ IA no borra  
✖ IA no bloquea

---

**Posverdad — AI Protocol v2**
