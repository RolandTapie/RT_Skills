# Code Review Fixer — Skill

**Correction semi-automatique des problèmes détectés par code-review-analysis.**

Cette skill corrige les problèmes identifiés dans le rapport `code_review_report.json`, avec confirmation de l'utilisateur avant chaque modification.

## ⚡ Avant de commencer

**Prérequis :**
1. Vous avez généré un rapport avec `code-review-analysis`
2. Le rapport JSON existe à `.claude/code_review_report.json`
3. Vos changements sont **commités** (vous pouvez revenir en arrière)

## TL;DR — Usage rapide

```bash
# 1. Voir les problèmes à corriger
python "$env:USERPROFILE\.claude\skills\code-review-fixer\fixer.py" "." --summary

# 2. Corriger les problèmes
python "$env:USERPROFILE\.claude\skills\code-review-fixer\fixer.py" "." --fix

# 3. Vérifier les corrections
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
```

## Mode semi-automatique

Pour chaque problème corrigible, le script :

1. **Affiche le contexte** (fichier, ligne, problème)
2. **Demande confirmation** : `Corriger? (o/n) [o]:`
3. **Applique la correction** si vous confirmez (o)
4. **Continue** avec le problème suivant

### Exemple

```
🔴 ERROR HANDLING (12 problèmes)
────────────────────────────────

  api/rag_api.py:42
    Problème: Bloc except vide (pass)
    Ligne: except Exception:
    Corriger? (o/n) [o]: o
    ✅ Corrigé: ajout logging.exception()

  models/chunk_models.py:105
    Problème: Bloc except vide (pass)
    Corriger? (o/n) [o]: n
    ⏭️ Ignoré
```

## Corrections appliquées

### ✅ Automatiques (sûres)

**Error Handling** — Ajoute `logging.exception()` dans les blocs `except: pass`
```python
# Avant
except Exception:
    pass

# Après
except Exception:
    logging.exception("Erreur")
```

**Unused Imports** — Supprime les imports non utilisés
```python
# Avant
import json
import os  # Non utilisé

# Après
import json
```

### ⚠️ Manuelles (besoin validation)

**Docstrings, Type Hints, Naming Conventions** — Affichées seulement, vous les ajoutez manuellement

**Long Functions** — Affichées seulement, refactoring manuel requis

## Workflow complet

```bash
cd "C:\mon\projet\python"

# Étape 1 : Analyser
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
# Génère code_review_report.json et code_review_report.md

# Étape 2 : Voir le résumé
python "$env:USERPROFILE\.claude\skills\code-review-fixer\fixer.py" "." --summary
# Affiche 1818 problèmes, 24 corrigibles automatiquement

# Étape 3 : Corriger
python "$env:USERPROFILE\.claude\skills\code-review-fixer\fixer.py" "." --fix
# Mode interactif : vous confirmez ou ignorez chaque correction

# Étape 4 : Vérifier
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
# Vérifier que le nombre de problèmes a baissé

# Étape 5 : Répéter
# Corriger manuellement les long_functions, docstrings, etc.
# Relancer l'analyse
```

## Sécurité & Reversibilité

✅ **Confirmations** avant chaque correction  
✅ **Git-safe** — Si quelque chose ne va pas, `git checkout .` pour revenir  
✅ **Vérifiable** — Relancez l'analyse après pour voir la progression  

**Avant d'utiliser la skill :**

```bash
git status          # Vérifier que c'est propre
git add .           # Ou committer vos changements
git commit -m "Before auto-corrections"
```

## Limitations

- **Long Functions** : Refactoring trop complexe, manuel requis
- **Docstrings** : Besoin compréhension du code
- **Type Hints** : Peuvent être imprécis sans context
- **Naming** : Risqué d'affecter d'autres références

## Troubleshooting

### "Rapport non trouvé"

```
❌ Rapport non trouvé: .\.claude\code_review_report.json
```

**Solution :** Générez d'abord un rapport avec `code-review-analysis`

```bash
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
```

### Erreur lors de la correction

Si une correction échoue (ex. syntaxe cassée), vous pouvez revenir en arrière :

```bash
git checkout <fichier>    # Annuler les changements du fichier
python fixer.py "." --fix # Relancer et ignorer ce fichier
```

### Besoin de modifier les corrections

Le script applique des corrections standardisées. Si vous voulez des corrections plus spécialisées, éditez le fichier manuellement ou modifiez `fixer.py`.

## Cas d'usage

✅ **Nettoyer les imports** → Suppression automatique  
✅ **Ajouter logging** → Blocs except vides  
✅ **Itération rapide** → Combiner avec l'analyse pour voir la progression  
✅ **Base de départ** → Avant de refactoriser manuellement  

## Architecture

```
fixer.py
  ├── CodeReviewFixer (classe principale)
  │   ├── find_report() — Cherche code_review_report.json
  │   ├── summary() — Affiche le résumé
  │   ├── interactive_fix() — Mode correction interactive
  │   └── _fix_* — Corrections spécifiques (error_handling, unused_imports, etc.)
  └── main() — Entrée principale
```

## Notes pour les contributeurs

Pour ajouter une nouvelle correction :

1. Créer une méthode `_handle_<type>()` 
2. Créer une méthode `_fix_<type>()`
3. Appeler depuis `interactive_fix()`

Exemple :
```python
def _handle_custom(self, findings: List[Finding]):
    print(f"🔧 CUSTOM ({len(findings)} problèmes)")
    for finding in findings:
        response = input("Corriger? (o/n) [o]: ").strip().lower() or 'o'
        if response == 'o':
            self._fix_custom(finding)
            self.corrections_applied += 1
        else:
            self.corrections_skipped += 1
```
