import os

import redis as redis_lib
from flask import render_template, current_app
from weasyprint import HTML

from extensions import celery, db
import models


def _get_redis():
    url = current_app.config["REDIS_URL"]
    return redis_lib.Redis.from_url(url)


def _build_pdf_bytes(template, **ctx):
    html = render_template(template, **ctx)
    # base_url = root aplikacji, dzięki czemu url('static/fonts/arial.ttf')
    # w templatkach PDF rozwiązuje się do realnego pliku.
    base_url = current_app.root_path + os.sep
    return HTML(string=html, base_url=base_url).write_pdf()


@celery.task(bind=True, max_retries=2)
def generate_pdf(self, praktyka_id, kind, user_id):
    from datetime import date

    KINDS = {
        "karta": "pdf/karta_1.html",
        "karta_1": "pdf/karta_1.html",
        "karta_2": "pdf/karta_2.html",
        "karta_3": "pdf/karta_3.html",
        "dziennik": "pdf/dziennik.html",
        "sprawozdanie": "pdf/sprawozdanie.html",
        "ankieta": "pdf/ankieta.html",
        "program": "pdf/program.html",
        "efekty": "pdf/efekty.html",
    }
    template = KINDS.get(kind)
    if not template:
        raise ValueError(f"Nieznany rodzaj dokumentu: {kind}")

    p = db.session.get(models.Praktyka, praktyka_id)
    if p is None:
        raise LookupError(f"Praktyka {praktyka_id} nie istnieje")

    student = p.student
    promotor = p.promotor
    wpisy = p.wpisy_dziennika.all()
    suma_godzin = sum(w.liczba_godzin or 0 for w in wpisy)

    ctx = dict(
        p=p,
        student=student,
        promotor=promotor,
        wpisy=wpisy,
        suma_godzin=suma_godzin,
        today=date.today(),
    )

    try:
        pdf_bytes = _build_pdf_bytes(template, **ctx)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=3)

    r = _get_redis()
    task_key = f"pdf_result:{self.request.id}"
    r.setex(task_key, current_app.config["CELERY_RESULT_EXPIRES"], pdf_bytes)

    FILENAMES = {
        "karta_1": f"karta_praktyki_1_skierowanie_{praktyka_id}.pdf",
        "karta_2": f"karta_praktyki_2_potwierdzenie_{praktyka_id}.pdf",
        "karta_3": f"karta_praktyki_3_ocena_{praktyka_id}.pdf",
    }
    filename = FILENAMES.get(kind, f"{kind}_praktyki_{praktyka_id}.pdf")
    r.setex(f"pdf_filename:{self.request.id}",
            current_app.config["CELERY_RESULT_EXPIRES"], filename)

    return {"task_id": self.request.id, "filename": filename}


@celery.task(bind=True, max_retries=2)
def generate_wniosek_pdf(self, wniosek_id, user_id):
    from datetime import date

    w = db.session.get(models.WniosekZaliczenia, wniosek_id)
    if w is None:
        raise LookupError(f"Wniosek {wniosek_id} nie istnieje")

    ctx = dict(w=w, student=w.student, today=date.today())

    try:
        pdf_bytes = _build_pdf_bytes("pdf/wniosek_4b.html", **ctx)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=3)

    r = _get_redis()
    filename = f"wniosek_4b_{wniosek_id}.pdf"
    r.setex(f"pdf_result:{self.request.id}",
            current_app.config["CELERY_RESULT_EXPIRES"], pdf_bytes)
    r.setex(f"pdf_filename:{self.request.id}",
            current_app.config["CELERY_RESULT_EXPIRES"], filename)

    return {"task_id": self.request.id, "filename": filename}
