"""Smoke testy: sprawdzają że endpointy odpowiadają poprawnym statusem."""
from tests.conftest import login_as


# ---------- publiczne / anonim ----------

def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.is_json
    assert r.json["status"] == "ok"


def test_index_anonim(client):
    r = client.get("/")
    assert r.status_code == 200


def test_chroniony_endpoint_anonim_przekierowuje(client):
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code == 302


def test_404_html(client):
    r = client.get("/nie-istnieje")
    assert r.status_code == 404
    assert "text/html" in r.content_type


def test_404_api_json(client):
    r = client.get("/api/v1/nie-istnieje")
    assert r.status_code == 404
    assert r.is_json


# ---------- student ----------

def test_student_dashboard(client, student):
    login_as(client, student)
    r = client.get("/dashboard")
    assert r.status_code == 200


def test_student_praktyki_list(client, student):
    login_as(client, student)
    r = client.get("/praktyki")
    assert r.status_code == 200


def test_student_nowa_praktyka_form(client, student):
    login_as(client, student)
    r = client.get("/praktyki/nowa")
    assert r.status_code == 200


def test_student_profil(client, student):
    login_as(client, student)
    r = client.get("/profil")
    assert r.status_code == 200


def test_student_wnioski_list(client, student):
    login_as(client, student)
    r = client.get("/wnioski/")
    assert r.status_code == 200


# ---------- promotor ----------

def test_promotor_dashboard(client, promotor):
    login_as(client, promotor)
    r = client.get("/promotor/", follow_redirects=False)
    assert r.status_code == 200


def test_promotor_studenci(client, promotor):
    login_as(client, promotor)
    r = client.get("/promotor/studenci")
    assert r.status_code == 200


def test_promotor_wnioski(client, promotor):
    login_as(client, promotor)
    r = client.get("/promotor/wnioski/")
    assert r.status_code == 200


# ---------- admin (root) ----------

def test_admin_users_root(client, root_user):
    login_as(client, root_user)
    r = client.get("/admin/")
    assert r.status_code == 200


def test_admin_promotorzy_root(client, root_user):
    login_as(client, root_user)
    r = client.get("/admin/promotorzy/")
    assert r.status_code == 200


# ---------- kontrola dostępu ----------

def test_admin_users_403_dla_studenta(client, student):
    login_as(client, student)
    r = client.get("/admin/")
    assert r.status_code == 403


def test_promotor_403_dla_studenta(client, student):
    login_as(client, student)
    r = client.get("/promotor/studenci")
    assert r.status_code == 403
