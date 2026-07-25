"""Implémentation pgvector — voir references/vector-store.md §2.

À ADAPTER avant usage :
- La dimension du vecteur (1536 ici) doit correspondre au modèle d'embedding choisi et à la
  migration SQL (assets/backend/migrations/002_vector_store.sql).
- Le client Postgres (`_client`) est un stand-in — brancher le client réel du projet
  (ex. supabase-py, psycopg, SQLAlchemy...).
- `_RPC_FN` doit correspondre au nom de la fonction RPC créée par la migration.
"""
from __future__ import annotations

import uuid
from typing import Optional

from .interface import Document, IVectorStore

_BATCH_SIZE = 50
_RPC_FN = "match_chunks"


class PgvectorStore(IVectorStore):
    def __init__(self, client=None, table: str = "vecteurs.chunks", namespace: str = ""):
        self._client = client  # ex: create_client(url, service_key)
        self._table = table
        self._namespace = namespace
        self._embeddings = None

    def set_embedding_model(self, embedding_model) -> None:
        self._embeddings = embedding_model

    def _require_embeddings(self):
        if self._embeddings is None:
            raise RuntimeError("set_embedding_model() doit être appelé avant tout usage de PgvectorStore")
        return self._embeddings

    def add_documents(self, documents: list[Document], ids: Optional[list[str]] = None) -> list[str]:
        return self.upsert_documents(documents, ids or [str(uuid.uuid4()) for _ in documents])

    def upsert_documents(self, documents: list[Document], ids: list[str]) -> list[str]:
        embeddings = self._require_embeddings()
        vectors = embeddings.embed_documents([d.page_content for d in documents])
        rows = [
            {"id": doc_id, "content": doc.page_content, "metadata": doc.metadata,
             "namespace": self._namespace, "embedding": vec}
            for doc_id, doc, vec in zip(ids, documents, vectors)
        ]
        for i in range(0, len(rows), _BATCH_SIZE):
            batch = rows[i : i + _BATCH_SIZE]
            self._client.table(self._table).upsert(batch).execute()
        return ids

    def delete_documents(self, ids: list[str]) -> bool:
        self._client.table(self._table).delete().in_("id", ids).execute()
        return True

    def similarity_search(self, query, k=5, namespace=None, filter=None) -> list[Document]:
        return [doc for doc, _ in self.similarity_search_with_score(query, k, namespace, filter)]

    def similarity_search_with_score(self, query, k=5, namespace=None, filter=None):
        embeddings = self._require_embeddings()
        vector = embeddings.embed_query(query)
        collection_filter = (filter or {}).get("collection", {}).get("$in", [])
        resp = self._client.rpc(_RPC_FN, {
            "query_embedding": vector,
            "match_count": k,
            "namespace_filter": namespace or self._namespace,
            "collection_filter": collection_filter,
        }).execute()
        return [
            (Document(page_content=row["content"], metadata=row["metadata"]), row["similarity"])
            for row in resp.data
        ]

    def similarity_search_by_vector(self, embedding, k=5, filter=None) -> list[Document]:
        collection_filter = (filter or {}).get("collection", {}).get("$in", [])
        resp = self._client.rpc(_RPC_FN, {
            "query_embedding": embedding, "match_count": k,
            "namespace_filter": self._namespace, "collection_filter": collection_filter,
        }).execute()
        return [Document(page_content=row["content"], metadata=row["metadata"]) for row in resp.data]

    def count(self) -> int:
        resp = self._client.table(self._table).select("id", count="exact").execute()
        return resp.count or 0

    def health_check(self) -> bool:
        try:
            self._client.table(self._table).select("id").limit(1).execute()
            return True
        except Exception:
            return False

    def list_all_documents(self, allowed_collections: Optional[list[str]] = None) -> list[Document]:
        # Exclure explicitement un éventuel namespace de cache sémantique (voir
        # references/orchestrator.md §4) pour ne pas polluer un index secondaire reconstruit
        # à partir de ce dump.
        query = self._client.table(self._table).select("*").neq("namespace", "cache")
        resp = query.execute()
        return [Document(page_content=row["content"], metadata=row["metadata"]) for row in resp.data]
