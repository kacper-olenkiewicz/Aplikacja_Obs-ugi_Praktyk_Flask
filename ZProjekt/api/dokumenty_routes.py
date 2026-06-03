import uuid
from pathlib import Path

from flask import request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename

from extensions import db
from api import api_bp
from api.auth_utils import jwt_required, api_get_own_praktyka
from api.serializers import serialize_dokument
import models

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "odt", "jpg", "jpeg", "png"}


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@api_bp.route("/praktyki/<int:praktyka_id>/dokumenty")
@jwt_required
def api_dokumenty_list(praktyka_id):
    p, err = api_get_own_praktyka(praktyka_id)
    if err:
        return err
    docs = p.dokumenty.order_by(models.Dokument.created_at.desc()).all()
    return jsonify({
        "dokumenty": [serialize_dokument(d) for d in docs],
        "typy": models.Dokument.TYPY,
    })


@api_bp.route("/praktyki/<int:praktyka_id>/dokumenty", methods=["POST"])
@jwt_required
def api_dokumenty_upload(praktyka_id):
    p, err = api_get_own_praktyka(praktyka_id)
    if err:
        return err
    plik = request.files.get("plik")
    typ = request.form.get("typ", "inne")
    if not plik or not plik.filename:
        return jsonify({"error": "Wybierz plik do przesłania"}), 400
    if not _allowed_file(plik.filename):
        return jsonify({"error": "Dozwolone formaty: PDF, DOC/DOCX, ODT, JPG, PNG"}), 400

    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    original = secure_filename(plik.filename)
    ext = original.rsplit(".", 1)[1].lower()
    stored = f"{uuid.uuid4().hex}.{ext}"
    plik.save(upload_dir / stored)

    d = models.Dokument(
        praktyka_id=p.id,
        typ=typ,
        nazwa_oryginalna=original,
        nazwa_pliku=stored,
        mime_type=plik.mimetype,
        rozmiar=(upload_dir / stored).stat().st_size,
    )
    db.session.add(d)
    db.session.commit()
    return jsonify(serialize_dokument(d)), 201


@api_bp.route("/praktyki/<int:praktyka_id>/dokumenty/<int:dok_id>/pobierz")
@jwt_required
def api_dokument_download(praktyka_id, dok_id):
    p, err = api_get_own_praktyka(praktyka_id)
    if err:
        return err
    d = db.session.get(models.Dokument, dok_id)
    if d is None or d.praktyka_id != p.id:
        return jsonify({"error": "Dokument nie znaleziony"}), 404
    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    return send_from_directory(
        upload_dir, d.nazwa_pliku,
        as_attachment=True, download_name=d.nazwa_oryginalna,
    )


@api_bp.route("/praktyki/<int:praktyka_id>/dokumenty/<int:dok_id>", methods=["DELETE"])
@jwt_required
def api_dokument_delete(praktyka_id, dok_id):
    p, err = api_get_own_praktyka(praktyka_id)
    if err:
        return err
    d = db.session.get(models.Dokument, dok_id)
    if d is None or d.praktyka_id != p.id:
        return jsonify({"error": "Dokument nie znaleziony"}), 404
    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    try:
        (upload_dir / d.nazwa_pliku).unlink(missing_ok=True)
    except OSError:
        pass
    db.session.delete(d)
    db.session.commit()
    return jsonify({"message": "Usunięto dokument"})
