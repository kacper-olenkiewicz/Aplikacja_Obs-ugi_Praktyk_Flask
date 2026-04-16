# Praktyki ANS Elbląg

System elektronicznego rozliczania praktyk zawodowych dla kierunku Informatyka
Stosowana w Akademii Nauk Stosowanych w Elblągu.

Aplikacja wspiera pełny cykl praktyki — od zgłoszenia przez studenta, przez
akceptację opiekuna (UOPZ), realizację, hospitacje, egzamin komisyjny,
aż do zaliczenia semestru — zgodnie z regulaminem praktyk zawodowych
Instytutu Informatyki Stosowanej.

## Funkcjonalności

- Logowanie przez konto Microsoft (MSAL / Azure AD) z trybem DEV do testów
- Trzy role: **student**, **promotor** (opiekun UOPZ), **root** (dyrektor /
  administrator)
- Karta praktyki, dziennik, dokumenty, sprawozdanie, ankieta oceny
- Wnioski §4 — zaliczenie na podstawie pracy / stażu / działalności
- Wnioski §6.2 — przedłużenie praktyki (choroba / inne)
- Wnioski §3 — zmiana terminu praktyki (Erasmus / szczególny przypadek)
- Hospitacje, potwierdzenia ZOPZ, egzamin komisyjny
- Generowanie PDF (xhtml2pdf): program i harmonogram, karta, dziennik,
  sprawozdanie, ankieta — zgodnie z Zał. 2a, 3, 4, 5
- Filtrowanie, wyszukiwanie i eksport CSV dla promotora / dyrektora
- Paginacja, responsywny interfejs mobilny

## Wymagania

- Python 3.11+
- PostgreSQL 15+ (w repo zakładany Docker na porcie 5433)
- (opcjonalnie) rejestracja aplikacji w Azure AD dla logowania MS

## Instalacja

```bash
# 1. Sklonuj repo i wejdź do katalogu
git clone <url> praktyki-ans
cd praktyki-ans

# 2. Utwórz i aktywuj virtualenv
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# 3. Zainstaluj zależności
pip install -r requirements.txt

# 4. Skopiuj plik konfiguracyjny i uzupełnij wartości
cp .env.example .env
# otwórz .env i wpisz poprawne wartości (patrz sekcja Konfiguracja)
```

## Konfiguracja (`.env`)

| Zmienna | Opis |
|---|---|
| `FLASK_SECRET_KEY` | Losowy ciąg do podpisywania cookies sesji |
| `MS_CLIENT_ID` | Application (client) ID z Azure |
| `MS_CLIENT_SECRET` | Client secret z Azure |
| `MS_TENANT_ID` | Tenant ID / domena / `common` |
| `MS_REDIRECT_URI` | URL callback — domyślnie `http://localhost:5000/auth/callback` |
| `DATABASE_URL` | Connection string PostgreSQL |
| `DEV_LOGIN` | `1` włącza szybkie logowanie na dowolnego usera bez MS (tylko dev) |

## Baza danych

W katalogu nadrzędnym repo znajduje się `docker-compose.yml` uruchamiający
PostgreSQL na porcie **5433** (port `5432` bywa zajęty przez natywną usługę
Windows).

```bash
docker compose up -d
```

Następnie zainicjalizuj schemat:

```bash
flask db upgrade
```

Pierwszy użytkownik z rolą `root` (dyrektor) musi zostać utworzony ręcznie
komendą CLI:

```bash
flask create-user --email admin@example.com --imie Jan --nazwisko Kowalski --rola root
```

## Fonty PDF

Do generowania PDF z polskimi znakami wymagane są pliki Arial TTF
(`static/fonts/arial.ttf` i `static/fonts/arialbd.ttf`). Nie są commitowane
do repo ze względu na licencję Monotype. Na Windows skopiuj je z
`C:\Windows\Fonts\`. Szczegóły: `static/fonts/README.txt`.

## Uruchomienie

```bash
flask run
```

Aplikacja startuje na `http://localhost:5000`. Przy pierwszym uruchomieniu
z `DEV_LOGIN=1` na stronie głównej pojawi się lista użytkowników do
szybkiego logowania.

## Struktura projektu

```
ZProjekt/
├── app.py                 # routes, MSAL, PDF helpers
├── models.py              # modele SQLAlchemy
├── config.py              # konfiguracja Flask
├── extensions.py          # db, migrate
├── requirements.txt
├── migrations/            # Alembic
├── templates/
│   ├── base.html
│   ├── index.html         # login / dev-login
│   ├── student/           # panel studenta
│   ├── promotor/          # panel opiekuna UOPZ
│   ├── admin/             # panel dyrektora (root)
│   └── pdf/               # szablony PDF
├── static/
│   ├── style.css
│   ├── logo-ans.png
│   └── fonts/             # TTF (nie w repo)
└── uploads/               # pliki użytkowników (nie w repo)
```

## Role i uprawnienia

- **student** — zakłada praktykę, prowadzi dziennik, składa wnioski,
  wgrywa dokumenty, wypełnia sprawozdanie i ankietę
- **promotor** — akceptuje praktyki, potwierdza porozumienia, wystawia
  skierowania, prowadzi hospitacje, wystawia ocenę, zalicza semestr
- **root** (Dyrektor Instytutu) — rozpatruje wnioski §3 (zmiana terminu),
  §4 (zaliczenie z pracy), zarządza użytkownikami, ma dostęp do wszystkich
  praktyk oraz eksportu CSV

## Podstawa prawna

Aplikacja implementuje wymagania *Regulaminu praktyk zawodowych dla
studentów kierunku Informatyka Stosowana ANS w Elblągu* (organizacja
praktyk §§1–6 i rozliczenie §§1–4). Numery paragrafów są przywoływane w
UI i komentarzach kodu przy odpowiednich flows.

## Licencja

Projekt dyplomowy — ANS w Elblągu, 2026.
