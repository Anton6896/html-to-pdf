import logging
import logging.config
import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ROOT_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    SENTRY_DSN: Optional[str] = os.getenv('SENTRY_DSN')
    SENTRY_ENV: Optional[str] = os.getenv('SENTRY_ENV', 'dev')
    SENRTY_RELEASE: Optional[str] = os.getenv('SENTRY_RELEASE', '')
    SENTRY_RATE: float = int(os.getenv('SENTRY_SAMPLE_RATE', '50')) / 100.0

    LOGGING_LEVEL: str = os.getenv('LOGGING_LEVEL', 'DEBUG')
    API_PREFIX: str = os.getenv('ODIX_API_PREFIX', '/api/v1')
    REQUEST_TIMEOUT: float = float(os.getenv('REQUEST_TIMEOUT') or 120.0)  # 2 min timeout

    IS_HEALTH_CHECK_ON: bool = os.getenv('IS_HEALTH_CHECK_ON', 'yes') in ['yes', 1]

    # Prometheus
    PROMETHEUS_LATENCY_HIGHR_BUCKETS: tuple = (
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1,
        1.5,
        2,
        2.5,
        3,
        3.5,
        4,
        4.5,
        5,
        7.5,
        10,
        20,
        30,
        40,
        50,
        60,
        90,
        120,
    )

    PROMETHEUS_LATENCY_LOWR_BUCKETS: tuple = (
        0.01,
        0.05,
        0.1,
        0.5,
        1,
        2,
        3,
        4,
        5,
        10,
        20,
        30,
        60,
        120,
    )

    class Config:
        case_sensitive = True


settings = Settings()


def init_logger():
    from uvicorn.config import LOGGING_CONFIG

    LOGGING_CONFIG['formatters']['default']['fmt'] = '%(asctime)s [%(name)14s] %(levelprefix)s %(message)s'
    LOGGING_CONFIG['formatters']['access']['fmt'] = (
        "%(asctime)s [%(name)14s] %(levelprefix)s %(client_addr)s - '%(request_line)s' %(status_code)s"
    )

    LOGGING_CONFIG['loggers']['app'] = {
        'handlers': ['default',],
        'formatter': 'default',
        'level': settings.LOGGING_LEVEL,
        'propagate': True,
    }

    logging.config.dictConfig(LOGGING_CONFIG)
