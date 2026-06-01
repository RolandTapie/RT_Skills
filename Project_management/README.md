# Project Management Skills Collection

Ensemble de 3 skills Claude Code pour scaffolder, spécifier et générer du code de projet de manière structurée et cohérente.

## 🎯 Vue d'ensemble

Ces skills implémentent un **framework complet de gestion de projet** basé sur la spécification avant l'implémentation :

```
Descriptif du projet
       ↓
/project:analyze   → Spécifications (requirements, design, plan)
       ↓
/project:generate  → Code fonctionnel + tests
       ↓
Projet prêt à développer
```

---

## 📚 Les 3 Skills

### 1. `/project:setup` ⚙️
Configure la structure de base d'un nouveau projet.

**Usage:**
```bash
/project:setup --stack python
/project:setup --stack react
```

**Crée:**
- `project.toml` - Configuration du projet
- `pyproject.toml` ou `package.json` - Configuration stack
- Répertoires: `src/`, `tests/`, `features/`

**Quand l'utiliser:** Au démarrage d'un nouveau projet

[Documentation détaillée →](./project_setup/README.md)

---

### 2. `/project:analyze` 🔍
Analyse un descriptif textuel et génère les spécifications pour chaque feature.

**Usage:**
```bash
/project:analyze "Description complète du projet..."
```

**Génère pour chaque feature:**
- `requirements.md` - Spécifications fonctionnelles
- `design.md` - Design technique
- `plan.md` - Plan d'implémentation

**Features sont numérotées:** `001-feature-name/`, `002-feature-name/`, etc.

**Quand l'utiliser:** Après `/project:setup`, avant `/project:generate`

[Documentation détaillée →](./project_analyze/README.md)

---

### 3. `/project:generate` 🚀
Génère le code fonctionnel complet + tests pour chaque feature basé sur les spécifications.

**Usage:**
```bash
/project:generate 001-feature-name
/project:generate 002-another-feature
```

**Génère:**
- Code complet dans `src/{number}-feature-name/`
- Tests complets dans `tests/`
- Production-ready avec type hints et docstrings

**Quand l'utiliser:** Après que `/project:analyze` a créé les specs

[Documentation détaillée →](./project_generate/README.md)

---

## 🔄 Workflow Complet

### Exemple: Créer une API de gestion d'association

```bash
# 1. Initialiser le projet
/project:setup --stack python

# 2. Analyser le besoin
/project:analyze "Je veux une interface pour gérer les adhérents, événements, et finances d'une association..."

# Résultat: 
# - features/001-member-management/
# - features/002-event-management/
# - features/003-finance-management/
# (chacune avec requirements.md, design.md, plan.md)

# 3. Générer le code (feature par feature)
/project:generate 001-member-management
/project:generate 002-event-management
/project:generate 003-finance-management

# Résultat:
# - src/001-member-management/ (models, service, api)
# - src/002-event-management/ (models, service, api)
# - src/003-finance-management/ (models, service, api)
# - tests/ (tests complets)
```

---

## 📂 Structure de Répertoire Créée

```
mon-projet/
├── project.toml                    # Config du projet
├── pyproject.toml                  # (Python) ou package.json (React)
│
├── src/                            # Code centralisé, pas par feature !
│   ├── models/                     # Tous les modèles de données
│   │   ├── __init__.py
│   │   ├── member.py               # Modèles Member, Event, Finance, etc.
│   │   ├── event.py
│   │   └── finance.py
│   ├── services/                   # Tous les services métier
│   │   ├── __init__.py
│   │   ├── member_service.py
│   │   ├── event_service.py
│   │   └── finance_service.py
│   ├── repositories/               # Tous les accès données
│   │   ├── __init__.py
│   │   ├── member_repository.py
│   │   └── event_repository.py
│   ├── api/                        # Toutes les routes
│   │   ├── __init__.py
│   │   ├── members.py              # Routes /members
│   │   ├── events.py               # Routes /events
│   │   └── finance.py              # Routes /finance
│   ├── utils/                      # Utilitaires partagés
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   └── helpers.py
│   └── __init__.py
│
├── tests/                          # Tests globaux
│   ├── test_member_service.py
│   ├── test_event_service.py
│   └── test_finance_service.py
│
└── features/                       # Spécifications par feature
    ├── 001-member-management/
    │   ├── requirements.md
    │   ├── design.md
    │   └── plan.md
    ├── 002-event-management/
    │   ├── requirements.md
    │   ├── design.md
    │   └── plan.md
    └── 003-finance-management/
        ├── requirements.md
        ├── design.md
        └── plan.md
```

