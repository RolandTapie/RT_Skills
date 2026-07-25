-- Migration schéma vector store pgvector — voir references/vector-store.md §2.
-- À ADAPTER : la dimension du vecteur (1536) doit correspondre exactement au modèle
-- d'embedding choisi (ex: 1536 pour text-embedding-3-small, 1024 pour d'autres modèles).
-- N'utiliser cette migration que si VECTOR_STORE_PROVIDER=pgvector (voir
-- assets/backend/vector_store/provider.py) ; ignorer entièrement si Pinecone est choisi.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS vecteurs;

CREATE TABLE IF NOT EXISTS vecteurs.chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content     TEXT NOT NULL,
    metadata    JSONB NOT NULL DEFAULT '{}',
    namespace   TEXT NOT NULL DEFAULT '',
    embedding   vector(1536),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx
    ON vecteurs.chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS chunks_namespace_idx ON vecteurs.chunks (namespace);
CREATE INDEX IF NOT EXISTS chunks_metadata_gin_idx ON vecteurs.chunks USING gin (metadata);

ALTER TABLE vecteurs.chunks ENABLE ROW LEVEL SECURITY;
-- Ce schéma n'est volontairement PAS exposé via une API REST auto-générée (PostgREST/Supabase) :
-- tout accès en lecture passe exclusivement par la fonction RPC ci-dessous (SECURITY DEFINER).
CREATE POLICY service_role_all_chunks ON vecteurs.chunks FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE OR REPLACE FUNCTION public.match_chunks(
    query_embedding     vector(1536),
    match_count         INT DEFAULT 5,
    namespace_filter    TEXT DEFAULT '',
    collection_filter   TEXT[] DEFAULT '{}'
)
RETURNS TABLE (id UUID, content TEXT, metadata JSONB, namespace TEXT, similarity FLOAT)
LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    -- ATTENTION (contre-intuitif) : collection_filter vide = AUCUNE restriction, pas
    -- "aucun résultat autorisé". Si le RBAC du projet doit bloquer un utilisateur sans
    -- collection autorisée, ce blocage doit être fait explicitement côté appelant,
    -- jamais en comptant sur cette RPC pour le faire (voir references/vector-store.md §2).
    RETURN QUERY
    SELECT c.id, c.content, c.metadata, c.namespace,
           1 - (c.embedding <=> query_embedding) AS similarity
    FROM vecteurs.chunks c
    WHERE
        (namespace_filter = '' OR c.namespace = namespace_filter)
        AND (
            array_length(collection_filter, 1) IS NULL
            OR c.metadata->>'collection' = ANY(collection_filter)
        )
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

GRANT EXECUTE ON FUNCTION public.match_chunks TO authenticated, anon;
GRANT USAGE ON SCHEMA vecteurs TO service_role;
