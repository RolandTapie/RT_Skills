# Couche vector store

## 1. Poser l'interface abstraite avant le choix d'un backend

Définir un contrat unique que l'orchestrateur et le pipeline d'ingestion utilisent, indépendamment du backend réel. Un contrat large mais couvrant les besoins réels des deux flux (écriture depuis l'ingestion, lecture depuis le retrieval) :

```python
class IVectorStore(ABC):
    @abstractmethod
    def set_embedding_model(self, embedding_model) -> None: ...
    # Doit être appelée après construction, avant tout usage — poser un assert/RuntimeError
    # explicite dans chaque implémentation si ce n'est pas fait, plutôt que de laisser planter
    # plus loin avec une erreur obscure.

    @abstractmethod
    def add_documents(self, documents: list, ids: list[str] | None = None) -> list[str]: ...
    @abstractmethod
    def upsert_documents(self, documents: list, ids: list[str]) -> list[str]: ...
    @abstractmethod
    def delete_documents(self, ids: list[str]) -> bool: ...

    @abstractmethod
    def similarity_search(self, query: str, k: int = 5, namespace: str | None = None,
                            filter: dict | None = None) -> list: ...
    @abstractmethod
    def similarity_search_with_score(self, query: str, k: int = 5,
                                       namespace: str | None = None, filter: dict | None = None) -> list: ...
    @abstractmethod
    def similarity_search_by_vector(self, embedding: list[float], k: int = 5,
                                      filter: dict | None = None) -> list: ...

    @abstractmethod
    def count(self) -> int: ...
    @abstractmethod
    def health_check(self) -> bool: ...
    @abstractmethod
    def list_all_documents(self, allowed_collections: list[str] | None = None) -> list: ...
    # Dump complet, typiquement pour reconstruire un index secondaire (ex. lexical BM25) au démarrage.
```

Une version async de la recherche par similarité est utile si le client d'embedding utilisé a un mode async natif — sinon un simple wrapper synchrone suffit. Ne pas ajouter de méthode "au cas où" : chaque méthode de l'interface doit avoir un appelant réel identifié dans l'orchestrateur ou le pipeline d'ingestion.

**Décision d'implantation à trancher dès le départ** : où vit le fichier d'interface ? Le placer directement dans le module qui contient les implémentations concrètes (`vector_store/interfaces/`) plutôt que dans un autre module (ex. le module d'ingestion) même si l'ingestion en dépend aussi — sinon un développeur cherchant l'interface "vector store" dans le module vector store ne la trouvera pas, et devra deviner qu'elle a été définie ailleurs pour des raisons historiques.

## 2. Choisir un backend : Pinecone vs Postgres/pgvector

| Critère | Pinecone (managé) | Postgres/pgvector |
|---|---|---|
| Mise en route | Très rapide, aucune infra à gérer | Nécessite une extension `vector` activée, migration SQL |
| Coût | Facturation dédiée au vector store | Marginal si Postgres déjà utilisé pour le reste de l'app |
| Contrôle du schéma | Limité (namespaces, metadata JSON) | Total (index HNSW/IVFFlat configurables, jointures SQL possibles) |
| Filtrage par métadonnées | Syntaxe propriétaire (`$in`, `$eq`...) | SQL natif, filtrable/joignable comme n'importe quelle table |
| Cohérence transactionnelle avec le reste des données | Non (store séparé) | Oui si même instance Postgres |

Recommandation par défaut : si le projet a déjà Postgres/Supabase pour l'auth ou les données métier, pgvector évite un service supplémentaire à opérer et permet des jointures SQL utiles pour le RBAC. Si aucune base relationnelle n'est prévue par ailleurs, Pinecone démarre plus vite.

### Implémentation Pinecone — points d'attention

- Chaque instance cible un namespace par défaut, mais les méthodes de lecture acceptent un paramètre `namespace` optionnel pour cibler ponctuellement un autre namespace (utile pour un cache sémantique séparé du contenu documentaire, voir `references/orchestrator.md`).
- **Convention à documenter explicitement** : Pinecone ne stocke pas nativement le texte d'un chunk, seulement des vecteurs + métadonnées JSON. Convention à adopter : stocker le texte du chunk directement dans les métadonnées (`metadata["text"] = chunk_text`), sinon impossible de reconstruire le contenu pour un dump complet ou une recherche qui a besoin du texte en retour.
- `upsert` est nativement idempotent par id chez Pinecone — pas besoin de déduplication applicative supplémentaire, à condition que l'id soit stable entre deux ingestions du même chunk.
- Lister l'intégralité d'un index n'est en général pas exposé directement par le SDK — prévoir un parcours par lot (list + fetch par batch) plutôt que de chercher une méthode "list all" qui n'existe pas forcément.

### Implémentation Postgres/pgvector — points d'attention

Schéma minimal, dans un schéma Postgres dédié pour bien séparer les préoccupations :

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS vecteurs;

CREATE TABLE vecteurs.chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content     TEXT NOT NULL,
    metadata    JSONB NOT NULL DEFAULT '{}',
    namespace   TEXT NOT NULL DEFAULT '',
    embedding   vector(1536),                        -- adapter la dimension au modèle d'embedding choisi
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ON vecteurs.chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX ON vecteurs.chunks (namespace);
CREATE INDEX ON vecteurs.chunks USING gin (metadata);

ALTER TABLE vecteurs.chunks ENABLE ROW LEVEL SECURITY;
-- Ce schéma n'est volontairement pas exposé via l'API REST auto-générée (PostgREST/Supabase) :
-- l'accès en lecture passe exclusivement par la fonction RPC ci-dessous.
CREATE POLICY service_role_all ON vecteurs.chunks FOR ALL TO service_role USING (true) WITH CHECK (true);
```

Si la couche API du projet utilise une API REST auto-générée depuis le schéma Postgres (type PostgREST/Supabase), le point d'accès en lecture doit passer par une fonction RPC dédiée plutôt que par une lecture directe de la table :

```sql
CREATE OR REPLACE FUNCTION public.match_chunks(
    query_embedding   vector(1536),
    match_count       INT DEFAULT 5,
    namespace_filter  TEXT DEFAULT '',
    collection_filter TEXT[] DEFAULT '{}'
)
RETURNS TABLE (id UUID, content TEXT, metadata JSONB, namespace TEXT, similarity FLOAT)
LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.content, c.metadata, c.namespace, 1 - (c.embedding <=> query_embedding) AS similarity
    FROM vecteurs.chunks c
    WHERE (namespace_filter = '' OR c.namespace = namespace_filter)
      AND (array_length(collection_filter, 1) IS NULL OR c.metadata->>'collection' = ANY(collection_filter))
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END; $$;

GRANT EXECUTE ON FUNCTION public.match_chunks TO authenticated, anon;
```
`SECURITY DEFINER` est ce qui permet à un rôle sans aucun droit direct sur le schéma `vecteurs` d'exécuter quand même cette requête précise, avec les droits du propriétaire de la fonction — c'est le seul chemin d'accès en lecture depuis un client qui n'a pas la clé de service.

**Point contre-intuitif à documenter** : dans le filtre ci-dessus, un tableau `collection_filter` **vide** désactive le filtre (aucune restriction), ce n'est pas équivalent à "aucun résultat autorisé". Si le projet a besoin qu'une absence de collection autorisée bloque tout accès, il faut le gérer explicitement côté appelant (ne jamais appeler la RPC avec un scope vide en le laissant tel quel).

Batcher les upserts (par exemple 50 lignes à la fois) pour éviter des délais d'attente sur de gros volumes ; l'upsert sur clé primaire fait naturellement un `ON CONFLICT DO UPDATE`, donc idempotent tant que l'id est stable.

**Limitation à documenter** : un adaptateur retriever générique (type LangChain `Retriever`) n'a pas forcément de sens à implémenter pour un backend RPC custom comme celui-ci — ne pas prétendre le supporter si ce n'est pas vraiment câblé, préférer lever une erreur explicite plutôt qu'un faux support silencieux.

## 3. Sélection du backend par configuration

```python
_instance: IVectorStore | None = None
_lock = threading.Lock()

def get_vector_store() -> IVectorStore:
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = _build()
    return _instance

def _build() -> IVectorStore:
    provider = os.getenv("VECTOR_STORE_PROVIDER", "pinecone").lower()
    if provider == "pgvector":
        return PgvectorStore(...)
    if provider == "pinecone":
        return PineconeStore(...)
    raise ValueError(f"VECTOR_STORE_PROVIDER inconnu : {provider!r}")
```

Vérifier systématiquement, après avoir ajouté une nouvelle implémentation, qu'elle est bien branchée dans cette fonction — une implémentation qui compile mais n'est jamais atteignable en configuration est un piège classique.

Si plusieurs modèles d'embedding peuvent coexister dans le temps (changement de modèle en cours de vie du projet), calculer le namespace/la clé de partitionnement dynamiquement à partir de la configuration d'embedding active (`f"{provider}|{model}|{dimension}"`) plutôt qu'en dur — ainsi un changement de modèle d'embedding route automatiquement les nouveaux vecteurs vers un espace différent, évitant de mélanger des vecteurs de dimensions incompatibles dans une même recherche de similarité.

## 4. Isolation RBAC au niveau du retrieval

Le filtre sur les collections autorisées doit être appliqué à l'intérieur de l'appel de recherche par similarité (`filter={"collection": {"$in": allowed_collections}}` ou équivalent SQL), jamais après coup en filtrant les résultats côté application — sans quoi un utilisateur peut recevoir moins de résultats que le `k` demandé simplement parce que les meilleurs résultats bruts appartenaient à une collection non autorisée, alors qu'un filtrage en amont aurait renvoyé les k meilleurs résultats *parmi les autorisés*. `allowed_collections=None` doit signifier "aucune restriction" (accès admin) et `allowed_collections=[]` doit signifier "aucun accès" — ne jamais confondre ces deux valeurs, et faire relire ce point précis en revue de code tant l'erreur est facile (voir `references/rbac-auth.md`).

## Où aller ensuite

- Comment le retrieval combine ce vector store avec une recherche lexicale et un éventuel graphe → `references/orchestrator.md`
- D'où vient `allowed_collections` et comment il est résolu depuis le token utilisateur → `references/rbac-auth.md`
