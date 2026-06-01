# `/project:analyze` - Project Analysis Skill

**Analyse un descriptif de projet et génère les spécifications pour chaque feature.**

---

## 📌 Vue d'Ensemble

Cette skill prend un descriptif textuel et le transforme en **spécifications structurées et numérotées** pour chaque feature.

**Elle crée:**
- Répertoires numérotés `001-feature-name/`, `002-feature-name/`, etc.
- Pour chaque feature : `requirements.md`, `design.md`, `plan.md`
- Spécifications complètes, cohérentes et prêtes pour `/project:generate`

---

## 🚀 Utilisation

### Commande
```bash
/project:analyze "Description complète du projet..."
```

### Paramètre
- **Description** : Texte descriptif du projet
  - Doit inclure les features principales
  - Peut être long ou court (la skill adapte)
  - Langue : Français ou Anglais

---

## 📝 Exemple d'Utilisation

### Input
```bash
/project:analyze "Je veux créer une plateforme de gestion d'association :
- Gestion des adhérents : profils, statut d'adhésion, renouvellements
- Gestion des événements : création, inscriptions, présences, rappels
- Gestion des finances : cotisations, dépenses, budgets, rapports
- Système de communication : newsletters, annonces, forum
- Authentification sécurisée : login, rôles (admin, trésorier, membre)
- Dashboard moderne et responsive pour tous les rôles
- Rapports et analytics pour l'administration"
```

### Output
```
features/
├── 001-member-management/
│   ├── requirements.md
│   ├── design.md
│   └── plan.md
├── 002-event-management/
│   ├── requirements.md
│   ├── design.md
│   └── plan.md
├── 003-finance-management/
│   ├── requirements.md
│   ├── design.md
│   └── plan.md
├── 004-communication/
│   ├── requirements.md
│   ├── design.md
│   └── plan.md
├── 005-authentication/
│   ├── requirements.md
│   ├── design.md
│   └── plan.md
├── 006-dashboard-ui/
│   ├── requirements.md
│   ├── design.md
│   └── plan.md
└── 007-reporting-analytics/
    ├── requirements.md
    ├── design.md
    └── plan.md
```

---

## 📂 Structure des Spécifications

### requirements.md
```markdown
# Requirements: {Feature Name}

## Description
Description de la feature, ce qu'elle fait, pourquoi elle existe.

## User Stories
- As a [user type], I want [action], so that [benefit]
- As a [user type], I want [action], so that [benefit]

## Acceptance Criteria
- [ ] Criterion 1 - Testable, précis
- [ ] Criterion 2
- [ ] Criterion 3

## Dependencies
- feature-001 (si applicable)
- External service X (si applicable)

## Non-Functional Requirements
- Performance targets
- Security requirements
- Compliance (RGPD, etc.)
- Scalability
```

### design.md
```markdown
# Design: {Feature Name}

## Overview
Architecture et composants principaux.

## Components/Modules
- `ModuleA` - What it does
- `ModuleB` - What it does

## Data Models
```python
class User(BaseModel):
    id: int
    name: str
    email: str
```

## API Endpoints
- `GET /users` - List users
- `POST /users` - Create user
- `GET /users/{id}` - Get user

## External Dependencies
- fastapi
- sqlalchemy
- pydantic

## Database Schema
[SQL or diagram]

## Business Schema
[Visual representation if complex]
```

### plan.md
```markdown
# Implementation Plan: {Feature Name}

## Files to Create
- src/001-member-management/__init__.py
- src/001-member-management/models.py
- src/001-member-management/service.py
- src/001-member-management/repository.py
- src/001-member-management/api.py
- tests/test_001_member_management.py

## Implementation Steps
1. Create data models (Pydantic)
2. Implement repository/data access
3. Implement service/business logic
4. Create API routes
5. Write comprehensive tests

## Testing Strategy
- Unit tests for: models, service logic
- Integration tests for: API endpoints
- Edge cases: validation, error handling

## Complexity Estimate
- Simple / Medium / Complex
- Estimated LOC: 500-800
- Time estimate: 2-3 days
```

---

## 🔢 Numérotation des Features

### Règles
- Commençar à `001`
- Toujours **3 chiffres**
- Incrémentale : `001`, `002`, `003`, ...
- Continue si tu relances (exemple : si `001-003` existent, la nouvelle sera `004`)

### Format du Répertoire
```
features/
├── 001-feature-one/
├── 002-feature-two/
└── 003-feature-three/
```

### Nommage des Features
- Kebab-case : `member-management`, `user-auth`, `email-notifications`
- Descriptif de la responsabilité
- Unique dans le projet

