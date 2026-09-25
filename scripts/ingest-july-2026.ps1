param(
    [Parameter(Mandatory=$true)]
    [string]$Arquivo
)

$ErrorActionPreference = "Stop"

Write-Host "Validando ambiente..."
python scripts/check_environment.py

Write-Host "Executando pipeline local de julho/2026..."
python -m src.cli local-pipeline 202607 $Arquivo --kind MOV

Write-Host "Concluído. Consulte:"
Write-Host "  data/silver/"
Write-Host "  data/gold/"
Write-Host "  http://localhost:8000/docs"
