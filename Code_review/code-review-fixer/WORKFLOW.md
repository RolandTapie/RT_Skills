# 🔄 Workflow Complet : Analyse + Correction

Guide pour utiliser les deux skills ensemble : `code-review-analysis` et `code-review-fixer`.

## Workflow en 5 étapes

```
Projet Python
     ↓
[1] Analyser           (code-review-analysis)
     ↓
[2] Voir résumé        (code-review-fixer --summary)
     ↓
[3] Corriger           (code-review-fixer --fix)
     ↓
[4] Vérifier           (code-review-analysis)
     ↓
[5] Répéter ou Terminer
```

---

## Étape 1 : Analyser le projet

```bash
cd "C:\mon\projet\python"
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
```

**Résultat :**
- ✅ Rapport Markdown : `.claude/code_review_report.md`
- ✅ Rapport JSON : `.claude/code_review_report.json`
- ℹ️ Résumé en console

**À faire :**
- Ouvrir `.claude/code_review_report.md` dans VS Code
- Noter les **🔴 critiques** à corriger en priorité

---

## Étape 2 : Voir le résumé des corrections possibles

```bash
python "$env:USERPROFILE\.claude\skills\code-review-fixer\fixer.py" "." --summary
```

**Résultat :**
```
📊 RAPPORT DE CODE REVIEW
━━━━━━━━━━━━━━━━━━━━━━━━
Projet: C:\mon\projet\python
Total problèmes: 1818

Résumé par type:
  • error_handling       : 163 (163 corrigibles) ✅
  • unused_imports       :  45 (45 corrigibles)  ✅
  • docstrings           : 500 (500 corrigibles) ✅
  • type_hints           : 777 (777 corrigibles) ✅
  • long_functions       :  65 (0 corrigibles)   ⚠️
  • naming_conventions   :  15 (15 corrigibles)  ✅
```

**À faire :**
- Voir quels problèmes sont **corrigibles** ✅
- Identifier les **manuels** (long_functions)

---

## Étape 3 : Corriger les problèmes (Mode semi-automatique)

```bash
python "$env:USERPROFILE\.claude\skills\code-review-fixer\fixer.py" "." --fix
```

**Fonctionnement :**

Pour chaque problème corrigible, vous voyez :

```
🔴 ERROR HANDLING (163 problèmes)
────────────────────────────────

  api/rag_api.py:42
    Problème: Bloc except vide (pass)
    Ligne: except Exception:
    Corriger? (o/n) [o]: 
```

**Vous pouvez :**
- `o` (ou Entrée) → Appliquer la correction
- `n` → Ignorer et continuer

**Corrections appliquées :**
```
✅ Corrigé: ajout logging.exception()
```

**Résumé à la fin :**
```
📋 RÉSUMÉ DES CORRECTIONS
  ✅ Appliquées: 208
  ⏭️  Ignorées: 12
  ℹ️  Manuelles: 1598
```

---

## Étape 4 : Vérifier la progression

```bash
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
```

**Comparer avant/après :**

| | Avant | Après | Δ |
|---|---|---|---|
| Critiques | 163 | 0 | -163 ✅ |
| Avertissements | 670 | 662 | -8 |
| Infos | 1090 | 1090 | 0 |
| **Total** | **1818** | **1800** | **-18** |

---

## Étape 5 : Répéter ou Terminer

### Option A : Corriger davantage

```bash
# Corriger les docstrings manuellement
# Ouvrir .claude/code_review_report.md et ajouter les docstrings

# Ou corriger les long_functions
# Refactoriser manuellement les 65 fonctions

# Relancer l'analyse
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
```

### Option B : Terminer

```bash
# Committer vos changements
git add -A
git commit -m "Corrections automatiques: error_handling, unused_imports"

# Ou continuer plus tard
```

---

## Exemple Complet : Session de nettoyage

```bash
# === SESSION 1 ===
# Nettoyer les blocs except vides et imports

cd "C:\PROJETS\RAG"
git status                    # Vérifier propre
git commit -m "WIP"           # Committer en attente

# Analyser
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
# → 1818 problèmes

# Corriger
python "$env:USERPROFILE\.claude\skills\code-review-fixer\fixer.py" "." --fix
# → Correction 170 problèmes (error_handling + unused_imports)

# Vérifier
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
# → 1648 problèmes (bien!)

# Committer
git commit -m "Auto-fix: error_handling, unused_imports"


# === SESSION 2 (le lendemain) ===
# Corriger les docstrings

# Analyser
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
# → 1648 problèmes

# Lire le rapport Markdown
# .claude/code_review_report.md → Ajouter docstrings manuellement

# Corriger manuellement les docstrings critiques (~50)
# (Trop complexe pour automatiser)

# Vérifier
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
# → 1598 problèmes

# Committer
git commit -m "Add docstrings to 50 critical functions"


# === SESSION 3 (la semaine suivante) ===
# Refactoriser les long_functions

# Les 65 long_functions nécessitent du refactoring manuel
# Consulter le rapport Markdown pour localiser
# Refactoriser fonction par fonction
# Tester à chaque étape

# Committer petit à petit
git commit -m "Refactor: split long functions in api/rag_api.py"

# Vérifier
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
```

---

## Bonnes pratiques

✅ **À faire :**
- Committer avant d'utiliser `fixer.py`
- Vérifier les corrections avec `--analyze` après
- Confirmer chaque correction (mode semi-auto)
- Progresser itérativement

❌ **À éviter :**
- Utiliser `fixer.py` sans commit précédent
- Ignorer les manuels (long_functions)
- Trusting aveuglément les corrections
- Tout corriger d'un coup

---

## Debugging

### "Quelque chose s'est mal passé"

```bash
# Voir les changements
git diff

# Revenir en arrière
git checkout .

# Réessayer
python "$env:USERPROFILE\.claude\skills\code-review-fixer\fixer.py" "." --fix
```

### "La correction a cassé quelque chose"

```bash
# Chercher l'erreur
git diff <fichier>

# Éditer manuellement
code <fichier>

# Relancer l'analyse pour voir si c'est mieux
python "$env:USERPROFILE\.claude\skills\code-review-analysis\analyzer.py" "." --analyze
```

---

## Résumé

| Étape | Skill | Commande |
|-------|-------|----------|
| 1. Analyser | `code-review-analysis` | `analyzer.py "." --analyze` |
| 2. Résumé | `code-review-fixer` | `fixer.py "." --summary` |
| 3. Corriger | `code-review-fixer` | `fixer.py "." --fix` |
| 4. Vérifier | `code-review-analysis` | `analyzer.py "." --analyze` |
| 5. Répéter | [Manuel] | Éditeur de code + commit |

**À chaque itération, le nombre de problèmes diminue jusqu'à satisfaction! 🚀**
