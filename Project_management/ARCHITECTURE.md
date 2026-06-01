# Architecture - Comment les Skills Fonctionnent Ensemble

---

## 🏗️ Vue d'Ensemble Architecturale

Les 3 skills forment un pipeline séquenciel :

```
┌─────────────────────────────────────────────────────────────┐
│                    PROJECT SETUP PHASE                      │
│  /project:setup --stack python                              │
│  ├─ Crée project.toml (stack config)                        │
│  ├─ Crée pyproject.toml ou package.json                     │
│  └─ Crée répertoires src/, tests/, features/                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  ANALYSIS PHASE                              │
│  /project:analyze "Description du projet..."                │
│  ├─ Parse descriptif                                         │
│  ├─ Identifie features                                       │
│  ├─ Numérote: 001-, 002-, 003-, ...                          │
│  └─ Génère specs (requirements, design, plan)               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 GENERATION PHASE                             │
│  /project:generate 001-feature                              │
│  /project:generate 002-feature                              │
│  /project:generate 003-feature                              │
│  ├─ Lit les spécifications                                   │
│  ├─ Génère code (models, service, api)                      │
│  ├─ Génère tests (pytest, React Testing)                    │
│  └─ Code est prêt à utiliser                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow

### Setup → Analyze
```
project.toml (stack config)
        ↓
/project:analyze lit project.toml pour confirmer le stack
        ↓
Génère specs cohérentes avec le stack (Python vs React)
```

### Analyze → Generate
```
features/
├── 001-feature-name/
│   ├── requirements.md  ─┐
│   ├── design.md        ├─→ /project:generate lit ces 3 fichiers
│   └── plan.md          ┘
        ↓
Génère code selon le contenu des specs
```

### Generate → Code
```
Spec: "API endpoints: GET /users, POST /users"
        ↓
/project:generate créé api.py avec:
    @router.get("/users")
    @router.post("/users")
```

---

## 🔢 Numérotation Sequentielle

La numérotation est **centralisée** dans le répertoire `features/` :

```
features/
├── 001-first/
├── 002-second/
└── 003-third/
```

### Comment ça Marche

1. **Setup** ne touche pas à la numérotation
2. **Analyze** regarde `features/` pour voir le plus haut numéro
3. **Analyze** continue de là (001 → 002 → 003 → ...)
4. **Generate** lit simplement le numéro du répertoire

### Implication
Si tu relances `/project:analyze` :
```bash
# Première fois
/project:analyze "Feature 1, Feature 2, Feature 3"
# Crée: 001-, 002-, 003-

# Si tu ajoutes plus tard
/project:analyze "Feature 4, Feature 5"
# Crée: 004-, 005- (continue de 003)
```

---

## 🔄 Dependencies Entre Features

### Dans les Specs
```markdown
# design.md
## External Dependencies
- 001-member-management (pour accès aux users)
- 002-authentication (pour vérifier les rôles)
```

### Dans le Code Généré
```python
# 003-feature-dependent/service.py
from src.001_member_management import MemberService
from src.002_authentication import AuthService

class MyService:
    def __init__(self, member_svc: MemberService, auth_svc: AuthService):
        self.member_svc = member_svc
        self.auth_svc = auth_svc
```

### Implication
- Générer dans le bon ordre (001 avant 002 avant 003)
- Les imports automatiques fonctionnent si ordre respecté
- Dépendances sont **explicites** dans les specs

---

## 📁 Structure de Répertoires Finale

```
mon-projet/
│
├── project.toml                    ← Config (créé par setup)
├── pyproject.toml ou package.json  ← Stack config (créé par setup)
│
├── features/                       ← Spécifications (créé par analyze)
│   ├── 001-member-management/
│   │   ├── requirements.md
│   │   ├── design.md
│   │   └── plan.md
│   ├── 002-event-management/
│   │   ├── requirements.md
│   │   ├── design.md
│   │   └── plan.md
│   └── ...
│
├── src/                            ← Code CENTRALISÉ (créé par generate)
│   ├── models/                     # Tous les modèles (member, event, etc.)
│   │   ├── __init__.py
│   │   ├── member.py
│   │   ├── event.py
│   │   └── finance.py
│   ├── services/                   # Tous les services métier
│   │   ├── __init__.py
│   │   ├── member_service.py
│   │   ├── event_service.py
│   │   └── finance_service.py
│   ├── repositories/               # Tous les repositories
│   │   ├── __init__.py
│   │   ├── member_repository.py
│   │   └── event_repository.py
│   ├── api/                        # Toutes les routes
│   │   ├── __init__.py
│   │   ├── members.py
│   │   ├── events.py
│   │   └── finance.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py
│   └── __init__.py
│
└── tests/                          ← Tests (créé par generate)
    ├── test_member_service.py
    ├── test_event_service.py
    └── test_finance_service.py
