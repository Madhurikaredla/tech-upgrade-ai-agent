from contextlib import asynccontextmanager
from typing import AsyncIterator

import logfire
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from packages.config.settings import get_settings
from packages.db.database import init_db
from packages.handlers.exceptions import AppError
from packages.handlers.http_handlers import (
    app_error_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from packages.logging.setup import configure_logfire

# Configure logging at import time — before uvicorn, routes, or any other
# module emits a log line.
configure_logfire()

from .middleware.logging import LogfireLoggingMiddleware
from .routes.routes import root_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logfire.instrument_fastapi(app)
    await init_db()
    logfire.info("application startup")
    yield
    logfire.info("application shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LogfireLoggingMiddleware)

    # Exception handlers — order matters: most specific first
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, general_exception_handler)

    app.include_router(root_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "apps.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
