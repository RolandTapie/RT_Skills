# Exemples & Cas d'Usage Pratiques

---

## 📌 Exemple 1: API Simple de Blog (Python)

### Descriptif Initial
```bash
/project:setup --stack python
```

```bash
/project:analyze "Je veux créer une API de blog simple avec:
- Gestion des articles (créer, lire, modifier, supprimer)
- Gestion des commentaires sur les articles
- Authentification utilisateur simple
- Listing articles avec pagination"
```

### Features Créées
```
features/
├── 001-article-management/
├── 002-comment-management/
├── 003-user-authentication/
└── 004-article-listing/
```

### Génération
```bash
/project:generate 001-article-management
# Génère: models, service, repository, api.py avec CRUD articles

/project:generate 002-comment-management
# Génère: dépend de 001 pour l'article_id

/project:generate 003-user-authentication
# Génère: users, JWT tokens

/project:generate 004-article-listing
# Génère: pagination, filtering
```

### Structure Finale (Centralisée)
```
src/
├── models/
│   ├── article.py (Article, ArticleCreate, ArticleUpdate)
│   ├── comment.py (Comment, CommentCreate)
│   └── user.py (User, UserCreate)
├── services/
│   ├── article_service.py (CRUD operations)
│   ├── comment_service.py
│   └── user_service.py (JWT, password hashing)
├── repositories/
│   ├── article_repository.py (database queries)
│   ├── comment_repository.py
│   └── user_repository.py
├── api/
│   ├── articles.py (GET /articles, POST /articles, etc.)
│   ├── comments.py
│   └── auth.py (authentication routes)
└── __init__.py

tests/
├── test_article_service.py
├── test_comment_service.py
├── test_user_service.py
└── test_article_listing.py
```

**Tout est centralisé :** modèles, services, repositories et API routes au même endroit !

### Main.py Final
```python
from fastapi import FastAPI
from src.api import articles, comments, auth

app = FastAPI()

# Routes importées depuis src/api/ centralisé
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(comments.router, prefix="/api/comments", tags=["comments"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Remarque:** Tous les routers viennent de `src/api/`, code complètement centralisé.

---

## 📌 Exemple 2: Dashboard React (React)

### Descriptif
```bash
/project:setup --stack react
```

```bash
/project:analyze "Dashboard pour gestion de tâches:
- Liste des tâches avec filtrage
- Créer/éditer/supprimer tâches
- Catégories de tâches
- Système de priorités
- Vue statistiques
- Authentification utilisateur"
```

### Features Créées
```
features/
├── 001-task-management/
├── 002-category-management/
├── 003-authentication/
├── 004-statistics-dashboard/
└── 005-ui-components/
```

### Génération
```bash
/project:generate 001-task-management
# Génère: TaskList.tsx, TaskForm.tsx, useTask hook

/project:generate 002-category-management
# Génère: CategorySelector component, useCategoryApi hook

/project:generate 003-authentication
# Génère: LoginForm, useAuth hook

/project:generate 004-statistics-dashboard
# Génère: Dashboard.tsx avec Chart.js

/project:generate 005-ui-components
# Génère: réutilisables Button, Card, Modal
```

### Structure
```
src/
├── 001_task_management/
│   ├── components/
│   │   ├── TaskList.tsx
│   │   ├── TaskForm.tsx
│   │   └── TaskDetail.tsx
│   ├── hooks/
│   │   └── useTask.ts
│   ├── services/
│   │   └── taskApi.ts
│   ├── types.ts
│   └── index.ts
├── 002_category_management/
│   └── (similar)
├── 003_authentication/
│   └── (similar + useAuth hook)
├── 004_statistics_dashboard/
│   └── Dashboard.tsx avec Chart.js
└── 005_ui_components/
    └── Button, Card, Modal, etc.

tests/
├── test_001_task_management.test.tsx
├── test_002_category_management.test.tsx
├── test_003_authentication.test.tsx
├── test_004_statistics_dashboard.test.tsx
└── test_005_ui_components.test.tsx
```

### App.tsx Final
```typescript
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { TaskDashboard } from './src/001_task_management/components/TaskList';
import { StatisticsDashboard } from './src/004_statistics_dashboard/Dashboard';
import { LoginPage } from './src/003_authentication/pages/LoginPage';
import { useAuth } from './src/003_authentication/hooks/useAuth';

