from flask import request, jsonify

from extensions import db
from api import api_bp
from api.auth_utils import jwt_required, api_current_user
from api.serializers import serialize_user


def _parse_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@api_bp.route("/profile")
@jwt_required
def api_profile():
    return jsonify(serialize_user(api_current_user()))


@api_bp.route("/profile", methods=["PUT"])
@jwt_required
def api_profile_update():
    user = api_current_user()
    data = request.get_json(silent=True) or {}
    user.imie = (data.get("imie") or "").strip() or None
    user.nazwisko = (data.get("nazwisko") or "").strip() or None
    user.nr_albumu = (data.get("nr_albumu") or "").strip() or None
    user.kierunek = (data.get("kierunek") or "").strip() or None
    user.specjalnosc = (data.get("specjalnosc") or "").strip() or None
    user.rok_studiow = _parse_int(data.get("rok_studiow"))
    user.semestr = _parse_int(data.get("semestr"))
    user.telefon = (data.get("telefon") or "").strip() or None
    user.adres = (data.get("adres") or "").strip() or None
    db.session.commit()
    return jsonify(serialize_user(user))
