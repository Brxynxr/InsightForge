from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import logger
from app.middleware.logging_middleware import LoggingMiddleware

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.include_router(router)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info(f"Shutting down {settings.APP_NAME}")
