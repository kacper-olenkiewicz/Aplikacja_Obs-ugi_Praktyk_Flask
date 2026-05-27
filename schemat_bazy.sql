-- =============================================================================
-- SCHEMAT BAZY DANYCH — Projekt Praktyki ANS Elbląg
-- Wygenerowany ręcznie na podstawie migracji Alembic
-- PostgreSQL 16
-- =============================================================================


-- -----------------------------------------------------------------------------
-- TABELA: users
-- Wszyscy użytkownicy systemu (studenci, promotorzy, dyrektor, dziekanat)
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    id                  SERIAL          PRIMARY KEY,
    ms_oid              VARCHAR(64)     NOT NULL UNIQUE,        -- ID konta Microsoft (MSAL)
    email               VARCHAR(255)    NOT NULL UNIQUE,
    imie                VARCHAR(100),
    nazwisko            VARCHAR(100),
    nr_albumu           VARCHAR(20),
    kierunek            VARCHAR(100),
    specjalnosc         VARCHAR(100),
    rok_studiow         INTEGER,
    semestr             INTEGER,
    telefon             VARCHAR(30),
    adres               VARCHAR(255),
    rola                VARCHAR(20)     NOT NULL DEFAULT 'student',  -- student | promotor | dyrektor | dziekanat
    created_at          TIMESTAMP       NOT NULL,
    last_login_at       TIMESTAMP
);

CREATE INDEX ix_users_email     ON users (email);
CREATE INDEX ix_users_ms_oid    ON users (ms_oid);
CREATE INDEX ix_users_nr_albumu ON users (nr_albumu);


-- -----------------------------------------------------------------------------
-- TABELA: praktyki
-- Główna tabela — jeden rekord = jeden tok praktyki studenta
-- -----------------------------------------------------------------------------
CREATE TABLE praktyki (
    id                              SERIAL          PRIMARY KEY,
    student_id                      INTEGER         NOT NULL REFERENCES users(id),
    promotor_id                     INTEGER         REFERENCES users(id),

    -- Dane firmy
    firma_nazwa                     VARCHAR(255)    NOT NULL,
    firma_adres                     VARCHAR(255),
    firma_nip                       VARCHAR(20),
    firma_profil                    VARCHAR(255),

    -- Opiekun zakładowy
    opiekun_zakladowy_imie_nazwisko VARCHAR(200),
    opiekun_zakladowy_stanowisko    VARCHAR(150),
    opiekun_zakladowy_kontakt       VARCHAR(150),
    opiekun_zakladowy_wyksztalcenie VARCHAR(255),

    -- Termin praktyki
    data_od                         DATE,
    data_do                         DATE,
    data_do_przedluzenie            DATE,           -- po ewentualnym przedłużeniu
    liczba_godzin                   INTEGER,
    rok_akademicki                  VARCHAR(20),
    semestr_od                      INTEGER,
    semestr_do                      INTEGER,
    tryb_realizacji                 VARCHAR(20),    -- stacjonarny | zdalny | hybrydowy

    -- Zakres i harmonogram
    zakres_zadan                    TEXT,
    harmonogram                     TEXT,

    -- Status i ocena
    status                          VARCHAR(20)     NOT NULL,   -- zgloszony | w_trakcie | zakończony | ...
    ocena                           VARCHAR(20),
    komentarz_promotora             TEXT,

    -- Zaliczenie semestru 6
    zaliczenie_sem6                 BOOLEAN         NOT NULL DEFAULT FALSE,
    data_zaliczenia_sem6            DATE,
    komentarz_zaliczenia_sem6       TEXT,

    -- Sprawozdanie (3 sekcje)
    sprawozdanie_charakterystyka    TEXT,
    sprawozdanie_opis_prac          TEXT,
    sprawozdanie_samoocena          TEXT,

    -- Ankieta ewaluacyjna (14 pytań 1-5 + metadane)
    ankieta_p01                     INTEGER,
    ankieta_p02                     INTEGER,
    ankieta_p03                     INTEGER,
    ankieta_p04                     INTEGER,
    ankieta_p05                     INTEGER,
    ankieta_p06                     INTEGER,
    ankieta_p07                     INTEGER,
    ankieta_p08                     INTEGER,
    ankieta_p09                     INTEGER,
    ankieta_p10                     INTEGER,
    ankieta_p11                     INTEGER,
    ankieta_p12                     INTEGER,
    ankieta_p13                     INTEGER,
    ankieta_p14                     INTEGER,
    ankieta_uwagi                   TEXT,
    ankieta_rok_akademicki          VARCHAR(20),
    ankieta_forma_studiow           VARCHAR(20),

    -- Flagi formalne / dokumenty
    bhp_zaakceptowane               BOOLEAN         NOT NULL DEFAULT FALSE,
    regulamin_zapoznany             BOOLEAN         NOT NULL DEFAULT FALSE,
    ubezpieczenie_nnw               BOOLEAN         NOT NULL DEFAULT FALSE,
    erasmus_plus                    BOOLEAN         NOT NULL DEFAULT FALSE,
    porozumienie_podpisane          BOOLEAN         NOT NULL DEFAULT FALSE,
    skierowanie_wystawione          BOOLEAN         NOT NULL DEFAULT FALSE,
    dziennik_potwierdzony_zopz      BOOLEAN         NOT NULL DEFAULT FALSE,
    sprawozdanie_podpisane_zopz     BOOLEAN         NOT NULL DEFAULT FALSE,
    efekty_potwierdzone_zopz        BOOLEAN         NOT NULL DEFAULT FALSE,

    -- Ocena ZOPZ
    ocena_zopz_parametryczna        INTEGER,
    ocena_zopz_opisowa              TEXT,

    created_at                      TIMESTAMP       NOT NULL,
    updated_at                      TIMESTAMP       NOT NULL
);

