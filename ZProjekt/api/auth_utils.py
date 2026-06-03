import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import request, g, current_app, jsonify

import models
from extensions import db


def create_access_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        # PyJWT >= 2.10 wymaga, by "sub" było stringiem (RFC 7519).
        "sub": str(user.id),
        "email": user.email,
        "rola": user.rola,
        "type": "access",
        "iat": now,
        "exp": now + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def create_refresh_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "type": "refresh",
        "iat": now,
        "exp": now + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"],
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])


def jwt_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Brak tokenu autoryzacji"}), 401
        token = auth_header[7:]
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token wygasł"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Nieprawidłowy token"}), 401
        if payload.get("type") != "access":
            return jsonify({"error": "Nieprawidłowy typ tokenu"}), 401
        user = db.session.get(models.User, int(payload["sub"]))
        if user is None:
            return jsonify({"error": "Użytkownik nie istnieje"}), 401
        g.api_user = user
        return view(*args, **kwargs)
    return wrapper


def api_current_user():
    return g.api_user


def api_get_own_praktyka(praktyka_id):
    user = api_current_user()
    p = db.session.get(models.Praktyka, praktyka_id)
    if p is None:
        return None, (jsonify({"error": "Praktyka nie znaleziona"}), 404)
    if p.student_id != user.id:
        return None, (jsonify({"error": "Brak dostępu"}), 403)
    return p, None


def api_get_own_wniosek(wniosek_id):
    user = api_current_user()
    w = db.session.get(models.WniosekZaliczenia, wniosek_id)
    if w is None:
        return None, (jsonify({"error": "Wniosek nie znaleziony"}), 404)
    if w.student_id != user.id:
        return None, (jsonify({"error": "Brak dostępu"}), 403)
    return w, None
