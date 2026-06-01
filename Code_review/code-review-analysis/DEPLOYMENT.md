# 📦 Guide de Déploiement — code-review-analysis

Comment partager et installer la skill sur d'autres machines ou projets.

---

## Option 1 : Copier les fichiers manuellement

### Source
```
C:\Users\tallar\.claude\skills\code-review-analysis\
```

### Destination (autre machine)
```
C:\Users\{username}\.claude\skills\code-review-analysis\
```

**Fichiers à copier :**
- `analyzer.py` (obligatoire)
- `SKILL.md` (documentation)
- `README.md` (documentation)
- `run-analysis.ps1` (optionnel)

---

## Option 2 : Utiliser le script INSTALL.ps1

Un script PowerShell automatise l'installation :

```powershell
# Sur la machine source (où vous avez créé la skill)
C:\Users\tallar\.claude\skills\code-review-analysis\INSTALL.ps1

# Sur une autre machine
# 1. Copier le répertoire complet quelque part
# 2. Ouvrir PowerShell dans ce répertoire
# 3. .\INSTALL.ps1
```

**Le script :**
- ✓ Crée le répertoire `.claude/skills/` s'il n'existe pas
- ✓ Copie les fichiers au bon endroit
- ✓ Affiche les instructions d'utilisation

---

## Option 3 : Partager via Git / Repository

Idéal si vous maintenez plusieurs versions ou pour un partage d'équipe.

### Structure proposée

```
github.com/tallar/claude-skills
├── code-review-analysis/
│   ├── analyzer.py
│   ├── SKILL.md
│   ├── README.md
│   ├── INSTALL.ps1
│   └── DEPLOYMENT.md
└── [autres skills...]
```

### Utilisation

```bash
# Cloner le repo
git clone https://github.com/tallar/claude-skills.git

# Installer
cd claude-skills/code-review-analysis
.\INSTALL.ps1

# Ou installer sans git (copie manuelle)
Copy-Item code-review-analysis -Destination "$env:USERPROFILE\.claude\skills\" -Recurse -Force
```

---

## Vérifier l'installation

### Test 1 : Fichiers présents

```powershell
ls "$env:USERPROFILE\.claude\skills\code-review-analysis\"
```

Doit afficher : `analyzer.py`, `SKILL.md`, `README.md`, `run-analysis.ps1`

### Test 2 : Lister les opérations

```powershell
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --operations
```

Doit afficher la liste des 6 analyses disponibles.

### Test 3 : Analyser un petit projet

```powershell
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "C:\test\project" --analyze
```

Doit générer `.claude/code_review_report.md` et `.json`.

---

## Mise à jour

### Si vous modifiez la skill

1. **Modifier `analyzer.py`** dans la source
2. **Tester** localement
3. **Copier** vers `.claude/skills/` (option 1 ou 2)
4. **Communiquer** les changements si partagée via Git

### Sécurité des versions

Pour éviter les conflits de versions, vous pouvez ajouter un numéro de version dans le script :

```python
__VERSION__ = "1.0.0"

# Dans le rapport généré :
"generator_version": __VERSION__
```

---

## Support multi-plateformes

### Windows
- ✅ Testé sur Windows 11 Pro
- ✅ Nécessite Python 3.8+
- ✅ PowerShell scripts fournis

### macOS / Linux
- 🟡 Non testé, mais devrait fonctionner
- Modifier le chemin `.claude` selon la plateforme
- Adapter les scripts PowerShell en Bash si nécessaire

**Pour macOS/Linux :**

```bash
# Installation manuelle
mkdir -p ~/.claude/skills/code-review-analysis
cp analyzer.py ~/.claude/skills/code-review-analysis/
cp SKILL.md README.md ~/.claude/skills/code-review-analysis/

# Utilisation
python ~/.claude/skills/code-review-analysis/analyzer.py "." --analyze
```

---

## Résolution des problèmes

### "python: command not found"

Utilisez le chemin complet vers Python ou le chemin du venv :

```powershell
# Option 1: Chemin global
C:\Users\{username}\AppData\Local\Programs\Python\Python311\python.exe analyzer.py "." --analyze

# Option 2: Via venv du projet
.\venv\Scripts\python.exe "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
```

### "Accès refusé" lors de la copie

Exécutez PowerShell en mode administrateur :
```powershell
Start-Process powershell -ArgumentList "-File INSTALL.ps1" -Verb RunAs
```

### Le rapport ne se génère pas

Vérifiez les permissions d'écriture dans `.claude/` :

```powershell
Test-Path "$env:USERPROFILE\.claude"
# Doit retourner True

# Créer si absent
New-Item -ItemType Directory -Path "$env:USERPROFILE\.claude" -Force
```

---

## Feedback & Améliorations

Cette skill est réutilisable et maintenable. Pour suggérer des améliorations :

1. Tester sur votre projet
2. Noter les cas d'usage non couverts
3. Proposer des modifications

**Points d'amélioration potentiels :**
- Ajouter plus d'analyses (couverture de tests, etc.)
- Support de langages autres que Python
- Intégration CI/CD (GitHub Actions, etc.)
- Dashboard web pour visualiser les rapports
