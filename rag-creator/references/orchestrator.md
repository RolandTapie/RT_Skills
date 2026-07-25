# Orchestrateur de requête

## 1. Le pattern `RunState` — un état partagé unique par requête

Plutôt qu'une fonction monolithique qui empile des variables locales au fil de 7 stages, centraliser tout l'état de la requête en cours dans une seule structure, construite en tête de fonction et transmise à chaque stage :

```python
@dataclass
class RunState:
    request: RagRequest
    collector: MetricsCollector
    rag_response: RagResponse
    event_queue: asyncio.Queue | None = None
    allowed_collections: list[str] | None = None
    # ... champs remplis progressivement par chaque stage :
    user_data: dict | None = None
    guardrail_passed: bool = False
    query_list: list[str] = field(default_factory=list)
    all_retrieved_chunks: list = field(default_factory=list)
    contexts: list = field(default_factory=list)
    cache_hit: bool = False

    async def emit_cot(self, stage: str, message: str, elapsed_s: float = 0.0, done: bool = True) -> None:
        if self.event_queue is not None:
            await self.event_queue.put({"type": "cot", "stage": stage, "message": message,
                                          "elapsed_s": round(elapsed_s, 2), "done": done})

    async def emit_result(self, data: dict) -> None:
        if self.event_queue is not None:
            await self.event_queue.put({"type": "result", "data": data})
            await self.event_queue.put(None)  # sentinelle de fin de flux

    async def emit_error(self, message: str) -> None:
        if self.event_queue is not None:
            await self.event_queue.put({"type": "error", "message": message})
            await self.event_queue.put(None)
```

La fonction d'orchestration principale reste alors courte et lisible même avec de nombreux stages :

```python
async def run_async(self, request: RagRequest, event_queue=None, allowed_collections=None) -> RagResponse:
    state = RunState(request=request, collector=MetricsCollector(), rag_response=init_response(request),
                      event_queue=event_queue, allowed_collections=allowed_collections)
    try:
        if error := await self._run_stage_user_validation(state):
            return error
        cache_decision = await self._run_stage_context_loading(state)
        if state.cache_hit and cache_decision and cache_decision.get("can_answer"):
            return await self._serve_cache_hit(state, cache_decision)
        if not state.guardrail_passed:
            if rejected := await self._run_stage_guardrails(state):
                return rejected
        if short_circuit := await self._run_stage_reconstruction(state):
            return short_circuit
        await self._run_stage_router(state)
        await self._run_stage_retrieval(state)
        await self._run_stage_synthesis(state)
        self._schedule_persistence(state)  # fire-and-forget : mémoire, cache, monitoring
        await state.emit_result(self._build_final_response(state))
        return state.rag_response
    except Exception as exc:
        return await self._handle_pipeline_error(state, exc)
```

Chaque stage est gardé par un flag "actif" chargé depuis la configuration (voir "config-as-data" dans `references/architecture-overview.md`) — permet de désactiver un stage en production sans redéploiement.

## 2. Retrieval hybride en parallèle

Traiter chaque sous-question (issue du stage de routage) en parallèle (`asyncio.gather`), et à l'intérieur de chaque sous-question, lancer les différentes sources de retrieval (recherche lexicale type BM25, recherche vectorielle, éventuellement graphe de connaissances) en parallèle également, chacune avec son propre timeout indépendant — une source lente ou en panne ne doit jamais bloquer les autres. Fusionner ensuite les résultats des différentes sources par déduplication sur l'identifiant du chunk, avec une stratégie de fusion de rangs (type Reciprocal Rank Fusion) si plusieurs sources ont produit des résultats, puis un reranking optionnel (modèle de reranking dédié) pour affiner l'ordre final avant synthèse.

## 3. Mémoire conversationnelle

Modèle recommandé : une ligne par conversation (contrainte d'unicité sur l'identifiant de conversation), avec un champ JSON accumulant les tours (question/réponse), tronqué aux N derniers tours pour ne pas grossir indéfiniment.

**Deux granularités de lecture à distinguer** :
- mémoire globale utilisateur (toutes conversations confondues) — utile pour donner un contexte long terme ;
- historique de la conversation courante uniquement (les derniers tours) — celui qui compte pour résoudre les ellipses ("et l'année dernière ?").

**Garde-fou anti-empoisonnement — le point le plus important de cette section** : n'écrire en mémoire QUE les tours qui ont abouti à une réponse effectivement servie à l'utilisateur. Un rejet de guardrail ou une exception dans le pipeline ne doit JAMAIS être persisté comme tour de conversation — sinon les tours suivants, qui s'appuient sur cet historique pour résoudre leurs propres ellipses, hériteraient d'un contexte corrompu par un échec précédent.

```python
async def persist_memory(db, request, response_text: str) -> None:
    conv_id = getattr(request, "conversation_id", None)
    if not conv_id or not (response_text or "").strip():
        return
    existing = db.select_one("memories", "conversation_id", conv_id)
    new_pair = [{"role": "user", "content": request.query}, {"role": "assistant", "content": response_text}]
    if existing:
        messages = (existing["messages"] + new_pair)[-40:]
        db.update("memories", "conversation_id", conv_id, {"messages": messages, "updated_at": now()})
    else:
        db.insert("memories", {"conversation_id": conv_id, "messages": new_pair, ...})
```
Cette fonction ne doit être appelée que sur les chemins de succès (hit de cache sémantique servi, réponse finale du stage de synthèse) — jamais depuis le gestionnaire d'erreur ni depuis le chemin de rejet du guardrail.

