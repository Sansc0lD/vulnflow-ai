"""Celery application — PLAN.md FASE 4.7."""

import os

from celery import Celery


def get_celery_broker_url() -> str:
    url = os.environ.get("CELERY_BROKER_URL") or os.environ.get("REDIS_URL")
    if not url:
        raise RuntimeError("CELERY_BROKER_URL or REDIS_URL environment variable is not set.")
    return url


def get_celery_backend_url() -> str:
    url = (
        os.environ.get("CELERY_RESULT_BACKEND")
        or os.environ.get("CELERY_BROKER_URL")
        or os.environ.get("REDIS_URL")
    )
    if not url:
        raise RuntimeError("CELERY_RESULT_BACKEND environment variable is not set.")
    return url


def _init_broker_url() -> str:
    # Fail-closed in production, fall back to empty/unset for offline tests
    return os.environ.get("CELERY_BROKER_URL") or os.environ.get("REDIS_URL") or ""


def _init_backend_url() -> str:
    return os.environ.get("CELERY_RESULT_BACKEND") or _init_broker_url()


# F4-HIGH-08: include=["app.workers.report_worker"] registers the tasks
celery_app = Celery(
    "vulnflow",
    broker=_init_broker_url(),
    backend=_init_backend_url(),
    include=["app.workers.report_worker"],
)
# F4-MED-02: configure soft and hard time limits for report compilation
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_soft_time_limit=120,
    task_time_limit=150,
)
