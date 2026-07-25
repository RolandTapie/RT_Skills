"""Interface abstraite du vector store — voir references/vector-store.md §1.

À ADAPTER avant usage :
- Ajouter/retirer des méthodes selon les besoins réels de l'orchestrateur et de l'ingestion —
  ne pas garder une méthode sans appelant identifié.
- Le type `Document` ci-dessous est un stand-in minimal ; remplacer par le type réellement utilisé
  dans le projet (ex. `langchain_core.documents.Document` si LangChain est dans la stack).

Ce fichier doit vivre dans le même module que les implémentations concrètes (ex. vector_store/),
pas dans le module d'ingestion — sinon un développeur cherchant l'interface "vector store" dans
le module vector store ne la trouvera pas.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Document:
    page_content: str
    metadata: dict = field(default_factory=dict)


class IVectorStore(ABC):
    @abstractmethod
    def set_embedding_model(self, embedding_model) -> None:
        """Doit être appelée après construction, avant tout usage.

        Chaque implémentation doit poser un assert/RuntimeError explicite si un appel
        similarity_search/add_documents survient avant cet appel, plutôt que de laisser
        planter plus loin avec une erreur obscure.
        """

    @abstractmethod
    def add_documents(self, documents: list[Document], ids: Optional[list[str]] = None) -> list[str]: ...

    @abstractmethod
    def upsert_documents(self, documents: list[Document], ids: list[str]) -> list[str]: ...

    @abstractmethod
    def delete_documents(self, ids: list[str]) -> bool: ...

    @abstractmethod
    def similarity_search(
        self, query: str, k: int = 5, namespace: Optional[str] = None, filter: Optional[dict] = None
    ) -> list[Document]: ...

    @abstractmethod
    def similarity_search_with_score(
        self, query: str, k: int = 5, namespace: Optional[str] = None, filter: Optional[dict] = None
    ) -> list[tuple[Document, float]]: ...

    @abstractmethod
    def similarity_search_by_vector(
        self, embedding: list[float], k: int = 5, filter: Optional[dict] = None
    ) -> list[Document]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def health_check(self) -> bool: ...

    @abstractmethod
    def list_all_documents(self, allowed_collections: Optional[list[str]] = None) -> list[Document]:
        """Dump complet, typiquement pour reconstruire un index secondaire (ex. lexical) au démarrage.

        Si un namespace de cache sémantique existe (voir references/orchestrator.md §4),
        l'exclure explicitement ici — sinon ses entrées polluent l'index reconstruit.
        """
