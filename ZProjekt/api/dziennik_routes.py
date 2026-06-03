from datetime import datetime

from flask import request, jsonify

from extensions import db
from api import api_bp
from api.auth_utils import jwt_required, api_get_own_praktyka
from api.serializers import serialize_dziennik_wpis
import models


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_time(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return None


@api_bp.route("/praktyki/<int:praktyka_id>/dziennik")
@jwt_required
def api_dziennik_list(praktyka_id):
    p, err = api_get_own_praktyka(praktyka_id)
    if err:
        return err
    wpisy = p.wpisy_dziennika.all()
    suma_godzin = sum(w.liczba_godzin or 0 for w in wpisy)
    return jsonify({
        "wpisy": [serialize_dziennik_wpis(w) for w in wpisy],
        "suma_godzin": suma_godzin,
    })


@api_bp.route("/praktyki/<int:praktyka_id>/dziennik", methods=["POST"])
@jwt_required
def api_dziennik_create(praktyka_id):
    p, err = api_get_own_praktyka(praktyka_id)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    data_wpisu = _parse_date(data.get("data"))
    opis = (data.get("opis") or "").strip()
    if not data_wpisu or not opis:
        return jsonify({"error": "Podaj datę i opis czynności"}), 400

    efekty = data.get("efekty")
    if isinstance(efekty, list):
        efekty = ", ".join(efekty)

    wpis = models.DziennikWpis(
        praktyka_id=p.id,
        data=data_wpisu,
        godz_od=_parse_time(data.get("godz_od")),
        godz_do=_parse_time(data.get("godz_do")),
        opis=opis,
        efekty=efekty or None,
    )
    db.session.add(wpis)
    db.session.commit()
    return jsonify(serialize_dziennik_wpis(wpis)), 201


@api_bp.route("/praktyki/<int:praktyka_id>/dziennik/<int:wpis_id>", methods=["DELETE"])
@jwt_required
def api_dziennik_delete(praktyka_id, wpis_id):
    p, err = api_get_own_praktyka(praktyka_id)
    if err:
        return err
    w = models.DziennikWpis.query.get(wpis_id)
    if w is None or w.praktyka_id != p.id:
        return jsonify({"error": "Wpis nie znaleziony"}), 404
    db.session.delete(w)
    db.session.commit()
    return jsonify({"message": "Usunięto wpis"})
