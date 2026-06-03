from datetime import datetime

from flask import request, jsonify

from extensions import db
from api import api_bp
from api.auth_utils import jwt_required, api_get_own_praktyka
from api.serializers import serialize_przedluzenie
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


@api_bp.route("/praktyki/<int:praktyka_id>/przedluzenie")
@jwt_required
def api_przedluzenie_list(praktyka_id):
    p, err = api_get_own_praktyka(praktyka_id)
    if err:
        return err
    wnioski = p.wnioski_przedluzenia.order_by(
        models.WniosekPrzedluzenia.created_at.desc()
    ).all()
    return jsonify([serialize_przedluzenie(wn) for wn in wnioski])


@api_bp.route("/praktyki/<int:praktyka_id>/przedluzenie", methods=["POST"])
@jwt_required
def api_przedluzenie_create(praktyka_id):
    p, err = api_get_own_praktyka(praktyka_id)
    if err:
        return err
    if p.status != "w_trakcie":
        return jsonify({"error": "Wniosek o przedłużenie można złożyć tylko dla praktyki w trakcie realizacji"}), 400

    data = request.get_json(silent=True) or {}
    powod = (data.get("powod") or "").strip()
    godziny = _parse_int(data.get("godziny_nieobecnosci"))
    proponowana = _parse_date(data.get("proponowana_data_do"))

    if not powod:
        return jsonify({"error": "Wybierz powód"}), 400
    if powod == "choroba" and (not godziny or godziny <= 40):
        return jsonify({"error": "Przy chorobie wymagana łączna nieobecność powyżej 40 godzin (§6.2)"}), 400
    if proponowana and p.data_do and (proponowana - p.data_do).days > 31:
        return jsonify({"error": "Przedłużenie możliwe maksymalnie o 1 miesiąc (§6.3)"}), 400

    wn = models.WniosekPrzedluzenia(
        praktyka_id=p.id,
        powod=powod,
        godziny_nieobecnosci=godziny,
        opis=(data.get("opis") or "").strip() or None,
        proponowana_data_do=proponowana,
    )
    db.session.add(wn)
    db.session.commit()
    return jsonify(serialize_przedluzenie(wn)), 201
