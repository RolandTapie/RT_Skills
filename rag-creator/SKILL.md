---
name: rag-creator
description: Scaffolde un système RAG (Retrieval-Augmented Generation) de production complet — ingestion documentaire multi-étapes, vector store interchangeable, orchestrateur multi-stages (mémoire, cache sémantique), RBAC, monitoring, évaluation, frontend de chat streamé. Utilise ce skill dès que l'utilisateur veut créer, scaffolder, démarrer ou architecturer un RAG, un chatbot documentaire, un assistant sur base documentaire interne, un Q&A sur documents, ou toute app "retrieval + LLM" — même sans dire "RAG" explicitement (ex. "interroger nos PDF en langage naturel", "chatbot qui répond depuis notre base de connaissances"). Utilise-le aussi pour étendre un RAG existant (RBAC, monitoring, cache, évaluation, ingestion) ou choisir entre options d'architecture (Pinecone vs pgvector, avec/sans graphe de connaissances).
---

# rag-creator

Ce skill capture l'architecture d'un système RAG de production ayant tourné en réel (pipeline d'ingestion, orchestrateur 7 stages, RBAC, monitoring, évaluation, frontend). Il ne fournit pas un unique gabarit rigide : c'est un **ensemble de patterns éprouvés**, avec leurs raisons d'être et leurs pièges connus, à assembler selon les besoins du projet cible. Le code réel qu'un projet neuf doit produire dépend de sa stack et de son périmètre — génère-le à la volée en t'appuyant sur les références et les squelettes fournis, ne copie jamais aveuglément.

## Pourquoi ces patterns et pas d'autres

Un RAG naïf (embed → similarity search → prompt) fonctionne en démo et s'effondre en production : pas d'isolation multi-tenant, pas de mémoire conversationnelle propre, pas de visibilité sur les coûts/latences, pas de moyen de savoir si une réponse s'est dégradée après un changement de prompt. Les patterns ci-dessous existent pour répondre à des problèmes concrets rencontrés en exploitation réelle — chaque référence explique le *pourquoi*, pas seulement le *quoi*, pour que tu puisses juger quand t'en écarter.

## Étape 1 — Interview de cadrage

Avant d'écrire la moindre ligne de code, détermine avec l'utilisateur :

1. **Nouveau projet ou extension d'un projet existant ?** Si extension, explore d'abord le code existant (structure, stack, conventions) avant de proposer quoi que ce soit — n'impose jamais les choix ci-dessous sur une base qui a déjà fait d'autres choix cohérents.
2. **Nature des documents sources** : PDF/Office/HTML/Markdown ? Documents scannés (OCR) ? Volume approximatif et fréquence d'ingestion (ponctuel vs flux continu) ? → conditionne le besoin d'un vrai pipeline de job (stage 2 ci-dessous) vs un simple script.
3. **Multi-utilisateurs avec droits différenciés ?** Si tous les utilisateurs voient tout, le RBAC (couche 4) peut être omis ou réduit à l'authentification simple.
4. **Besoin de suivre coûts/latences/qualité en production ?** Si c'est un prototype interne à un seul utilisateur, le monitoring (couche 5) et l'évaluation (couche 6) sont probablement du sur-engineering — dis-le à l'utilisateur plutôt que de les imposer.
5. **Conversation multi-tours avec mémoire, ou question-réponse sans état ?** Conditionne la mémoire conversationnelle et la résolution d'ellipses (dans la couche 3).
6. **Stack technique** : par défaut, ce skill propose Python/FastAPI (backend) + React/TypeScript (frontend), un vector store parmi Pinecone (managé, simple à démarrer) ou Postgres/pgvector (si Supabase/Postgres déjà dans la stack, coût réduit, contrôle total du schéma), et Supabase Auth pour le RBAC si Supabase est déjà choisi. Mais rien n'est figé : si l'utilisateur a déjà une stack (Node/Express, Django, un autre vector store, un autre provider d'auth), adapte les *patterns* décrits dans les références à cette stack plutôt que d'imposer la stack par défaut.
7. **Fournisseur LLM** (OpenAI, Anthropic, Azure OpenAI, modèle local...) et si un besoin de bascule à chaud entre plusieurs modèles existe (→ pattern "config-as-data" décrit dans `references/orchestrator.md`).

Pose ces questions via l'outil de clarification si le contexte ne les rend pas évidentes — ne pars pas sur des hypothèses lourdes de conséquences (ex. choix du vector store, présence de RBAC) sans confirmation.

## Étape 2 — Les 6 couches, et quand les inclure

Lis `references/architecture-overview.md` en premier : il pose le vocabulaire commun (les 7 stages du pipeline de requête, le flux de données entre couches) réutilisé par toutes les autres références. Ensuite, charge uniquement les références pertinentes pour ce projet :

| Couche | Référence | Toujours nécessaire ? |
|---|---|---|
| Ingestion documentaire | `references/ingestion.md` | Oui, dès qu'il y a des documents à indexer (même un seul script d'ingestion a besoin des modèles Chunk et des invariants décrits) |
| Vector store | `references/vector-store.md` | Oui — c'est le cœur du "R" de RAG |
| Orchestrateur de requête | `references/orchestrator.md` | Oui — même une version minimale (2-3 stages) bénéficie du pattern d'état partagé (`RunState`) et du découplage guardrail/retrieval/génération |
| RBAC / Auth | `references/rbac-auth.md` | Seulement si multi-utilisateurs avec droits différenciés ou juste besoin d'authentification |
| Monitoring / Observabilité | `references/orchestrator.md` (section dédiée) | Seulement si suivi de production nécessaire |
| Évaluation | `references/evaluation.md` | Seulement si le projet doit comparer des variantes (modèles, prompts, stratégies de retrieval) de façon rigoureuse |
| Frontend | `references/frontend.md` | Seulement si une UI de chat est demandée (sinon une API suffit) |

Ne charge pas une référence "au cas où" — chaque fichier est écrit pour être lu en entier une fois consulté, mieux vaut ne consulter que ce qui sert.

## Étape 3 — Ordre de construction recommandé

L'ordre suivant minimise les reprises (chaque étape s'appuie sur des invariants posés par la précédente) :

