from datetime import datetime

from flask import request, jsonify

from extensions import db
from api import api_bp
from api.auth_utils import jwt_required, api_current_user, api_get_own_praktyka
from api.serializers import (
    serialize_praktyka,
    serialize_praktyka_brief,
    serialize_user_brief,
)
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


@api_bp.route("/dashboard")
@jwt_required
def api_dashboard():
    user = api_current_user()
    praktyki = user.praktyki.order_by(models.Praktyka.created_at.desc()).all()
    aktywne = [p for p in praktyki if p.status not in ("zaliczona", "odrzucona")]
    zakonczone = [p for p in praktyki if p.status in ("zaliczona", "odrzucona")]

    total_godzin = 0
    for p in praktyki:
        for w in p.wpisy_dziennika:
            if w.liczba_godzin:
                total_godzin += w.liczba_godzin

    liczba_dokumentow = sum(p.dokumenty.count() for p in praktyki)
    liczba_wpisow = sum(p.wpisy_dziennika.count() for p in praktyki)

    return jsonify({
        "user": serialize_user_brief(user),
        "praktyki": [serialize_praktyka_brief(p) for p in praktyki],
        "aktywne": [serialize_praktyka_brief(p) for p in aktywne],
        "zakonczone": [serialize_praktyka_brief(p) for p in zakonczone],
        "total_godzin": total_godzin,
        "liczba_dokumentow": liczba_dokumentow,
        "liczba_wpisow": liczba_wpisow,
    })


@api_bp.route("/praktyki")
@jwt_required
def api_praktyki_list():
    user = api_current_user()
    praktyki = user.praktyki.order_by(models.Praktyka.created_at.desc()).all()
    return jsonify([serialize_praktyka_brief(p) for p in praktyki])


@api_bp.route("/praktyki/<int:praktyka_id>")
@jwt_required
def api_praktyka_detail(praktyka_id):
    p, err = api_get_own_praktyka(praktyka_id)
    if err:
        return err
    return jsonify(serialize_praktyka(p, include_relations=True))


