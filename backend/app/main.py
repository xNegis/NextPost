import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.accounts import router as accounts_router
from app.api.consultations import router as consultations_router
from app.api.health import router as health_router
from app.api.photos import router as photos_router
from app.cleanup import run_cleanup
from app.config import get_settings
from app.consultation_service import ConsultationError
from app.db import get_session_factory
from app.photo_service import PhotoError
from app.storage import PhotoStorage

logger = logging.getLogger(__name__)


def _build_field_errors(exc: RequestValidationError) -> dict[str, str]:
    field_errors: dict[str, str] = {}
    for error in exc.errors():
        loc = error.get("loc", ())
        field = str(loc[-1]) if loc else "request"
        if field not in field_errors:
            field_errors[field] = error.get("msg", "Invalid value")
    return field_errors


def _run_cleanup_once() -> None:
    settings = get_settings()
    storage = PhotoStorage(settings.photo_storage_root)
    storage.ensure_dirs()
    session_factory = get_session_factory()
    with session_factory() as db:
        run_cleanup(db, storage)


async def _maintenance_loop() -> None:
    settings = get_settings()
    interval = settings.photo_cleanup_interval_seconds
    while True:
        try:
            await asyncio.to_thread(_run_cleanup_once)
        except Exception:
            logger.exception("photo cleanup pass failed")
        await asyncio.sleep(interval)


@asynccontextmanager
async def _lifespan(application: FastAPI) -> AsyncIterator[None]:
    task: asyncio.Task[None] | None = None
    if os.getenv("NEXTPOST_RUN_MAINTENANCE", "1") == "1":
        try:
            await asyncio.to_thread(_run_cleanup_once)
        except Exception:
            logger.exception("startup photo cleanup sweep failed")
        task = asyncio.create_task(_maintenance_loop())
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="NextPost API", version="0.1.0")
    application.router.lifespan_context = _lifespan

    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie="nextpost_session",
        max_age=None,
        same_site="lax",
        https_only=settings.app_env != "development",
        path="/",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def _protected_private_headers(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if (
            path.startswith("/api/consultations/")
            or path == "/api/my-consultations"
            or path.startswith("/api/my-consultations/")
        ):
            response.headers.setdefault("Cache-Control", "private, no-store")
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        if request.method == "POST" and request.url.path == "/api/session":
            request.session.pop("account_id", None)
        return JSONResponse(
            status_code=422,
            content={
                "detail": {
                    "code": "validation_error",
                    "field_errors": _build_field_errors(exc),
                }
            },
        )

    @application.exception_handler(PhotoError)
    async def handle_photo_error(request: Request, exc: PhotoError) -> JSONResponse:
        logger.warning(
            "photo request rejected: method=%s path=%s code=%s status=%s",
            request.method,
            request.url.path,
            exc.code,
            exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": {"code": exc.code}},
        )

    @application.exception_handler(ConsultationError)
    async def handle_consultation_error(request: Request, exc: ConsultationError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": {"code": exc.code}},
            headers={
                "Cache-Control": "private, no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
            },
        )

    application.include_router(health_router, prefix="/api")
    application.include_router(accounts_router, prefix="/api")
    application.include_router(photos_router, prefix="/api")
    application.include_router(consultations_router, prefix="/api")
    return application


app = create_app()
