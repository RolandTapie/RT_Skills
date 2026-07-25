# Pipeline d'ingestion

## 1. Découpage en étapes indépendantes

Découper l'ingestion en étapes séquentielles, chacune lisant/écrivant un statut persisté (pas un état en mémoire) permet de reprendre le traitement à n'importe quelle étape sans tout rejouer — précieux dès qu'un document volumineux échoue au milieu du pipeline. Étapes typiques, dans l'ordre :

```
A — Extraction       : document source (PDF, Office, HTML...) → texte/markdown brut + métadonnées
B — Restructuration   : texte brut → texte structuré avec repères de découpe explicites (optionnel, voir plus bas)
C — Chunking          : texte structuré → liste de chunks avec position hiérarchique
D — Embedding         : chunks → vecteurs, écrits dans le vector store
E — Graphe (optionnel): extraction d'entités/relations → graphe de connaissances
```

Chaque document en base porte un statut d'avancement (ex. `raw` → `restructured` → `chunked` → `embedded` → `graph_indexed`, avec des statuts d'erreur miroir `error_<étape>`). Une étape ne lit jamais la sortie en mémoire de l'étape précédente : elle relit l'état persisté correspondant à son statut d'entrée. Ça rend le pipeline redémarrable à froid à n'importe quelle étape, ce qui compte dès qu'on veut pouvoir relancer "juste le ré-embedding" après un changement de modèle sans re-parser tous les documents.

Le **scope** (quels documents traiter) doit être un paramètre explicite à chaque étape (`doc_ids: list[str] | None`, éventuellement `file_paths` pour l'étape d'extraction) — `None` doit systématiquement signifier "balayage complet du corpus" et être réservé à un usage de maintenance explicite, jamais déclenché implicitement par un upload ou une réingestion normale. C'est un garde-fou de sécurité simple qui évite de retraiter tout un corpus par accident.

### Le stage B (restructuration) est optionnel — ne le copier que si le besoin le justifie

Insérer une étape de restructuration (typiquement un passage LLM qui ajoute des repères explicites de découpe dans le texte, par exemple des marqueurs de début/fin de section) est utile quand les documents sources ont une structure implicite complexe (rapports longs, documentation à sections imbriquées) qu'un chunking naïf par taille de fenêtre casserait au mauvais endroit. Pour un corpus de documents courts et plats (FAQ, fiches produit), cette étape est un coût et une source de latence inutiles — un chunking direct sur le texte extrait (fenêtre glissante avec chevauchement, ou découpe par paragraphe) suffit. Ne présente jamais cette étape comme une convention universelle de RAG : c'est une option, à choisir selon la structure réelle des documents.

Si elle est retenue, le format d'échange entre restructuration et chunking (les repères de découpe) est une convention purement interne au projet — documente-la clairement en un seul endroit (ex. un module de constantes/regex partagé) plutôt que de la faire deviner implicitement au chunker.

### L'étape D (embedding) et l'étape E (graphe) méritent une interface formelle dès le départ

Contrairement aux étapes A-C, il est tentant de coder l'embedding et l'extraction de graphe comme des classes concrètes appelées directement — mais ça couple immédiatement le pipeline à un provider d'embedding ou un moteur de graphe précis. Définir une interface abstraite dès le début (même minimale, un seul provider derrière) évite une réécriture plus tard.

Le graphe de connaissances (étape E) est un bon candidat pour un **feature-flag à deux niveaux** : un flag global (activé/désactivé au niveau du déploiement — évite de payer le coût d'un moteur de graphe si personne n'en a besoin) et un flag par job (activé/désactivé au cas par cas selon le document ou la demande utilisateur). Si le vector store ou le moteur de graphe sous-jacent est indisponible à la construction du pipeline, dégrader proprement (composant optionnel désactivé, log d'avertissement) plutôt que de faire échouer toute la construction du pipeline.

## 2. Modèles de données du chunk

C'est la fondation partagée entre ingestion, vector store et affichage frontend des sources — à définir avant tout le reste (Pydantic pour Python, mais le principe est transposable à n'importe quel typage fort).

