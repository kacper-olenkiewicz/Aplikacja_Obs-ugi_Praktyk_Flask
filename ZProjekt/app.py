import io
import os
import uuid
from datetime import datetime, date, time
from functools import wraps
from pathlib import Path

import requests
import click
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    session,
    request,
    flash,
    abort,
    send_from_directory,
    send_file,
    g,
)
from msal import ConfidentialClientApplication
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from config import Config
from extensions import db, migrate
import models

app = Flask(__name__)
app.config.from_object(Config)

UPLOAD_DIR = Path(app.root_path) / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
app.config["UPLOAD_DIR"] = str(UPLOAD_DIR)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "odt", "jpg", "jpeg", "png"}

db.init_app(app)
migrate.init_app(app, db)


# ---------- pomocnicze ----------

def _msal_app():
    return ConfidentialClientApplication(
        client_id=app.config["MS_CLIENT_ID"],
        client_credential=app.config["MS_CLIENT_SECRET"],
        authority=app.config["MS_AUTHORITY"],
    )


def current_user():
    if "user" not in session:
        return None
    uid = session["user"].get("id")
    if not uid:
        return None
    if "_user_obj" not in g:
        g._user_obj = models.User.query.get(uid)
    return g._user_obj


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("index"))
        if not current_user():
            session.clear()
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapper


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


def _parse_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_own_praktyka(praktyka_id):
    user = current_user()
    p = models.Praktyka.query.get_or_404(praktyka_id)
    if p.student_id != user.id and user.rola not in ("promotor", "root"):
        abort(403)
    return p


def promotor_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u:
            return redirect(url_for("index"))
        if u.rola not in ("promotor", "root"):
            abort(403)
        return view(*args, **kwargs)
    return wrapper


def root_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u:
            return redirect(url_for("index"))
        if u.rola != "root":
            abort(403)
        return view(*args, **kwargs)
    return wrapper


def _promotor_praktyki(user):
    """Query na praktyki widoczne dla zalogowanego promotora (root widzi wszystkie)."""
    if user.rola == "root":
        return models.Praktyka.query
    return models.Praktyka.query.filter_by(promotor_id=user.id)


def _get_promotor_praktyka(praktyka_id):
    u = current_user()
    p = models.Praktyka.query.get_or_404(praktyka_id)
    if u.rola == "root":
        return p
    if p.promotor_id != u.id:
        abort(403)
    return p


@app.context_processor
def inject_globals():
    try:
        user_obj = current_user()
    except Exception:
        user_obj = None
    return {
        "current_user_obj": user_obj,
        "statusy": models.Praktyka.STATUSY,
        "wymagane_godziny": app.config["WYMAGANE_GODZINY_PRAKTYK"],
    }


_SESSION_EXEMPT = frozenset({"index", "login", "auth_callback", "logout", "dev_login", "static"})


@app.before_request
def check_session_health():
    """Przechwytuje wygasłe/uszkodzone sesje i przekierowuje na login."""
    if request.endpoint in _SESSION_EXEMPT:
        return
    if "user" not in session:
        return  # login_required zadba o przekierowanie w chronionych routach
    uid = session["user"].get("id")
    if uid is None:
        session.clear()
        flash("Sesja wygasła. Zaloguj się ponownie.", "error")
        return redirect(url_for("index"))
    try:
        if models.User.query.get(uid) is None:
            session.clear()
            flash("Konto nie istnieje lub sesja wygasła. Zaloguj się ponownie.", "error")
            return redirect(url_for("index"))
    except Exception:
        session.clear()
        return redirect(url_for("index"))


@app.errorhandler(401)
def handle_401(e):
    flash("Sesja wygasła lub brak dostępu. Zaloguj się ponownie.", "error")
    return redirect(url_for("index"))


@app.template_filter("pl_date")
def pl_date(value):
    if not value:
        return ""
    if isinstance(value, (datetime, date)):
        return value.strftime("%d.%m.%Y")
    return value


@app.template_filter("pl_time")
def pl_time(value):
    if not value:
        return ""
    return value.strftime("%H:%M")


# ---------- strony publiczne / auth ----------

@app.route("/")
def index():
    if "user" in session and current_user():
        return redirect(url_for("dashboard"))
    dev_users = []
    if app.config["DEV_LOGIN"]:
        dev_users = models.User.query.order_by(models.User.rola, models.User.nazwisko).all()
    return render_template(
        "index.html",
        user=session.get("user"),
        dev_login=app.config["DEV_LOGIN"],
        dev_users=dev_users,
    )


@app.route("/auth/dev-login/<int:user_id>")
def dev_login(user_id):
    if not app.config["DEV_LOGIN"]:
        abort(404)
    u = models.User.query.get_or_404(user_id)
    u.last_login_at = datetime.utcnow()
    db.session.commit()
    session.permanent = True
    session["user"] = {
        "id": u.id,
        "name": u.pelne_imie,
        "email": u.email,
        "oid": u.ms_oid,
        "rola": u.rola,
    }
    flash(f"Zalogowano jako {session['user']['name']} ({u.rola}) — tryb DEV", "info")
    return redirect(url_for("dashboard"))


@app.cli.command("create-user")
@click.option("--email", required=True)
@click.option("--imie", default="")
@click.option("--nazwisko", default="")
@click.option("--rola", default="student", type=click.Choice(["student", "promotor", "root"]))
@click.option("--nr-albumu", default=None)
@click.option("--kierunek", default=None)
def create_user(email, imie, nazwisko, rola, nr_albumu, kierunek):
    """Dodaje usera do bazy (do testow, bez logowania MS)."""
    if models.User.query.filter_by(email=email).first():
        click.echo(f"User {email} juz istnieje.")
        return
    u = models.User(
        ms_oid=f"dev-{uuid.uuid4().hex[:16]}",
        email=email,
        imie=imie or None,
        nazwisko=nazwisko or None,
        rola=rola,
        nr_albumu=nr_albumu,
        kierunek=kierunek,
    )
    db.session.add(u)
    db.session.commit()
    click.echo(f"Dodano #{u.id}: {u.email} ({u.rola})")


@app.route("/auth/login")
def login():
    if not app.config["MS_CLIENT_ID"]:
        flash("Logowanie Microsoft nie jest jeszcze skonfigurowane. Uzupełnij plik .env.", "error")
        return redirect(url_for("index"))

    session["state"] = str(uuid.uuid4())
    auth_url = _msal_app().get_authorization_request_url(
        scopes=app.config["MS_SCOPES"],
        state=session["state"],
        redirect_uri=app.config["MS_REDIRECT_URI"],
    )
    return redirect(auth_url)


