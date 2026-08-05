# Backend de PromptForge

## Configuración

```bash
# Instalar Poetry (si aún no está instalado)
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependencias
poetry install

# Crear archivo .env
cp .env.example .env

# Ejecutar migraciones (opcional durante la Fase 1)
poetry run alembic upgrade head

# Iniciar servidor
poetry run uvicorn app.main:app --reload
```

## API

- **Health Check**: `GET /api/v1/health`
- **Procesar Archivo**: `POST /api/v1/process` (carga de archivo Excel)
- **Historial**: `GET /api/v1/history`

## Testing

```bash
poetry run pytest -v
poetry run ruff check app/
poetry run mypy app/
```

## Arquitectura

El backend sigue una arquitectura layered:

```
app/
├── api/              # Capa de API (rutas REST)
├── core/             # Configuración, base de datos, logging
├── middleware/       # Middleware personalizado
├── engines/          # Motores de procesamiento (cada uno con contrato execute(context))
├── models/           # Modelos SQLAlchemy
├── schemas/          # Esquemas Pydantic (DTOs)
├── services/         # Lógica de negocio
├── migrations/       # Migraciones con Alembic
└── main.py           # Punto de entrada de la aplicación FastAPI
```

## Pipeline de Procesamiento

Cada motor sigue el contrato `execute(context: EngineContext) -> EngineContext`:

1. **Input Engine** - Lee archivos Excel, genera batches
2. **Validation Engine** - Valida registros y esquema
3. **Optimization Engine** - Traducción, normalización, caché
4. **Tokenizer Engine** - Conteo de tokens con tiktoken (o200k_base)
5. **Cost Engine** - Estimación de costos
6. **Prompt Builder Engine** - Construye prompts para LLM
7. **LLM Engine** - Comunicación con proveedores
8. **Parser Engine** - Parsea respuestas de AI a JSON
9. **Export Engine** - Exporta a Excel/JSON/CSV
10. **History Engine** - Almacena metadatos y métricas
