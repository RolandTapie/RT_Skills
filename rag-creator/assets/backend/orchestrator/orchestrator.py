"""Squelette d'orchestrateur — voir references/orchestrator.md.

Volontairement minimal : 3 stages (validation, retrieval, synthèse). N'ajoute guardrail
séparé / reconstruction d'ellipses / routage multi-sous-questions / mémoire / cache que si
le cadrage du projet (voir SKILL.md étape 1) les justifie — chaque stage ajouté est une
responsabilité et une latence en plus, pas un standard à cocher par défaut.

À ADAPTER avant usage :
- Chaque méthode `_run_stage_*` est un stub à remplacer par la logique réelle du projet.
- Brancher le vector store réel (assets/backend/vector_store/) dans `_run_stage_retrieval`.
"""
from __future__ import annotations

import traceback
from typing import Optional

from .run_state import RagRequest, RagResponse, RunState, MetricsCollector


class Orchestrator:
    def __init__(self, vector_store, llm_client):
        self._vector_store = vector_store
        self._llm = llm_client

    async def run_async(
        self,
        request: RagRequest,
        event_queue=None,
        allowed_collections: Optional[list[str]] = None,
    ) -> RagResponse:
        state = RunState(
            request=request,
            collector=MetricsCollector(),
            rag_response=RagResponse(),
            event_queue=event_queue,
            allowed_collections=allowed_collections,
        )
        try:
            if error := await self._run_stage_validation(state):
                return error

            await self._run_stage_retrieval(state)
            await self._run_stage_synthesis(state)

            state.rag_response.status = "completed"
            await state.emit_result({
                "response": state.rag_response.response,
                "sources": state.rag_response.sources,
            })
            return state.rag_response
        except Exception as exc:
            await state.emit_error(str(exc))
            state.rag_response.status = "error"
            # Ne jamais persister ce tour en mémoire conversationnelle (voir
            # references/orchestrator.md §3, garde-fou anti-empoisonnement).
            return state.rag_response

    async def _run_stage_validation(self, state: RunState) -> Optional[RagResponse]:
        state.collector.start_stage("validation")
        if not state.request.query.strip():
            state.rag_response.status = "rejected"
            await state.emit_error("Question vide")
            return state.rag_response
        state.collector.end_stage("validation")
        return None

    async def _run_stage_retrieval(self, state: RunState) -> None:
        await state.emit_cot("retrieval", "Recherche du contexte…", done=False)
        state.collector.start_stage("retrieval")

        filter_ = None
        if state.allowed_collections is not None:
            # allowed_collections=[] doit bloquer tout accès, jamais être traité comme
            # "pas de filtre" (voir references/vector-store.md §4).
            filter_ = {"collection": {"$in": state.allowed_collections}}

        results = self._vector_store.similarity_search_with_score(
            state.request.query, k=5, filter=filter_,
        )
        state.all_retrieved_chunks = [doc for doc, _ in results]
        state.contexts = [doc.page_content for doc in state.all_retrieved_chunks]
        state.rag_response.sources = [doc.metadata for doc in state.all_retrieved_chunks]

        state.collector.end_stage("retrieval")
        await state.emit_cot("retrieval", "Contexte récupéré", done=True)

    async def _run_stage_synthesis(self, state: RunState) -> None:
        await state.emit_cot("synthesis", "Rédaction de la réponse…", done=False)
        state.collector.start_stage("synthesis")

        context_text = "\n\n".join(state.contexts)
        prompt = f"Contexte:\n{context_text}\n\nQuestion: {state.request.query}\nRéponse:"

        response_text = ""
        async for token in self._llm.stream(prompt):
            response_text += token
            await state.emit_token(token)

        state.rag_response.response = response_text
        state.collector.end_stage("synthesis")
        await state.emit_cot("synthesis", "Réponse générée", done=True)
