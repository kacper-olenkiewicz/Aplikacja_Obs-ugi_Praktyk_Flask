# System Obslugi Praktyk Zawodowych -- ANS Elblag

System elektronicznego rozliczania praktyk zawodowych dla kierunku
Informatyka Stosowana w Akademii Nauk Stosowanych w Elblągu.

Aplikacja wspiera pelny cykl praktyki -- od zgloszenia przez studenta,
przez akceptacje opiekuna (UOPZ), realizacje, hospitacje, egzamin
komisyjny, az do zaliczenia semestru -- zgodnie z regulaminem praktyk
zawodowych Instytutu Informatyki Stosowanej.

---

## 1. Podstawy aplikacji Flask

Aplikacja zbudowana jest w oparciu o framework Flask (Python 3.12).

| Element | Realizacja |
|---|---|
| Plik glowny | `ZProjekt/app.py` -- trasy, logika uwierzytelniania, helpery PDF |
| Szablony HTML | `ZProjekt/templates/` -- Jinja2, dziedziczenie z `base.html` |
| Nawigacja | menu glowne w `base.html`, panele wg roli (`student/`, `promotor/`, `admin/`) |
| Srodowisko wirtualne | `venv/` (Python `venv`) |
| Zarzadzanie konfiguracja | `ZProjekt/config.py` + plik `.env` |
| Render szablonow | `render_template` we wszystkich trasach |

Zdefiniowane trasy obejmuja m.in.:
- `/` -- strona glowna / logowanie
- `/student/dashboard`, `/promotor/dashboard` -- panele uzytkownikow
- `/praktyki/<id>/...` -- szczegoly, edycja, dokumenty, dziennik
- `/wnioski/...` -- wnioski o zaliczenie, przedluzenie, zmiane terminu
- `/admin/users`, `/admin/promotorzy` -- zarzadzanie uzytkownikami

---

## 2. Obsluga formularzy i walidacja danych

| Wymaganie | Realizacja |
|---|---|
| Obsluga formularzy POST | formularze praktyki, dziennika, wnioskow (`request.form`) |
| Rozroznienie GET / POST | kazdy widok edycji obsluguje oba typy zadan |
| Zwracanie JSON | `jsonify` w endpointach PDF (`/pdf/status/<task_id>`) oraz eksporcie CSV |
| Walidacja danych | walidacja po stronie serwera: wymagane pola, format dat, poprawnosc NIP, dozwolone rozszerzenia plikow |
| Klasy Python | modele danych w `models.py` (klasy SQLAlchemy: `User`, `Praktyka`, `DziennikWpis` itd.) |
| Zapis danych | trwaly zapis do bazy PostgreSQL (nie do plikow JSON) |

Formularze obsluguja rowniez:
- `request.form.getlist()` -- dynamiczne listy (efekty ksztalcenia, czlonkowie komisji)
- walidacje miedzy formularzami (np. liczba godzin w dzienniku vs. wymagane 120 dni)

---

## 3. Trwalosc danych

Dane przechowywane sa w relacyjnej bazie danych PostgreSQL 16.

| Aspekt | Realizacja |
|---|---|
| ORM | SQLAlchemy 2.0 + Flask-SQLAlchemy |
| Migracje | Flask-Migrate (Alembic) -- `ZProjekt/migrations/versions/` |
| Dynamiczne formularze | wpisy dziennika (dodawanie/usuwanie wierszy w tabeli) |
| Integracja z JavaScript | dynamiczne dodawanie wpisow, obsluga statusu generowania PDF |
| Synchronizacja frontend-backend | formularze POST + AJAX (status PDF, eksport CSV) |

Zamiast funkcji `load_data()` / `save_data()` operujacych na plikach JSON,
projekt wykorzystuje ORM SQLAlchemy -- dane odczytywane sa przez
`Model.query.filter_by(...)`, a zapisywane przez `db.session.add()` /
`db.session.commit()`.

