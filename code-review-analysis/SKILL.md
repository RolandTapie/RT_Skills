---
name: code-review-analysis
description: Analyser n'importe quel projet Python pour générer un rapport de code review (normes, conventions, docstrings, type hints). Accepte project_root en paramètre. Génère rapports JSON et Markdown. Ne modifie pas le code.
scope: global
---

# Skill: Analyse de Code Review

**Réutilisable sur tous vos projets Python** — Analyser sans modifier.

Génère deux rapports :
- 📘 **Markdown** — Organisé par fichier, lisible directement dans VS Code
- 📊 **JSON** — Structure complète pour exploitation programmatique

## Usage

La skill accepte `project_root` en paramètre et exécute des analyses statiques du code Python.

### 1. Lister les opérations d'analyse disponibles

```bash
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "<project_root>" --operations
```

Affiche toutes les analyses disponibles :
- **error_handling** — Blocs `except: pass`, bare `except:`, `except Exception:` génériques
- **docstrings** — Docstrings manquantes (classes et fonctions)
- **type_hints** — Type hints manquants (paramètres et retours)
- **long_functions** — Fonctions trop longues (> 50 lignes)
- **naming_conventions** — Violations PEP 8 (PascalCase/snake_case)
- **unused_imports** — Imports non utilisés

### 2. Générer le rapport complet (JSON + Markdown)

```bash
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "<project_root>" --analyze
```

Génère **deux rapports** dans `.claude/` :
- 📘 `code_review_report.md` — Lisible, organisé par fichier
- 📊 `code_review_report.json` — Structure complète

Affiche aussi un résumé console :
- ✓ Fichiers Python analysés
- 📊 Problèmes par sévérité (🔴 🟠 ℹ️)
- 🔴 Détail des 10 premiers critiques

## Sur n'importe quel projet

Depuis **n'importe quel répertoire**, analyser un projet Python :

```bash
# Analyser un projet situé ailleurs
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "C:\chemin\vers\projet" --analyze

# Ou utiliser un chemin relatif
cd C:\mon\projet
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
```

## Alias pratique (optionnel)

Pour simplifier l'utilisation, créez un alias PowerShell :

```powershell
# Ajouter à votre profil PowerShell
function code-review {
    param([string]$Path = ".")
    python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" $Path --analyze
}

# Utilisation
code-review "."
code-review "C:\autre\projet"
```

## Rapports générés

L'analyse génère **deux rapports complémentaires** :

### 1️⃣ Rapport Markdown (`.claude/code_review_report.md`)

**Pour la lisibilité humaine** — organisé par :
- 📈 Résumé des statistiques (tableau)
- 📋 Décompte par type d'analyse
- 📁 **Détail par fichier**, groupés par ligne
- Emojis pour les sévérités (🔴 🟠 ℹ️)

**Exemple de structure :**
```markdown
### `api/rag_api.py` (39 problèmes) 🔴 6, ℹ️ 19, 🟠 14

**Ligne 42:**
  - 🔴 `[error_handling]` Bloc except vide (pass)
  - ℹ️ `[type_hints]` Sans type hints pour les paramètres
```

### 2️⃣ Rapport JSON (`.claude/code_review_report.json`)

**Pour l'exploitation programmatique** — structure complète :
- Toutes les données brutes
- Groupement par type et sévérité
- Facile à filtrer/transformer avec jq ou Python

## Sévérités expliquées

| Sévérité | Signification | Exemples |
|----------|---------------|----------|
| 🔴 **Critical** | Bugs évidents ou risques sécurité | `except: pass` (erreur silencieuse), bare `except:` |
| 🟠 **Warning** | Mauvaise pratique ou code fragile | Fonctions > 50 lignes, `except Exception:` générique |
| ℹ️ **Info** | Amélioration de qualité, pas urgent | Docstrings manquantes, type hints manquants |

## Structure du rapport JSON

Le rapport généré (`.claude/code_review_report.json`) contient la structure complète :

