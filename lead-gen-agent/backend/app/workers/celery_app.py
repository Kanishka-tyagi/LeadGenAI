"""
Celery app configuration — uses Redis as both broker and result backend.
"""
from celery import Celery

celery_app = Celery(
    "lead_gen_agent",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Ensures tasks.py's @celery_app.task definitions are registered when the worker starts
import app.workers.tasks  # noqa: E402,F401