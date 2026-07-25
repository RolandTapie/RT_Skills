"""Squelette générique des modèles de chunk — voir references/ingestion.md §2.

À ADAPTER avant usage :
- La liste des enums (Language, ContentType) selon les langues/formats réels du projet.
- Le format de `section_path` si la restructuration produit une convention différente de "A > B > C".
- La dimension du champ `embedding` selon le modèle d'embedding choisi (non fixée ici, gérée au niveau
  du vector store, voir assets/backend/vector_store/).
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field, model_validator


class ChunkStatus(str, Enum):
    PENDING = "pending"
    EMBEDDED = "embedded"
    INDEXED = "indexed"
    ERROR = "error"


class ChunkMetadata(BaseModel):
    doc_id: str
    file_name: str
    collection: str
    source_type: str = "document"
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def _normalize(self) -> "ChunkMetadata":
        # Normaliser la casse du champ utilisé pour le filtrage RBAC — un filtre
        # {"collection": {"$in": [...]}} échoue silencieusement sur une différence de casse.
        self.collection = self.collection.strip().lower()
        return self


class ChunkPosition(BaseModel):
    """Position hiérarchique du chunk dans le document source.

    `section_path` est la donnée d'entrée (ex: "Chapitre 1 > Section 2 > Sous-section 3"),
    tous les autres champs sont dérivés automatiquement — ne jamais les fixer à la main ailleurs
    dans le code, sous peine d'incohérence entre deux endroits qui recalculeraient différemment
    le même breadcrumb.
    """

    section_path: str = ""
    title: str = ""
    path_parts: list[str] = Field(default_factory=list)
    path_depth: int = 0
    parent_title: Optional[str] = None
    breadcrumb: str = ""

    @model_validator(mode="after")
    def derive_sourcing_fields(self) -> "ChunkPosition":
        parts = [p.strip() for p in self.section_path.split(">") if p.strip()]
        self.path_parts = parts
        self.path_depth = len(parts)
        if self.parent_title is None and len(parts) >= 2:
            self.parent_title = parts[-2]
        self.breadcrumb = " › ".join(parts) if parts else self.title
        return self


class Chunk(BaseModel):
    model_config = {"extra": "ignore"}

    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    metadata: ChunkMetadata
    position: ChunkPosition = Field(default_factory=ChunkPosition)
    status: ChunkStatus = ChunkStatus.PENDING
    embedding: list[float] = Field(default_factory=list)
    error_msg: Optional[str] = None

    @computed_field
    @property
    def content_hash(self) -> str:
        # Hash tronqué pour une déduplication rapide par contenu identique.
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()[:16]

    @model_validator(mode="after")
    def _check_invariants(self) -> "Chunk":
        # Invariants métier posés une fois pour toutes plutôt que vérifiés à chaque usage :
        # un chunk conclu (embedded/indexed) DOIT avoir un vecteur, un chunk en erreur DOIT
        # avoir un message.
        if self.status in (ChunkStatus.EMBEDDED, ChunkStatus.INDEXED) and not self.embedding:
            raise ValueError(f"Chunk {self.chunk_id} au statut {self.status} sans embedding")
        if self.status == ChunkStatus.ERROR and not self.error_msg:
            raise ValueError(f"Chunk {self.chunk_id} en erreur sans error_msg")
        return self

    def mark_embedded(self, vector: list[float]) -> "Chunk":
        return self.model_copy(update={"embedding": vector, "status": ChunkStatus.EMBEDDED})

    def mark_indexed(self) -> "Chunk":
        if self.status != ChunkStatus.EMBEDDED:
            raise ValueError("Un chunk doit être EMBEDDED avant d'être marqué INDEXED")
        return self.model_copy(update={"status": ChunkStatus.INDEXED})

    def mark_error(self, message: str) -> "Chunk":
        return self.model_copy(update={"status": ChunkStatus.ERROR, "error_msg": message})


class ChunkBatch(BaseModel):
    """Regroupement des chunks issus d'un même document source."""

    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str
    chunks: list[Chunk] = Field(default_factory=list)

    @computed_field
    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    @computed_field
    @property
    def error_count(self) -> int:
        return sum(1 for c in self.chunks if c.status == ChunkStatus.ERROR)
