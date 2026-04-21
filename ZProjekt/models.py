from datetime import datetime

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    ms_oid = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    imie = db.Column(db.String(100))
    nazwisko = db.Column(db.String(100))
    nr_albumu = db.Column(db.String(20), index=True)
    kierunek = db.Column(db.String(100))
    specjalnosc = db.Column(db.String(100))
    rok_studiow = db.Column(db.Integer)
    semestr = db.Column(db.Integer)
    telefon = db.Column(db.String(30))
    adres = db.Column(db.String(255))
    rola = db.Column(db.String(20), default="student", nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime)

    praktyki = db.relationship(
        "Praktyka",
        foreign_keys="Praktyka.student_id",
        backref="student",
        lazy="dynamic",
    )
    prowadzone_praktyki = db.relationship(
        "Praktyka",
        foreign_keys="Praktyka.promotor_id",
        backref="promotor",
        lazy="dynamic",
    )
    wnioski_zaliczenia = db.relationship(
        "WniosekZaliczenia",
        backref="student",
        lazy="dynamic",
        foreign_keys="WniosekZaliczenia.student_id",
    )

    @property
    def pelne_imie(self):
        return f"{self.imie or ''} {self.nazwisko or ''}".strip() or self.email

    def __repr__(self):
        return f"<User {self.email}>"


