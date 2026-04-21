import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-zmien-mnie")

    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    MS_CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
    MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "")
    MS_TENANT_ID = os.getenv("MS_TENANT_ID", "common")
    MS_REDIRECT_URI = os.getenv("MS_REDIRECT_URI", "http://localhost:5000/auth/callback")

    MS_AUTHORITY = f"https://login.microsoftonline.com/{MS_TENANT_ID}"
    MS_SCOPES = ["User.Read"]

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://praktyki:haslo@localhost:5433/praktyki_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # PgBouncer robi pooling po swojej stronie; SQLAlchemy trzyma mały bufor per worker
    SQLALCHEMY_POOL_SIZE = int(os.getenv("SQLALCHEMY_POOL_SIZE", "5"))
    SQLALCHEMY_MAX_OVERFLOW = int(os.getenv("SQLALCHEMY_MAX_OVERFLOW", "5"))
    SQLALCHEMY_POOL_TIMEOUT = 10
    SQLALCHEMY_POOL_RECYCLE = 1800

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    # Wyniki tasków PDF trzymamy 1 godzinę
    CELERY_RESULT_EXPIRES = 3600

    DEV_LOGIN = os.getenv("DEV_LOGIN", "0") == "1"

    WYMAGANE_GODZINY_PRAKTYK = 960