Nettoyer le texte avant de l'injecter dans un prompt (`{conversation_recent}`) : retirer les formules de politesse répétitives, aplatir le markdown/retours ligne, tronquer à une longueur raisonnable, dédupliquer les tours identiques (le cache sémantique peut faire alterner deux formulations très proches d'une même réponse).

Si le pipeline a un mode explicite "sans cache/sans historique" demandé par l'utilisateur, poser un garde-fou déterministe qui empêche un LLM de reconstruction de court-circuiter le retrieval via l'historique conversationnel dans ce mode — ne pas se fier uniquement à l'instruction dans le prompt, écraser explicitement toute décision du LLM qui irait dans ce sens.

## 4. Cache sémantique (optionnel)

Utile pour éviter de refaire un retrieval + génération complets sur une question déjà posée sous une formulation proche. Deux composants :
- une entrée dans le vector store (namespace dédié, ex. `"cache"`), indexée sur l'embedding de la question ;
- une table qui stocke la question, les sous-questions, les chunks utilisés, et la réponse complète.

Recherche par similarité sur la nouvelle question, avec deux seuils : un seuil bas qui filtre les candidats à considérer, et un seuil très haut qui permet un court-circuit direct sans passer par un arbitre si la similarité est quasi-parfaite. Entre les deux, un LLM arbitre (léger, rapide) décide si l'entrée de cache trouvée répond réellement à la nouvelle question — ne jamais se fier uniquement au score de similarité vectorielle pour décider, une question proche en surface peut avoir un sens différent.

Écrire dans le cache en fire-and-forget après la synthèse (jamais sur le chemin critique), et exclure explicitement le namespace du cache de tout dump complet destiné à reconstruire un index secondaire — sinon les entrées de cache (qui n'ont pas les mêmes métadonnées que les chunks documentaires) polluent cet index.

## 5. Contrat d'événements temps réel (SSE)

Streamer la progression et la réponse au frontend via Server-Sent Events, avec un contrat à 4 types d'événements strictement typés :

```python
class CotEvent(BaseModel):
    type: Literal["cot"] = "cot"
    stage: str = ""
    message: str = ""
    elapsed_s: float = 0.0
    done: bool = True          # False = "stage en cours" (affichage live), True = stage terminé

class TokenEvent(BaseModel):
    type: Literal["token"] = "token"
    content: str = ""

class ResultEvent(BaseModel):
    type: Literal["result"] = "result"
    data: RagStreamResult      # réponse complète, sources, coûts, tokens, métriques

class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str = ""
```

Endpoint : une `asyncio.Queue` partagée entre le pipeline (producteur) et le générateur SSE (consommateur), un `None` déposé sur la queue signalant la fin du flux :

```python
@app.post("/rag/stream")
async def stream_rag(rag_request: RagRequest, current_user=Depends(require_auth)):
    queue: asyncio.Queue = asyncio.Queue()

    async def _pipeline():
        try:
            await orchestrator.run_async(rag_request, event_queue=queue,
                                           allowed_collections=current_user["allowed_collections"])
        except Exception as exc:
            await queue.put({"type": "error", "message": str(exc)})
            await queue.put(None)

    async def _events():
        asyncio.create_task(_pipeline())
        while (event := await queue.get()) is not None:
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"})
```

Chaque stage émet un événement `cot` non terminé (`done=False`) au démarrage et un terminé (`done=True`) à la fin, avec un message métier lisible par un humain (pas un nom de fonction technique) — seuls les événements terminés doivent alimenter la trace finale conservée avec la réponse, le `done=False` ne sert qu'à l'affichage live côté UI. Toujours terminer un flux par un `result` ou un `error`, jamais laisser la queue ouverte indéfiniment.

## 6. Collecte de métriques

Une structure de mesure par exécution de stage (nom du stage, horodatage début/fin, coût, tokens entrée/sortie, modèle utilisé), collectées dans un objet unique construit en tête de `run_async`. Si des stages tournent en parallèle (retrieval multi-sous-questions), garder une file par nom de stage (pas une seule valeur) pour ne pas mélanger les mesures de deux exécutions concurrentes du même stage.

Calculer et exposer au minimum :
- durée, coût et tokens par stage ;
- une répartition des chunks récupérés par source (lexical/vectoriel/graphe) — utile pour diagnostiquer si une source de retrieval sous-performe silencieusement ;
- le prompt et la réponse brute des stages "à risque" (guardrail, synthèse) pour pouvoir déboguer un refus ou une hallucination a posteriori.

Persister en fire-and-forget (tâche de fond), avec une écriture précoce d'une ligne "en cours" dès le début de la requête (pour éviter des références cassées si une persistance intermédiaire arrive avant la persistance finale), et une réconciliation au démarrage du serveur qui marque en erreur toute exécution restée "en cours" après un redémarrage.

## Où aller ensuite

- RBAC : comment `allowed_collections` est résolu et propagé jusqu'ici → `references/rbac-auth.md`
- Frontend : comment consommer ce flux SSE et afficher la trace de raisonnement → `references/frontend.md`
- Évaluation : comment rejouer ce pipeline en boîte noire pour comparer des variantes → `references/evaluation.md`
