# Code Review Analysis Skill

**Skill réutilisable** — Analysez n'importe quel projet Python sans le modifier.

Génère deux rapports (📘 Markdown + 📊 JSON) : violations PEP 8, conventions de nommage, docstrings, type hints, gestion d'erreurs.

## TL;DR — Usage rapide

```bash
# Depuis n'importe quel projet Python
cd "C:\votre\projet\python"

# Lister les analyses disponibles
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --operations

# Générer le rapport complet
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
```

Les rapports sont sauvegardés dans `.claude/` :
- `code_review_report.md` (Markdown — lisible)
- `code_review_report.json` (JSON — complet)

## Qu'est-ce qu'elle analyze ?

La skill effectue **6 analyses statiques** :

| Analyse | Description | Sévérité |
|---------|-------------|----------|
| **error_handling** | Blocs `except: pass`, bare `except:`, `except Exception:` génériques | 🔴 Critical/⚠️ Warning |
| **docstrings** | Classes et fonctions sans docstring | ℹ️ Info |
| **type_hints** | Paramètres et retours sans type hints | ℹ️ Info |
| **long_functions** | Fonctions > 50 lignes | ⚠️ Warning |
| **naming_conventions** | Violations PEP 8 (PascalCase/snake_case) | ℹ️ Info |
| **unused_imports** | Imports déclarés mais non utilisés | ℹ️ Info |

## Résultats pour votre RAG

```
102 fichiers Python
1818 problèmes détectés
  🔴 57 critiques (error_handling — blocs except: pass)
  🟠 671 avertissements (long_functions, except Exception:)
  ℹ️ 1090 infos (docstrings, type_hints)
```

**Rapports générés :**
- 📘 **Markdown** (168 KB) — lisible, groupé par fichier → `.claude/code_review_report.md`
- 📊 **JSON** (849 KB) — structure complète pour filtrage → `.claude/code_review_report.json`

### Top 3 priorités pour votre RAG

1. **Corriger les 57 `except: pass` critiques** → Ajouter du logging ou lever l'exception
2. **Réduire 65 fonctions longues** → Refactoriser en petites fonctions
3. **Ajouter docstrings** → 500 manquantes (priorité basse)

## Exploiter le rapport Markdown

Ouvrez `.claude/code_review_report.md` dans votre éditeur (VS Code, Sublime, etc.). Le rapport est organisé ainsi :

```markdown
# 📊 Rapport d'Analyse de Code

## 📈 Résumé
| Métrique | Valeur |
| Fichiers | 102 |
| Problèmes | 1818 |
| 🔴 Critiques | 57 |

## 📋 Par type d'analyse
- **type_hints:** 777 problèmes
- **docstrings:** 500 problèmes
- **error_handling:** 163 problèmes (😱 à fixer)

## 📁 Détail par fichier

### `api/rag_api.py` (39 problèmes) 🔴 6, ℹ️ 19, 🟠 14

**Ligne 42:**
  - 🔴 `[error_handling]` Bloc except vide
  - ℹ️ `[type_hints]` Sans type hints
```

**Workflow typique :**
1. Ouvrir le Markdown
2. Chercher les `🔴 critiques` (Ctrl+F : "🔴")
3. Aller à chaque ligne indiquée et corriger
4. Relancer l'analyse pour vérifier la progression

## Exploiter le rapport JSON

Le rapport est structuré pour une exploitation facile :

### Compter les problèmes par type
```json
{
  "findings_by_type": {
    "error_handling": [...],
    "docstrings": [...],
    "type_hints": [...]
  }
}
```

### Localiser un problème
```json
{
  "file": "api/rag_api.py",
  "line": 42,
  "message": "FunctionDef \"get_answer\" sans docstring"
}
```

→ Ouvrir `api/rag_api.py`, aller à la ligne 42.

### Filtrer par sévérité (Python)

```python
import json

with open('.claude/code_review_report.json') as f:
    report = json.load(f)

# Problèmes critiques seulement
criticals = [f for f in report['all_findings'] if f['severity'] == 'critical']
print(f"⚠️ {len(criticals)} problèmes à fixer immédiatement")
```

## Intégration CI/CD

### Ajouter à un workflow GitHub Actions

```yaml
- name: Code Review Analysis
  run: |
    python .claude/skills/code-review-analysis/analyzer.py . --analyze
    
- name: Check Critical Findings
  run: |
    python -c "
    import json
    r = json.load(open('.claude/code_review_report.json'))
    if r['severity_summary']['critical'] > 10:
      print('❌ Trop de problèmes critiques')
      exit(1)
    "
```

## Points d'attention

### ✅ Ce qu'elle fait bien

- **Rapide** — analyse 100+ fichiers en < 5 sec
- **Précis** — utilise l'AST Python pour les analyses syntaxiques
- **Sans dépendance** — aucune dépendance externe requise
- **Passif** — aucune modification du code
- **Reproductible** — même résultat à chaque exécution

### ⚠️ Limitations

- **Faux positifs** — les imports dynamiques ou via `eval()` peuvent être marqués comme non utilisés
- **Pas de logique** — ne détecte pas les bugs logiques, seulement le style
- **Pas de tests** — n'analyse pas la couverture ou l'existence de tests

## Troubleshooting

### Erreur : "python: command not found"

Utilisez le chemin complet vers Python :
```bash
C:\Users\tallar\Documents\PROJETS\RAG\.venv\Scripts\python analyzer.py "." --analyze
```

### Le rapport JSON est vide ou incorrect

Vérifiez que le chemin du projet existe :
```bash
python analyzer.py "C:\Users\tallar\Documents\PROJETS\RAG" --analyze
```

### Trop de faux positifs sur les imports

C'est normal pour les imports dynamiques. Filtrez manuellement dans le JSON.

## Installation & Utilisation globale

Cette skill est installée **au niveau utilisateur** et disponible pour tous les projets Python :

```
C:\Users\tallar\.claude\skills\code-review-analysis\
```

### Utiliser sur n'importe quel projet

```bash
# Depuis n'importe quel répertoire
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "<project_path>" --analyze

# Exemples
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "C:\autre\projet" --analyze
```

### Créer un alias PowerShell (optionnel)

Ajouter à votre profil PowerShell (`$PROFILE`) :

```powershell
function code-review {
    param([string]$Path = ".")
    python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" $Path --analyze
}
```

Utilisation simplifiée :
```bash
code-review "."
code-review "C:\autre\projet"
```

## Workflow typique

1. **Générer le rapport** : `python analyzer.py "." --analyze`
2. **Ouvrir le Markdown** : `.claude/code_review_report.md` dans VS Code
3. **Chercher les 🔴 critiques** : Ctrl+F "🔴"
4. **Corriger par priorité** : error_handling → long_functions → docstrings
5. **Itérer** → Corriger, re-générer, vérifier la progression

---

**Pour plus de détails**, consultez `SKILL.md` (documentation technique).