function App() {
  const { user } = useAuth();
  
  if (!user) {
    return <LoginPage />;
  }
  
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/tasks" element={<TaskDashboard />} />
        <Route path="/stats" element={<StatisticsDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

---

## 📌 Exemple 3: Association Management (Complet - Python)

### Descriptif
Celui-ci a été généré plus tôt dans notre conversation (gestion d'association).

```bash
/project:analyze "Interface pour gestion d'association:
- Gestion adhérents
- Gestion événements
- Gestion finances
- Communication (newsletters, forum)
- Authentification
- Dashboard et analytics"
```

### 7 Features Générées
```
001-member-management
002-event-management
003-finance-management
004-communication
005-authentication
006-dashboard-ui
007-reporting-analytics
```

### Pattern de Génération
```bash
# Day 1
/project:generate 001-member-management

# Day 2-3
/project:generate 002-event-management
/project:generate 003-finance-management

# Day 4
/project:generate 004-communication
/project:generate 005-authentication

# Day 5
/project:generate 006-dashboard-ui
/project:generate 007-reporting-analytics
```

### Code Structure (Centralisée)
```
src/
├── models/
│   ├── member.py
│   ├── event.py
│   ├── finance.py
│   ├── user.py
│   └── ...
├── services/
│   ├── member_service.py
│   ├── event_service.py
│   ├── finance_service.py
│   └── ...
├── repositories/
│   ├── member_repository.py
│   ├── event_repository.py
│   ├── finance_repository.py
│   └── ...
├── api/
│   ├── members.py (routes /members)
│   ├── events.py (routes /events)
│   ├── finance.py (routes /finance)
│   ├── communication.py
│   └── auth.py
└── __init__.py

tests/
├── test_member_service.py
├── test_event_service.py
├── test_finance_service.py
├── test_communication_service.py
└── ...
```

**Tout au même endroit** : pas de dossiers séparés par feature !

---

## 🔄 Cas d'Usage: Ajouter une Feature à un Projet Existant

### Scenario
Tu as déjà 3 features générées (001, 002, 003) et tu veux ajouter une 4e.

### Étapes
```bash
# 1. Ajouter la nouvelle feature aux spécifications
/project:analyze "Je veux aussi ajouter: notifications par email..."

# Cela crée automatically: 004-email-notifications/

# 2. Générer le code pour la nouvelle feature
/project:generate 004-email-notifications

# 3. Intégrer dans main.py
# Ajouter l'import et le router
```

---

## 🔄 Cas d'Usage: Corriger une Feature

### Scenario
Après génération de feature 001, tu réalises qu'il manque un champ.

### Étapes
```bash
# 1. Editer les spécifications
# Modifier features/001-member-management/design.md
# Ajouter le nouveau champ aux Data Models

# 2. Régénérer la feature
/project:generate 001-member-management

# 3. Remercier Claude 🙏 car le code est complètement re-généré
```

---

## 📊 Comparaison: Sans Skills vs Avec Skills

### Sans Skills (Approche Traditionnelle)
```
Semaine 1: Réunion requirements
Semaine 2: Discussions sur l'architecture
Semaine 3: Commencer à coder
Semaine 4: Bugs découverts, architecture inadaptée
Semaine 5-6: Refactoring et corrections
```

### Avec Skills (Approche Structurée)
```
Jour 1: /project:setup + /project:analyze
        → Spécifications claires et approuvées
Jour 2: /project:generate 001
        → Code testé et intégré
Jour 3: /project:generate 002
        → Code testé et intégré
Jour 4: /project:generate 003
        → Code testé et intégré
Jour 5: Integration testing & déploiement
```

---

## 💡 Tips Pratiques

### Tip 1: Validate Specs Avant de Générer
Après `/project:analyze`, relis les specs avec ton équipe AVANT de générer le code.
```bash
# Partager les specs
cat features/001-feature-name/requirements.md
cat features/001-feature-name/design.md
# Feedback → corrections si besoin
```

### Tip 2: Générer Pendant les Réunions
Pendant que l'équipe discute de la feature suivante, tu peux générer la feature courante :
```bash
# Pendant la réunion sur feature 002
/project:generate 001-feature
# Après la réunion, code est prêt
```

### Tip 3: One Feature = One Commit
Après chaque `/project:generate` et test :
```bash
git add src/001-feature/ tests/test_001_*
git commit -m "feat(001): add feature implementation"
```

### Tip 4: Spécifications = Documentation
Les spécifications deviennent ta documentation du projet :
```bash
# Pour le wiki ou documentation
cp -r features/ ../docs/specifications/
```

### Tip 5: Itérer Rapidement
Si une feature n'est pas suffisante :
```bash
# Modifier la spec
vim features/001-feature/design.md

# Régénérer
/project:generate 001-feature

# Tester
pytest tests/test_001_*
```

---

## 🎯 Best Practices

### ✅ À Faire
- Générer une feature à la fois
- Tester immédiatement après génération
- Revoir les spécifications avant génération
- Documenter les dépendances inter-features
- Comitter régulièrement

### ❌ À Éviter
- Générer toutes les features en même temps
- Modifier les spécifications après génération sans régénérer
- Features avec responsabilités mixtes
- Dépendances circulaires entre features
- Ignorer les tests

---

## 📈 Scaling: Projet de 50 Features

### Stratégie
Pour un grand projet :

```bash
# Phase 1: Spécifications complètes
/project:analyze "Feature 1, 2, 3, ... 50..."
# Résultat: Toutes les 50 features ont leurs specs

# Phase 2: Features Foundationnelles
/project:generate 001-data-models
/project:generate 002-authentication
/project:generate 003-api-framework

# Phase 3: Features de Métier (en parallèle)
# Dev team A:
/project:generate 004-users
/project:generate 005-orders

# Dev team B:
/project:generate 006-payments
/project:generate 007-notifications

# Phase 4: Features Optionnelles
/project:generate 008-analytics
/project:generate 009-reporting
```

### Organisations
```
specs/
├── requirements/ (001-050.md)
├── designs/ (001-050.md)
└── plans/ (001-050.md)

dev/
├── team-a/
│   └── features-001-010/
├── team-b/
│   └── features-011-020/
└── team-c/
    └── features-021-050/
```

---

**Ces exemples montrent comment utiliser les skills dans différents contextes et à différentes échelles.**