---

## 4. Analiza systemu i wymagania

### Aktorzy systemu

| Aktor | Rola w systemie |
|---|---|
| Student | zaklada praktyke, prowadzi dziennik, sklada wnioski, wgrywa dokumenty, wypelnia sprawozdanie i ankiete |
| Opiekun uczelniany (UOPZ / promotor) | akceptuje praktyki, potwierdza porozumienia, wystawia skierowania, prowadzi hospitacje, ocenia, zalicza semestr |
| Opiekun zakladowy (ZOPZ) | podspisuje potwierdzenia BHP, zaswiadczenie odbycia praktyki, wystawia ocene parametryczna i opisowa (drukowana w PDF) |
| Dyrektor Instytutu (root) | rozpatruje wnioski o zmiane terminu i zaliczenie z pracy, zarzadza uzytkownikami, ma dostep do wszystkich praktyk i eksportu CSV |

### Wymagania funkcjonalne

1. Logowanie uzytkownikow przez konto Microsoft (OAuth2 / MSAL)
2. Rejestracja praktyki z danymi firmy, opiekuna zakladowego i terminem
3. Prowadzenie dziennika praktyk z wpisami dziennymi (data, godziny, opis, efekty)
4. Skladanie wnioskow o zaliczenie praktyki na podstawie pracy / stazu / dzialalnosci (par. 4)
5. Skladanie wnioskow o przedluzenie terminu praktyki (par. 6.2)
6. Skladanie wnioskow o zmiane terminu/semestru praktyki (par. 3)
7. Generowanie dokumentow PDF: karta praktyki, dziennik, sprawozdanie, ankieta, program, efekty
8. Wgrywanie dokumentow (porozumienie, zaswiadczenia, oswiadczenia)
9. Hospitacje -- rejestracja wizyt opiekuna w zakladzie pracy
10. Egzamin komisyjny -- protokol z ocena

### User stories

1. *Jako student* chce zglosic praktyke z danymi firmy i opiekuna, aby promotor mogl ja zaakceptowac i wystawic skierowanie.
2. *Jako promotor* chce przegladac praktyki moich studentow, prowadzic hospitacje i wystawiac ocene, aby rozliczyc semestr.
3. *Jako dyrektor* chce rozpatrywac wnioski o zmiane terminu praktyki (Erasmus, przypadki szczegolne), aby studenci mogli realizowac praktyki w innym semestrze.

### Wymagania niefunkcjonalne

| Kategoria | Opis |
|---|---|
| Bezpieczenstwo | uwierzytelnianie OAuth2 (Microsoft MSAL), dekorator `@login_required`, kontrola dostepu wg roli, CSRF przez sesje Flask |
| Wydajnosc | generowanie PDF w tle (Celery + Redis), paginacja list, indeksy na kluczach obcych |
| Uzytecznosc | responsywny interfejs, panele dedykowane dla kazdej roli, komunikaty flash |
| Archiwizacja | dane w PostgreSQL z wolumenem Docker, pliki uzytkownikow w katalogu `uploads/` |

### Workflow dokumentow

```
Student tworzy praktyke (robocza)
    |
    v
Student zglasza do akceptacji (zgloszona)
    |
    v
Promotor akceptuje (zaakceptowana)   <-- lub odrzuca (odrzucona)
    |
    v
Student rozpoczyna realizacje (w_trakcie)
    |-- prowadzi dziennik
    |-- wgrywa dokumenty
    |-- moze zlozyc wniosek o przedluzenie
    v
Student sklada do oceny (do_oceny)
    |
    v
Promotor wystawia ocene (zaliczona)
```

---

## 5. Modelowanie systemu

### Diagram stanow praktyki

```
robocza --> zgloszona --> zaakceptowana --> w_trakcie --> do_oceny --> zaliczona
                |                                                       ^
                v                                                       |
            odrzucona                                               (egzamin)
```

