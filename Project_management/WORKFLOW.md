# Workflow Complet - Guide Étape par Étape

Ce guide te montre comment utiliser les 3 skills pour créer un projet complet de A à Z.

---

## Étape 1️⃣ : `/project:setup` - Initialiser le projet

### Commande
```bash
/project:setup --stack python
# ou
/project:setup --stack react
```

### Résultat
```
mon-projet/
├── project.toml              # Configuration du projet
├── pyproject.toml            # Python config (si Python)
│  ou package.json            # React config (si React)
├── src/                      # Code source (vide pour le moment)
├── tests/                    # Tests (vide pour le moment)
└── features/                 # Spécifications (vide pour le moment)
```

### Fichier `project.toml` créé
```toml
[project]
stack = "python"  # ou "react"
```

### Après cette étape
✅ Le projet a une structure de base
✅ Prêt pour `/project:analyze`

---

## Étape 2️⃣ : `/project:analyze` - Analyser et Spécifier

### Commande
```bash
/project:analyze "Descrition complète de ton projet..."
```

### Exemple
```bash
/project:analyze "Je veux créer une interface pour gérer une association : 
- Gestion des adhérents (profil, statut, renouvellement)
- Gestion des événements (création, inscriptions, présences)
- Gestion des finances (cotisations, dépenses, rapports)
- Authentification sécurisée avec rôles
- Dashboard moderne et responsive"
```

### Ce que ça fait
1. **Parse** ton descriptif
2. **Identifie** les features distinctes
3. **Numérote** chaque feature : `001-`, `002-`, `003-`, etc.
4. **Crée** pour chaque feature :
   - `features/{number}-{name}/requirements.md`
   - `features/{number}-{name}/design.md`
   - `features/{number}-{name}/plan.md`

### Résultat
```
features/
├── 001-member-management/
│   ├── requirements.md       # Spécifications fonctionnelles
│   ├── design.md             # Design technique
│   └── plan.md               # Plan d'implémentation
├── 002-event-management/
│   ├── requirements.md
│   ├── design.md
│   └── plan.md
├── 003-finance-management/
│   ├── requirements.md
│   ├── design.md
│   └── plan.md
└── 004-authentication/
    ├── requirements.md
    ├── design.md
    └── plan.md
```

### Contenu des Spécifications

#### requirements.md
```markdown
# Requirements: Member Management

## Description
Système de gestion des adhérents...

## User Stories
- As a user, I want...

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Dependencies
- Other features (if any)
```

#### design.md
```markdown
# Design: Member Management

## Overview
...

## Components/Modules
...

## Data Models
[Pydantic/TypeScript models]

## API Endpoints
[Routes/Functions]

## External Dependencies
[Libraries needed]
```

#### plan.md
```markdown
# Implementation Plan: Member Management

## Files to Create
- src/001-member-management/__init__.py
- src/001-member-management/models.py
- src/001-member-management/service.py
- tests/test_001_member_management.py

## Implementation Steps
1. Create models
2. Implement business logic
3. Create API endpoints
4. Write tests

## Complexity
- Simple / Medium / Complex
```

### Après cette étape
✅ Tu as des spécifications claires pour chaque feature
✅ Les specs sont numérotées et organisées
✅ Prêt pour `/project:generate`

---

## Étape 3️⃣ : `/project:generate` - Générer le Code

### Commande
```bash
/project:generate 001-member-management
/project:generate 002-event-management
/project:generate 003-finance-management
/project:generate 004-authentication
```

### Important
⚠️ **Génère une feature à la fois**, pas toutes ensemble !
Cela permet de :
- Tester chaque feature indépendamment
- Intégrer progressivement
- Gérer les erreurs plus facilement

### Ce que ça fait pour chaque feature
1. Lit les 3 fichiers de spécifications
2. Génère le code complet dans `src/{number}-{name}/`
3. Génère les tests dans `tests/`
4. Code est production-ready (type hints, docstrings, tests)

### Résultat pour Python

**Code généré (structure centralisée):**
```
src/
├── models/
│   ├── __init__.py
│   ├── member.py        # Modèles pour Member
│   ├── event.py         # Modèles pour Event
│   └── finance.py       # Modèles pour Finance
├── services/
│   ├── __init__.py
│   ├── member_service.py
│   ├── event_service.py
│   └── finance_service.py
├── repositories/
│   ├── __init__.py
│   ├── member_repository.py
│   └── event_repository.py
├── api/
│   ├── __init__.py
│   ├── members.py       # Routes /members
│   ├── events.py        # Routes /events
│   └── finance.py       # Routes /finance
└── __init__.py

tests/
├── test_member_service.py
├── test_event_service.py
└── test_finance_service.py
```

**Important:** Code est CENTRALISÉ par type (models/, services/, etc.), pas par feature !

