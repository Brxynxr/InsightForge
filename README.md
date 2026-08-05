# PromptForge

> Plataforma AI modular de grado empresarial para optimizar flujos de trabajo de procesamiento de texto antes de enviarlos a LLMs.

[![CI](.github/workflows/ci.yml)](.github/workflows/ci.yml)

## Descripción General

PromptForge ingresa conjuntos de datos de Excel, opcionalmente optimiza texto mediante traducción o futuras estrategias, mide el consumo de tokens usando tiktoken, estima costos, envía prompts a un LLM, parsea respuestas estructuradas y exporta resultados.

## Arquitectura

Desarrollada como una plataforma de software empresarial con una arquitectura layered:

```
SPA React → API REST FastAPI → Pipeline de Procesamiento → Proveedor LLM → Parser → Exportador → Historia
```

Cada etapa de procesamiento es un Engine independiente con un contrato único: `execute(context)`.

### Fases de Desarrollo

| Fase | Descripción |
|------|-------------|
| Fase 1 | Fundamentos (estructura, Docker, configuración, CI/CD, docs) ✅ |
| Fase 2 | SPA Frontend ✅ |
| Fase 3 | API Backend Completa |
| Fase 4 | Módulos de Negocio + Engines |
| Fase 5 | Deploy de Producción |

## Tecnologías Utilizadas

**Frontend**: React 19, TypeScript, Vite, TailwindCSS, React Router, TanStack Query, React Hook Form, Zod, Zustand

**Backend**: FastAPI, Python 3.12+, Pydantic, Poetry, Loguru

**Procesamiento**: Pandas, OpenPyXL, NumPy, tiktoken (o200k_base), deep_translator

**Base de Datos**: PostgreSQL, Redis (cache opcional)

## Inicio Rápido

### Opción 1: Docker (Recomendado)

```bash
# Desde la raíz del proyecto
docker compose up --build

# O en segundo plano
docker compose up -d --build
```

Una vez levantado, accede a:
- **Frontend**: http://localhost:5173
- **API Backend**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Opción 2: Desarrollo Local

#### Backend

```bash
cd backend
poetry install
cp .env.example .env
poetry run uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Parar servicios

```bash
docker compose down -v
```

## Estructura del Proyecto

```
promptforge/
├── frontend/              # SPA React 19
├── backend/               # Backend FastAPI
│   ├── app/
│   │   ├── api/           # Rutas REST API
│   │   ├── core/          # Configuración, base de datos, logging
│   │   ├── middleware/    # Middleware personalizado
│   │   ├── engines/       # Motores de procesamiento
│   │   ├── models/        # Modelos SQLAlchemy
│   │   ├── schemas/       # DTOs Pydantic
│   │   ├── services/      # Lógica de negocio
│   │   ├── migrations/    # Migraciones Alembic
│   │   └── main.py        # Punto de entrada
│   ├── tests/
│   ├── .env.example
│   └── pyproject.toml
├── docs/                  # Documentación + ADRs
├── prompts/               # Plantillas de prompts
├── docker/                # Dockerfiles, configuración nginx
├── scripts/               # Scripts de utilidad
├── docker-compose.yml     # Docker Compose (raíz del proyecto)
├── .github/workflows/     # CI/CD
└── README.md              # Este archivo
```

## Licencia

Ver archivo LICENSE.