Stany zdefiniowane w `models.py` (`Praktyka.STATUSY`):
- `robocza` -- student edytuje dane
- `zgloszona` -- czeka na akceptacje promotora
- `zaakceptowana` -- promotor zatwierdzil
- `w_trakcie` -- student realizuje praktyke
- `do_oceny` -- student zlozyl dokumenty do oceny
- `zaliczona` -- promotor wystawil ocene koncowa
- `odrzucona` -- promotor odrzucil zgloszenie

### Diagram przepływu -- logika uprawnien

```
Uzytkownik wchodzi na strone
    |
    v
Zalogowany? --[NIE]--> Strona logowania (Microsoft OAuth2)
    |
   [TAK]
    |
    v
Sprawdz role (student / promotor / root)
    |
    +--> student:  panel studenta   (swoje praktyki, wnioski, dziennik)
    +--> promotor: panel promotora  (przydzieleni studenci, hospitacje, oceny)
    +--> root:     panel dyrektora  (wszyscy uzytkownicy, wnioski, eksport CSV)
```

---

## 6. Projekt bazy danych

### Schemat SQL

Plik `schemat_bazy.sql` w katalogu glownym repozytorium zawiera pelny schemat
bazy danych z instrukcjami `CREATE TABLE`, kluczami glownymi i obcymi,
ograniczeniami `NOT NULL`, `UNIQUE` oraz indeksami.

### Wybor bazy danych

| Aspekt | Decyzja |
|---|---|
| Baza docelowa | PostgreSQL 16 |
| Baza prototypowa | ta sama (PostgreSQL) -- dzieki Dockerowi nie ma potrzeby uzywania SQLite |
| ORM | SQLAlchemy 2.0 -- modele w `models.py` |
| Migracje | Alembic (Flask-Migrate) -- pliki w `migrations/versions/` |

### Diagram ERD (relacje)

```
users 1──N praktyki          (student_id, promotor_id)
praktyki 1──N dokumenty      (praktyka_id)
praktyki 1──N dziennik_wpisy (praktyka_id)
praktyki 1──N hospitacje     (praktyka_id)
praktyki 1──1 egzaminy_protokoly (praktyka_id, UNIQUE)
praktyki 1──N wnioski_przedluzenia (praktyka_id)

users 1──N wnioski_zaliczenia (student_id)
wnioski_zaliczenia 1──N wnioski_dokumenty (wniosek_id)

users 1──N wnioski_zmiana_terminu (student_id)
```

### Tabele

| Tabela | Opis |
|---|---|
| `users` | uzytkownicy systemu (studenci, promotorzy, dyrektor) |
| `praktyki` | glowna tabela -- caly tok praktyki studenta |
| `dokumenty` | pliki zalaczone do praktyki |
| `dziennik_wpisy` | codzienne wpisy dziennika studenta |
| `hospitacje` | wizyty promotora w firmie |
| `egzaminy_protokoly` | protokol komisji egzaminacyjnej |
| `wnioski_zaliczenia` | wniosek o zaliczenie przez prace/staz (par. 4) |
| `wnioski_dokumenty` | pliki do wniosku o zaliczenie |
| `wnioski_przedluzenia` | wniosek o przedluzenie terminu (par. 6.2) |
| `wnioski_zmiana_terminu` | wniosek o zmiane semestru (par. 3) |

---

## 7. Model danych i walidacja

### Normalizacja

Dane sa znormalizowane -- kazda encja ma wlasna tabele:
- dane firmy i opiekuna zakladowego przechowywane w tabeli `praktyki` (1:1 z praktyka)
- wpisy dziennika, dokumenty, hospitacje -- osobne tabele z kluczem obcym do `praktyki`
- wnioski o zaliczenie z wlasnymi dokumentami -- oddzielna struktura od praktyk

### Walidacja danych

