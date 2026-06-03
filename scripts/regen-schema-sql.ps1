# Regeneruje schemat_bazy.sql z aktualnego stanu migracji Alembic.
#
# Uruchamia tymczasowy kontener Postgres, aplikuje na nim 'flask db upgrade',
# zrzuca schemat przez pg_dump i zapisuje do schemat_bazy.sql w korzeniu repo.
#
# Wymagania:
#   - Docker Desktop dziala
#   - Aktywne venv z zainstalowanym requirements.txt (flask + alembic + psycopg2)
#
# Uruchomienie z korzenia repo:
#   .\venv\Scripts\Activate.ps1
#   .\scripts\regen-schema-sql.ps1

$ErrorActionPreference = "Stop"

$RepoRoot      = Resolve-Path (Join-Path $PSScriptRoot "..")
$AppDir        = Join-Path $RepoRoot "ZProjekt"
$OutFile       = Join-Path $RepoRoot "schemat_bazy.sql"

$ContainerName = "praktyki_schema_dump"
$HostPort      = "55444"
$User          = "schema"
$Password      = "schema"
$Db            = "schema_db"

# Usun ewentualnie wiszacy kontener z poprzedniego biegu
docker rm -f $ContainerName 2>$null | Out-Null

Write-Host "[1/4] Startuje tymczasowy Postgres ($ContainerName)..."
docker run -d --name $ContainerName `
    -e POSTGRES_USER=$User `
    -e POSTGRES_PASSWORD=$Password `
    -e POSTGRES_DB=$Db `
    -p "${HostPort}:5432" `
    postgres:16-alpine | Out-Null

try {
    Write-Host "[2/4] Czekam na gotowosc Postgresa..."
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        docker exec $ContainerName pg_isready -U $User -d $Db 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $ready = $true; break }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) { throw "Postgres nie wstal w 30 sekund." }

    Write-Host "[3/4] Aplikuje migracje (flask db upgrade)..."
    $prevDbUrl = $env:DATABASE_URL
    $prevFlaskApp = $env:FLASK_APP
    $env:DATABASE_URL = "postgresql+psycopg2://${User}:${Password}@localhost:${HostPort}/${Db}"
    $env:FLASK_APP    = "app.py"
    Push-Location $AppDir
    try {
        flask db upgrade
        if ($LASTEXITCODE -ne 0) { throw "flask db upgrade zwrocil kod $LASTEXITCODE" }
    } finally {
        Pop-Location
        $env:DATABASE_URL = $prevDbUrl
        $env:FLASK_APP    = $prevFlaskApp
    }

    Write-Host "[4/4] Zrzucam schemat przez pg_dump..."
    $dump = docker exec $ContainerName pg_dump `
        --schema-only --no-owner --no-privileges `
        -U $User $Db
    if ($LASTEXITCODE -ne 0) { throw "pg_dump zwrocil kod $LASTEXITCODE" }

    $header = @"
-- =============================================================================
-- SCHEMAT BAZY DANYCH - Projekt Praktyki ANS Elblag
-- WYGENEROWANO AUTOMATYCZNIE przez scripts/regen-schema-sql.ps1
-- ze stanu migracji Alembic (flask db upgrade). Nie edytuj recznie.
-- PostgreSQL 16
-- =============================================================================

"@
    Set-Content -Path $OutFile -Value ($header + ($dump -join "`n")) -Encoding utf8
    Write-Host "OK: zapisano $OutFile"
}
finally {
    Write-Host "Sprzatam tymczasowy kontener..."
    docker rm -f $ContainerName 2>$null | Out-Null
}
