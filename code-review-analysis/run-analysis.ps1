#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Analyser un projet Python pour générer un rapport de code review
.DESCRIPTION
    Lance l'analyseur de code Python sur un projet donné.
.PARAMETER ProjectRoot
    Chemin vers la racine du projet à analyser (défaut: .)
.PARAMETER Operation
    Type d'opération: 'list' pour lister les analyses, 'analyze' pour générer le rapport
.EXAMPLE
    .\run-analysis.ps1 -ProjectRoot . -Operation list
    .\run-analysis.ps1 -ProjectRoot . -Operation analyze
#>

param(
    [string]$ProjectRoot = ".",
    [ValidateSet("list", "analyze")]
    [string]$Operation = "analyze"
)

$analyzerScript = "$PSScriptRoot\analyzer.py"

if (-not (Test-Path $analyzerScript)) {
    Write-Error "❌ Script analyzer.py non trouvé à $analyzerScript"
    exit 1
}

if (-not (Test-Path $ProjectRoot)) {
    Write-Error "❌ Chemin du projet non trouvé: $ProjectRoot"
    exit 1
}

$ProjectRoot = (Get-Item $ProjectRoot).FullName

Write-Host "🔍 Analyse du projet: $ProjectRoot"
Write-Host ""

$operationMap = @{
    "list"    = "--operations"
    "analyze" = "--analyze"
}

$pythonCmd = $operationMap[$Operation]

& python $analyzerScript "$ProjectRoot" $pythonCmd

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ L'analyse a échoué avec le code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "✅ Analyse terminée avec succès"

# Afficher le chemin du rapport JSON si l'operation était analyze
if ($Operation -eq "analyze") {
    $reportPath = Join-Path $ProjectRoot ".claude\code_review_report.json"
    if (Test-Path $reportPath) {
        Write-Host "📄 Rapport JSON disponible à: $reportPath"
    }
}
