#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script d'installation de la skill code-review-analysis
.DESCRIPTION
    Installe la skill de code review au niveau utilisateur global (~/.claude/skills/)
    Après installation, la skill est disponible pour tous les projets Python.
.EXAMPLE
    .\INSTALL.ps1
    # Installe la skill depuis le répertoire courant
#>

param(
    [switch]$Force
)

Write-Host ""
Write-Host "📦 Installation de la skill: code-review-analysis" -ForegroundColor Cyan
Write-Host "━" * 60

# Déterminer les chemins
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$globalSkillDir = "$env:USERPROFILE\.claude\skills\code-review-analysis"

Write-Host ""
Write-Host "📂 Emplacements:" -ForegroundColor Yellow
Write-Host "  Source:      $scriptDir"
Write-Host "  Destination: $globalSkillDir"
Write-Host ""

# Vérifier si la skill existe déjà
if ((Test-Path $globalSkillDir) -and -not $Force) {
    Write-Host "⚠️  La skill existe déjà à $globalSkillDir" -ForegroundColor Yellow
    $response = Read-Host "Voulez-vous la remplacer? (O/n)"
    if ($response -eq "n") {
        Write-Host "Annulé."
        exit 0
    }
}

# Créer le répertoire
Write-Host "📁 Création du répertoire..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $globalSkillDir -Force | Out-Null

# Copier les fichiers
Write-Host "📋 Copie des fichiers..." -ForegroundColor Cyan
$filesToCopy = @("analyzer.py", "SKILL.md", "README.md", "run-analysis.ps1")

foreach ($file in $filesToCopy) {
    $source = Join-Path $scriptDir $file
    if (Test-Path $source) {
        Copy-Item $source $globalSkillDir -Force
        Write-Host "  ✓ $file"
    } else {
        Write-Host "  ⚠️  $file non trouvé"
    }
}

Write-Host ""
Write-Host "✅ Installation terminée!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 La skill est maintenant disponible globalement." -ForegroundColor Cyan
Write-Host ""
Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  python `"`$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py`" `".`" --analyze"
Write-Host ""
Write-Host "Ou depuis n'importe quel projet Python:" -ForegroundColor Yellow
Write-Host "  python `"`$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py`" <project_path> --analyze"
Write-Host ""