@app.route("/auth/callback")
def auth_callback():
    if request.args.get("state") != session.get("state"):
        flash("Nieprawidłowy stan sesji, spróbuj ponownie.", "error")
        return redirect(url_for("index"))

    if "error" in request.args:
        flash(f"Błąd logowania: {request.args.get('error_description', request.args['error'])}", "error")
        return redirect(url_for("index"))

    code = request.args.get("code")
    if not code:
        return redirect(url_for("index"))

    result = _msal_app().acquire_token_by_authorization_code(
        code=code,
        scopes=app.config["MS_SCOPES"],
        redirect_uri=app.config["MS_REDIRECT_URI"],
    )

    if "error" in result:
        flash(f"Nie udało się pobrać tokenu: {result.get('error_description')}", "error")
        return redirect(url_for("index"))

    claims = result.get("id_token_claims", {})
    profile = {
        "name": claims.get("name"),
        "email": claims.get("preferred_username") or claims.get("email"),
        "oid": claims.get("oid"),
    }

    try:
        graph = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {result['access_token']}"},
            timeout=10,
        )
        if graph.ok:
            data = graph.json()
            profile["name"] = profile["name"] or data.get("displayName")
            profile["email"] = profile["email"] or data.get("userPrincipalName") or data.get("mail")
    except requests.RequestException:
        pass

    if profile["oid"] and profile["email"]:
        user = models.User.query.filter_by(ms_oid=profile["oid"]).one_or_none()
        if user is None:
            user = models.User(ms_oid=profile["oid"], email=profile["email"])
            db.session.add(user)
        user.email = profile["email"]
        if profile["name"]:
            parts = profile["name"].split(" ", 1)
            user.imie = parts[0]
            user.nazwisko = parts[1] if len(parts) > 1 else user.nazwisko
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        profile["id"] = user.id
        profile["rola"] = user.rola

    session.permanent = True
    session["user"] = profile
    return redirect(url_for("dashboard"))


@app.route("/auth/logout")
def logout():
    session.clear()
    logout_url = (
        f"{app.config['MS_AUTHORITY']}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={url_for('index', _external=True)}"
    )
    return redirect(logout_url)


# ---------- dashboard / profil ----------

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    if user.rola == "root":
        return redirect(url_for("admin_users"))
    if user.rola == "promotor":
        return redirect(url_for("promotor_dashboard"))
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

    return render_template(
        "student/dashboard.html",
        user=user,
        praktyki=praktyki,
        aktywne=aktywne,
        zakonczone=zakonczone,
        total_godzin=total_godzin,
        liczba_dokumentow=liczba_dokumentow,
        liczba_wpisow=liczba_wpisow,
    )


@app.route("/profil", methods=["GET", "POST"])
@login_required
def profil():
    user = current_user()
    if request.method == "POST":
        user.imie = request.form.get("imie", "").strip() or None
        user.nazwisko = request.form.get("nazwisko", "").strip() or None
        user.nr_albumu = request.form.get("nr_albumu", "").strip() or None
        user.kierunek = request.form.get("kierunek", "").strip() or None
        user.rok_studiow = _parse_int(request.form.get("rok_studiow"))
        user.semestr = _parse_int(request.form.get("semestr"))
        user.telefon = request.form.get("telefon", "").strip() or None
        user.adres = request.form.get("adres", "").strip() or None
        db.session.commit()
        session["user"]["name"] = user.pelne_imie
        flash("Profil zaktualizowany.", "info")
        return redirect(url_for("profil"))
    return render_template("student/profil.html", user=user)


# ---------- praktyki ----------

@app.route("/praktyki")
@login_required
def praktyki_list():
    user = current_user()
    praktyki = user.praktyki.order_by(models.Praktyka.created_at.desc()).all()
    return render_template("student/praktyki_list.html", praktyki=praktyki, user=user)


@app.route("/praktyki/nowa", methods=["GET", "POST"])
@login_required
def praktyka_nowa():
    user = current_user()
    promotorzy = models.User.query.filter_by(rola="promotor").order_by(models.User.nazwisko).all()
    if request.method == "POST":
        firma = request.form.get("firma_nazwa", "").strip()
        if not firma:
            flash("Podaj nazwę firmy / instytucji.", "error")
            return render_template("student/praktyka_form.html", promotorzy=promotorzy, p=None)
        if request.form.get("zglos") and not request.form.get("bhp_zaakceptowane"):
            flash("Aby zgłosić praktykę, potwierdź zapoznanie się z przepisami BHP.", "error")
            return render_template("student/praktyka_form.html", promotorzy=promotorzy, p=None)
        if request.form.get("zglos") and not request.form.get("regulamin_zapoznany"):
            flash("Aby zgłosić praktykę, potwierdź zapoznanie się z regulaminem praktyk.", "error")
            return render_template("student/praktyka_form.html", promotorzy=promotorzy, p=None)

        p = models.Praktyka(
            student_id=user.id,
            promotor_id=_parse_int(request.form.get("promotor_id")),
            firma_nazwa=firma,
            firma_adres=request.form.get("firma_adres", "").strip() or None,
            firma_nip=request.form.get("firma_nip", "").strip() or None,
            firma_profil=request.form.get("firma_profil", "").strip() or None,
            opiekun_zakladowy_imie_nazwisko=request.form.get("opiekun_zakladowy_imie_nazwisko", "").strip() or None,
            opiekun_zakladowy_stanowisko=request.form.get("opiekun_zakladowy_stanowisko", "").strip() or None,
            opiekun_zakladowy_kontakt=request.form.get("opiekun_zakladowy_kontakt", "").strip() or None,
            opiekun_zakladowy_wyksztalcenie=request.form.get("opiekun_zakladowy_wyksztalcenie", "").strip() or None,
            rok_akademicki=request.form.get("rok_akademicki", "").strip() or None,
            semestr_od=_parse_int(request.form.get("semestr_od")) or 6,
            semestr_do=_parse_int(request.form.get("semestr_do")) or 7,
            data_od=_parse_date(request.form.get("data_od")),
            data_do=_parse_date(request.form.get("data_do")),
            liczba_godzin=_parse_int(request.form.get("liczba_godzin")),
            tryb_realizacji=request.form.get("tryb_realizacji") or None,
            harmonogram=request.form.get("harmonogram", "").strip() or None,
            zakres_zadan=request.form.get("zakres_zadan", "").strip() or None,
            bhp_zaakceptowane=bool(request.form.get("bhp_zaakceptowane")),
            regulamin_zapoznany=bool(request.form.get("regulamin_zapoznany")),
            ubezpieczenie_nnw=bool(request.form.get("ubezpieczenie_nnw")),
            erasmus_plus=bool(request.form.get("erasmus_plus")),
            status="zgloszona" if request.form.get("zglos") else "robocza",
        )
        db.session.add(p)
        db.session.commit()
        flash("Utworzono zgłoszenie praktyki.", "info")
        return redirect(url_for("praktyka_detail", praktyka_id=p.id))
    return render_template("student/praktyka_form.html", promotorzy=promotorzy, p=None)


@app.route("/praktyki/<int:praktyka_id>")
@login_required
def praktyka_detail(praktyka_id):
    p = _get_own_praktyka(praktyka_id)
    return render_template("student/praktyka_detail.html", p=p)