**Exemple de code généré:**
```python
# models.py
from pydantic import BaseModel
from datetime import date

class MemberModel(BaseModel):
    id: int
    name: str
    email: str
    membership_date: date

# service.py
class MemberService:
    """Member management service."""
    
    def __init__(self, repository):
        self.repository = repository
    
    def create_member(self, data: MemberModel) -> MemberModel:
        """Create a new member."""
        return self.repository.create(data)

# api.py
from fastapi import APIRouter

router = APIRouter(prefix="/members", tags=["members"])

@router.get("/")
async def list_members():
    """List all members."""
    pass

@router.post("/")
async def create_member(data: MemberModel):
    """Create a new member."""
    pass
```

### Résultat pour React

**Code généré:**
```
src/001-member-management/
├── components/          # React components
├── hooks/               # Custom hooks
├── services/            # API calls
├── types.ts             # TypeScript interfaces
└── index.ts             # Barrel export

tests/
└── test_001_member_management.test.tsx  # React tests
```

### Après `/project:generate 001`

✅ Fonction 001 est codée et testée
✅ Code est prêt à être intégré
✅ Peut être utilisée dans les autres features

Ensuite → Répète avec la feature suivante

---

## Workflow Complet - Timeline

### Jour 1 : Setup & Analysis
```bash
# Matin
/project:setup --stack python

# Après-midi
/project:analyze "Description du projet..."
```

✅ Résultat : Spécifications claires, organisées, numérotées dans `features/`

### Jour 2-5 : Code Generation & Integration

**Chaque jour / Chaque feature générer :**
```bash
/project:generate 001-feature
# → Génère code CENTRALISÉ dans src/
#   (models/*, services/*, repositories/*, api/*)
# → Tests dans tests/test_*.py
# → Intégrer et tester
# → Corriger les problèmes

/project:generate 002-feature
# → Ajoute plus à src/ (pas de dossier séparé)
# → Ajoute plus de tests
# → Intégrer et tester

/project:generate 003-feature
# → Même pattern
```

✅ Résultat : Code complètement centralisé dans `src/`

### Fin : Assembly & Testing

```bash
# Tests end-to-end (tous dans tests/)
pytest tests/

# Lancer l'app
python -m uvicorn src.main:app

# Ou pour React
npm run dev
```

✅ Résultat : Projet complet, fonctionnel, code bien organisé au même endroit

---

## ⚙️ Récapitulatif des Commandes

| Étape | Commande | Quand |
|-------|----------|-------|
| 1 | `/project:setup --stack python` | Début du projet |
| 2 | `/project:analyze "..."` | Après setup |
| 3 | `/project:generate 001-xxx` | Après analyze |
| 3 | `/project:generate 002-yyy` | Feature 001 finie |
| 3 | `/project:generate 003-zzz` | Feature 002 finie |

---

## 🎯 Checklist - Fin de chaque étape

### Après `/project:setup`
- [ ] `project.toml` créé avec le bon stack
- [ ] Répertoires `src/`, `tests/`, `features/` existent
- [ ] Config de base en place (pyproject.toml ou package.json)

### Après `/project:analyze`
- [ ] Features identifiées et numérotées
- [ ] Chaque feature a 3 fichiers (requirements, design, plan)
- [ ] Spécifications cohérentes (checklist du design)
- [ ] Dépendances entre features documentées

### Après chaque `/project:generate`
- [ ] Code généré dans `src/{number}-{name}/`
- [ ] Tests générés dans `tests/`
- [ ] Code compile/type-checks (pas d'erreurs)
- [ ] Tests passent (pytest ou npm test)
- [ ] Feature intégrée au reste du projet

---

## 💡 Tips & Tricks

### 1. Tester le code généré immédiatement
```bash
# Python
pytest tests/test_001_member_management.py -v

# React
npm test -- test_001_member_management
```

### 2. Intégrer progressivement
Ne pas attendre que tout soit généré avant de tester !
Génère → Teste → Intègre → Répète

### 3. Vérifier les dépendances
Si feature 002 dépend de feature 001 :
- Générer 001 d'abord
- Puis 002 (qui peut importer de 001)

### 4. Modifier les spécifications au besoin
Si tu dois corriger une spec après génération :
1. Modifie le fichier (requirements.md, design.md, plan.md)
2. Régénère la feature : `/project:generate 001-xxx`
3. Le nouveau code remplace l'ancien

### 5. Exporter les spécifications
Pour partager avec l'équipe :
```bash
# Copier tout le dossier features/
cp -r features/ ../exported-specs/

# Ou générer un PDF (si tu as un outil)
```

---

## ❓ Questions Fréquentes

**Q: Et si je me trompe dans le descriptif initial ?**
R: Tu peux re-lancer `/project:analyze` pour ajouter/modifier des features. Les noms seront numérotés continuellement.

**Q: Puis-je modifier le code généré ?**
R: Bien sûr ! Le code généré est un point de départ. Tu peux l'améliorer, l'adapter, ajouter de la logique.

**Q: Et si une feature dépend fortement d'une autre ?**
R: Document ça dans `dependencies:` du requirements.md et la génération en tiendra compte (imports, structure).

**Q: Combien de temps prend la génération ?**
R: Dépend de la complexité : Simple (5-10 min), Medium (15-20 min), Complex (30+ min).

---

## 🚀 Prêt à commencer ?

```bash
# Go !
/project:setup --stack python
```