1. **Modèles de données du chunk** (`references/ingestion.md` §2) — poser `Chunk`/`ChunkPosition` avant tout le reste, tout en dépend (ingestion, vector store, retrieval, affichage frontend des sources).
2. **Interface du vector store** (`references/vector-store.md` §1) — définir le contrat abstrait avant de choisir une implémentation concrète ; permet de changer de backend sans toucher à l'orchestrateur.
3. **Pipeline d'ingestion** (`references/ingestion.md`) — extraction → chunking → embedding, avec le mécanisme de job si le volume/la fréquence le justifie.
4. **Orchestrateur de requête** (`references/orchestrator.md`) — stages de retrieval + génération, en commençant volontairement minimal (retrieve + synthesize) avant d'ajouter guardrails/router/mémoire/cache si le cadrage les justifie.
5. **RBAC** (`references/rbac-auth.md`), si retenu — brancher tôt, car le filtrage par droits doit traverser retrieval ET affichage, pas être ajouté après coup en surface.
6. **Monitoring**, si retenu — s'accroche aux points d'entrée/sortie de chaque stage de l'orchestrateur déjà posé à l'étape 4.
7. **Frontend** (`references/frontend.md`), si retenu — consomme le contrat SSE et les endpoints posés aux étapes précédentes.
8. **Évaluation** (`references/evaluation.md`), si retenu — vient en dernier, elle réutilise l'orchestrateur en boîte noire.

## Étape 4 — Utiliser les squelettes de `assets/`

