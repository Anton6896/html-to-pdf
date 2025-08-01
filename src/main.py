import logging
import time
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from fastapi.exceptions import RequestValidationError
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import ValidationError
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.responses import JSONResponse

from src.config import init_logger
from src.config import settings
from src.errors import CustomHTTPException
from src.legacy_soffice_convert import router as old_soffice_convert
from src.metrics import REQUEST_TIME
from src.soffice_convert import router as soffice_router


def create_app(settings):
    app = FastAPI()
    init_logger()
    global logger
    logger = logging.getLogger('app')

    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENV,
            release=settings.SENRTY_RELEASE,
            traces_sample_rate=settings.SENTRY_RATE,
        )
        app.add_middleware(SentryAsgiMiddleware)

    async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={'error': str(exc.detail)},
        )

    async def http422_error_handler(_, exc):
        logger.error('422 error: %s', exc.errors())
        return JSONResponse(
            {'errors': [{'code': x['type'], 'message': f'{x["msg"]}: {x.get("loc")}'} for x in exc.errors()]},
            status_code=400,
        )

    app.add_exception_handler(ValidationError, http422_error_handler)
    app.add_exception_handler(RequestValidationError, http422_error_handler)
    app.add_exception_handler(CustomHTTPException, custom_http_exception_handler)

    return app


app = create_app(settings)
main_app_lifespan = app.router.lifespan_context


@asynccontextmanager
async def lifespan_wrapper(app):
    logger.info('sub process starter')
    """
    not sure if we need to start some health check on server start event
    """
    async with main_app_lifespan(app) as state:
        yield state


@app.middleware('http')
async def log_request(request: Request, call_next) -> Response:
    start = time.time()
    response = await call_next(request)
    stop = time.time()
    method = request.method
    status = response.status_code
    path = request.url
    REQUEST_TIME.labels(method=method, status=status, path=path).observe(stop - start)

    return response


app.router.lifespan_context = lifespan_wrapper

Instrumentator().instrument(
    app,
    latency_highr_buckets=settings.PROMETHEUS_LATENCY_HIGHR_BUCKETS,
    latency_lowr_buckets=settings.PROMETHEUS_LATENCY_LOWR_BUCKETS,
).expose(app, include_in_schema=False, should_gzip=True)

# routers
app.include_router(soffice_router)
app.include_router(old_soffice_convert)