**Enums de base** : un statut de cycle de vie du chunk (`pending` / `embedded` / `indexed` / `error`), éventuellement une langue détectée, un type de contenu (texte/tableau/liste/code/mixte) — utile pour adapter l'affichage ou le prompt de génération selon le type de contenu retrouvé.

**Position hiérarchique** — le sous-modèle le plus important à bien penser dès le départ : un chunk doit porter assez d'information pour reconstruire sa position dans le document d'origine (fil d'Ariane / breadcrumb, profondeur, titre parent), pas seulement son contenu brut. Exemple de pattern (dérivation automatique via validateur, à partir d'un chemin de section format libre type `"Chapitre 1 > Section 2 > Sous-section 3"`) :

```python
@model_validator(mode="after")
def derive_sourcing_fields(self) -> "ChunkPosition":
    parts = [p.strip() for p in self.section_path.split(" > ") if p.strip()]
    self.path_parts = parts
    self.path_depth = len(parts)
    if self.parent_title is None and len(parts) >= 2:
        self.parent_title = parts[-2]
    self.breadcrumb = " › ".join(parts) if parts else self.title
    return self
```
Cette dérivation automatique (calculée une fois à la construction, jamais recalculée à la main ailleurs) évite l'incohérence entre plusieurs endroits du code qui recalculeraient différemment le même breadcrumb.

**Métadonnées de provenance** : identifiant du document source, nom/chemin de fichier, collection logique (pour le filtrage RBAC — voir `references/rbac-auth.md`), langue, type de source, date. Normaliser systématiquement les champs utilisés pour le filtrage (ex. mettre `collection` en minuscules à la validation) pour éviter des filtres RBAC qui échouent silencieusement sur une différence de casse.

**Statistiques de contenu** : longueur en caractères/mots, indicateurs de présence de tableau/code/liste/image — calculables automatiquement depuis le texte (factory `from_text()`), utiles pour le tuning du chunking et pour des heuristiques de retrieval (ex. prioriser les chunks tabulaires pour une question chiffrée).

**Modèle principal `Chunk`** :
- Identifiant unique généré à la construction (UUID), et un hash de contenu calculé (champ calculé, pas stocké séparément) pour permettre une déduplication rapide par contenu identique.
- Invariants métier posés en validateur plutôt que vérifiés manuellement à chaque usage : un chunk au statut `embedded`/`indexed` DOIT avoir un vecteur non vide ; un chunk au statut `error` DOIT avoir un message d'erreur. Poser ces règles comme validateurs Pydantic (ou équivalent) plutôt que comme conventions documentées évite qu'un chunk incohérent circule silencieusement dans le pipeline.
- Méthodes de transition immuables (retourner une copie modifiée plutôt que muter en place) : marquer comme embeddé, marquer comme indexé (en levant une erreur si l'état précédent n'est pas cohérent), marquer en erreur.

**`ChunkBatch`** : regroupement des chunks d'un même document (utile pour la persistance intermédiaire en fichier, et pour des statistiques agrégées par document : nombre de chunks, nombre en erreur). Si des convertisseurs sont écrits vers/depuis un format externe (le format attendu par le vector store, par exemple), les tester avec de vraies données avant de les considérer fiables — un piège classique est un convertisseur qui écrit le **nom** d'un champ comme valeur littérale au lieu de la valeur réelle (reliquat de code de développement jamais nettoyé, ex. `"embedding_dim": "1056"` en dur au lieu de la variable). Toujours relire ces convertisseurs ligne à ligne avant de les copier d'un projet à un autre.

## 3. Mécanisme de job d'ingestion (si volume/fréquence le justifient)

