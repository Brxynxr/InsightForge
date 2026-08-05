# PromptForge

> Plataforma AI modular para análisis de reseñas de App Store con procesamiento de alto rendimiento.

[![CI](.github/workflows/ci.yml)](.github/workflows/ci.yml)

## Descripción

PromptForge procesa archivos Excel con reseñas de aplicaciones, las tokeniza con tiktoken, opcionalmente las traduce para optimizar costos, las envía a un LLM para clasificación de errores técnicos, y exporta resultados estructurados con métricas detalladas.

### Benchmark (150k reseñas en ~12 segundos)

| Archivo | Registros | Tiempo | Tokens | Costo estimado |
|---------|-----------|--------|--------|----------------|
| 50k reseñas | 50,000 | ~4s | 741,737 | $1.85 USD |
| 100k reseñas | 100,000 | ~8s | 1,480,734 | $3.70 USD |
| 150k reseñas | 150,000 | ~12s | 2,219,100 | $5.55 USD |

## Arquitectura

```
SPA React → API REST FastAPI → Pipeline de Engines → LLM → Parser → Export → DB
```

Cada etapa es un Engine independiente con contrato `execute(context)`:

- **InputEngine** — Lectura de archivos Excel/CSV
- **ValidationEngine** — Validación de columnas y registros vacíos
- **OptimizationEngine** — Traducción y optimización de tokens
- **TokenizerEngine** — Conteo de tokens (tiktoken o200k_base)
- **CostEngine** — Cálculo de costos ($2.50/M tokens)
- **ExportEngine** — Exportación a JSON/CSV
- **HistoryEngine** — Tracking de métricas en pipeline
- **TokenCompareEngine** — Comparación ES vs EN
- **AnalyzeEngine** — Clasificación de errores via LLM

## Tecnologías

| Capa | Stack |
|------|-------|
| Frontend | React 19, TypeScript, Vite, TailwindCSS, TanStack Query, Zustand |
| Backend | FastAPI, Python 3.12+, Pydantic, Poetry |
| Procesamiento | Pandas, tiktoken, httpx, OpenPyXL |
| Base de datos | PostgreSQL 16, Redis 7 |
| Infraestructura | Docker Compose, Nginx, GitHub Actions CI |

## Inicio Rápido

### Docker (Recomendado)

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

### Desarrollo Local

```bash
# Backend
cd backend && poetry install && poetry run uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Estructura

```
promptforge/
├── frontend/                  # SPA React 19
│   └── src/
│       ├── components/pages/  # Upload, Benchmark, History, Dashboard, Settings
│       ├── hooks/             # React Query hooks
│       ├── services/          # API client (axios)
│       ├── stores/            # Zustand state
│       └── types/             # TypeScript interfaces
├── backend/                   # FastAPI
│   └── app/
│       ├── api/routes.py      # Endpoints REST
│       ├── engines/           # 9 motores de procesamiento
│       ├── models/            # SQLAlchemy (Job, JobRecord)
│       ├── schemas/           # Pydantic DTOs
│       ├── services/          # Pipeline + Benchmark
│       └── main.py            # FastAPI app
├── docker/                    # Dockerfiles + nginx + init.sql
├── scripts/                   # Generador de reseñas de prueba
├── docs/                      # Documentación + ADRs
├── prompts/                   # Plantillas de prompts
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/benchmark` | Benchmark de rendimiento (sin LLM) |
| POST | `/api/v1/analyze` | Análisis completo con LLM |
| POST | `/api/v1/process` | Pipeline estándar |
| GET | `/api/v1/history` | Historial de procesos |
| GET | `/api/v1/history/{id}` | Detalle de un proceso |
| GET | `/api/v1/health` | Health check |

## Licencia

Ver archivo LICENSE.
