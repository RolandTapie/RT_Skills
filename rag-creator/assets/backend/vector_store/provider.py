"""Factory + singleton de sélection du vector store — voir references/vector-store.md §3.

À ADAPTER avant usage :
- Ajouter une branche par backend réellement supporté par le projet.
- IMPORTANT : après avoir ajouté une nouvelle implémentation, vérifie qu'elle est bien
  branchée ici. Une implémentation qui compile mais n'est jamais atteignable en
  configuration est le piège le plus fréquent de ce pattern.
"""
from __future__ import annotations

import os
import threading
from typing import Optional

from .interface import IVectorStore

_instance: Optional[IVectorStore] = None
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
        from .pgvector_store import PgvectorStore  # import local : évite de charger le driver Postgres si inutile

        return PgvectorStore()

    if provider == "pinecone":
        from .pinecone_store import PineconeStore  # import local : idem pour le SDK Pinecone

        return PineconeStore()

    raise ValueError(
        f"VECTOR_STORE_PROVIDER inconnu : {provider!r}. "
        "Ajoute une branche dans _build() après avoir implémenté ce backend."
    )
