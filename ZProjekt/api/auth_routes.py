from datetime import datetime

import requests as http_requests
from flask import request, jsonify

import models
from extensions import db
from api import api_bp
from api.auth_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    jwt_required,
    api_current_user,
)
from api.serializers import serialize_user
import jwt


@api_bp.route("/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True)
    if not data or not data.get("ms_access_token"):
        return jsonify({"error": "Wymagany ms_access_token"}), 400

    ms_token = data["ms_access_token"]
    try:
        resp = http_requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {ms_token}"},
            timeout=10,
        )
    except http_requests.RequestException:
        return jsonify({"error": "Nie można połączyć z Microsoft Graph"}), 502

    if not resp.ok:
        return jsonify({"error": "Nieprawidłowy token Microsoft"}), 401

    profile = resp.json()
    oid = profile.get("id")
    email = profile.get("userPrincipalName") or profile.get("mail")
    display_name = profile.get("displayName", "")

    if not oid or not email:
        return jsonify({"error": "Brak danych użytkownika z Microsoft"}), 400

    user = models.User.query.filter_by(ms_oid=oid).one_or_none()
    if user is None:
        user = models.User(ms_oid=oid, email=email)
        db.session.add(user)

    user.email = email
    if display_name:
        parts = display_name.split(" ", 1)
        user.imie = parts[0]
        if len(parts) > 1:
            user.nazwisko = parts[1]
    user.last_login_at = datetime.utcnow()
    db.session.commit()

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": serialize_user(user),
    })


@api_bp.route("/auth/refresh", methods=["POST"])
def api_refresh():
    data = request.get_json(silent=True)
    if not data or not data.get("refresh_token"):
        return jsonify({"error": "Wymagany refresh_token"}), 400

    try:
        payload = decode_token(data["refresh_token"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Refresh token wygasł"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Nieprawidłowy refresh token"}), 401

    if payload.get("type") != "refresh":
        return jsonify({"error": "Nieprawidłowy typ tokenu"}), 401

    user = models.User.query.get(int(payload["sub"]))
    if user is None:
        return jsonify({"error": "Użytkownik nie istnieje"}), 401

    return jsonify({"access_token": create_access_token(user)})


@api_bp.route("/auth/me")
@jwt_required
def api_me():
    return jsonify(serialize_user(api_current_user()))


@api_bp.route("/auth/dev-login/<int:user_id>")
def api_dev_login(user_id):
    from flask import current_app
    if not current_app.config.get("DEV_LOGIN"):
        return jsonify({"error": "Dev login wyłączony"}), 404

    user = models.User.query.get(user_id)
    if user is None:
        return jsonify({"error": "Użytkownik nie istnieje"}), 404

    user.last_login_at = datetime.utcnow()
    db.session.commit()

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": serialize_user(user),
    })
