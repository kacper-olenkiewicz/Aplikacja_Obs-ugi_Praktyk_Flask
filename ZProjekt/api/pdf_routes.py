import io

import redis as redis_lib
from flask import jsonify, send_file, current_app
from celery.result import AsyncResult

from api import api_bp
from api.auth_utils import jwt_required, api_current_user, api_get_own_praktyka, api_get_own_wniosek
from extensions import celery

VALID_PDF_KINDS = {
    "karta", "karta_1", "karta_2", "karta_3",
    "dziennik", "sprawozdanie", "ankieta", "program", "efekty",
}


@api_bp.route("/praktyki/<int:praktyka_id>/pdf/<kind>")
@jwt_required
def api_praktyka_pdf(praktyka_id, kind):
    from tasks import generate_pdf as _task
    p, err = api_get_own_praktyka(praktyka_id)
    if err:
        return err
    if kind not in VALID_PDF_KINDS:
        return jsonify({"error": "Nieprawidłowy typ dokumentu PDF"}), 404
    user = api_current_user()
    task = _task.delay(praktyka_id=p.id, kind=kind, user_id=user.id)
    return jsonify({"task_id": task.id})


@api_bp.route("/wnioski/<int:wniosek_id>/pdf")
@jwt_required
def api_wniosek_pdf(wniosek_id):
    from tasks import generate_wniosek_pdf as _task
    w, err = api_get_own_wniosek(wniosek_id)
    if err:
        return err
    user = api_current_user()
    task = _task.delay(wniosek_id=w.id, user_id=user.id)
    return jsonify({"task_id": task.id})


@api_bp.route("/pdf/status/<task_id>")
@jwt_required
def api_pdf_status(task_id):
    result = AsyncResult(task_id, app=celery)
    state = result.state
    ready = state == "SUCCESS"
    failed = state == "FAILURE"
    return jsonify({"state": state, "ready": ready, "failed": failed})


@api_bp.route("/pdf/download/<task_id>")
@jwt_required
def api_pdf_download(task_id):
    r = redis_lib.Redis.from_url(current_app.config["REDIS_URL"])
    pdf_bytes = r.get(f"pdf_result:{task_id}")
    filename = r.get(f"pdf_filename:{task_id}")
    if not pdf_bytes:
        return jsonify({"error": "PDF nie znaleziony lub wygasł"}), 404
    filename = filename.decode() if filename else "dokument.pdf"
    buf = io.BytesIO(pdf_bytes)
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True, download_name=filename)