`assets/backend/` et `assets/frontend/` contiennent des fichiers de code minimaux mais fonctionnels (pas des placeholders vides) illustrant les interfaces et patterns les plus structurants : interface vector store, modèles Chunk, `RunState`, dépendances FastAPI RBAC, migration SQL de base, store Zustand + parsing SSE, contrat de types partagé frontend/backend. Ce sont des points de départ génériques à copier puis adapter — jamais du code propriétaire d'un projet existant, et jamais à coller tel quel sans relire (adapte les noms de tables, les champs métier, les imports au projet cible). Chaque fichier commence par un commentaire d'en-tête expliquant ce qu'il faut adapter.

## Anti-patterns à ne pas reproduire

Ces pièges ont été rencontrés en conditions réelles — les références détaillées les rappellent au bon endroit, mais les voici en un coup d'œil :

- **Deux tables qui se recouvrent pour le même concept** (ex. un profil utilisateur "officiel" + une table legacy parallèle avec sa propre notion de droits). Une seule source de vérité par concept, quitte à migrer l'historique.
- **Générer un identifiant/timestamp et se contenter du nom du champ comme valeur** (copier-coller de dev jamais nettoyé). Toujours vérifier qu'un convertisseur écrit la valeur réelle, pas une chaîne littérale portant le nom du champ.
- **RLS activée mais avec policy `USING (true)`** en pensant que ça sécurise quelque chose : si l'API accède via une clé de service qui bypass RLS de toute façon, la sécurité réelle repose entièrement sur les dépendances d'auth côté API — dis-le explicitement dans le code et la doc, ne laisse pas croire que RLS protège.
- **Persister un tour de conversation en échec** (guardrail rejeté, exception) dans la mémoire conversationnelle : ça empoisonne les tours suivants qui s'appuient sur cet historique. Ne persister que les tours réussis.
- **Implémenter une nouvelle interface (ex. un nouveau backend vector store) sans l'enregistrer dans la factory de sélection** : le code existe, compile, mais n'est jamais atteignable en configuration — vérifier systématiquement le point de câblage après avoir ajouté une implémentation.
- **Dupliquer la même logique de mapping/style à 3 endroits du frontend** (ex. badge de source de chunk répété dans 3 composants) : extraire un seul module partagé dès le deuxième usage.
- **Fusionner guardrail de sécurité et reformulation/routage dans un seul prompt** pour "économiser un appel LLM" : un prompt à trop de responsabilités dégrade silencieusement la fiabilité de chacune ; préférer un stage = une responsabilité, quitte à paralléliser pour limiter la latence.
- **Confondre isolation technique (namespace par dimension/modèle d'embedding) et isolation métier RBAC (collection/tenant autorisés)** : ce sont deux axes orthogonaux, ne pas les fusionner dans un seul mécanisme de filtrage.

## Après le scaffolding

Une fois le projet généré, relis la checklist ci-dessous avec l'utilisateur avant de considérer la tâche terminée :

- [ ] Les secrets (clés API, service key) sont en variables d'environnement, jamais commit, avec un `.env.example` sans valeurs réelles
- [ ] Chaque route qui doit être protégée porte explicitement sa dépendance d'auth (pas de middleware global silencieux dont on pourrait croire qu'il protège tout)
- [ ] Le filtrage RBAC est appliqué au retrieval (pas seulement à l'affichage)
- [ ] Une réponse en échec (erreur, guardrail rejeté) n'est jamais persistée dans la mémoire conversationnelle
- [ ] Le choix de vector store/LLM est piloté par configuration (env ou base), pas en dur dans le code
- [ ] Si le frontend consomme du SSE, le contrat d'événements est un type partagé documenté, pas un dict libre

Propose de committer par petites étapes cohérentes (modèles → vector store → ingestion → orchestrateur → RBAC → frontend) plutôt qu'un unique gros commit, pour garder chaque étape testable indépendamment.
