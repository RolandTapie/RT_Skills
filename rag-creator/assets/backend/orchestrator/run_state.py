"""État partagé d'une requête RAG en cours — voir references/orchestrator.md §1.

À ADAPTER avant usage :
- Ajouter les champs propres au projet au fil de l'implémentation des stages (ne pas
  pré-remplir des champs qui n'ont pas encore d'appelant réel).
- `RagRequest`/`RagResponse`/`MetricsCollector` sont des stand-ins minimaux à remplacer par
  les types réels du projet.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RagRequest:
    query: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    use_cache: bool = True


@dataclass
class RagResponse:
    response: str = ""
    sources: list[dict] = field(default_factory=list)
    status: str = "pending"


@dataclass
class MetricsCollector:
    stages: dict[str, list[dict]] = field(default_factory=dict)
    chunks_by_source: dict[str, int] = field(default_factory=dict)

    def start_stage(self, name: str) -> None:
        self.stages.setdefault(name, []).append({"start": True})

    def end_stage(self, name: str, **kwargs: Any) -> None:
        if self.stages.get(name):
            self.stages[name][-1].update(kwargs)


@dataclass
class RunState:
    request: RagRequest
    collector: MetricsCollector
    rag_response: RagResponse
    event_queue: Optional[asyncio.Queue] = None
    allowed_collections: Optional[list[str]] = None
    # allowed_collections=None -> pas de restriction (admin) ; []  -> aucun accès.
    # Ne jamais confondre ces deux valeurs (voir references/rbac-auth.md §3).

    user_data: Optional[dict] = None
    guardrail_passed: bool = False
    cache_hit: bool = False
    query_list: list[str] = field(default_factory=list)
    all_retrieved_chunks: list[Any] = field(default_factory=list)
    contexts: list[str] = field(default_factory=list)

    async def emit_cot(self, stage: str, message: str, elapsed_s: float = 0.0, done: bool = True) -> None:
        if self.event_queue is not None:
            await self.event_queue.put({
                "type": "cot", "stage": stage, "message": message,
                "elapsed_s": round(elapsed_s, 2), "done": done,
            })

    async def emit_token(self, content: str) -> None:
        if self.event_queue is not None:
            await self.event_queue.put({"type": "token", "content": content})

    async def emit_result(self, data: dict) -> None:
        if self.event_queue is not None:
            await self.event_queue.put({"type": "result", "data": data})
            await self.event_queue.put(None)  # sentinelle de fin de flux

    async def emit_error(self, message: str) -> None:
        if self.event_queue is not None:
            await self.event_queue.put({"type": "error", "message": message})
            await self.event_queue.put(None)
