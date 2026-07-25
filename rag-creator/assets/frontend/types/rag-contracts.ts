/**
 * Contrat de types partagé frontend/backend — voir references/frontend.md §4.
 *
 * À ADAPTER : ce fichier est un miroir MANUEL des modèles backend (pas de génération
 * automatique depuis un schéma OpenAPI). À chaque changement du contrat backend
 * (nouveau champ dans RagStreamResult, nouveau type d'événement SSE...), mettre ce
 * fichier à jour dans le même changement — ne pas laisser diverger silencieusement.
 */

export interface SourceItem {
  chunk_id: string;
  file_name: string;
  breadcrumb: string;
  collection: string;
}

export interface RagStreamResult {
  response: string;
  sources: SourceItem[];
  chunk_ids: string[];
  task_id: string;
  status: "completed" | "rejected" | "error";
  // Champs de coût/tokens/metrics optionnels selon si le monitoring est activé côté projet.
  cost_usd?: number;
  tokens_input?: number;
  tokens_output?: number;
}

export interface CotStepItem {
  stage: string;
  message: string;
  elapsed_s: number;
  done: boolean;
}

export type SSEEvent =
  | ({ type: "cot" } & CotStepItem)
  | { type: "token"; content: string }
  | { type: "result"; data: RagStreamResult }
  | { type: "error"; message: string };
