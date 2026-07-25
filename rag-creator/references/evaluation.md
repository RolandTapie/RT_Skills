# Protocole d'évaluation

Ne construire cette couche que si le projet a un vrai besoin de comparer rigoureusement des variantes (modèles, stratégies de retrieval, prompts) — pour un simple contrôle qualité ponctuel, un mode d'import de questions + notation par un unique évaluateur (section 4) suffit largement et évite la complexité des sections 1-3.

## 1. Protocole en 3 phases (comparaison rigoureuse)

Séparer la mesure en 3 phases indépendantes permet de réutiliser le travail d'une phase pour plusieurs comparaisons de la suivante, et de ne rejouer que ce qui a changé :

- **Phase 1 — Retrieval seul** : pour chaque question d'un jeu de test, exécuter uniquement les stages de retrieval (pas de génération), en réutilisant l'orchestrateur mais en s'arrêtant après fusion/reranking. Calculer recall/precision par comparaison avec un jeu de `chunk_id` attendus annotés à l'avance. Sérialiser les chunks récupérés pour réutilisation en phase 2.
- **Phase 2 — Génération** : pour chaque question × modèle candidat, reconstruire un prompt de génération à partir du contexte déjà figé en phase 1 (pas de nouveau retrieval — on isole ainsi la variable "modèle de génération"), noter la réponse produite.
- **Phase 3 — Comparaison contrôlée** : reprendre le modèle gagnant de la phase 2, et pour chaque question exécuter deux variantes de retrieval réelles (par exemple : vectoriel seul vs hybride lexical+vectoriel+graphe), générer et noter chaque variante, en conservant un identifiant de paire commun entre les deux variantes — indispensable pour un test statistique apparié (t-test apparié) plutôt qu'un test non apparié moins puissant.

Rendre chaque phase reprenable indépendamment (statut par phase en base, sauter les questions/paires déjà traitées) — un run de comparaison sur un jeu de test de taille réaliste peut prendre du temps et doit pouvoir être interrompu puis repris sans tout rejouer.

## 2. Double évaluateur pour limiter le biais d'un seul juge LLM

Un LLM unique utilisé comme juge de qualité a ses propres biais systématiques (préférence pour des réponses plus longues, biais de style). Faire noter chaque réponse par deux évaluateurs indépendants (idéalement de providers différents) et consolider :

```python
def _score_dual(question, expected, answer, evaluator_models):
    results = []
    for model in evaluator_models[:2]:
        try:
            results.append((model.id, _score_single(question, expected, answer, model)))
        except Exception:
            continue  # dégradation gracieuse : un évaluateur indisponible ne bloque pas la notation

    if len(results) < 2:
        return results[0][1] if results else _score_single(question, expected, answer, None)

    (model1, r1), (model2, r2) = results
    consensus = {}
    for key in r1["scores"]:
        v1, v2 = r1["scores"].get(key), r2["scores"].get(key)
        consensus[key] = round((v1 + v2) / 2, 4) if isinstance(v1, (int, float)) else v1
    consensus["_eval1"] = {"model": model1, "scores": r1["scores"]}
    consensus["_eval2"] = {"model": model2, "scores": r2["scores"]}
    consensus["_score_diff"] = round(abs(r1["scores"]["score_global"] - r2["scores"]["score_global"]), 4)
    return {"scores": consensus, "cost_usd": r1["cost_usd"] + r2["cost_usd"]}
```

`_score_diff` est un signal de désaccord entre les deux évaluateurs — comparé à un seuil configurable, il permet de flaguer automatiquement les réponses litigieuses qui méritent une revue humaine plutôt que de faire confiance aveuglément à une moyenne qui masquerait un désaccord fort. Toujours prévoir la dégradation gracieuse : si un évaluateur échoue (timeout, erreur API), retomber sur le score du seul évaluateur disponible plutôt que de faire échouer toute la ligne de résultat.

## 3. Système de jobs d'évaluation (si le protocole tourne en tâche de fond)

Réutiliser le même pattern que les jobs d'ingestion (`references/ingestion.md` §3) : une table de jobs comme source de vérité (statuts `pending/running/stop_requested/stopped/completed/failed`, phase courante, comptage par phase), un composant CRUD pur pour la table, un composant d'orchestration séparé qui gère la boucle asynchrone et les points de contrôle d'arrêt.

Point de conception à retenir : le "stop" doit être **coopératif et non préemptif** — vérifier un signal d'arrêt avant chaque unité de travail (chaque question, ou chaque paire question×modèle), jamais interrompre une question ou un appel LLM en plein milieu. Ça garde les résultats partiels cohérents (jamais de ligne à moitié notée) et rend la reprise triviale (on sait exactement où on s'est arrêté).

Isoler ces tables dans leur propre schéma si la base le permet, avec RLS activée et tous les accès directs (anon/authenticated) révoqués — l'accès doit passer exclusivement par le backend avec une clé de service, jamais interrogé en direct depuis le frontend, car les résultats d'évaluation peuvent contenir des réponses candidates non validées.

API minimale : créer un job, interroger son état (polling périodique côté frontend), demander l'arrêt, reprendre un job arrêté ou en échec, lister les résultats filtrables par phase. Toutes ces routes réservées aux administrateurs (`Depends(require_admin)`, voir `references/rbac-auth.md`).

## 4. Mode simple — import + évaluateur unique

Pour un contrôle qualité ponctuel sans protocole complet : importer un petit jeu de questions/réponses attendues (fichier CSV/Excel à deux colonnes), et pour chaque ligne appeler le pipeline RAG complet tel qu'un utilisateur réel l'utiliserait (pas de retrieval isolé), noter la réponse via un unique évaluateur LLM. Capturer les droits RBAC de l'administrateur qui soumet le job au moment de la soumission (pas un token vivant qui expirerait pendant l'exécution en tâche de fond) plutôt que de dépendre d'une session active pendant toute la durée du job.

C'est le point d'entrée à recommander en premier à un projet qui n'a pas encore de besoin avéré de comparaison rigoureuse multi-modèles — le protocole 3 phases se justifie seulement une fois qu'une vraie question de choix entre variantes se pose.

## Où aller ensuite

- L'orchestrateur réutilisé en boîte noire par les phases de retrieval/génération → `references/orchestrator.md`
- Protection des routes d'évaluation → `references/rbac-auth.md`