---

## ✨ Étapes de l'Analyse

### 1. Lecture du Descriptif
- Parse le texte fourni
- Identifie les features principales
- Extrait les contraintes et dépendances

### 2. Identification des Features
- Extrait features distinctes et cohésives
- Crée des noms clairs
- Organise par dépendances (si feature A dépend de B, A vient après B)

### 3. Numérotation
- Attribue numéros `001`, `002`, `003`, ...
- Crée répertoires `features/{number}-{name}/`

### 4. Génération des Spécifications
- **requirements.md** : Quoi ? (User stories, AC)
- **design.md** : Comment ? (Architecture, models, API)
- **plan.md** : Quand et dans quel ordre ? (Étapes, complexité)

### 5. Validation de Cohérence
- Vérifie que les spécifications sont cohérentes
- Vérifie que les dépendances sont correctes
- Vérifie que tout est actionnable pour `/project:generate`

### 6. Summary
- Liste les features créées
- Affiche la structure
- Confirme que c'est prêt pour `/project:generate`

---

## 🎯 Guidelines

### 1. Be Thorough but Concise
- Assez de détail pour implémenter
- Pas trop verbose
- Focus sur le "pourquoi" et le "quoi"

### 2. Make Specs Actionable
- Assez spécifiques pour qu'un dev puisse coder
- Pas ambiguës
- Pas manquer de détails critiques

### 3. Coherence Between Specs
- Les 3 fichiers doivent être cohérents
- design.md doit respecter requirements.md
- plan.md doit respecter design.md

### 4. Handle Dependencies Clearly
- Si feature A dépend de B : explicite
- Ordre de dépendances correct (B avant A)
- Les imports entre features vont fonctionner

### 5. State Assumptions
- Si quelque chose est ambigu : préciser
- Example : "Nous supposons que X sera fait avec Y"

---

## 🔄 Workflow

```
/project:setup
        ↓
/project:analyze "..."
        ↓
  features/001-*/ créé
  features/002-*/ créé
  features/003-*/ créé
        ↓
/project:generate 001-*
/project:generate 002-*
/project:generate 003-*
```

---

## ⚠️ Bonnes Pratiques

### 1. Descriptif Clair
Plutôt que :
> "Je veux une app cool avec gestion d'users"

Plutôt :
> "Je veux une app pour gérer une association :
> - Adhérents avec profil et statut
> - Événements avec inscriptions
> - Finances avec rapports
> - Authentification avec rôles"

### 2. Features Indépendantes
Chaque feature doit :
- Avoir une responsabilité unique
- Pouvoir être testée seule
- Pouvoir être intégrée progressivement

### 3. Dépendances Explicites
Si une feature dépend d'une autre :
```markdown
## Dependencies
- 001-member-management (pour accès aux adhérents)
- 002-authentication (pour vérifier rôles)
```

### 4. Non-Functional Requirements
Ne pas oublier :
- Performance (latence, throughput)
- Security (authentification, cryptage)
- Scalability (nombre d'utilisateurs)
- Compliance (RGPD, normes)

---

## 💡 Tips

### 1. Itération Si Besoin
Tu peux relancer `analyze` pour ajouter des features :
```bash
/project:analyze "Je veux aussi : gestion des rapports..."
```
Ça crée `004-reporting/` (en continuant la numérotation).

### 2. Relire les Spécifications
Après que `/project:analyze` a généré, relis les specs pour vérifier qu'elles sont bonnes. Si pas bon, tu peux modifier les fichiers .md directement.

### 3. Impliquer l'Équipe
Partage les spécifications avec ton équipe AVANT de générer le code. Ça permet de valider l'architecture.

### 4. Exporter les Specs
```bash
# Copier pour partager
cp -r features/ ../specs-review/

# Ou générer un PDF (outil externe)
```

---

## ❓ FAQ

**Q: Que faire si mon descriptif est trop vague ?**
R: La skill va faire de son mieux. Après, tu peux modifier les spécifications manuellement ou relancer avec plus de détails.

**Q: Combien de features max par projet ?**
R: Aucune limite technique. Pratiquement : 5-15 features c'est bien structuré. Plus de 20 = considère découper en sous-projets.

**Q: Peux-tu modifier les specs après génération ?**
R: Bien sûr ! Edite directement requirements.md, design.md, plan.md. Ou relance `/project:analyze` si tu veux ré-analyser.

**Q: Que faire si j'oublie une feature ?**
R: Relance `analyze` avec la feature manquante. La skill continuera la numérotation.

---

**Version:** 1.0  
**Prochaine étape:** `/project:generate {number}-{feature}`