---

## ✨ Points Clés

### 🔢 Numérotation des Features
- Les features sont automatiquement numérotées : `001-`, `002-`, `003-`, etc.
- Toujours 3 chiffres
- Continue sequentiellement (si `001` existe, la nouvelle est `002`)
- Le numéro est utilisé partout (directory names, file names)

### 📋 Spécifications (Artifacts de /project:analyze)

Chaque feature a **3 fichiers de spécifications** :

1. **requirements.md**
   - Description
   - User stories
   - Acceptance criteria
   - Dépendances
   - Non-functional requirements

2. **design.md**
   - Overview architecture
   - Components/Modules
   - Data models (Pydantic/TypeScript)
   - API endpoints
   - Dépendances externes
   - Database schema (si applicable)

3. **plan.md**
   - Fichiers à créer
   - Étapes d'implémentation
   - Stratégie de test
   - Complexité estimée

### 💻 Code Généré (Output de /project:generate)

**Python:**
- Models (Pydantic)
- Service (business logic)
- Repository (data access)
- API (FastAPI routes)
- Type hints complets
- Docstrings
- Tests pytest complets

**React:**
- Components (functional)
- Hooks (custom)
- Services (API calls)
- Types TypeScript
- Tests (React Testing Library)

---

## 🎓 Bonnes Pratiques

### 1. Spécifications d'Abord
Avant d'écrire du code, spécifiez clairement :
- Qu'est-ce que ça fait ? (requirements)
- Comment ça marche techniquement ? (design)
- Comment on le bâtit ? (plan)

### 2. Features Indépendantes
Chaque feature doit être :
- Une responsabilité unique
- Testable indépendamment
- Intégrable progressivement

### 3. Une Feature à la Fois
Générez et intégrez feature par feature :
```bash
/project:generate 001-xxx
# Tester et intégrer 001

/project:generate 002-yyy
# Tester et intégrer 002

/project:generate 003-zzz
# Tester et intégrer 003
```

---

## 🔗 Stack Supportés

### Python
- Framework: FastAPI (recommandé) ou Django
- Package manager: uv
- Testing: pytest
- ORM: SQLAlchemy
- Validation: Pydantic

### React
- Framework: React 18+ with TypeScript
- Package manager: npm
- Testing: React Testing Library + Vitest
- State: TanStack Query, Zustand
- Styling: Tailwind CSS

---

## 🚨 Prérequis

- **Python setup:** `python 3.11+`, `uv` installé
- **React setup:** `node 18+`, `npm` installé
- **Claude Code:** Version récente avec support des skills

---

## 📖 Documentation Détaillée

- [Workflow Complet](./WORKFLOW.md)
- [Architecture des Skills](./ARCHITECTURE.md)
- [Exemples & Cas d'Usage](./EXAMPLES.md)
- [Troubleshooting](./TROUBLESHOOTING.md)

---

## 💡 Cas d'Usage

✅ **Idéal pour:**
- Nouveaux projets (greenfield)
- Refactorisation (quand on veut une architecture claire)
- Prototypage rapide
- Onboarding équipe (spécifications claires)

⚠️ **Moins idéal pour:**
- Legacy code (existant)
- Très petits projets (une feature)
- Cas très spécialisés non couverts

---

## 🤝 Contribution

Pour améliorer ces skills :
1. Tester sur vos projets
2. Signaler les bugs ou améliorations
3. Proposer des extensions (nouvelles languages, patterns)

---

**Version:** 1.0  
**Dernière mise à jour:** Juin 2026  
**Auteur:** Roland (Data Analyst)
