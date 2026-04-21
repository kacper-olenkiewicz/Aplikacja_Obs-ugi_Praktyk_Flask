# Entry point dla Celery workera:
#   celery -A celery_worker.celery worker --loglevel=info --concurrency=4
from app import app
from extensions import celery, init_celery

init_celery(app)

import tasks  # noqa: F401 – rejestruje taski w celery
