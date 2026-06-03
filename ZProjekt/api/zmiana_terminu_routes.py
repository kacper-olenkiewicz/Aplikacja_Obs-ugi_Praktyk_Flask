from datetime import datetime

from flask import request, jsonify

from extensions import db
from api import api_bp
from api.auth_utils import jwt_required, api_current_user
from api.serializers import serialize_zmiana_terminu
import models


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@api_bp.route("/zmiana-terminu")
@jwt_required
def api_zmiana_terminu_list():
    user = api_current_user()
    wnioski = user.wnioski_zmiana_terminu.order_by(
        models.WniosekZmianaTerminu.created_at.desc()
    ).all()
    return jsonify([serialize_zmiana_terminu(wn) for wn in wnioski])


@api_bp.route("/zmiana-terminu/<int:wn_id>")
@jwt_required
def api_zmiana_terminu_detail(wn_id):
    user = api_current_user()
    wn = db.session.get(models.WniosekZmianaTerminu, wn_id)
    if wn is None:
        return jsonify({"error": "Wniosek nie znaleziony"}), 404
    if wn.student_id != user.id:
        return jsonify({"error": "Brak dostępu"}), 403
    return jsonify(serialize_zmiana_terminu(wn))


@api_bp.route("/zmiana-terminu", methods=["POST"])
@jwt_required
def api_zmiana_terminu_create():
    user = api_current_user()
    data = request.get_json(silent=True) or {}
    powod = (data.get("powod") or "").strip()
    opis = (data.get("opis") or "").strip()
    if not powod or not opis:
        return jsonify({"error": "Wybierz powód i podaj opis uzasadnienia"}), 400

    data_od = _parse_date(data.get("proponowana_data_od"))
    data_do = _parse_date(data.get("proponowana_data_do"))
    if data_od and data_do and data_do < data_od:
        return jsonify({"error": "Data zakończenia nie może być wcześniejsza niż data rozpoczęcia"}), 400

    wn = models.WniosekZmianaTerminu(
        student_id=user.id,
        powod=powod,
        opis=opis,
        proponowany_semestr=_parse_int(data.get("proponowany_semestr")),
        proponowana_data_od=data_od,
        proponowana_data_do=data_do,
    )
    db.session.add(wn)
    db.session.commit()
    return jsonify(serialize_zmiana_terminu(wn)), 201
