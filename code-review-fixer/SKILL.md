---
name: code-review-fixer
description: Corriger les problèmes détectés par code-review-analysis. Mode semi-automatique avec confirmation avant chaque correction. L'humain garde la main sur long_functions.
scope: global
---

# Skill: Code Review Fixer

**Complémentaire à code-review-analysis** — Applique les corrections de manière semi-automatique.

Cette skill :
1. Cherche le rapport `code_review_report.json`
2. Propose les corrections avec confirmation
3. Applique les modifications
4. Génère un résumé des corrections

## Usage

### 1. Afficher le résumé des problèmes

```bash
python "$env:USERPROFILE\.claude\skills\code-review-fixer\fixer.py" "<project_root>" --summary
```

Affiche :
- Nombre total de problèmes
- Décompte par type
- Lesquels sont corrigibles automatiquement

### 2. Corriger les problèmes (mode semi-automatique)

```bash
python "$env:USERPROFILE\.claude\skills\code-review-fixer\fixer.py" "<project_root>" --fix
```

Pour chaque problème corrigible :
- Affiche le contexte (fichier, ligne)
- Demande confirmation avant de corriger
- Applique la correction

## Corrections gérées

### ✅ Automatiques (avec confirmation)

| Type | Correction | Risque |
|------|-----------|--------|
| **error_handling** | Ajoute `logging.exception()` dans les blocs `except: pass` | 🟢 Bas |
| **unused_imports** | Supprime les imports non utilisés | 🟢 Bas |

### ⚠️ Semi-automatiques (avec confirmation, moins safe)

| Type | Correction | Risque |
|------|-----------|--------|
| **docstrings** | Affiche la liste, l'utilisateur ajoute manuellement | 🟡 Nécessite review |
| **naming_conventions** | Affiche la liste, l'utilisateur renomme manuellement | 🟡 Peut affecter d'autres références |
| **type_hints** | Affiche la liste, l'utilisateur ajoute manuellement | 🟡 Peut être imprécis |

### 🔧 Manuels (décision utilisateur)

| Type | Raison |
|------|--------|
| **long_functions** | Refactoring trop complexe, nécessite compréhension du contexte métier |

## Workflow typique

```bash
# 1. Générer le rapport
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze

# 2. Voir le résumé
python "$env:USERPROFILE\.claude\skills\code-review-fixer\fixer.py" "." --summary

# 3. Corriger les problèmes
python "$env:USERPROFILE\.claude\skills\code-review-fixer\fixer.py" "." --fix

# 4. Vérifier les corrections
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze

# 5. Répéter jusqu'à satisfaction
```

## Mode semi-automatique expliqué

**Vous gardez la main** sur chaque correction :

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
    Ligne: except:
    Corriger? (o/n) [o]: n
    ⏭️ Ignoré
```

## Sécurité

✅ **Aucune modification sans confirmation**  
✅ **Sauvegarde les fichiers modifiés** (override original)  
✅ **Affiche ce qui va être changé** avant de le faire  
✅ **Permet de relancer** la analyse après pour vérifier  

## Limitations

- **Pas de refactoring automatique** pour les long_functions
- **Type hints** doivent être vérifiés manuellement
- **Renommages** (naming_conventions) sont risqués, donc manuels
- **Docstrings** nécessitent compréhension du code

## Note importante

Cette skill est **destructive** — elle modifie vos fichiers. Assurez-vous que :
- ✅ Vos changements sont **commités** (`git commit`)
- ✅ Vous pouvez **revenir en arrière** (`git checkout`)
- ✅ Vous **relancez l'analyse** après pour vérifier
