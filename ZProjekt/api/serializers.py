def _iso(val):
    return val.isoformat() if val else None


def _time_str(val):
    return val.strftime("%H:%M") if val else None


def serialize_user(user):
    return {
        "id": user.id,
        "email": user.email,
        "imie": user.imie,
        "nazwisko": user.nazwisko,
        "pelne_imie": user.pelne_imie,
        "nr_albumu": user.nr_albumu,
        "kierunek": user.kierunek,
        "specjalnosc": user.specjalnosc,
        "rok_studiow": user.rok_studiow,
        "semestr": user.semestr,
        "telefon": user.telefon,
        "adres": user.adres,
        "rola": user.rola,
    }


def serialize_user_brief(user):
    if user is None:
        return None
    return {
        "id": user.id,
        "pelne_imie": user.pelne_imie,
        "email": user.email,
    }


def serialize_praktyka(p, include_relations=False):
    d = {
        "id": p.id,
        "student_id": p.student_id,
        "promotor_id": p.promotor_id,
        "firma_nazwa": p.firma_nazwa,
        "firma_adres": p.firma_adres,
        "firma_nip": p.firma_nip,
        "firma_profil": p.firma_profil,
        "opiekun_zakladowy_imie_nazwisko": p.opiekun_zakladowy_imie_nazwisko,
        "opiekun_zakladowy_stanowisko": p.opiekun_zakladowy_stanowisko,
        "opiekun_zakladowy_kontakt": p.opiekun_zakladowy_kontakt,
        "opiekun_zakladowy_wyksztalcenie": p.opiekun_zakladowy_wyksztalcenie,
        "rok_akademicki": p.rok_akademicki,
        "semestr_od": p.semestr_od,
        "semestr_do": p.semestr_do,
        "data_od": _iso(p.data_od),
        "data_do": _iso(p.data_do),
        "data_do_przedluzenie": _iso(p.data_do_przedluzenie),
        "liczba_godzin": p.liczba_godzin,
        "tryb_realizacji": p.tryb_realizacji,
        "harmonogram": p.harmonogram,
        "zakres_zadan": p.zakres_zadan,
        "bhp_zaakceptowane": p.bhp_zaakceptowane,
        "regulamin_zapoznany": p.regulamin_zapoznany,
        "ubezpieczenie_nnw": p.ubezpieczenie_nnw,
        "erasmus_plus": p.erasmus_plus,
        "porozumienie_podpisane": p.porozumienie_podpisane,
        "skierowanie_wystawione": p.skierowanie_wystawione,
        "dziennik_potwierdzony_zopz": p.dziennik_potwierdzony_zopz,
        "sprawozdanie_podpisane_zopz": p.sprawozdanie_podpisane_zopz,
        "efekty_potwierdzone_zopz": p.efekty_potwierdzone_zopz,
        "status": p.status,
        "status_label": p.status_label,
        "ocena": p.ocena,
        "komentarz_promotora": p.komentarz_promotora,
        "zaliczenie_sem6": p.zaliczenie_sem6,
        "data_zaliczenia_sem6": _iso(p.data_zaliczenia_sem6),
        "komentarz_zaliczenia_sem6": p.komentarz_zaliczenia_sem6,
        "ocena_zopz_parametryczna": p.ocena_zopz_parametryczna,
        "ocena_zopz_opisowa": p.ocena_zopz_opisowa,
        "sprawozdanie_charakterystyka": p.sprawozdanie_charakterystyka,
        "sprawozdanie_opis_prac": p.sprawozdanie_opis_prac,
        "sprawozdanie_samoocena": p.sprawozdanie_samoocena,
        "ankieta": {
            f"p{i:02d}": getattr(p, f"ankieta_p{i:02d}") for i in range(1, 15)
        },
        "ankieta_uwagi": p.ankieta_uwagi,
        "ankieta_rok_akademicki": p.ankieta_rok_akademicki,
        "ankieta_forma_studiow": p.ankieta_forma_studiow,
        "mozna_edytowac": p.mozna_edytowac,
        "efektywna_data_do": _iso(p.efektywna_data_do),
        "suma_godzin_dziennik": p.suma_godzin_dziennik,
        "created_at": _iso(p.created_at),
        "updated_at": _iso(p.updated_at),
    }
    if include_relations:
        d["promotor"] = serialize_user_brief(p.promotor)
        d["dokumenty_count"] = p.dokumenty.count()
        d["wpisy_count"] = p.wpisy_dziennika.count()
    return d