@app.route("/praktyki/<int:praktyka_id>/edycja", methods=["GET", "POST"])
@login_required
def praktyka_edit(praktyka_id):
    p = _get_own_praktyka(praktyka_id)
    if not p.mozna_edytowac:
        flash("Nie można edytować tej praktyki.", "error")
        return redirect(url_for("praktyka_detail", praktyka_id=p.id))

    promotorzy = models.User.query.filter_by(rola="promotor").order_by(models.User.nazwisko).all()
    if request.method == "POST":
        p.promotor_id = _parse_int(request.form.get("promotor_id"))
        p.firma_nazwa = request.form.get("firma_nazwa", "").strip() or p.firma_nazwa
        p.firma_adres = request.form.get("firma_adres", "").strip() or None
        p.firma_nip = request.form.get("firma_nip", "").strip() or None
        p.firma_profil = request.form.get("firma_profil", "").strip() or None
        p.opiekun_zakladowy_imie_nazwisko = request.form.get("opiekun_zakladowy_imie_nazwisko", "").strip() or None
        p.opiekun_zakladowy_stanowisko = request.form.get("opiekun_zakladowy_stanowisko", "").strip() or None
        p.opiekun_zakladowy_kontakt = request.form.get("opiekun_zakladowy_kontakt", "").strip() or None
        p.opiekun_zakladowy_wyksztalcenie = request.form.get("opiekun_zakladowy_wyksztalcenie", "").strip() or None
        p.rok_akademicki = request.form.get("rok_akademicki", "").strip() or None
        p.semestr_od = _parse_int(request.form.get("semestr_od")) or p.semestr_od
        p.semestr_do = _parse_int(request.form.get("semestr_do")) or p.semestr_do
        p.data_od = _parse_date(request.form.get("data_od"))
        p.data_do = _parse_date(request.form.get("data_do"))
        p.liczba_godzin = _parse_int(request.form.get("liczba_godzin"))
        p.tryb_realizacji = request.form.get("tryb_realizacji") or None
        p.harmonogram = request.form.get("harmonogram", "").strip() or None
        p.zakres_zadan = request.form.get("zakres_zadan", "").strip() or None
        p.sprawozdanie_tresc = request.form.get("sprawozdanie_tresc", "").strip() or None
        p.sprawozdanie_wnioski = request.form.get("sprawozdanie_wnioski", "").strip() or None
        p.ankieta_atmosfera = _parse_int(request.form.get("ankieta_atmosfera"))
        p.ankieta_organizacja = _parse_int(request.form.get("ankieta_organizacja"))
        p.ankieta_wiedza = _parse_int(request.form.get("ankieta_wiedza"))
        p.ankieta_komentarz = request.form.get("ankieta_komentarz", "").strip() or None
        p.bhp_zaakceptowane = bool(request.form.get("bhp_zaakceptowane"))
        p.regulamin_zapoznany = bool(request.form.get("regulamin_zapoznany"))
        p.ubezpieczenie_nnw = bool(request.form.get("ubezpieczenie_nnw"))
        p.erasmus_plus = bool(request.form.get("erasmus_plus"))
        db.session.commit()
        flash("Zapisano zmiany.", "info")
        return redirect(url_for("praktyka_detail", praktyka_id=p.id))

    return render_template("student/praktyka_form.html", p=p, promotorzy=promotorzy)


@app.route("/praktyki/<int:praktyka_id>/zloz", methods=["POST"])
@login_required
def praktyka_zloz(praktyka_id):
    p = _get_own_praktyka(praktyka_id)
    if p.status == "robocza":
        p.status = "zgloszona"
        flash("Zgłoszenie wysłane do promotora.", "info")
    elif p.status == "zaakceptowana":
        if not p.porozumienie_podpisane:
            flash("Nie można rozpocząć praktyki — porozumienie z zakładem pracy nie zostało jeszcze potwierdzone przez promotora.", "error")
            return redirect(url_for("praktyka_detail", praktyka_id=p.id))
        p.status = "w_trakcie"
        flash("Realizacja praktyki rozpoczęta.", "info")
    elif p.status == "w_trakcie":
        p.status = "do_oceny"
        flash("Dokumentacja złożona do oceny.", "info")
    else:
        flash("Niedozwolona akcja dla bieżącego statusu.", "error")
    db.session.commit()
    return redirect(url_for("praktyka_detail", praktyka_id=p.id))


# ---------- dziennik ----------

@app.route("/praktyki/<int:praktyka_id>/dziennik", methods=["GET", "POST"])
@login_required
def dziennik(praktyka_id):
    p = _get_own_praktyka(praktyka_id)
    if request.method == "POST":
        data = _parse_date(request.form.get("data"))
        opis = request.form.get("opis", "").strip()
        if not data or not opis:
            flash("Podaj datę i opis czynności.", "error")
        else:
            wpis = models.DziennikWpis(
                praktyka_id=p.id,
                data=data,
                godz_od=_parse_time(request.form.get("godz_od")),
                godz_do=_parse_time(request.form.get("godz_do")),
                opis=opis,
                efekty=request.form.get("efekty", "").strip() or None,
            )
            db.session.add(wpis)
            db.session.commit()
            flash("Dodano wpis do dziennika.", "info")
            return redirect(url_for("dziennik", praktyka_id=p.id))
    wpisy = p.wpisy_dziennika.all()
    suma_godzin = sum(w.liczba_godzin or 0 for w in wpisy)
    return render_template("student/dziennik.html", p=p, wpisy=wpisy, suma_godzin=suma_godzin)


@app.route("/praktyki/<int:praktyka_id>/dziennik/<int:wpis_id>/usun", methods=["POST"])
@login_required
def dziennik_usun(praktyka_id, wpis_id):
    p = _get_own_praktyka(praktyka_id)
    w = models.DziennikWpis.query.get_or_404(wpis_id)
    if w.praktyka_id != p.id:
        abort(404)
    db.session.delete(w)
    db.session.commit()
    flash("Usunięto wpis.", "info")
    return redirect(url_for("dziennik", praktyka_id=p.id))


# ---------- dokumenty ----------

@app.route("/praktyki/<int:praktyka_id>/dokumenty", methods=["GET", "POST"])
@login_required
def dokumenty(praktyka_id):
    p = _get_own_praktyka(praktyka_id)
    if request.method == "POST":
        plik = request.files.get("plik")
        typ = request.form.get("typ", "inne")
        if not plik or not plik.filename:
            flash("Wybierz plik do przesłania.", "error")
        elif not _allowed_file(plik.filename):
            flash("Dozwolone formaty: PDF, DOC/DOCX, ODT, JPG, PNG.", "error")
        else:
            original = secure_filename(plik.filename)
            ext = original.rsplit(".", 1)[1].lower()
            stored = f"{uuid.uuid4().hex}.{ext}"
            plik.save(UPLOAD_DIR / stored)
            d = models.Dokument(
                praktyka_id=p.id,
                typ=typ,
                nazwa_oryginalna=original,
                nazwa_pliku=stored,
                mime_type=plik.mimetype,
                rozmiar=(UPLOAD_DIR / stored).stat().st_size,
            )
            db.session.add(d)
            db.session.commit()
            flash("Dodano dokument.", "info")
            return redirect(url_for("dokumenty", praktyka_id=p.id))
    dokumenty = p.dokumenty.order_by(models.Dokument.created_at.desc()).all()
    return render_template(
        "student/dokumenty.html",
        p=p,
        dokumenty=dokumenty,
        typy=models.Dokument.TYPY,
    )


@app.route("/praktyki/<int:praktyka_id>/dokumenty/<int:dok_id>/pobierz")
@login_required
def dokument_pobierz(praktyka_id, dok_id):
    p = _get_own_praktyka(praktyka_id)
    d = models.Dokument.query.get_or_404(dok_id)
    if d.praktyka_id != p.id:
        abort(404)
    return send_from_directory(
        UPLOAD_DIR, d.nazwa_pliku,
        as_attachment=True, download_name=d.nazwa_oryginalna,
    )


