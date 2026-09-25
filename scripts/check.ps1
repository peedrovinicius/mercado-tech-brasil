$ErrorActionPreference = "Stop"

Write-Host "Lint..."
ruff check src tests

Write-Host "Tests..."
pytest -q

Write-Host "Tudo certo."