Pour de l'ingestion ponctuelle et peu fréquente (quelques documents à la fois), un script synchrone suffit — ne pas construire de système de jobs pour ce cas. Le mécanisme ci-dessous se justifie dès qu'il faut : ingérer en tâche de fond sans bloquer une requête HTTP, permettre l'annulation, ou supporter plusieurs workers.

**Table de jobs comme source de vérité unique** — pas de registre en mémoire dans le process API (perdu au redémarrage, invisible d'un autre worker) :
```sql
CREATE TABLE ingestion_jobs (
    job_id TEXT UNIQUE NOT NULL,
    kind   TEXT NOT NULL,                          -- ex: upload, reingest, batch, reconcile
    status TEXT NOT NULL DEFAULT 'queued',          -- queued, running, stop_requested, stopped, completed, failed
    current_stage TEXT,
    scope_doc_ids JSONB, scope_file_names JSONB,    -- scope explicite, jamais implicite
    pid INTEGER,                                     -- PID du process qui exécute le job, pour l'annulation
    started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ,
    error_message TEXT, params JSONB
);
```

**Isoler le travail lourd dans un process séparé** de l'API si le pipeline utilise des bibliothèques gourmandes en mémoire (parsing de documents avec des modèles ML embarqués, par exemple) — exécuter ce travail dans le process API partagé peut provoquer des erreurs mémoire cumulatives au fil des jobs (la mémoire n'est jamais rendue à l'OS tant que le process vit). Un process frais par job, qui se termine et rend sa mémoire à l'OS, est un pattern robuste même s'il coûte un peu de latence de démarrage.

Point d'attention plateforme : sous Windows, si le serveur web tourne avec un rechargement à chaud (auto-reload), la boucle d'événements asyncio peut ne pas supporter la création de subprocess asynchrone — préférer un lancement de process synchrone classique (`subprocess.Popen`) à un équivalent asyncio si le projet doit tourner sous Windows en développement.

**Annulation** : passer le statut à `stop_requested` en base, puis envoyer un signal de terminaison au PID stocké (une bibliothèque portable process comme `psutil` évite les différences Windows/Unix). Le process qui exécute le job doit détecter dans son bloc de nettoyage final (`finally` ou équivalent) que l'arrêt a été demandé et écrire le statut `stopped` plutôt que `failed`.

**Concurrence multi-worker** : si plusieurs workers API peuvent recevoir des requêtes de lancement de job, un simple verrou en mémoire process ne suffit pas — utiliser un mécanisme atomique côté base (ex. une fonction SQL de type compare-and-swap sur un compteur de slots utilisés) pour éviter de dépasser un nombre maximal de jobs concurrents.

**Réconciliation au démarrage** : au lancement du serveur, tout job resté `running`/`stop_requested` dont le PID stocké n'existe plus doit être marqué `failed` (le process a été tué avec l'ancien serveur, sans passer par le nettoyage normal), et les documents dans son scope au statut intermédiaire doivent être requalifiés en erreur explicite plutôt que laissés dans un état ambigu. Sans cette réconciliation, un redémarrage serveur laisse des jobs éternellement "en cours" en base.

**Diagnostic d'échec** : si le worker et l'API communiquent uniquement via un fichier de log (pas de canal structuré), le diagnostic de la cause d'échec devra parser le texte du log a posteriori — fonctionnel mais fragile ; si un canal structuré (queue, callback HTTP) est possible dans le projet cible, il est préférable.

**Best-effort systématique pour tout ce qui n'est pas le cœur du job** : mise à jour du stage courant pour l'affichage, rechargement d'un index secondaire, résolution d'entités incrémentale — envelopper chacune de ces opérations annexes dans un `try/except` avec log d'avertissement explicite "non bloquant", jamais laisser une de ces opérations annexes faire échouer le job entier.

## Où aller ensuite

- Interface et implémentations du vector store qui reçoit les chunks embeddés → `references/vector-store.md`
- Comment le retrieval applique le filtrage RBAC sur les collections → `references/rbac-auth.md`