@app.route("/praktyki/<int:praktyka_id>/dokumenty/<int:dok_id>/usun", methods=["POST"])
@login_required
def dokument_usun(praktyka_id, dok_id):
    p = _get_own_praktyka(praktyka_id)
    d = models.Dokument.query.get_or_404(dok_id)
    if d.praktyka_id != p.id:
        abort(404)
    try:
        (UPLOAD_DIR / d.nazwa_pliku).unlink(missing_ok=True)
    except OSError:
        pass
    db.session.delete(d)
    db.session.commit()
    flash("Usunięto dokument.", "info")
    return redirect(url_for("dokumenty", praktyka_id=p.id))


# ---------- PDF ----------

def _fix_xhtml2pdf_windows():
    """Naprawia blokadę NamedTemporaryFile na Windowsie w xhtml2pdf.

    xhtml2pdf otwiera font przez NamedTemporaryFile i pozostawia go otwartego.
    Na Windowsie drugi open() tego samego pliku powoduje PermissionError.
    Poprawka: delete=False + close() po zapisie, żeby ReportLab mógł plik otworzyć.
    """
    import tempfile
    import xhtml2pdf.files as xf

    def _get_named_tmp_file(self):
        data = self.get_data()
        tmp_file = tempfile.NamedTemporaryFile(suffix=self.suffix, delete=False)
        if data:
            tmp_file.write(data)
            tmp_file.flush()
            tmp_file.close()  # zamknij blokadę — plik pozostaje na dysku
        if self.path is None:
            self.path = tmp_file.name
        return tmp_file

    xf.BaseFile.get_named_tmp_file = _get_named_tmp_file


_fix_xhtml2pdf_windows()


def _render_pdf(template, filename, **ctx):
    from xhtml2pdf import pisa

    static_root = app.static_folder

    def link_callback(uri, rel):
        if uri.startswith("/static/"):
            return os.path.join(static_root, uri[len("/static/"):].replace("/", os.sep))
        return uri

    html = render_template(template, **ctx)
    buf = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=buf, encoding="utf-8",
                            link_callback=link_callback)
    if result.err:
        abort(500)
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename)


@app.route("/praktyki/<int:praktyka_id>/pdf/<kind>")
@login_required
def praktyka_pdf(praktyka_id, kind):
    p = _get_own_praktyka(praktyka_id)
    wpisy = p.wpisy_dziennika.all()
    suma_godzin = sum(w.liczba_godzin or 0 for w in wpisy)

    mapping = {
        "karta": ("pdf/karta.html", f"karta_praktyki_{p.id}.pdf"),
        "dziennik": ("pdf/dziennik.html", f"dziennik_praktyki_{p.id}.pdf"),
        "sprawozdanie": ("pdf/sprawozdanie.html", f"sprawozdanie_praktyki_{p.id}.pdf"),
        "ankieta": ("pdf/ankieta.html", f"ankieta_praktyki_{p.id}.pdf"),
        "program": ("pdf/program.html", f"program_harmonogram_{p.id}.pdf"),
    }
    if kind not in mapping:
        abort(404)
    template, filename = mapping[kind]
    return _render_pdf(
        template, filename,
        p=p, student=p.student, promotor=p.promotor,
        wpisy=wpisy, suma_godzin=suma_godzin,
        today=date.today(),
    )


OCENY = ["2", "3", "3+", "4", "4+", "5"]


# ---------- panel promotora ----------

@app.route("/promotor/")
@login_required
@promotor_required
def promotor_dashboard():
    u = current_user()
    wszystkie = _promotor_praktyki(u).order_by(models.Praktyka.created_at.desc()).all()
    oczekujace = [p for p in wszystkie if p.status in ("zgloszona", "do_oceny")]
    w_trakcie  = [p for p in wszystkie if p.status == "w_trakcie"]
    studenci_ids = {p.student_id for p in wszystkie}
    return render_template(
        "promotor/dashboard.html",
        wszystkie=wszystkie,
        oczekujace=oczekujace,
        w_trakcie=w_trakcie,
        liczba_studentow=len(studenci_ids),
    )


_STUDENCI_PER_PAGE = 25


@app.route("/promotor/studenci")
@login_required
@promotor_required
def promotor_studenci():
    u = current_user()
    page = request.args.get("page", 1, type=int)
    q_text = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "")
    kierunek_filter = request.args.get("kierunek", "")
    sort_by = request.args.get("sort", "nazwisko")

    if u.rola == "root":
        q = models.User.query \
            .join(models.Praktyka, models.Praktyka.student_id == models.User.id)
    else:
        q = models.User.query \
            .join(models.Praktyka, models.Praktyka.student_id == models.User.id) \
            .filter(models.Praktyka.promotor_id == u.id)

    if q_text:
        q = q.filter(
            or_(
                models.User.imie.ilike(f"%{q_text}%"),
                models.User.nazwisko.ilike(f"%{q_text}%"),
                models.User.nr_albumu.ilike(f"%{q_text}%"),
            )
        )
    if status_filter:
        q = q.filter(models.Praktyka.status == status_filter)
    if kierunek_filter:
        q = q.filter(models.User.kierunek == kierunek_filter)

    order_col = models.User.nr_albumu if sort_by == "nr_albumu" else models.User.nazwisko
    q = q.distinct().order_by(order_col)

    pagination = q.paginate(page=page, per_page=_STUDENCI_PER_PAGE, error_out=False)

    studenci = []
    for s in pagination.items:
        if u.rola == "root":
            pp = models.Praktyka.query.filter_by(student_id=s.id) \
                .order_by(models.Praktyka.created_at.desc()).all()
        else:
            pp = models.Praktyka.query.filter_by(student_id=s.id, promotor_id=u.id) \
                .order_by(models.Praktyka.created_at.desc()).all()
        studenci.append({"student": s, "praktyki": pp})

    # Kierunki do dropdownu filtra
    kierunki_q = db.session.query(models.User.kierunek).filter(
        models.User.kierunek.isnot(None)
    )
    if u.rola != "root":
        kierunki_q = kierunki_q.join(
            models.Praktyka, models.Praktyka.student_id == models.User.id
        ).filter(models.Praktyka.promotor_id == u.id)
    kierunki = [k[0] for k in kierunki_q.distinct().order_by(models.User.kierunek).all()]

    return render_template(
        "promotor/studenci.html",
        studenci=studenci,
        pagination=pagination,
        q=q_text,
        status_filter=status_filter,
        kierunek_filter=kierunek_filter,
        sort_by=sort_by,
        kierunki=kierunki,
        statusy=models.Praktyka.STATUSY,
    )