| Regula | Realizacja |
|---|---|
| Kompletnosc danych | wymagane pola oznaczone `nullable=False` w modelu i walidowane w widokach |
| Liczba dni (120) | suma godzin z dziennika obliczana automatycznie (`Praktyka.suma_godzin_dziennik`) |
| Poprawnosc dat | walidacja `data_od < data_do`, daty wpisow w zakresie praktyki |
| Dopuszczalne statusy | zdefiniowane w slownikach `STATUSY` w modelach |
| Poprawnosc ocen | egzamin: dozwolone wartosci `["2", "3", "3+", "4", "4+", "5"]` |
| Typy plikow | ograniczenie do `pdf, doc, docx, odt, jpg, jpeg, png` |
| Rozmiar plikow | max 16 MB (`MAX_CONTENT_LENGTH`) |

---

## 8. System logowania

| Element | Realizacja |
|---|---|
| Protokol | OAuth2 (Microsoft MSAL) |
| Callback | `/auth/callback` -- odbiera token, pobiera dane z Microsoft Graph |
| Model User | `models.py` -- `User(ms_oid, email, imie, nazwisko, rola, ...)` |
| Sesja | Flask session (`session["user"]`) |
| Dekorator | `@login_required` -- sprawdza sesje i istnienie uzytkownika w bazie |
| Role | `student`, `promotor`, `root` (dyrektor/administrator) |
| Pierwsze logowanie | automatyczne tworzenie konta z danymi z Microsoft Graph |
| Konfiguracja | zmienne `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MS_TENANT_ID` w `.env` |
| Tryb DEV | `DEV_LOGIN=1` wlacza szybkie logowanie bez konta Microsoft (tylko development) |

---

## 9. REST API i endpointy

Aplikacja nie posiada oddzielnego modulu REST API -- logika backendowa
i warstwa prezentacji sa zintegrowane w jednym pliku `app.py` (wzorzec MVC
z szablonami Jinja2).

Endpointy zwracajace JSON:
- `GET /praktyki/<id>/pdf/<kind>` -- zleca generowanie PDF, zwraca `{"task_id": "..."}`
- `GET /pdf/status/<task_id>` -- sprawdza status zadania Celery, zwraca `{"state": "...", "ready": true/false}`
- `GET /pdf/download/<task_id>` -- pobiera wygenerowany plik PDF

Endpointy obslugujace formularze (POST):
- `/student/praktyki/nowa` -- tworzenie praktyki
- `/student/praktyki/<id>/dziennik` -- dodawanie wpisow dziennika
- `/student/praktyki/<id>/dokumenty/upload` -- wgrywanie plikow
- `/student/wnioski/nowy` -- skladanie wniosku o zaliczenie
- `/promotor/praktyki/<id>/ocena` -- wystawianie oceny

---

## 10. Frontend (interfejs uzytkownika)

Interfejs zbudowany jest w oparciu o szablony Jinja2 z dziedziczeniem
(`base.html` -> layout roli -> widok).

| Element | Realizacja |
|---|---|
| Dashboard | osobny dla kazdej roli: `student/dashboard.html`, `promotor/dashboard.html` |
| Formularze | praktyki, dziennik, sprawozdanie, ankieta, wnioski |
| Dynamiczne wiersze | JavaScript -- dodawanie/usuwanie wpisow dziennika i czlonkow komisji |
| Komunikaty | `flash()` -- powiadomienia o sukcesie/bledzie |
| Obsluga bledow | strony bledow, walidacja po stronie klienta |
| Responsywnosc | CSS responsywny, interfejs mobilny |

### Struktura szablonow

