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

    DEV_LOGIN = os.getenv("DEV_LOGIN", "0") == "1"

    
    WYMAGANE_GODZINY_PRAKTYK = 960