@app.route("/promotor/export-csv")
@login_required
@promotor_required
def promotor_export_csv():
    import csv
    u = current_user()
    praktyki = _promotor_praktyki(u).order_by(
        models.Praktyka.student_id,
        models.Praktyka.created_at.desc(),
    ).all()

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow([
        "ID", "Student", "Nr albumu", "Kierunek", "Semestr",
        "Firma", "Data od", "Data do", "Godziny plan.", "Status",
        "Promotor", "Rok akademicki", "Data zgłoszenia",
    ])
    for p in praktyki:
        writer.writerow([
            p.id,
            p.student.pelne_imie,
            p.student.nr_albumu or "",
            p.student.kierunek or "",
            p.student.semestr or "",
            p.firma_nazwa,
            p.data_od.strftime("%d.%m.%Y") if p.data_od else "",
            p.data_do.strftime("%d.%m.%Y") if p.data_do else "",
            p.liczba_godzin or "",
            p.status_label,
            p.promotor.pelne_imie if p.promotor else "",
            p.rok_akademicki or "",
            p.created_at.strftime("%d.%m.%Y") if p.created_at else "",
        ])

    content = buf.getvalue()
    return send_file(
        io.BytesIO(content.encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"praktyki_{date.today().strftime('%Y%m%d')}.csv",
    )


@app.route("/promotor/studenci/<int:student_id>")
@login_required
@promotor_required
def promotor_student(student_id):
    u = current_user()
    student = models.User.query.get_or_404(student_id)
    praktyki = _promotor_praktyki(u).filter_by(student_id=student_id)\
        .order_by(models.Praktyka.created_at.desc()).all()
    if not praktyki and u.rola != "root":
        abort(403)
    return render_template("promotor/student_detail.html", student=student, praktyki=praktyki)


@app.route("/promotor/praktyki/<int:praktyka_id>")
@login_required
@promotor_required
def promotor_praktyka(praktyka_id):
    p = _get_promotor_praktyka(praktyka_id)
    wpisy = p.wpisy_dziennika.all()
    suma_godzin = sum(w.liczba_godzin or 0 for w in wpisy)
    docs = p.dokumenty.order_by(models.Dokument.created_at.desc()).all()
    return render_template(
        "promotor/praktyka_detail.html",
        p=p, wpisy=wpisy, suma_godzin=suma_godzin, docs=docs, oceny=OCENY,
    )


@app.route("/promotor/praktyki/<int:praktyka_id>/akcja", methods=["POST"])
@login_required
@promotor_required
def promotor_akcja(praktyka_id):
    p = _get_promotor_praktyka(praktyka_id)
    akcja     = request.form.get("akcja")
    komentarz = request.form.get("komentarz", "").strip() or None
    ocena     = request.form.get("ocena", "").strip() or None

    if akcja == "akceptuj" and p.status == "zgloszona":
        p.status = "zaakceptowana"
        p.komentarz_promotora = komentarz
        p.porozumienie_podpisane = bool(request.form.get("porozumienie_podpisane"))
        p.skierowanie_wystawione = bool(request.form.get("skierowanie_wystawione"))
        flash("Praktyka zaakceptowana — student może teraz rozpocząć realizację.", "info")
    elif akcja == "odrzuc" and p.status in ("zgloszona", "do_oceny"):
        p.status = "odrzucona"
        p.komentarz_promotora = komentarz
        flash("Praktyka odrzucona.", "info")
    elif akcja == "zalicz_sem6" and p.status == "w_trakcie":
        p.zaliczenie_sem6 = True
        p.data_zaliczenia_sem6 = date.today()
        p.komentarz_zaliczenia_sem6 = komentarz
        flash("Zaliczenie częściowe semestru 6 wystawione.", "info")
    elif akcja == "zalicz" and p.status == "do_oceny":
        if not ocena:
            flash("Wybierz ocenę przed zaliczeniem.", "error")
            return redirect(url_for("promotor_praktyka", praktyka_id=p.id))
        p.status = "zaliczona"
        p.ocena = ocena
        p.komentarz_promotora = komentarz
        flash(f"Praktyka zaliczona z oceną {ocena}.", "info")
    else:
        flash("Niedozwolona akcja dla bieżącego statusu.", "error")

    db.session.commit()
    return redirect(url_for("promotor_praktyka", praktyka_id=p.id))


# ---------- panel administratora (root) ----------

@app.route("/admin/promotorzy/")
@login_required
@root_required
def admin_promotorzy():
    promotorzy_users = models.User.query.filter(
        models.User.rola.in_(["promotor", "root"])
    ).order_by(models.User.nazwisko, models.User.imie).all()

    result = []
    for pr in promotorzy_users:
        praktyki = models.Praktyka.query.filter_by(promotor_id=pr.id).all()
        studenci_ids = {p.student_id for p in praktyki}
        oczekujace = sum(1 for p in praktyki if p.status in ("zgloszona", "do_oceny"))
        result.append({
            "promotor": pr,
            "liczba_studentow": len(studenci_ids),
            "liczba_praktyk": len(praktyki),
            "oczekujace": oczekujace,
        })
    return render_template("admin/promotorzy.html", promotorzy=result)


@app.route("/admin/promotorzy/<int:user_id>")
@login_required
@root_required
def admin_promotor_detail(user_id):
    promotor = models.User.query.get_or_404(user_id)
    if promotor.rola not in ("promotor", "root"):
        flash("Ten użytkownik nie jest promotorem.", "error")
        return redirect(url_for("admin_promotorzy"))

    praktyki = models.Praktyka.query.filter_by(promotor_id=promotor.id)\
        .order_by(models.Praktyka.created_at.desc()).all()

    studenci_map_dict = {}
    for p in praktyki:
        sid = p.student_id
        if sid not in studenci_map_dict:
            studenci_map_dict[sid] = {"student": p.student, "praktyki": []}
        studenci_map_dict[sid]["praktyki"].append(p)

    studenci_map = sorted(
        [(v["student"], v["praktyki"]) for v in studenci_map_dict.values()],
        key=lambda x: x[0].nazwisko or ""
    )
    return render_template(
        "admin/promotor_detail.html",
        promotor=promotor,
        studenci_map=studenci_map,
        liczba_praktyk=len(praktyki),
    )


@app.route("/admin/")
@login_required
@root_required
def admin_users():
    q = request.args.get("q", "").strip()
    rola_filter = request.args.get("rola", "").strip()

    query = models.User.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                models.User.imie.ilike(like),
                models.User.nazwisko.ilike(like),
                models.User.email.ilike(like),
                models.User.nr_albumu.ilike(like),
            )
        )
    if rola_filter:
        query = query.filter_by(rola=rola_filter)

    users = query.order_by(models.User.rola, models.User.nazwisko, models.User.imie).all()
    return render_template("admin/users.html", users=users, q=q, rola_filter=rola_filter)


@app.route("/admin/uzytkownicy/nowy", methods=["GET", "POST"])
@login_required
@root_required
def admin_user_new():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            flash("Adres e-mail jest wymagany.", "error")
            return render_template("admin/user_form.html", u=None)
        if models.User.query.filter_by(email=email).first():
            flash("Użytkownik z tym adresem e-mail już istnieje.", "error")
            return render_template("admin/user_form.html", u=None)

        u = models.User(
            ms_oid=f"manual-{uuid.uuid4().hex[:16]}",
            email=email,
            imie=request.form.get("imie", "").strip() or None,
            nazwisko=request.form.get("nazwisko", "").strip() or None,
            rola=request.form.get("rola", "student"),
            nr_albumu=request.form.get("nr_albumu", "").strip() or None,
            kierunek=request.form.get("kierunek", "").strip() or None,
            rok_studiow=_parse_int(request.form.get("rok_studiow")),
            semestr=_parse_int(request.form.get("semestr")),
            telefon=request.form.get("telefon", "").strip() or None,
            adres=request.form.get("adres", "").strip() or None,
        )
        db.session.add(u)
        db.session.commit()
        flash(f"Utworzono użytkownika {u.pelne_imie} ({u.rola}).", "info")
        return redirect(url_for("admin_users"))

    return render_template("admin/user_form.html", u=None)