CREATE INDEX ix_praktyki_student_id  ON praktyki (student_id);
CREATE INDEX ix_praktyki_promotor_id ON praktyki (promotor_id);


-- -----------------------------------------------------------------------------
-- TABELA: dokumenty
-- Pliki załączone do praktyki (skierowanie, porozumienie, zaświadczenia itd.)
-- -----------------------------------------------------------------------------
CREATE TABLE dokumenty (
    id                  SERIAL          PRIMARY KEY,
    praktyka_id         INTEGER         NOT NULL REFERENCES praktyki(id) ON DELETE CASCADE,
    typ                 VARCHAR(30)     NOT NULL,
    nazwa_oryginalna    VARCHAR(255)    NOT NULL,
    nazwa_pliku         VARCHAR(255)    NOT NULL,    -- nazwa na dysku / w storage
    mime_type           VARCHAR(100),
    rozmiar             INTEGER,                     -- bajty
    created_at          TIMESTAMP       NOT NULL
);

CREATE INDEX ix_dokumenty_praktyka_id ON dokumenty (praktyka_id);


-- -----------------------------------------------------------------------------
-- TABELA: dziennik_wpisy
-- Dziennik praktyki — codzienne wpisy studenta
-- -----------------------------------------------------------------------------
CREATE TABLE dziennik_wpisy (
    id                  SERIAL          PRIMARY KEY,
    praktyka_id         INTEGER         NOT NULL REFERENCES praktyki(id) ON DELETE CASCADE,
    data                DATE            NOT NULL,
    godz_od             TIME,
    godz_do             TIME,
    opis                TEXT            NOT NULL,
    efekty              TEXT,
    created_at          TIMESTAMP       NOT NULL
);

CREATE INDEX ix_dziennik_wpisy_praktyka_id ON dziennik_wpisy (praktyka_id);


-- -----------------------------------------------------------------------------
-- TABELA: hospitacje
-- Wizyty promotora / opiekuna w zakładzie pracy
-- -----------------------------------------------------------------------------
CREATE TABLE hospitacje (
    id                  SERIAL          PRIMARY KEY,
    praktyka_id         INTEGER         NOT NULL REFERENCES praktyki(id) ON DELETE CASCADE,
    data                DATE            NOT NULL,
    prowadzacy          VARCHAR(200)    NOT NULL,
    notatka             TEXT,
    created_by_id       INTEGER         REFERENCES users(id),
    created_at          TIMESTAMP       NOT NULL
);


