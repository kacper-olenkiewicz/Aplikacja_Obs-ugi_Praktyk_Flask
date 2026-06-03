"""Test pełnego cyklu praktyki: robocza/zgloszona → zaakceptowana → w_trakcie → do_oceny → zaliczona."""
import models
from extensions import db
from tests.conftest import login_as


def test_pelny_cykl_praktyki(client, student, promotor):
    # 1. Student tworzy i zglasza praktyke
    login_as(client, student)
    r = client.post("/praktyki/nowa", data={
        "firma_nazwa": "Testowa Sp. z o.o.",
        "promotor_id": str(promotor.id),
        "data_od": "2026-07-01",
        "data_do": "2026-09-30",
        "semestr_od": "6",
        "semestr_do": "7",
        "liczba_godzin": "960",
        "rok_akademicki": "2025/2026",
        "tryb_realizacji": "stacjonarny",
        "bhp_zaakceptowane": "on",
        "regulamin_zapoznany": "on",
        "zglos": "1",
    }, follow_redirects=False)
    assert r.status_code == 302

    p = models.Praktyka.query.filter_by(student_id=student.id).first()
    assert p is not None
    assert p.status == "zgloszona"
    assert p.promotor_id == promotor.id

    # 2. Promotor akceptuje + zaznacza porozumienie podpisane
    client.get("/auth/logout")
    login_as(client, promotor)
    r = client.post(f"/promotor/praktyki/{p.id}/akcja", data={
        "akcja": "akceptuj",
        "porozumienie_podpisane": "on",
        "skierowanie_wystawione": "on",
    })
    db.session.refresh(p)
    assert p.status == "zaakceptowana"
    assert p.porozumienie_podpisane is True

    # 3. Student rozpoczyna realizację (zaakceptowana → w_trakcie)
    client.get("/auth/logout")
    login_as(client, student)
    client.post(f"/praktyki/{p.id}/zloz")
    db.session.refresh(p)
    assert p.status == "w_trakcie"

    # 4. Student zglasza dokumentacje (w_trakcie → do_oceny)
    client.post(f"/praktyki/{p.id}/zloz")
    db.session.refresh(p)
    assert p.status == "do_oceny"

    # 5. Promotor zalicza z ocena
    client.get("/auth/logout")
    login_as(client, promotor)
    client.post(f"/promotor/praktyki/{p.id}/akcja", data={
        "akcja": "zalicz",
        "ocena": "5",
    })
    db.session.refresh(p)
    assert p.status == "zaliczona"
    assert p.ocena == "5"


def test_promotor_nie_widzi_obcej_praktyki(client, student, promotor):
    # Student tworzy praktyke BEZ wskazania promotora
    login_as(client, student)
    client.post("/praktyki/nowa", data={
        "firma_nazwa": "Firma bez promotora",
        "promotor_id": "",
    }, follow_redirects=False)
    p = models.Praktyka.query.first()
    assert p is not None
    assert p.promotor_id is None

    # Promotor probuje wejsc — powinien dostac 403/404
    client.get("/auth/logout")
    login_as(client, promotor)
    r = client.get(f"/promotor/praktyki/{p.id}", follow_redirects=False)
    assert r.status_code in (403, 404)


def test_odrzucenie_praktyki_przez_promotora(client, student, promotor):
    login_as(client, student)
    client.post("/praktyki/nowa", data={
        "firma_nazwa": "Do odrzucenia",
        "promotor_id": str(promotor.id),
        "bhp_zaakceptowane": "on",
        "regulamin_zapoznany": "on",
        "zglos": "1",
    })
    p = models.Praktyka.query.first()
    assert p.status == "zgloszona"

    client.get("/auth/logout")
    login_as(client, promotor)
    client.post(f"/promotor/praktyki/{p.id}/akcja", data={
        "akcja": "odrzuc",
        "komentarz": "Brakuje danych firmy",
    })
    db.session.refresh(p)
    assert p.status == "odrzucona"
    assert "Brakuje" in (p.komentarz_promotora or "")