@app.route("/admin/uzytkownicy/<int:user_id>/edytuj", methods=["GET", "POST"])
@login_required
@root_required
def admin_user_edit(user_id):
    u = models.User.query.get_or_404(user_id)
    me = current_user()

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            flash("Adres e-mail jest wymagany.", "error")
            return render_template("admin/user_form.html", u=u)
        conflict = models.User.query.filter(
            models.User.email == email, models.User.id != u.id
        ).first()
        if conflict:
            flash("Inny użytkownik używa już tego adresu e-mail.", "error")
            return render_template("admin/user_form.html", u=u)

        u.email = email
        u.imie = request.form.get("imie", "").strip() or None
        u.nazwisko = request.form.get("nazwisko", "").strip() or None
        u.nr_albumu = request.form.get("nr_albumu", "").strip() or None
        u.kierunek = request.form.get("kierunek", "").strip() or None
        u.rok_studiow = _parse_int(request.form.get("rok_studiow"))
        u.semestr = _parse_int(request.form.get("semestr"))
        u.telefon = request.form.get("telefon", "").strip() or None
        u.adres = request.form.get("adres", "").strip() or None
        if u.id != me.id:
            u.rola = request.form.get("rola", u.rola)
        db.session.commit()
        flash("Dane użytkownika zaktualizowane.", "info")
        return redirect(url_for("admin_users"))

    return render_template("admin/user_form.html", u=u)


@app.route("/admin/uzytkownicy/<int:user_id>/usun", methods=["POST"])
@login_required
@root_required
def admin_user_delete(user_id):
    u = models.User.query.get_or_404(user_id)
    me = current_user()
    if u.id == me.id:
        flash("Nie możesz usunąć własnego konta.", "error")
        return redirect(url_for("admin_users"))
    name = u.pelne_imie
    db.session.delete(u)
    db.session.commit()
    flash(f"Usunięto użytkownika {name}.", "info")
    return redirect(url_for("admin_users"))


# ---------- hospitacje ----------

@app.route("/promotor/praktyki/<int:praktyka_id>/hospitacja", methods=["POST"])
@login_required
@promotor_required
def promotor_hospitacja_dodaj(praktyka_id):
    p = _get_promotor_praktyka(praktyka_id)
    data = _parse_date(request.form.get("data"))
    prowadzacy = request.form.get("prowadzacy", "").strip()
    if not data or not prowadzacy:
        flash("Podaj datę i prowadzącego hospitację.", "error")
    else:
        h = models.Hospitacja(
            praktyka_id=p.id,
            data=data,
            prowadzacy=prowadzacy,
            notatka=request.form.get("notatka", "").strip() or None,
            created_by_id=current_user().id,
        )
        db.session.add(h)
        db.session.commit()
        flash("Hospitacja zapisana.", "info")
    return redirect(url_for("promotor_praktyka", praktyka_id=p.id))


@app.route("/promotor/praktyki/<int:praktyka_id>/hospitacja/<int:h_id>/usun", methods=["POST"])
@login_required
@promotor_required
def promotor_hospitacja_usun(praktyka_id, h_id):
    p = _get_promotor_praktyka(praktyka_id)
    h = models.Hospitacja.query.get_or_404(h_id)
    if h.praktyka_id != p.id:
        abort(404)
    db.session.delete(h)
    db.session.commit()
    flash("Hospitacja usunięta.", "info")
    return redirect(url_for("promotor_praktyka", praktyka_id=p.id))


# ---------- potwierdzenia ZOPZ ----------

@app.route("/promotor/praktyki/<int:praktyka_id>/zopz", methods=["POST"])
@login_required
@promotor_required
def promotor_zopz(praktyka_id):
    p = _get_promotor_praktyka(praktyka_id)
    p.dziennik_potwierdzony_zopz = bool(request.form.get("dziennik_potwierdzony_zopz"))
    p.sprawozdanie_podpisane_zopz = bool(request.form.get("sprawozdanie_podpisane_zopz"))
    db.session.commit()
    flash("Potwierdzenia ZOPZ zapisane.", "info")
    return redirect(url_for("promotor_praktyka", praktyka_id=p.id))


# ---------- egzamin komisyjny ----------

@app.route("/promotor/praktyki/<int:praktyka_id>/egzamin", methods=["GET", "POST"])
@login_required
@promotor_required
def promotor_egzamin(praktyka_id):
    p = _get_promotor_praktyka(praktyka_id)
    if p.status != "do_oceny":
        flash("Egzamin można przeprowadzić tylko dla praktyki w statusie 'do oceny'.", "error")
        return redirect(url_for("promotor_praktyka", praktyka_id=p.id))

    if request.method == "POST":
        data_eg = _parse_date(request.form.get("data_egzaminu"))
        przewodniczacy = request.form.get("przewodniczacy", "").strip()
        ocena = request.form.get("ocena", "").strip()
        if not data_eg or not przewodniczacy or not ocena:
            flash("Wypełnij datę egzaminu, przewodniczącego i ocenę.", "error")
        else:
            prot = models.EgzaminProtokol(
                praktyka_id=p.id,
                data_egzaminu=data_eg,
                przewodniczacy=przewodniczacy,
                czlonkowie=request.form.get("czlonkowie", "").strip() or None,
                ocena=ocena,
                uwagi=request.form.get("uwagi", "").strip() or None,
                created_by_id=current_user().id,
            )
            p.ocena = ocena
            p.komentarz_promotora = request.form.get("uwagi", "").strip() or None
            p.status = "zaliczona"
            db.session.add(prot)
            db.session.commit()
            flash(f"Egzamin zaliczony z oceną {ocena}. Protokół zapisany.", "info")
            return redirect(url_for("promotor_praktyka", praktyka_id=p.id))

    wpisy = p.wpisy_dziennika.all()
    suma_godzin = sum(w.liczba_godzin or 0 for w in wpisy)
    return render_template(
        "promotor/egzamin_form.html",
        p=p, suma_godzin=suma_godzin,
        oceny=models.EgzaminProtokol.OCENY,
    )


# ---------- wnioski o zaliczenie §4 ----------

def _get_own_wniosek(wniosek_id):
    user = current_user()
    w = models.WniosekZaliczenia.query.get_or_404(wniosek_id)
    if w.student_id != user.id and user.rola not in ("promotor", "root"):
        abort(403)
    return w


@app.route("/wnioski/")
@login_required
def wnioski_list():
    user = current_user()
    wnioski = user.wnioski_zaliczenia.order_by(
        models.WniosekZaliczenia.created_at.desc()
    ).all()
    return render_template("student/wnioski_list.html", wnioski=wnioski)