@api_bp.route("/praktyki", methods=["POST"])
@jwt_required
def api_praktyka_create():
    user = api_current_user()
    data = request.get_json(silent=True) or {}
    firma = (data.get("firma_nazwa") or "").strip()
    if not firma:
        return jsonify({"error": "Podaj nazwę firmy / instytucji"}), 400

    zglos = data.get("zglos", False)
    if zglos and not data.get("bhp_zaakceptowane"):
        return jsonify({"error": "Aby zgłosić praktykę, potwierdź zapoznanie się z przepisami BHP"}), 400
    if zglos and not data.get("regulamin_zapoznany"):
        return jsonify({"error": "Aby zgłosić praktykę, potwierdź zapoznanie się z regulaminem praktyk"}), 400

    p = models.Praktyka(
        student_id=user.id,
        promotor_id=_parse_int(data.get("promotor_id")),
        firma_nazwa=firma,
        firma_adres=(data.get("firma_adres") or "").strip() or None,
        firma_nip=(data.get("firma_nip") or "").strip() or None,
        firma_profil=(data.get("firma_profil") or "").strip() or None,
        opiekun_zakladowy_imie_nazwisko=(data.get("opiekun_zakladowy_imie_nazwisko") or "").strip() or None,
        opiekun_zakladowy_stanowisko=(data.get("opiekun_zakladowy_stanowisko") or "").strip() or None,
        opiekun_zakladowy_kontakt=(data.get("opiekun_zakladowy_kontakt") or "").strip() or None,
        opiekun_zakladowy_wyksztalcenie=(data.get("opiekun_zakladowy_wyksztalcenie") or "").strip() or None,
        rok_akademicki=(data.get("rok_akademicki") or "").strip() or None,
        semestr_od=_parse_int(data.get("semestr_od")) or 6,
        semestr_do=_parse_int(data.get("semestr_do")) or 7,
        data_od=_parse_date(data.get("data_od")),
        data_do=_parse_date(data.get("data_do")),
        liczba_godzin=_parse_int(data.get("liczba_godzin")),
        tryb_realizacji=data.get("tryb_realizacji") or None,
        harmonogram=(data.get("harmonogram") or "").strip() or None,
        zakres_zadan=(data.get("zakres_zadan") or "").strip() or None,
        bhp_zaakceptowane=bool(data.get("bhp_zaakceptowane")),
        regulamin_zapoznany=bool(data.get("regulamin_zapoznany")),
        ubezpieczenie_nnw=bool(data.get("ubezpieczenie_nnw")),
        erasmus_plus=bool(data.get("erasmus_plus")),
        status="zgloszona" if zglos else "robocza",
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(serialize_praktyka(p)), 201


@api_bp.route("/praktyki/<int:praktyka_id>", methods=["PUT"])
@jwt_required
def api_praktyka_update(praktyka_id):
    p, err = api_get_own_praktyka(praktyka_id)
    if err:
        return err
    if not p.mozna_edytowac:
        return jsonify({"error": "Nie można edytować tej praktyki"}), 400

    data = request.get_json(silent=True) or {}
    p.promotor_id = _parse_int(data.get("promotor_id"))
    p.firma_nazwa = (data.get("firma_nazwa") or "").strip() or p.firma_nazwa
    p.firma_adres = (data.get("firma_adres") or "").strip() or None
    p.firma_nip = (data.get("firma_nip") or "").strip() or None
    p.firma_profil = (data.get("firma_profil") or "").strip() or None
    p.opiekun_zakladowy_imie_nazwisko = (data.get("opiekun_zakladowy_imie_nazwisko") or "").strip() or None
    p.opiekun_zakladowy_stanowisko = (data.get("opiekun_zakladowy_stanowisko") or "").strip() or None
    p.opiekun_zakladowy_kontakt = (data.get("opiekun_zakladowy_kontakt") or "").strip() or None
    p.opiekun_zakladowy_wyksztalcenie = (data.get("opiekun_zakladowy_wyksztalcenie") or "").strip() or None
    p.rok_akademicki = (data.get("rok_akademicki") or "").strip() or None
    p.semestr_od = _parse_int(data.get("semestr_od")) or p.semestr_od
    p.semestr_do = _parse_int(data.get("semestr_do")) or p.semestr_do
    p.data_od = _parse_date(data.get("data_od"))
    p.data_do = _parse_date(data.get("data_do"))
    p.liczba_godzin = _parse_int(data.get("liczba_godzin"))
    p.tryb_realizacji = data.get("tryb_realizacji") or None
    p.harmonogram = (data.get("harmonogram") or "").strip() or None
    p.zakres_zadan = (data.get("zakres_zadan") or "").strip() or None
    p.sprawozdanie_charakterystyka = (data.get("sprawozdanie_charakterystyka") or "").strip() or None
    p.sprawozdanie_opis_prac = (data.get("sprawozdanie_opis_prac") or "").strip() or None
    p.sprawozdanie_samoocena = (data.get("sprawozdanie_samoocena") or "").strip() or None
    for i in range(1, 15):
        val = _parse_int(data.get(f"ankieta_p{i:02d}"))
        setattr(p, f"ankieta_p{i:02d}", val)
    p.ankieta_uwagi = (data.get("ankieta_uwagi") or "").strip() or None
    p.ankieta_rok_akademicki = (data.get("ankieta_rok_akademicki") or "").strip() or None
    p.ankieta_forma_studiow = (data.get("ankieta_forma_studiow") or "").strip() or None
    p.bhp_zaakceptowane = bool(data.get("bhp_zaakceptowane"))
    p.regulamin_zapoznany = bool(data.get("regulamin_zapoznany"))
    p.ubezpieczenie_nnw = bool(data.get("ubezpieczenie_nnw"))
    p.erasmus_plus = bool(data.get("erasmus_plus"))
    db.session.commit()
    return jsonify(serialize_praktyka(p))


@api_bp.route("/praktyki/<int:praktyka_id>/zloz", methods=["POST"])
@jwt_required
def api_praktyka_zloz(praktyka_id):
    p, err = api_get_own_praktyka(praktyka_id)
    if err:
        return err
    if p.status == "robocza":
        p.status = "zgloszona"
        msg = "Zgłoszenie wysłane do promotora"
    elif p.status == "zaakceptowana":
        if not p.porozumienie_podpisane:
            return jsonify({"error": "Nie można rozpocząć praktyki — porozumienie nie zostało potwierdzone"}), 400
        p.status = "w_trakcie"
        msg = "Realizacja praktyki rozpoczęta"
    elif p.status == "w_trakcie":
        p.status = "do_oceny"
        msg = "Dokumentacja złożona do oceny"
    else:
        return jsonify({"error": "Niedozwolona akcja dla bieżącego statusu"}), 400
    db.session.commit()
    return jsonify({"message": msg, "status": p.status, "status_label": p.status_label})


@api_bp.route("/promotorzy")
@jwt_required
def api_promotorzy():
    promotorzy = models.User.query.filter_by(rola="promotor").order_by(models.User.nazwisko).all()
    return jsonify([serialize_user_brief(u) for u in promotorzy])