class Praktyka(db.Model):
    __tablename__ = "praktyki"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    promotor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    firma_nazwa = db.Column(db.String(255), nullable=False)
    firma_adres = db.Column(db.String(255))
    firma_nip = db.Column(db.String(20))
    firma_profil = db.Column(db.String(255))
    opiekun_zakladowy_imie_nazwisko = db.Column(db.String(200))
    opiekun_zakladowy_stanowisko = db.Column(db.String(150))
    opiekun_zakladowy_kontakt = db.Column(db.String(150))
    opiekun_zakladowy_wyksztalcenie = db.Column(db.String(255))

    rok_akademicki = db.Column(db.String(20))
    semestr_od = db.Column(db.Integer, default=6)
    semestr_do = db.Column(db.Integer, default=7)

    data_od = db.Column(db.Date)
    data_do = db.Column(db.Date)
    data_do_przedluzenie = db.Column(db.Date)  # zatwierdzona nowa data zakończenia
    liczba_godzin = db.Column(db.Integer)
    tryb_realizacji = db.Column(db.String(20))
    harmonogram = db.Column(db.Text)
    zakres_zadan = db.Column(db.Text)
    bhp_zaakceptowane = db.Column(db.Boolean, default=False, nullable=False, server_default="false")
    regulamin_zapoznany = db.Column(db.Boolean, default=False, nullable=False, server_default="false")
    ubezpieczenie_nnw = db.Column(db.Boolean, default=False, nullable=False, server_default="false")
    erasmus_plus = db.Column(db.Boolean, default=False, nullable=False, server_default="false")
    porozumienie_podpisane = db.Column(db.Boolean, default=False, nullable=False, server_default="false")
    skierowanie_wystawione = db.Column(db.Boolean, default=False, nullable=False, server_default="false")
    dziennik_potwierdzony_zopz = db.Column(db.Boolean, default=False, nullable=False, server_default="false")
    sprawozdanie_podpisane_zopz = db.Column(db.Boolean, default=False, nullable=False, server_default="false")

    status = db.Column(db.String(20), default="robocza", nullable=False)
    ocena = db.Column(db.String(20))
    komentarz_promotora = db.Column(db.Text)

    zaliczenie_sem6 = db.Column(db.Boolean, default=False, nullable=False, server_default="false")
    data_zaliczenia_sem6 = db.Column(db.Date)
    komentarz_zaliczenia_sem6 = db.Column(db.Text)

    ocena_zopz_parametryczna = db.Column(db.Integer)          # 1–5 (Karta / Zał. 3)
    ocena_zopz_opisowa = db.Column(db.Text)                   # opisowa ocena ZOPZ (Karta / Zał. 3)
    efekty_potwierdzone_zopz = db.Column(db.Boolean, default=False, nullable=False, server_default="false")  # Zał. 4

    # Sprawozdanie studenta z praktyki (Załącznik nr 7) – trzy sekcje
    sprawozdanie_charakterystyka = db.Column(db.Text)   # I. Charakterystyka miejsca odbywania praktyki
    sprawozdanie_opis_prac = db.Column(db.Text)         # II. Opis i analiza wykonywanych prac
    sprawozdanie_samoocena = db.Column(db.Text)         # III. Wiedza i umiejętności / samoocena efektów

    # Ankieta (Zał. 5) – 14 pytań, skala 1=zdecydowanie nie … 5=zdecydowanie tak
    ankieta_p01 = db.Column(db.Integer)
    ankieta_p02 = db.Column(db.Integer)
    ankieta_p03 = db.Column(db.Integer)
    ankieta_p04 = db.Column(db.Integer)
    ankieta_p05 = db.Column(db.Integer)
    ankieta_p06 = db.Column(db.Integer)
    ankieta_p07 = db.Column(db.Integer)
    ankieta_p08 = db.Column(db.Integer)
    ankieta_p09 = db.Column(db.Integer)
    ankieta_p10 = db.Column(db.Integer)
    ankieta_p11 = db.Column(db.Integer)
    ankieta_p12 = db.Column(db.Integer)
    ankieta_p13 = db.Column(db.Integer)
    ankieta_p14 = db.Column(db.Integer)
    ankieta_uwagi = db.Column(db.Text)
    # Metryczka ankiety
    ankieta_rok_akademicki = db.Column(db.String(20))
    ankieta_forma_studiow = db.Column(db.String(20))   # stacjonarne / niestacjonarne

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    dokumenty = db.relationship(
        "Dokument",
        backref="praktyka",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    wpisy_dziennika = db.relationship(
        "DziennikWpis",
        backref="praktyka",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="DziennikWpis.data",
    )
    hospitacje = db.relationship(
        "Hospitacja",
        backref="praktyka",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Hospitacja.data",
    )
    egzamin = db.relationship(
        "EgzaminProtokol",
        backref="praktyka",
        cascade="all, delete-orphan",
        uselist=False,
    )
    wnioski_przedluzenia = db.relationship(
        "WniosekPrzedluzenia",
        backref="praktyka",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    STATUSY = {
        "robocza": "Robocza",
        "zgloszona": "Zgłoszona do akceptacji",
        "zaakceptowana": "Zaakceptowana",
        "w_trakcie": "W trakcie realizacji",
        "do_oceny": "Złożona do oceny",
        "zaliczona": "Zaliczona",
        "odrzucona": "Odrzucona",
    }

    @property
    def status_label(self):
        return self.STATUSY.get(self.status, self.status)

    @property
    def suma_godzin_dziennik(self):
        return sum(w.liczba_godzin or 0 for w in self.wpisy_dziennika)

    @property
    def mozna_edytowac(self):
        return self.status in ("robocza", "zgloszona", "zaakceptowana", "w_trakcie")

    @property
    def efektywna_data_do(self):
        return self.data_do_przedluzenie or self.data_do

    @property
    def termin_zlozenia_dokumentow(self):
        from datetime import timedelta
        d = self.efektywna_data_do
        return d + timedelta(days=7) if d else None


class Dokument(db.Model):
    __tablename__ = "dokumenty"

    id = db.Column(db.Integer, primary_key=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey("praktyki.id", ondelete="CASCADE"), nullable=False, index=True)
    typ = db.Column(db.String(30), nullable=False)
    nazwa_oryginalna = db.Column(db.String(255), nullable=False)
    nazwa_pliku = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100))
    rozmiar = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    TYPY = {
        "karta": "Karta praktyki",
        "dziennik": "Dziennik praktyki",
        "sprawozdanie": "Sprawozdanie",
        "ankieta": "Ankieta",
        "efekty": "Potwierdzenie efektów",
        "umowa": "Umowa / porozumienie",
        "oswiadczenie_instytucji": "Oświadczenie instytucji (Zał. 9)",
        "inne": "Inne",
    }

    @property
    def typ_label(self):
        return self.TYPY.get(self.typ, self.typ)