@app.route("/wnioski/nowy", methods=["GET", "POST"])
@login_required
def wniosek_nowy():
    user = current_user()
    if request.method == "POST":
        pracodawca = request.form.get("pracodawca_nazwa", "").strip()
        typ = request.form.get("typ", "").strip()
        if not pracodawca or not typ:
            flash("Podaj typ i nazwę pracodawcy.", "error")
            return render_template("student/wniosek_form.html", w=None)
        w = models.WniosekZaliczenia(
            student_id=user.id,
            typ=typ,
            pracodawca_nazwa=pracodawca,
            pracodawca_adres=request.form.get("pracodawca_adres", "").strip() or None,
            nr_rejestrowy=request.form.get("nr_rejestrowy", "").strip() or None,
            stanowisko=request.form.get("stanowisko", "").strip() or None,
            data_od=_parse_date(request.form.get("data_od")),
            data_do=_parse_date(request.form.get("data_do")),
            opis_obowiazkow=request.form.get("opis_obowiazkow", "").strip() or None,
            uzasadnienie=request.form.get("uzasadnienie", "").strip() or None,
        )
        db.session.add(w)
        db.session.commit()
        flash("Wniosek złożony.", "info")
        return redirect(url_for("wniosek_detail", wniosek_id=w.id))
    return render_template("student/wniosek_form.html", w=None)


@app.route("/wnioski/<int:wniosek_id>")
@login_required
def wniosek_detail(wniosek_id):
    w = _get_own_wniosek(wniosek_id)
    return render_template("student/wniosek_detail.html", w=w)


@app.route("/wnioski/<int:wniosek_id>/dokument", methods=["POST"])
@login_required
def wniosek_dodaj_dok(wniosek_id):
    w = _get_own_wniosek(wniosek_id)
    if w.status not in ("zlozony", "w_ocenie_komisji"):
        flash("Nie można dodać dokumentu do wniosku w tym statusie.", "error")
        return redirect(url_for("wniosek_detail", wniosek_id=w.id))
    plik = request.files.get("plik")
    typ = request.form.get("typ", "inne")
    if not plik or not plik.filename:
        flash("Wybierz plik.", "error")
    elif not _allowed_file(plik.filename):
        flash("Dozwolone formaty: PDF, DOC/DOCX, ODT, JPG, PNG.", "error")
    else:
        original = secure_filename(plik.filename)
        ext = original.rsplit(".", 1)[1].lower()
        stored = f"{uuid.uuid4().hex}.{ext}"
        plik.save(UPLOAD_DIR / stored)
        d = models.WniosekDokument(
            wniosek_id=w.id,
            typ=typ,
            nazwa_oryginalna=original,
            nazwa_pliku=stored,
            mime_type=plik.mimetype,
            rozmiar=(UPLOAD_DIR / stored).stat().st_size,
        )
        db.session.add(d)
        db.session.commit()
        flash("Dokument dodany.", "info")
    return redirect(url_for("wniosek_detail", wniosek_id=w.id))


@app.route("/wnioski/<int:wniosek_id>/dokument/<int:dok_id>/usun", methods=["POST"])
@login_required
def wniosek_usun_dok(wniosek_id, dok_id):
    w = _get_own_wniosek(wniosek_id)
    d = models.WniosekDokument.query.get_or_404(dok_id)
    if d.wniosek_id != w.id:
        abort(404)
    try:
        (UPLOAD_DIR / d.nazwa_pliku).unlink(missing_ok=True)
    except OSError:
        pass
    db.session.delete(d)
    db.session.commit()
    flash("Dokument usunięty.", "info")
    return redirect(url_for("wniosek_detail", wniosek_id=w.id))


@app.route("/wnioski/<int:wniosek_id>/dokument/<int:dok_id>/pobierz")
@login_required
def wniosek_pobierz_dok(wniosek_id, dok_id):
    w = _get_own_wniosek(wniosek_id)
    d = models.WniosekDokument.query.get_or_404(dok_id)
    if d.wniosek_id != w.id:
        abort(404)
    return send_from_directory(
        UPLOAD_DIR, d.nazwa_pliku,
        as_attachment=True, download_name=d.nazwa_oryginalna,
    )


@app.route("/promotor/wnioski/")
@login_required
@promotor_required
def promotor_wnioski():
    u = current_user()
    if u.rola == "root":
        wnioski = models.WniosekZaliczenia.query.order_by(
            models.WniosekZaliczenia.created_at.desc()
        ).all()
    else:
        student_ids = {p.student_id for p in models.Praktyka.query.filter_by(promotor_id=u.id)}
        wnioski = models.WniosekZaliczenia.query.filter(
            models.WniosekZaliczenia.student_id.in_(student_ids)
        ).order_by(models.WniosekZaliczenia.created_at.desc()).all()
    return render_template("promotor/wnioski.html", wnioski=wnioski)


@app.route("/promotor/wnioski/<int:wniosek_id>", methods=["GET", "POST"])
@login_required
@promotor_required
def promotor_wniosek(wniosek_id):
    w = models.WniosekZaliczenia.query.get_or_404(wniosek_id)
    if request.method == "POST":
        akcja = request.form.get("akcja")
        komentarz = request.form.get("komentarz", "").strip() or None
        if akcja == "ocen_pozytywnie" and w.status in ("zlozony", "w_ocenie_komisji"):
            w.ocena_komisji = "pozytywna"
            w.komentarz_komisji = komentarz
            w.data_oceny_komisji = date.today()
            w.status = "u_dyrektora"
            flash("Ocena merytoryczna komisji: pozytywna. Wniosek przekazany do dyrektora.", "info")
        elif akcja == "ocen_negatywnie" and w.status in ("zlozony", "w_ocenie_komisji"):
            w.ocena_komisji = "negatywna"
            w.komentarz_komisji = komentarz
            w.data_oceny_komisji = date.today()
            w.status = "odrzucony"
            flash("Ocena merytoryczna komisji: negatywna. Wniosek odrzucony.", "info")
        else:
            flash("Niedozwolona akcja.", "error")
        db.session.commit()
        return redirect(url_for("promotor_wniosek", wniosek_id=w.id))
    return render_template("promotor/wniosek_detail.html", w=w)


@app.route("/admin/wnioski/<int:wniosek_id>/decyzja", methods=["POST"])
@login_required
@root_required
def admin_wniosek_decyzja(wniosek_id):
    w = models.WniosekZaliczenia.query.get_or_404(wniosek_id)
    if w.status != "u_dyrektora":
        flash("Decyzja możliwa tylko dla wniosków po ocenie komisji.", "error")
        return redirect(url_for("promotor_wniosek", wniosek_id=w.id))
    akcja = request.form.get("akcja")
    komentarz = request.form.get("komentarz", "").strip() or None
    if akcja == "zatwierdz":
        w.decyzja_dyrektora = "zatwierdzona"
        w.komentarz_dyrektora = komentarz
        w.data_decyzji = date.today()
        w.status = "zatwierdzony"
        flash("Wniosek zatwierdzony przez dyrektora.", "info")
    elif akcja == "odrzuc":
        w.decyzja_dyrektora = "odrzucona"
        w.komentarz_dyrektora = komentarz
        w.data_decyzji = date.today()
        w.status = "odrzucony"
        flash("Wniosek odrzucony przez dyrektora.", "info")
    else:
        flash("Niedozwolona akcja.", "error")
    db.session.commit()
    return redirect(url_for("promotor_wniosek", wniosek_id=w.id))