```

**Points clés:**
- `features/` = Spécifications **par feature**
- `src/` = Code **CENTRALISÉ et PARTAGÉ** pour TOUTES les features
- `src/` est structuré par **type** (models/, services/, etc.), pas par feature
- Tests au niveau racine `tests/`, regroupés par domaine (test_member_*, test_event_*, etc.)

---

## 🎯 Responsabilités de Chaque Skill

### `/project:setup`
**Responsabilité:** Initialiser la structure
- ✅ Crée project.toml
- ✅ Crée config du stack
- ✅ Crée répertoires de base
- ❌ Ne génère pas de code
- ❌ Ne crée pas de spécifications

### `/project:analyze`
**Responsabilité:** Analyser et spécifier
- ✅ Lit le descriptif utilisateur
- ✅ Identifie features
- ✅ Crée spécifications
- ✅ Numérote séquentiellement
- ✅ Valide cohérence
- ❌ Ne génère pas de code
- ❌ Ne modifie pas project.toml

### `/project:generate`
**Responsabilité:** Générer le code
- ✅ Lit les spécifications
- ✅ Génère code complet
- ✅ Génère tests
- ✅ Inclut type hints et docstrings
- ❌ Ne modifie pas les spécifications
- ❌ Ne touche pas project.toml

---

## 🔐 Invariants du Système

### 1. project.toml est Immutable
Une fois créé, `project.toml` n'est pas modifié par les skills.
```toml
[project]
stack = "python"  # défini par setup, jamais changé
```

### 2. features/ est Toujours à Jour
Chaque feature a TOUJOURS ses 3 spécifications :
- ✅ requirements.md
- ✅ design.md
- ✅ plan.md

### 3. Code Correspond aux Specs
Le code généré correspond **exactement** aux spécifications :
- Modèles de données = ce qui est dans design.md
- Routes API = ce qui est dans design.md
- Tests = basés sur plan.md et requirements.md

### 4. Numérotation Continue
Les numéros montent toujours : 001, 002, 003, ... sans gaps.

---

## 🔄 Cycles d'Itération

### Cycle 1: Initial
```
/project:setup
/project:analyze
→ Spécifications générées
```

### Cycle 2: Code Generation
```
/project:generate 001-feature
/project:generate 002-feature
/project:generate 003-feature
→ Code généré pour toutes les features
```

### Cycle 3: Refinement (Optionnel)
```
Modifier features/XXX-feature/requirements.md
/project:generate XXX-feature
→ Code re-généré avec modifications
```

### Cycle 4: Integration & Testing
```
Tests, debug, modifications du code
→ Intégration avec le reste du projet
```

---

## ⚡ Performance Considerations

### Setup
- **Temps**: < 1 seconde
- **Opérations**: File création/listing
- **Bottleneck**: Système de fichiers

### Analyze
- **Temps**: 30 secondes - 2 minutes
- **Opérations**: Claude API call, parsing, écriture fichiers
- **Bottleneck**: Claude API latency

### Generate
- **Temps**: 5-30 minutes par feature
- **Opérations**: Claude API call, code generation, écriture fichiers
- **Bottleneck**: Claude API latency, complexité feature
- **Parallélizable**: ❌ Non (une à la fois)

---

## 🛡️ Error Handling & Recovery

### Setup Fails
```
Erreur possible: Répertoire existant non accessible
Récupération: Vérifier permissions ou déplacer ailleurs
```

### Analyze Fails
```
Erreur possible: Description trop vague, identificiation features impossible
Récupération: Relancer avec description plus claire/détaillée
```

### Generate Fails
```
Erreur possible: Spécifications incohérentes, missing fields
Récupération: Corriger specs, relancer generate
```

### Specs Incohérentes
```
Erreur possible: design.md ne match pas requirements.md
Détection: Validate avant generate
Récupération: Éditer specs, relancer generate
```

---

## 🔗 Integration avec l'Écosystème

### Dépendances Externes
Chaque feature peut avoir des dépendances externes :
```markdown
# design.md
## External Dependencies
- fastapi
- sqlalchemy
- pydantic
```

→ À installer manuellement :
```bash
uv pip install fastapi sqlalchemy pydantic
```

### Entre Features
Features peuvent dépendre d'autres features:
```python
# feature-003 dépend de feature-001
from src.001_member_management import MemberService
```

→ Genéré automatiquement par generate

### Avec le Reste du Projet
Code généré est "top-level" :
```python
# Dans main.py
from src.001_member_management.api import router as members_router
from src.002_event_management.api import router as events_router

app.include_router(members_router)
app.include_router(events_router)
```

---

## 📈 Scalability

### Nombre de Features
- **Small** (1-5): Très facile
- **Medium** (5-15): Facile, structure claire
- **Large** (15-50): Possible, mais considère sous-projets
- **Very Large** (50+): ❌ Considère découper en plusieurs projets

### Taille du Code par Feature
- **Small** (100-300 LOC): 5-10 minutes
- **Medium** (300-1000 LOC): 15-25 minutes
- **Large** (1000+ LOC): 30+ minutes

### Dépendances Entre Features
- **Linear** (001→002→003): Pas de problème
- **Complex** (beaucoup de croisements): ⚠️ Document clairement
- **Circular** (A→B→A): ❌ À éviter, restructurer

---

**Ce document décrit comment les skills interagissent et maintiennent l'intégrité du système.**
