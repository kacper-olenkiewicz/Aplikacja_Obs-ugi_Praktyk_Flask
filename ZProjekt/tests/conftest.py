import os
import sys
from pathlib import Path

# Ustaw env zanim zaimportujemy app/config.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret")
os.environ.setdefault("DEV_LOGIN", "1")
os.environ.setdefault("MS_CLIENT_ID", "")
os.environ.setdefault("MS_CLIENT_SECRET", "")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")
os.environ.setdefault("CORS_ORIGINS", "*")

# ZProjekt na sys.path, zeby `from app import app` zadzialalo.
ZPROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ZPROJ))

import pytest

from app import app as flask_app
from extensions import db
import models


@pytest.fixture
def app():
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        DEV_LOGIN=True,
        WTF_CSRF_ENABLED=False,
    )
    with flask_app.app_context():
        db.create_all()
        try:
            yield flask_app
        finally:
            db.session.remove()
            db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _make_user(rola, email, imie, nazwisko):
    u = models.User(
        ms_oid=f"dev-{rola}-{email}",
        email=email,
        imie=imie,
        nazwisko=nazwisko,
        rola=rola,
    )
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def student(app):
    return _make_user("student", "student@test.pl", "Jan", "Student")


@pytest.fixture
def promotor(app):
    return _make_user("promotor", "promotor@test.pl", "Anna", "Promotor")


@pytest.fixture
def root_user(app):
    return _make_user("root", "root@test.pl", "Dyrektor", "Instytutu")


def login_as(client, user):
    """Loguje w sesji przez DEV_LOGIN."""
    return client.get(f"/auth/dev-login/{user.id}", follow_redirects=False)
