# Vue d'ensemble architecturale

## Le principe central : séparer ingestion (écriture) et requête (lecture)

Un système RAG a deux flux de données complètement indépendants, qui ne doivent jamais partager de code métier :

- **Ingestion** (asynchrone, par lot ou en flux, tolérante à la latence) : document brut → texte structuré → chunks → vecteurs stockés.
- **Requête** (synchrone du point de vue utilisateur, sensible à la latence) : question → chunks pertinents → réponse générée.

Les deux flux partagent uniquement deux choses : le modèle de données du chunk, et l'interface du vector store. Tout le reste (parsing de documents d'un côté, prompts de génération de l'autre) doit rester séparé — les mélanger rend les deux flux plus difficiles à faire évoluer indépendamment.

## Les stages du flux de requête

Le flux de requête se découpe naturellement en stages successifs, chacun avec une seule responsabilité. Un projet minimal peut n'en implémenter que 2-3 (validation → retrieval → génération) ; un projet en production bénéficie de les séparer davantage à mesure que les besoins apparaissent :

```
1. Validation / résolution utilisateur
   → qui pose la question, quels droits (RBAC), guard rapide (rate limit, session valide)

2. Chargement du contexte
   → mémoire conversationnelle, décision de cache sémantique (a-t-on déjà répondu à une question équivalente ?)

3. Garde-fou de sécurité (guardrail)
   → détection d'injection de prompt, de demandes hors-périmètre, de contenu à risque
   → RESPONSABILITÉ UNIQUE : ne fait QUE de la sécurité, ne reformule pas la question, ne décide pas du routage
     (voir "Pourquoi séparer guardrail/reformulation/routage" ci-dessous)

3a. Reconstruction de la question
   → résolution des ellipses / références au contexte conversationnel ("et l'an dernier ?" → question autonome)

3b. Routage / décomposition
   → une question complexe peut se décomposer en plusieurs sous-questions indépendantes,
     chacune éventuellement dirigée vers un sous-ensemble différent des sources documentaires

4-6. Retrieval, fusion, reranking
   → récupération hybride (recherche lexicale + recherche vectorielle + éventuellement graphe de connaissances)
     en parallèle par sous-question, fusion des résultats (ex. Reciprocal Rank Fusion), reranking optionnel

7. Synthèse
   → génération de la réponse finale à partir des contextes accumulés, typiquement streamée token par token
```

Numéroter les stages (même approximativement) donne un vocabulaire commun pour le monitoring, les logs et l'UI ("STAGE 3: guardrail a rejeté la question") — bien plus lisible en debug qu'un nom de fonction interne.

## Pourquoi séparer guardrail / reformulation / routage

Il est tentant de fusionner ces trois responsabilités dans un unique prompt LLM pour économiser un appel et de la latence. En pratique, un prompt qui doit simultanément juger la sécurité d'une question, la reformuler ET décider de son routage dégrade la fiabilité de chacune de ces trois tâches — un modèle occupé à vérifier une injection de prompt devient moins bon à décomposer la question, et inversement. Préférer trois stages courts et mono-responsabilité, parallélisables ou utilisant des modèles de tailles différentes (un petit modèle rapide suffit souvent pour le guardrail), plutôt qu'un stage monolithique.

## Le pattern d'état partagé

Plutôt que de faire circuler une dizaine de variables entre stages via des arguments de fonction qui s'accumulent, centraliser l'état de la requête en cours dans un seul objet (souvent appelé `RunState` ou équivalent) : requête initiale, résultats accumulés de chaque stage, utilisateur résolu, collecteur de métriques, émetteur d'événements temps réel. Chaque stage lit ce qu'il lui faut dans l'état et y écrit son résultat. Voir `references/orchestrator.md` pour le détail de ce pattern — c'est probablement la décision de structure la plus rentable de tout le projet : elle garde la fonction d'orchestration principale courte (une vingtaine de lignes) même avec 7 stages.

## Pattern transverse : Interface (abstraite) + Provider (factory/singleton)

Réapparaît à plusieurs endroits (vector store, base de données, index de recherche lexicale) : définir un contrat abstrait (`ABC` en Python, `interface` en TypeScript) puis exposer une unique fonction `get_xxx_instance()` qui construit (une fois, en singleton) l'implémentation concrète choisie par configuration. Ne jamais instancier une classe concrète ailleurs que dans cette fonction de construction. Bénéfices :
- changer de backend = changer une variable d'environnement, zéro modification du code appelant ;
- les tests peuvent injecter un faux provider sans toucher au code métier.

Piège à surveiller : si une nouvelle implémentation est ajoutée mais jamais branchée dans la factory de sélection, elle existe, compile, mais reste invisible/inatteignable en configuration — toujours vérifier ce câblage après avoir ajouté un backend.

## Deux axes d'isolation à ne pas confondre

- **Isolation technique** : les vecteurs de deux modèles d'embedding différents (ou de dimensions différentes) ne doivent jamais se mélanger dans la même recherche de similarité — géré via un espace de nommage technique (namespace Pinecone, colonne dédiée pgvector), dérivé automatiquement de la configuration d'embedding active.
- **Isolation métier (RBAC)** : quels documents/collections un utilisateur donné a le droit de voir — géré via un filtre sur les métadonnées, appliqué explicitement à chaque appel de retrieval, jamais supposé implicite.

Ce sont deux mécanismes de filtrage indépendants qui peuvent coexister sur le même vector store ; les fusionner dans un seul système rend l'un des deux invisible en cas de bug.

## Fire-and-forget pour tout ce qui n'est pas la réponse utilisateur

Toute opération de persistance qui n'est pas strictement nécessaire pour répondre à l'utilisateur (écrire en mémoire conversationnelle, indexer dans le cache sémantique, persister les métriques de monitoring) doit s'exécuter en tâche de fond (best-effort, avec log d'avertissement en cas d'échec) et ne jamais bloquer ni faire échouer la réponse. La latence perçue par l'utilisateur ne doit dépendre que du chemin critique : validation → retrieval → génération.

## Config-as-data pour les paramètres LLM

Plutôt que de coder en dur le modèle, le prompt système, la température ou le statut actif/inactif de chaque stage, stocker ces paramètres dans une table de configuration (une ligne par "couche" logique : guardrail, reconstruction, routeur, synthèse...). Permet de changer de modèle ou de désactiver un stage sans redéploiement, et donne un point d'accroche naturel pour le monitoring (associer chaque mesure de coût/latence à la ligne de config qui l'a produite). Un projet plus simple peut se contenter de variables d'environnement — ce pattern se justifie surtout à partir du moment où plusieurs stages LLM doivent être ajustés indépendamment en production sans redéploiement.

## Où aller ensuite

- Modèles de données du chunk et pipeline d'ingestion → `references/ingestion.md`
- Interface et implémentations du vector store → `references/vector-store.md`
- Détail de chaque stage, `RunState`, mémoire, cache, SSE, monitoring → `references/orchestrator.md`
- RBAC / authentification → `references/rbac-auth.md`
- Protocole d'évaluation → `references/evaluation.md`
- Frontend de chat → `references/frontend.md`
