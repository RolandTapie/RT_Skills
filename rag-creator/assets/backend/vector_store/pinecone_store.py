"""Implémentation Pinecone — voir references/vector-store.md §2.

À ADAPTER avant usage :
- Nécessite le SDK `pinecone` réel (`from pinecone import Pinecone`) — non importé ici pour
  garder ce squelette lisible sans dépendance installée.
- `PINECONE_INDEX` / `PINECONE_API_KEY` : variables d'environnement à adapter au projet.

Convention IMPORTANTE à respecter : Pinecone ne stocke pas nativement de texte, seulement des
vecteurs + métadonnées JSON. Le texte du chunk est donc dupliqué dans metadata["text"] — sans
cette convention, `list_all_documents` et la reconstruction du contenu depuis une recherche
ne peuvent pas fonctionner.
"""
from __future__ import annotations

import os
import uuid
from typing import Optional

from .interface import Document, IVectorStore


class PineconeStore(IVectorStore):
    def __init__(self, index_name: Optional[str] = None, namespace: str = "default"):
        # from pinecone import Pinecone
        # self._pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        # self._index = self._pc.Index(index_name or os.environ["PINECONE_INDEX"])
        self._index = None  # brancher le client réel ici
        self._namespace = namespace
        self._embeddings = None

    def set_embedding_model(self, embedding_model) -> None:
        self._embeddings = embedding_model

    def _require_embeddings(self):
        if self._embeddings is None:
            raise RuntimeError("set_embedding_model() doit être appelé avant tout usage de PineconeStore")
        return self._embeddings

    def add_documents(self, documents: list[Document], ids: Optional[list[str]] = None) -> list[str]:
        return self.upsert_documents(documents, ids or [str(uuid.uuid4()) for _ in documents])

    def upsert_documents(self, documents: list[Document], ids: list[str]) -> list[str]:
        embeddings = self._require_embeddings()
        vectors_emb = embeddings.embed_documents([d.page_content for d in documents])
        vectors = [
            {"id": doc_id, "values": vec, "metadata": {**doc.metadata, "text": doc.page_content}}
            for doc_id, doc, vec in zip(ids, documents, vectors_emb)
        ]
        self._index.upsert(vectors=vectors, namespace=self._namespace)
        return ids

    def delete_documents(self, ids: list[str]) -> bool:
        self._index.delete(ids=ids, namespace=self._namespace)
        return True

    def similarity_search(self, query, k=5, namespace=None, filter=None) -> list[Document]:
        return [doc for doc, _ in self.similarity_search_with_score(query, k, namespace, filter)]

    def similarity_search_with_score(self, query, k=5, namespace=None, filter=None):
        embeddings = self._require_embeddings()
        vector = embeddings.embed_query(query)
        resp = self._index.query(
            vector=vector, top_k=k, namespace=namespace or self._namespace,
            filter=filter, include_metadata=True,
        )
        results = []
        for match in resp.matches:
            meta = dict(match.metadata or {})
            text = meta.pop("text", "")
            results.append((Document(page_content=text, metadata=meta), match.score))
        return results

    def similarity_search_by_vector(self, embedding, k=5, filter=None) -> list[Document]:
        resp = self._index.query(vector=embedding, top_k=k, namespace=self._namespace,
                                   filter=filter, include_metadata=True)
        out = []
        for match in resp.matches:
            meta = dict(match.metadata or {})
            text = meta.pop("text", "")
            out.append(Document(page_content=text, metadata=meta))
        return out

    def count(self) -> int:
        stats = self._index.describe_index_stats()
        return stats.namespaces.get(self._namespace, {}).get("vector_count", 0)

    def health_check(self) -> bool:
        try:
            self._index.describe_index_stats()
            return True
        except Exception:
            return False

    def list_all_documents(self, allowed_collections: Optional[list[str]] = None) -> list[Document]:
        # Le SDK n'expose en général pas d'itération complète native sur l'index —
        # parcourir par lot via list() + fetch(), voir la doc du SDK Pinecone utilisé.
        raise NotImplementedError("À implémenter avec list()/fetch() par batch selon le SDK Pinecone du projet")
