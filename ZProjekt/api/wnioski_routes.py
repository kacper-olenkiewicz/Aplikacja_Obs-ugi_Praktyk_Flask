import uuid
from datetime import datetime
from pathlib import Path

from flask import request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename

from extensions import db
from api import api_bp
from api.auth_utils import jwt_required, api_current_user, api_get_own_wniosek
from api.serializers import serialize_wniosek_zaliczenia, serialize_wniosek_dokument
import models

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "odt", "jpg", "jpeg", "png"}


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


@api_bp.route("/wnioski")
@jwt_required
def api_wnioski_list():
    user = api_current_user()
    wnioski = user.wnioski_zaliczenia.order_by(
        models.WniosekZaliczenia.created_at.desc()
    ).all()
    return jsonify([serialize_wniosek_zaliczenia(w) for w in wnioski])


@api_bp.route("/wnioski/<int:wniosek_id>")
@jwt_required
def api_wniosek_detail(wniosek_id):
    w, err = api_get_own_wniosek(wniosek_id)
    if err:
        return err
    return jsonify(serialize_wniosek_zaliczenia(w, include_docs=True))


@api_bp.route("/wnioski", methods=["POST"])
@jwt_required
def api_wniosek_create():
    user = api_current_user()
    data = request.get_json(silent=True) or {}
    pracodawca = (data.get("pracodawca_nazwa") or "").strip()
    typ = (data.get("typ") or "").strip()
    if not pracodawca or not typ:
        return jsonify({"error": "Podaj typ i nazwę pracodawcy"}), 400

    w = models.WniosekZaliczenia(
        student_id=user.id,
        typ=typ,
        pracodawca_nazwa=pracodawca,
        pracodawca_adres=(data.get("pracodawca_adres") or "").strip() or None,
        nr_rejestrowy=(data.get("nr_rejestrowy") or "").strip() or None,
        stanowisko=(data.get("stanowisko") or "").strip() or None,
        data_od=_parse_date(data.get("data_od")),
        data_do=_parse_date(data.get("data_do")),
        opis_obowiazkow=(data.get("opis_obowiazkow") or "").strip() or None,
        uzasadnienie=(data.get("uzasadnienie") or "").strip() or None,
    )
    db.session.add(w)
    db.session.commit()
    return jsonify(serialize_wniosek_zaliczenia(w)), 201


@api_bp.route("/wnioski/<int:wniosek_id>/dokument", methods=["POST"])
@jwt_required
def api_wniosek_upload_dok(wniosek_id):
    w, err = api_get_own_wniosek(wniosek_id)
    if err:
        return err
    if w.status not in ("zlozony", "w_ocenie_komisji"):
        return jsonify({"error": "Nie można dodać dokumentu do wniosku w tym statusie"}), 400

    plik = request.files.get("plik")
    typ = request.form.get("typ", "inne")
    if not plik or not plik.filename:
        return jsonify({"error": "Wybierz plik"}), 400
    if not _allowed_file(plik.filename):
        return jsonify({"error": "Dozwolone formaty: PDF, DOC/DOCX, ODT, JPG, PNG"}), 400

    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    original = secure_filename(plik.filename)
    ext = original.rsplit(".", 1)[1].lower()
    stored = f"{uuid.uuid4().hex}.{ext}"
    plik.save(upload_dir / stored)

    d = models.WniosekDokument(
        wniosek_id=w.id,
        typ=typ,
        nazwa_oryginalna=original,
        nazwa_pliku=stored,
        mime_type=plik.mimetype,
        rozmiar=(upload_dir / stored).stat().st_size,
    )
    db.session.add(d)
    db.session.commit()
    return jsonify(serialize_wniosek_dokument(d)), 201


@api_bp.route("/wnioski/<int:wniosek_id>/dokument/<int:dok_id>", methods=["DELETE"])
@jwt_required
def api_wniosek_delete_dok(wniosek_id, dok_id):
    w, err = api_get_own_wniosek(wniosek_id)
    if err:
        return err
    d = db.session.get(models.WniosekDokument, dok_id)
    if d is None or d.wniosek_id != w.id:
        return jsonify({"error": "Dokument nie znaleziony"}), 404
    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    try:
        (upload_dir / d.nazwa_pliku).unlink(missing_ok=True)
    except OSError:
        pass
    db.session.delete(d)
    db.session.commit()
    return jsonify({"message": "Dokument usunięty"})


@api_bp.route("/wnioski/<int:wniosek_id>/dokument/<int:dok_id>/pobierz")
@jwt_required
def api_wniosek_download_dok(wniosek_id, dok_id):
    w, err = api_get_own_wniosek(wniosek_id)
    if err:
        return err
    d = db.session.get(models.WniosekDokument, dok_id)
    if d is None or d.wniosek_id != w.id:
        return jsonify({"error": "Dokument nie znaleziony"}), 404
    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    return send_from_directory(
        upload_dir, d.nazwa_pliku,
        as_attachment=True, download_name=d.nazwa_oryginalna,
    )
