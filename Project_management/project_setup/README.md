# `/project:setup` - Project Setup Skill

**Initialise la structure de base d'un nouveau projet.**

---

## 📌 Vue d'Ensemble

Cette skill crée la structure fondationnelle d'un projet avec le stack choisi (Python ou React).

**Elle crée:**
- Configuration du projet (`project.toml`)
- Configuration du stack (`pyproject.toml` ou `package.json`)
- Répertoires de base (`src/`, `tests/`, `features/`)

---

## 🚀 Utilisation

### Commande
```bash
/project:setup --stack python
```
ou
```bash
/project:setup --stack react
```

### Paramètres
- `--stack` : **Requis**
  - `python` - Pour projets Python avec uv
  - `react` - Pour projets React avec npm

---

## 📂 Structure Créée

### Python
```
mon-projet/
├── project.toml              # [project] stack = "python"
├── pyproject.toml            # [build-system] [project] config
├── src/                      # Code source (vide pour le moment)
│   └── __init__.py           # Sera rempli par /project:generate
├── tests/                    # Tests (vide pour le moment)
└── features/                 # Spécifications (vide pour le moment)
```

**pyproject.toml généré:**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-project"
version = "0.1.0"
description = "Project description"
```

### React
```
mon-projet/
├── project.toml              # [project] stack = "react"
├── package.json              # React config + dependencies
├── src/                      # Code source (vide pour le moment)
│   └── App.tsx               # Sera rempli par /project:generate
├── tests/                    # Tests (vide pour le moment)
└── features/                 # Spécifications (vide pour le moment)
```

**package.json généré:**
```json
{
  "name": "my-project",
  "version": "0.1.0",
  "type": "module",
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "devDependencies": {
    "vite": "^4.0.0",
    "typescript": "^5.0.0"
  }
}
```

---

## 📋 Étapes de Setup

### 1. Validation du Stack
- ✅ Must be `python` ou `react`
- ❌ Invalide : `python3`, `nodejs`, `express`, etc.

### 2. Vérification de `project.toml`
- **Existe ?** → Update `[project]` section uniquement
- **N'existe pas ?** → Créer un nouveau

### 3. Création Configuration du Stack
- **Python:** `pyproject.toml` (si n'existe pas)
- **React:** `package.json` (si n'existe pas)

### 4. Création des Répertoires
- `src/` - Code source
- `tests/` - Tests
- `features/` - Spécifications des features

### 5. Report
Affiche :
- Fichiers créés/existants
- Structure de répertoires
- Prochaine étape : `/project:analyze`

---

## ⚠️ Notes Importantes

### Ne Pas Overwrite
- Si `pyproject.toml` ou `package.json` existe → Avertissement
- Si `src/`, `tests/`, `features/` existent → Pas modifiés

### project.toml est Minimal
```toml
[project]
stack = "python"  # ou "react"
```
C'est tout ce qui est stocké dans le setup. Les autres configurations viennent plus tard.

### Dépendances Pas Installées
- `pyproject.toml` est créé mais dépendances pas installées
- `package.json` est créé mais `npm install` pas lancé
- À faire manuellement : `uv pip install` ou `npm install`

---

## 🔄 Workflow

```
/project:setup --stack python
        ↓
   project.toml créé
   src/, tests/, features/ créés
        ↓
/project:analyze "..."
```

---

## 🎯 Checklist

Après `/project:setup --stack python` :
- [ ] `project.toml` existe avec `stack = "python"`
- [ ] `pyproject.toml` existe
- [ ] Répertoire `src/` existe
- [ ] Répertoire `tests/` existe
- [ ] Répertoire `features/` existe
- [ ] Prêt pour `/project:analyze`

---

## 💡 Tips

### 1. Créer plusieurs projets
Chaque projet son répertoire, chaque répertoire son `/project:setup`.

### 2. Redémarrer le setup
Si tu veux reset la config, supprimer `project.toml` et relancer `/project:setup`.

### 3. Changer le stack après coup
Pas recommandé (code peut être spécifique). Mieux : créer nouveau projet.

### 4. Dépendances
Après setup, installer manuellement :
```bash
# Python
uv pip install fastapi sqlalchemy pydantic

# React
npm install
```

---

## ❓ FAQ

**Q: Peux-tu utiliser les deux stacks en même temps ?**
R: Non, un seul stack par projet. Si tu veux full-stack : crée deux projets séparés.

**Q: Où sont les autres configs (black, eslint, pytest, etc.) ?**
R: Minimales par défaut. À ajouter manuellement selon tes besoins.

**Q: Puis-je modifier project.toml manuellement ?**
R: Oui, mais ne change pas le format. Garde juste `[project]` avec `stack = ...`.

---

**Version:** 1.0  
**Prochaine étape:** `/project:analyze`