# ---------- wnioski o przedłużenie §6.2 ----------

@app.route("/praktyki/<int:praktyka_id>/przedluzenie", methods=["GET", "POST"])
@login_required
def praktyka_przedluzenie(praktyka_id):
    p = _get_own_praktyka(praktyka_id)
    if p.status != "w_trakcie":
        flash("Wniosek o przedłużenie można złożyć tylko dla praktyki w trakcie realizacji.", "error")
        return redirect(url_for("praktyka_detail", praktyka_id=p.id))
    if request.method == "POST":
        powod = request.form.get("powod", "").strip()
        godziny = _parse_int(request.form.get("godziny_nieobecnosci"))
        proponowana = _parse_date(request.form.get("proponowana_data_do"))
        if not powod:
            flash("Wybierz powód.", "error")
        elif powod == "choroba" and (not godziny or godziny <= 40):
            flash("Przy chorobie wymagana łączna nieobecność powyżej 40 godzin (§6.2).", "error")
        elif proponowana and p.data_do and (proponowana - p.data_do).days > 31:
            flash("Przedłużenie możliwe maksymalnie o 1 miesiąc od planowanego zakończenia (§6.3).", "error")
        else:
            wn = models.WniosekPrzedluzenia(
                praktyka_id=p.id,
                powod=powod,
                godziny_nieobecnosci=godziny,
                opis=request.form.get("opis", "").strip() or None,
                proponowana_data_do=proponowana,
            )
            db.session.add(wn)
            db.session.commit()
            flash("Wniosek o przedłużenie złożony.", "info")
            return redirect(url_for("praktyka_detail", praktyka_id=p.id))
    return render_template("student/przedluzenie_form.html", p=p)


@app.route("/admin/przedluzenia/")
@login_required
@root_required
def admin_przedluzenia():
    wnioski = models.WniosekPrzedluzenia.query.order_by(
        models.WniosekPrzedluzenia.created_at.desc()
    ).all()
    return render_template("admin/przedluzenia.html", wnioski=wnioski)


@app.route("/admin/przedluzenia/<int:wniosek_id>/akcja", methods=["POST"])
@login_required
@root_required
def admin_przedluzenie_akcja(wniosek_id):
    wn = models.WniosekPrzedluzenia.query.get_or_404(wniosek_id)
    if wn.status != "zlozony":
        flash("Wniosek już rozpatrzony.", "error")
        return redirect(url_for("admin_przedluzenia"))
    akcja = request.form.get("akcja")
    komentarz = request.form.get("komentarz", "").strip() or None
    nowa_data = _parse_date(request.form.get("nowa_data_do"))
    if akcja == "zatwierdz":
        if not nowa_data:
            flash("Podaj nową datę zakończenia.", "error")
            return redirect(url_for("admin_przedluzenia"))
        if wn.praktyka.data_do and (nowa_data - wn.praktyka.data_do).days > 31:
            flash("Przedłużenie nie może przekraczać 1 miesiąca od oryginalnej daty zakończenia (§6.3).", "error")
            return redirect(url_for("admin_przedluzenia"))
        wn.status = "zatwierdzony"
        wn.nowa_data_do = nowa_data
        wn.komentarz = komentarz
        wn.praktyka.data_do_przedluzenie = nowa_data
        flash("Przedłużenie zatwierdzone.", "info")
    elif akcja == "odrzuc":
        wn.status = "odrzucony"
        wn.komentarz = komentarz
        flash("Wniosek o przedłużenie odrzucony.", "info")
    else:
        flash("Niedozwolona akcja.", "error")
    db.session.commit()
    return redirect(url_for("admin_przedluzenia"))


# ---------- wnioski o zmianę terminu §3 Org. pkt 3 & 7 ----------

@app.route("/zmiana-terminu/")
@login_required
def zmiana_terminu_list():
    user = current_user()
    wnioski = user.wnioski_zmiana_terminu.order_by(
        models.WniosekZmianaTerminu.created_at.desc()
    ).all()
    return render_template("student/zmiana_terminu_list.html", wnioski=wnioski)


@app.route("/zmiana-terminu/nowy", methods=["GET", "POST"])
@login_required
def zmiana_terminu_nowy():
    user = current_user()
    if request.method == "POST":
        powod = request.form.get("powod", "").strip()
        opis = request.form.get("opis", "").strip()
        if not powod or not opis:
            flash("Wybierz powód i podaj opis uzasadnienia.", "error")
            return render_template("student/zmiana_terminu_form.html", wn=None)
        data_od = _parse_date(request.form.get("proponowana_data_od"))
        data_do = _parse_date(request.form.get("proponowana_data_do"))
        if data_od and data_do and data_do < data_od:
            flash("Data zakończenia nie może być wcześniejsza niż data rozpoczęcia.", "error")
            return render_template("student/zmiana_terminu_form.html", wn=None)
        wn = models.WniosekZmianaTerminu(
            student_id=user.id,
            powod=powod,
            opis=opis,
            proponowany_semestr=_parse_int(request.form.get("proponowany_semestr")),
            proponowana_data_od=data_od,
            proponowana_data_do=data_do,
        )
        db.session.add(wn)
        db.session.commit()
        flash("Wniosek o zmianę terminu złożony.", "info")
        return redirect(url_for("zmiana_terminu_detail", wn_id=wn.id))
    return render_template("student/zmiana_terminu_form.html", wn=None)


@app.route("/zmiana-terminu/<int:wn_id>")
@login_required
def zmiana_terminu_detail(wn_id):
    user = current_user()
    wn = models.WniosekZmianaTerminu.query.get_or_404(wn_id)
    if wn.student_id != user.id and user.rola not in ("promotor", "root"):
        abort(403)
    return render_template("student/zmiana_terminu_detail.html", wn=wn)


@app.route("/admin/zmiana-terminu/")
@login_required
@root_required
def admin_zmiana_terminu():
    wnioski = models.WniosekZmianaTerminu.query.order_by(
        models.WniosekZmianaTerminu.created_at.desc()
    ).all()
    return render_template("admin/zmiana_terminu.html", wnioski=wnioski)


@app.route("/admin/zmiana-terminu/<int:wn_id>/decyzja", methods=["POST"])
@login_required
@root_required
def admin_zmiana_terminu_decyzja(wn_id):
    wn = models.WniosekZmianaTerminu.query.get_or_404(wn_id)
    if wn.status != "zlozony":
        flash("Wniosek już rozpatrzony.", "error")
        return redirect(url_for("admin_zmiana_terminu"))
    akcja = request.form.get("akcja")
    komentarz = request.form.get("komentarz", "").strip() or None
    if akcja == "zatwierdz":
        wn.status = "zatwierdzony"
        wn.komentarz_dyrektora = komentarz
        wn.data_decyzji = date.today()
        flash("Wniosek zatwierdzony.", "info")
    elif akcja == "odrzuc":
        wn.status = "odrzucony"
        wn.komentarz_dyrektora = komentarz
        wn.data_decyzji = date.today()
        flash("Wniosek odrzucony.", "info")
    else:
        flash("Niedozwolona akcja.", "error")
    db.session.commit()
    return redirect(url_for("admin_zmiana_terminu"))


if __name__ == "__main__":
    app.run(debug=True)
