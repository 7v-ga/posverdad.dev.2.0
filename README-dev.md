# 👩‍💻 Guía de desarrollo — Posverdad

Guía para preparar el entorno, correr pruebas y contribuir a **Posverdad** en local.

---

## 🔧 Requisitos

- Ubuntu 22.04+ (recomendado 24.04)
- Python **3.12** con `venv` / `pip`
- **Docker** + Docker Compose plugin
- **GNU make**
- Internet (descarga de modelos NLP)
- Node.js + pnpm (para el frontend Next.js)

> Opcional pero útil: acceso a Docker sin sudo
>
> ```bash
> sudo usermod -aG docker "$USER"  # cierra sesión y vuelve a entrar
> ```

---

## ⚡️ Setup rápido (recomendado)

```bash
make setup
make health-check
```

---

## 🚀 Levantar API y frontend

### Backend — FastAPI (`apps/api`)

```bash
make api-dev
```

Disponible en:

- http://localhost:8000
- http://localhost:8000/docs
- http://localhost:8000/articles/

### Frontend — Next.js (`apps/web`)

Desde la raíz del repo:

```bash
pnpm dev
```

Frontend en:

- http://localhost:3000

### Configuración obligatoria del frontend

Archivo:

```
apps/web/.env.local
```

Contenido:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

> La antigua ruta `/api/articles` de Next.js está eliminada y ya no se usa.

---

## 🧪 Testing

```bash
make test
DEFAULT_TEST_SCOPE=all make test
make test-int
make coverage-html
make reset
make reset-all
```

---

## 🗂️ Estructura relevante del proyecto

```
apps/
  api/
  web/
scrapy_project/
db/
makefiles/
scripts/
tests/
```

---

## 🧯 Problemas comunes

- **DB no responde:**  
  `make db-up && make db-wait`

- **spaCy no instalado:**  
  `python -m spacy download es_core_news_md`

- **Docker sin permisos:**  
  `sudo usermod -aG docker "$USER"`

---

## 🤝 Contribuir

1. Crear rama feature.
2. Ejecutar `make test`.
3. Ejecutar integración antes de merge.
4. Abrir PR.

---

## 📬 Contacto

Desarrollado por **Gabriel Aguayo Young**  
gabrielaguayo@7v.cl