```json
{
  "project_root": ".",
  "total_python_files": 102,
  "total_findings": 1815,
  "severity_summary": {
    "critical": 57,
    "warning": 670,
    "info": 1088
  },
  "findings_by_type": {
    "docstrings": [
      {
        "file": "api/rag_api.py",
        "line": 42,
        "type": "docstrings",
        "message": "FunctionDef \"get_answer\" sans docstring",
        "severity": "info"
      }
    ],
    "error_handling": [
      {
        "file": "couches/A_Ingestion/services/ingestor.py",
        "line": 128,
        "type": "error_handling",
        "message": "Bloc except vide (pass) — ajoutez du logging ou levez l'exception",
        "severity": "critical"
      }
    ]
  },
  "all_findings": [...]
}
```

Chaque `finding` contient :
- **file** — Chemin relatif au projet
- **line** — Numéro de ligne exact
- **type** — Type d'analyse (`docstrings`, `type_hints`, `error_handling`, etc.)
- **message** — Description claire du problème détecté
- **severity** — `critical`, `warning`, ou `info`

## Comment exploiter le rapport

### Par priorité : commencez par les critiques

```bash
# Ouvrir le rapport JSON et filtrer les critiques
# (utiliser jq, Python, ou un éditeur JSON)
cat .claude/code_review_report.json | jq '.all_findings[] | select(.severity=="critical")'
```

### Par type : cibler une analyse

Si vous voulez corriger les `error_handling` d'abord, le JSON les groupe par type :

```bash
cat .claude/code_review_report.json | jq '.findings_by_type.error_handling'
```

### Localiser rapidement

Chaque finding inclut `file` et `line` — ouvrez le fichier à cette ligne :
```
api/rag_api.py:42 → "Docstring manquante"
```

## Points clés

- ✅ **Aucune modification du code** — l'analyse est **100% passive** et lecture seule
- ✅ **Aucune dépendance externe** — utilise uniquement la stdlib Python (`ast`)
- ✅ **Exclusions intelligentes** — ignore automatiquement `.venv/`, `__pycache__/`, `.git/`, etc.
- ✅ **Rapport structuré** — JSON pour exploitation programmatique + console lisible
- ✅ **Rapide** — analyse 100+ fichiers en quelques secondes

## Limitations

- **Analyse statique uniquement** — pas d'exécution du code, donc pas de détection des erreurs logiques
- **Faux positifs possibles** — les imports utilisés via `eval()` ou importation dynamique ne sont pas détectés
- **Scope limité** — analyse uniquement le style et les conventions, pas la couverture de tests
- **Pas de correctifs** — le rapport identifie les problèmes, ne les répare pas

## Prochaines étapes typiques

1. **Générer le rapport** → `python analyzer.py "." --analyze`
2. **Ouvrir le Markdown** → `.claude/code_review_report.md` (ou `.json` si vous préférez)
3. **Lire par fichier** → Commencez par les fichiers avec 🔴 critiques
4. **Corriger par priorité** :
   - D'abord les `error_handling` critiques (57)
   - Ensuite les `long_functions` avertissements (65)
   - Puis les `docstrings` infos (500)
5. **Itérer** → Corriger, relancer, vérifier la progression
6. **Intégrer au CI/CD** (optionnel) → Ajouter des seuils d'alerte

## Intégration dans votre workflow

### Python : réutiliser le code d'analyse

```python
from analyzer import CodeAnalyzer

analyzer = CodeAnalyzer("/path/to/project")

# Analyser spécifiquement
analyzer.analyze_docstrings()
analyzer.analyze_error_handling()

# Générer le rapport personnalisé
report = analyzer._generate_report()
```

### Shell : intégrer dans un script

```bash
#!/bin/bash
PROJECT_ROOT="/path/to/rag"
python .claude/skills/code-review-analysis/analyzer.py "$PROJECT_ROOT" --analyze

# Extraire les critiques et lancer une alerte
CRITICALS=$(python -c "import json; r=json.load(open('.claude/code_review_report.json')); print(r['severity_summary']['critical'])")
if [ $CRITICALS -gt 0 ]; then
  echo "⚠️ $CRITICALS problèmes critiques détectés"
fi
```