```
templates/
  base.html                -- layout glowny
  index.html               -- strona logowania
  student/
    _layout.html            -- menu studenta
    dashboard.html          -- panel glowny
    praktyka_form.html      -- formularz praktyki
    praktyka_detail.html    -- szczegoly praktyki
    dziennik.html           -- dziennik praktyk
    dokumenty.html          -- wgrywanie plikow
    profil.html             -- edycja profilu
    wnioski_list.html       -- lista wnioskow
    wniosek_form.html       -- nowy wniosek par. 4
    przedluzenie_form.html  -- wniosek par. 6.2
    zmiana_terminu_form.html -- wniosek par. 3
  promotor/
    _layout.html            -- menu promotora
    dashboard.html          -- panel glowny
    studenci.html           -- lista studentow
    praktyka_detail.html    -- szczegoly praktyki studenta
    egzamin_form.html       -- protokol egzaminu
    wnioski.html            -- lista wnioskow do oceny
  admin/
    _layout.html            -- menu dyrektora
    users.html              -- zarzadzanie uzytkownikami
    promotorzy.html         -- lista promotorow
    przedluzenia.html       -- wnioski o przedluzenie
    zmiana_terminu.html     -- wnioski o zmiane terminu
  pdf/
    _base.html              -- bazowy layout PDF
    karta_1.html            -- skierowanie na praktyke
    karta_2.html            -- potwierdzenie odbycia
    karta_3.html            -- ocena przebiegu
    dziennik.html           -- dziennik praktyk
    sprawozdanie.html       -- sprawozdanie studenta
    ankieta.html            -- ankieta ewaluacyjna
    program.html            -- program praktyki
    efekty.html             -- potwierdzenie efektow
    wniosek_4b.html         -- wniosek o zaliczenie
```

---

## 11. Generowanie dokumentow PDF

| Aspekt | Realizacja |
|---|---|
| Biblioteka | xhtml2pdf (html2pdf) |
| Szablony | HTML/CSS w `templates/pdf/` -- renderowane przez Jinja2 |
| Generowanie w tle | Celery + Redis -- zadania asynchroniczne (`tasks.py`) |
| Fonty | Arial TTF (`static/fonts/`) -- wymagane do polskich znakow |
| Pobieranie | uzytkownik klika "Pobierz PDF", frontend odpytuje status, po zakonczeniu pobiera plik |

Generowane dokumenty:
- Karta praktyki czesc 1/3 -- Skierowanie na praktyke
- Karta praktyki czesc 2/3 -- Potwierdzenie odbycia praktyki
- Karta praktyki czesc 3/3 -- Ocena przebiegu praktyki
- Dziennik praktyk
- Sprawozdanie z praktyki (3 sekcje)
- Ankieta ewaluacyjna (14 pytan)
- Program praktyki i harmonogram
- Potwierdzenie efektow ksztalcenia
- Wniosek o zaliczenie (par. 4b)

---

## 12. Bezpieczenstwo i wdrozenie

### Bezpieczenstwo

| Zagrozenie | Ochrona |
|---|---|
| Nieautoryzowany dostep | OAuth2 (Microsoft MSAL), dekorator `@login_required`, kontrola roli |
| SQL Injection | SQLAlchemy ORM -- parametryzowane zapytania |
| XSS | automatyczne escapowanie Jinja2 |
| CSRF | sesja Flask z `SECRET_KEY`, formularze POST |
| Upload zlosliwych plikow | whitelist rozszerzen, `secure_filename()`, limit rozmiaru 16 MB |

### Konfiguracja srodowisk

| Srodowisko | Opis |
|---|---|
| Development | `flask run` na localhost:5000, `DEV_LOGIN=1`, PostgreSQL na porcie 5433 |
| Production | Docker Compose: Gunicorn + Nginx + PostgreSQL + Redis + Celery |

### Wdrozenie (Docker)

Projekt zawiera pelna konfiguracje Docker:
- `Dockerfile` -- obraz Python 3.12 + Gunicorn
- `docker-compose.yml` -- orkiestracja 5 serwisow:
  - `postgres` -- baza danych PostgreSQL 16
  - `redis` -- broker Celery i cache wynikow PDF
  - `web` -- aplikacja Flask (Gunicorn)
  - `worker` -- Celery worker (generowanie PDF w tle)
  - `nginx` -- reverse proxy + pliki statyczne