-- -----------------------------------------------------------------------------
-- TABELA: egzaminy_protokoly
-- Protokół komisji egzaminacyjnej (jeden na praktykę)
-- -----------------------------------------------------------------------------
CREATE TABLE egzaminy_protokoly (
    id                  SERIAL          PRIMARY KEY,
    praktyka_id         INTEGER         NOT NULL UNIQUE REFERENCES praktyki(id) ON DELETE CASCADE,
    data_egzaminu       DATE            NOT NULL,
    przewodniczacy      VARCHAR(200)    NOT NULL,
    czlonkowie          TEXT,
    ocena               VARCHAR(20)     NOT NULL,
    uwagi               TEXT,
    created_by_id       INTEGER         REFERENCES users(id),
    created_at          TIMESTAMP       NOT NULL
);


-- -----------------------------------------------------------------------------
-- TABELA: wnioski_zaliczenia
-- Wniosek o zaliczenie praktyki przez pracę / staż / działalność
-- -----------------------------------------------------------------------------
CREATE TABLE wnioski_zaliczenia (
    id                      SERIAL          PRIMARY KEY,
    student_id              INTEGER         NOT NULL REFERENCES users(id),
    typ                     VARCHAR(30)     NOT NULL,   -- praca | staz | dzialalnosc
    pracodawca_nazwa        VARCHAR(255)    NOT NULL,
    pracodawca_adres        VARCHAR(255),
    nr_rejestrowy           VARCHAR(100),
    stanowisko              VARCHAR(200),
    data_od                 DATE,
    data_do                 DATE,
    opis_obowiazkow         TEXT,
    uzasadnienie            TEXT,
    status                  VARCHAR(30)     NOT NULL DEFAULT 'zlozony',
    ocena_komisji           VARCHAR(20),
    komentarz_komisji       TEXT,
    data_oceny_komisji      DATE,
    decyzja_dyrektora       VARCHAR(20),
    komentarz_dyrektora     TEXT,
    data_decyzji            DATE,
    created_at              TIMESTAMP       NOT NULL,
    updated_at              TIMESTAMP       NOT NULL
);


-- -----------------------------------------------------------------------------
-- TABELA: wnioski_dokumenty
-- Pliki załączone do wniosku o zaliczenie
-- -----------------------------------------------------------------------------
CREATE TABLE wnioski_dokumenty (
    id                  SERIAL          PRIMARY KEY,
    wniosek_id          INTEGER         NOT NULL REFERENCES wnioski_zaliczenia(id) ON DELETE CASCADE,
    typ                 VARCHAR(30)     NOT NULL,
    nazwa_oryginalna    VARCHAR(255)    NOT NULL,
    nazwa_pliku         VARCHAR(255)    NOT NULL,
    mime_type           VARCHAR(100),
    rozmiar             INTEGER,
    created_at          TIMESTAMP       NOT NULL
);


-- -----------------------------------------------------------------------------
-- TABELA: wnioski_przedluzenia
-- Wniosek o przedłużenie terminu praktyki (choroba, zdarzenie losowe itp.)
-- -----------------------------------------------------------------------------
CREATE TABLE wnioski_przedluzenia (
    id                      SERIAL          PRIMARY KEY,
    praktyka_id             INTEGER         NOT NULL REFERENCES praktyki(id) ON DELETE CASCADE,
    powod                   VARCHAR(30)     NOT NULL,
    godziny_nieobecnosci    INTEGER,
    opis                    TEXT,
    proponowana_data_do     DATE,
    status                  VARCHAR(20)     NOT NULL DEFAULT 'zlozony',
    nowa_data_do            DATE,
    komentarz               TEXT,
    created_at              TIMESTAMP       NOT NULL
);


-- -----------------------------------------------------------------------------
-- TABELA: wnioski_zmiana_terminu
-- Wniosek o zmianę semestru realizacji praktyki
-- -----------------------------------------------------------------------------
CREATE TABLE wnioski_zmiana_terminu (
    id                      SERIAL          PRIMARY KEY,
    student_id              INTEGER         NOT NULL REFERENCES users(id),
    powod                   VARCHAR(20)     NOT NULL,
    opis                    TEXT            NOT NULL,
    proponowany_semestr     INTEGER,
    proponowana_data_od     DATE,
    proponowana_data_do     DATE,
    status                  VARCHAR(20)     NOT NULL DEFAULT 'zlozony',
    komentarz_dyrektora     TEXT,
    data_decyzji            DATE,
    created_at              TIMESTAMP       NOT NULL
);

CREATE INDEX ix_wnioski_zmiana_terminu_student_id ON wnioski_zmiana_terminu (student_id);