def serialize_praktyka_brief(p):
    return {
        "id": p.id,
        "firma_nazwa": p.firma_nazwa,
        "status": p.status,
        "status_label": p.status_label,
        "data_od": _iso(p.data_od),
        "data_do": _iso(p.data_do),
        "suma_godzin_dziennik": p.suma_godzin_dziennik,
        "created_at": _iso(p.created_at),
    }


def serialize_dziennik_wpis(w):
    return {
        "id": w.id,
        "praktyka_id": w.praktyka_id,
        "data": _iso(w.data),
        "godz_od": _time_str(w.godz_od),
        "godz_do": _time_str(w.godz_do),
        "opis": w.opis,
        "efekty": w.efekty,
        "liczba_godzin": w.liczba_godzin,
        "created_at": _iso(w.created_at),
    }


def serialize_dokument(d):
    return {
        "id": d.id,
        "praktyka_id": d.praktyka_id,
        "typ": d.typ,
        "typ_label": d.typ_label,
        "nazwa_oryginalna": d.nazwa_oryginalna,
        "mime_type": d.mime_type,
        "rozmiar": d.rozmiar,
        "created_at": _iso(d.created_at),
    }


def serialize_wniosek_zaliczenia(w, include_docs=False):
    d = {
        "id": w.id,
        "student_id": w.student_id,
        "typ": w.typ,
        "typ_label": w.typ_label,
        "pracodawca_nazwa": w.pracodawca_nazwa,
        "pracodawca_adres": w.pracodawca_adres,
        "nr_rejestrowy": w.nr_rejestrowy,
        "stanowisko": w.stanowisko,
        "data_od": _iso(w.data_od),
        "data_do": _iso(w.data_do),
        "opis_obowiazkow": w.opis_obowiazkow,
        "uzasadnienie": w.uzasadnienie,
        "status": w.status,
        "status_label": w.status_label,
        "ocena_komisji": w.ocena_komisji,
        "komentarz_komisji": w.komentarz_komisji,
        "data_oceny_komisji": _iso(w.data_oceny_komisji),
        "decyzja_dyrektora": w.decyzja_dyrektora,
        "komentarz_dyrektora": w.komentarz_dyrektora,
        "data_decyzji": _iso(w.data_decyzji),
        "created_at": _iso(w.created_at),
        "updated_at": _iso(w.updated_at),
    }
    if include_docs:
        d["dokumenty"] = [serialize_wniosek_dokument(dok) for dok in w.dokumenty.all()]
    return d


def serialize_wniosek_dokument(d):
    return {
        "id": d.id,
        "wniosek_id": d.wniosek_id,
        "typ": d.typ,
        "typ_label": d.typ_label,
        "nazwa_oryginalna": d.nazwa_oryginalna,
        "mime_type": d.mime_type,
        "rozmiar": d.rozmiar,
        "created_at": _iso(d.created_at),
    }


def serialize_zmiana_terminu(wn):
    return {
        "id": wn.id,
        "student_id": wn.student_id,
        "powod": wn.powod,
        "powod_label": wn.powod_label,
        "opis": wn.opis,
        "proponowany_semestr": wn.proponowany_semestr,
        "proponowana_data_od": _iso(wn.proponowana_data_od),
        "proponowana_data_do": _iso(wn.proponowana_data_do),
        "status": wn.status,
        "status_label": wn.status_label,
        "komentarz_dyrektora": wn.komentarz_dyrektora,
        "data_decyzji": _iso(wn.data_decyzji),
        "created_at": _iso(wn.created_at),
    }


def serialize_przedluzenie(wn):
    return {
        "id": wn.id,
        "praktyka_id": wn.praktyka_id,
        "powod": wn.powod,
        "powod_label": wn.powod_label,
        "godziny_nieobecnosci": wn.godziny_nieobecnosci,
        "opis": wn.opis,
        "proponowana_data_do": _iso(wn.proponowana_data_do),
        "status": wn.status,
        "status_label": wn.status_label,
        "nowa_data_do": _iso(wn.nowa_data_do),
        "komentarz": wn.komentarz,
        "created_at": _iso(wn.created_at),
    }