- `nginx/nginx.conf` -- konfiguracja Nginx

Uruchomienie produkcyjne:

```bash
docker compose up -d
docker compose run --rm web flask db upgrade
```

---

## Wymagania techniczne

- Python 3.11+
- PostgreSQL 15+ (w repo Docker na porcie 5433)
- Redis 7+ (broker Celery)
- (opcjonalnie) rejestracja aplikacji w Azure AD dla logowania Microsoft

## Instalacja lokalna

```bash
# 1. Sklonuj repo
git clone <url> praktyki-ans
cd praktyki-ans

# 2. Utworz i aktywuj virtualenv
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# 3. Zainstaluj zaleznosci
pip install -r ZProjekt/requirements.txt

# 4. Skopiuj plik konfiguracyjny i uzupelnij wartosci
cp ZProjekt/.env.example ZProjekt/.env

# 5. Uruchom baze danych
docker compose up -d postgres redis

# 6. Zastosuj migracje
cd ZProjekt
flask db upgrade

# 7. Utworz konto administratora
flask create-user --email admin@example.com --imie Jan --nazwisko Kowalski --rola root

# 8. Uruchom aplikacje
flask run
```

Aplikacja startuje na `http://localhost:5000`.

## Konfiguracja (.env)

| Zmienna | Opis |
|---|---|
| `FLASK_SECRET_KEY` | losowy ciag do podpisywania cookies sesji |
| `MS_CLIENT_ID` | Application (client) ID z Azure |
| `MS_CLIENT_SECRET` | Client secret z Azure |
| `MS_TENANT_ID` | Tenant ID / domena / `common` |
| `MS_REDIRECT_URI` | URL callback (domyslnie `http://localhost:5000/auth/callback`) |
| `DATABASE_URL` | connection string PostgreSQL |
| `REDIS_URL` | adres Redis (domyslnie `redis://localhost:6379/0`) |
| `DEV_LOGIN` | `1` wlacza szybkie logowanie bez konta Microsoft (tylko dev) |

## Fonty PDF

Do generowania PDF z polskimi znakami wymagane sa pliki Arial TTF
(`static/fonts/arial.ttf` i `static/fonts/arialbd.ttf`). Nie sa commitowane
do repo ze wzgledu na licencje Monotype. Na Windows nalezy skopiowac je
z `C:\Windows\Fonts\`.

## Struktura projektu

```
ProjektFlask/
  docker-compose.yml        -- orkiestracja Docker (5 serwisow)
  Dockerfile                -- obraz aplikacji
  nginx/nginx.conf          -- konfiguracja reverse proxy
  schemat_bazy.sql          -- pelny schemat bazy danych (SQL)
  ZProjekt/
    app.py                  -- trasy, logika MSAL, helpery PDF
    models.py               -- modele SQLAlchemy (10 tabel)
    config.py               -- konfiguracja Flask
    extensions.py           -- db, migrate, celery
    tasks.py                -- zadania Celery (generowanie PDF)
    gunicorn.conf.py        -- konfiguracja serwera produkcyjnego
    celery_worker.py        -- punkt wejscia Celery
    requirements.txt        -- zaleznosci Python
    .env.example            -- szablon konfiguracji
    migrations/             -- migracje Alembic (11 wersji)
    templates/              -- szablony Jinja2 (40+ plikow)
    static/                 -- CSS, logo, fonty
    uploads/                -- pliki uzytkownikow (nie w repo)
```

## Podstawa prawna

Aplikacja implementuje wymagania *Regulaminu praktyk zawodowych dla
studentow kierunku Informatyka Stosowana ANS w Elblągu* (organizacja
praktyk par. 1-6 i rozliczenie par. 1-4).

## Licencja

MIT License -- patrz plik `LICENSE`.