class DziennikWpis(db.Model):
    __tablename__ = "dziennik_wpisy"

    id = db.Column(db.Integer, primary_key=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey("praktyki.id", ondelete="CASCADE"), nullable=False, index=True)
    data = db.Column(db.Date, nullable=False)
    godz_od = db.Column(db.Time)
    godz_do = db.Column(db.Time)
    opis = db.Column(db.Text, nullable=False)
    efekty = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def liczba_godzin(self):
        if not self.godz_od or not self.godz_do:
            return None
        delta = (
            datetime.combine(self.data, self.godz_do)
            - datetime.combine(self.data, self.godz_od)
        )
        return round(delta.total_seconds() / 3600, 1)


# ── Hospitacja ───────────────────────────────────────────────────────────────

class Hospitacja(db.Model):
    __tablename__ = "hospitacje"

    id = db.Column(db.Integer, primary_key=True)
    praktyka_id = db.Column(
        db.Integer, db.ForeignKey("praktyki.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    data = db.Column(db.Date, nullable=False)
    prowadzacy = db.Column(db.String(200), nullable=False)
    notatka = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    created_by = db.relationship("User", foreign_keys=[created_by_id])


# ── Egzamin komisyjny ─────────────────────────────────────────────────────────

class EgzaminProtokol(db.Model):
    __tablename__ = "egzaminy_protokoly"

    id = db.Column(db.Integer, primary_key=True)
    praktyka_id = db.Column(
        db.Integer, db.ForeignKey("praktyki.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    data_egzaminu = db.Column(db.Date, nullable=False)
    przewodniczacy = db.Column(db.String(200), nullable=False)
    czlonkowie = db.Column(db.Text)
    ocena = db.Column(db.String(20), nullable=False)
    uwagi = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    created_by = db.relationship("User", foreign_keys=[created_by_id])

    OCENY = ["2", "3", "3+", "4", "4+", "5"]


# ── Wniosek o zaliczenie przez pracę / staż / działalność (§4) ───────────────

class WniosekZaliczenia(db.Model):
    __tablename__ = "wnioski_zaliczenia"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    typ = db.Column(db.String(30), nullable=False)
    pracodawca_nazwa = db.Column(db.String(255), nullable=False)
    pracodawca_adres = db.Column(db.String(255))
    nr_rejestrowy = db.Column(db.String(100))   # NIP / CEIDG / KRS
    stanowisko = db.Column(db.String(200))
    data_od = db.Column(db.Date)
    data_do = db.Column(db.Date)
    opis_obowiazkow = db.Column(db.Text)
    uzasadnienie = db.Column(db.Text)           # dlaczego zakres = program praktyki

    # Ocena merytoryczna komisji (promotor)
    status = db.Column(db.String(30), default="zlozony", nullable=False)
    ocena_komisji = db.Column(db.String(20))     # pozytywna / negatywna
    komentarz_komisji = db.Column(db.Text)
    data_oceny_komisji = db.Column(db.Date)

    # Decyzja dyrektora (root)
    decyzja_dyrektora = db.Column(db.String(20)) # zatwierdzona / odrzucona
    komentarz_dyrektora = db.Column(db.Text)
    data_decyzji = db.Column(db.Date)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    dokumenty = db.relationship(
        "WniosekDokument",
        backref="wniosek",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    TYPY = {
        "praca_zawodowa": "Praca zawodowa",
        "staz": "Staż",
        "dzialalnosc": "Działalność gospodarcza",
    }

    STATUSY = {
        "zlozony": "Złożony",
        "w_ocenie_komisji": "W ocenie komisji",
        "u_dyrektora": "Przekazany do dyrektora",
        "zatwierdzony": "Zatwierdzony",
        "odrzucony": "Odrzucony",
    }

    @property
    def status_label(self):
        return self.STATUSY.get(self.status, self.status)

    @property
    def typ_label(self):
        return self.TYPY.get(self.typ, self.typ)


class WniosekDokument(db.Model):
    __tablename__ = "wnioski_dokumenty"

    id = db.Column(db.Integer, primary_key=True)
    wniosek_id = db.Column(
        db.Integer, db.ForeignKey("wnioski_zaliczenia.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    typ = db.Column(db.String(30), nullable=False)
    nazwa_oryginalna = db.Column(db.String(255), nullable=False)
    nazwa_pliku = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100))
    rozmiar = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    TYPY = {
        "zatrudnienie": "Zaświadczenie o zatrudnieniu",
        "zakres_obowiazkow": "Zakres obowiązków / opis stanowiska",
        "ceidg_krs": "Wyciąg CEIDG / KRS",
        "inne": "Inne",
    }

    @property
    def typ_label(self):
        return self.TYPY.get(self.typ, self.typ)


# ── Wniosek o zmianę terminu praktyki (§3 Org. pkt 3 & 7) ───────────────────

class WniosekZmianaTerminu(db.Model):
    """Pisemny wniosek studenta o realizację praktyki w innym terminie niż
    wskazany w programie studiów (§3 Org. pkt 3) lub przesunięcie terminu
    z powodu wyjazdu zagranicznego / Erasmus (§3 Org. pkt 7).
    Decyzję podejmuje Dyrektor Instytutu (rola root).
    """
    __tablename__ = "wnioski_zmiana_terminu"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    powod = db.Column(db.String(20), nullable=False)   # erasmus / szczegolny
    opis = db.Column(db.Text, nullable=False)
    proponowany_semestr = db.Column(db.Integer)         # docelowy semestr realizacji
    proponowana_data_od = db.Column(db.Date)
    proponowana_data_do = db.Column(db.Date)

    status = db.Column(db.String(20), default="zlozony", nullable=False)
    komentarz_dyrektora = db.Column(db.Text)
    data_decyzji = db.Column(db.Date)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = db.relationship("User", foreign_keys=[student_id],
                              backref=db.backref("wnioski_zmiana_terminu", lazy="dynamic"))

    POWODY = {
        "erasmus": "Wyjazd zagraniczny / Erasmus+",
        "szczegolny": "Szczególnie uzasadniony przypadek (§3 Org. pkt 3)",
    }

    STATUSY = {
        "zlozony": "Złożony",
        "zatwierdzony": "Zatwierdzony",
        "odrzucony": "Odrzucony",
    }

    @property
    def status_label(self):
        return self.STATUSY.get(self.status, self.status)

    @property
    def powod_label(self):
        return self.POWODY.get(self.powod, self.powod)


# ── Wniosek o przedłużenie praktyki (§6.2) ───────────────────────────────────

class WniosekPrzedluzenia(db.Model):
    __tablename__ = "wnioski_przedluzenia"

    id = db.Column(db.Integer, primary_key=True)
    praktyka_id = db.Column(
        db.Integer, db.ForeignKey("praktyki.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    powod = db.Column(db.String(30), nullable=False)   # choroba / inne
    godziny_nieobecnosci = db.Column(db.Integer)       # przy chorobie
    opis = db.Column(db.Text)
    proponowana_data_do = db.Column(db.Date)

    status = db.Column(db.String(20), default="zlozony", nullable=False)
    nowa_data_do = db.Column(db.Date)                  # zatwierdzona data
    komentarz = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    POWODY = {
        "choroba": "Choroba",
        "inne": "Inne przyczyny niezależne od studenta",
    }

    STATUSY = {
        "zlozony": "Złożony",
        "zatwierdzony": "Zatwierdzony",
        "odrzucony": "Odrzucony",
    }

    @property
    def status_label(self):
        return self.STATUSY.get(self.status, self.status)

    @property
    def powod_label(self):
        return self.POWODY.get(self.powod, self.powod)
