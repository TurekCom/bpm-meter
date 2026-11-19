$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

git remote get-url origin | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Skonfiguruj zdalne repozytorium origin.' }

& .venv/Scripts/python.exe -m unittest -v
if ($LASTEXITCODE -ne 0) { throw 'Testy nie przeszły.' }

git add --update
if ($LASTEXITCODE -ne 0) { throw 'Nie udało się przygotować zmian.' }
git diff --cached --quiet
if ($LASTEXITCODE -eq 1) {
    '' | git commit --allow-empty-message --file=-
    if ($LASTEXITCODE -ne 0) { throw 'Nie udało się utworzyć commitu.' }
} elseif ($LASTEXITCODE -ne 0) {
    throw 'Nie udało się sprawdzić zmian.'
}

git push --set-upstream origin HEAD
if ($LASTEXITCODE -ne 0) { throw 'Nie udało się wysłać zmian.' }
