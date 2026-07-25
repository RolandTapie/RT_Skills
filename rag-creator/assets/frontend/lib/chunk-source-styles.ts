/**
 * Styles de badge par source de retrieval — voir references/frontend.md §2.
 *
 * Module volontairement isolé : dans les projets similaires, ce mapping a été recopié à
 * l'identique dans plusieurs composants (chat, monitoring, info-bulles) et a fini par
 * diverger légèrement entre les copies. Importer ce module partout plutôt que de
 * recopier l'objet — dès qu'un deuxième composant a besoin du même badge.
 *
 * À ADAPTER : les clés doivent correspondre exactement aux valeurs de `retrieval_source`
 * émises par le backend (voir references/orchestrator.md §2).
 */

export type ChunkSource = "bm25" | "vector" | "bm25+vector" | "graph" | "unknown";

export const CHUNK_SOURCE_STYLES: Record<ChunkSource, { label: string; className: string }> = {
  bm25: { label: "Lexical", className: "bg-amber-100 text-amber-800" },
  vector: { label: "Vectoriel", className: "bg-blue-100 text-blue-800" },
  "bm25+vector": { label: "Hybride", className: "bg-purple-100 text-purple-800" },
  graph: { label: "Graphe", className: "bg-emerald-100 text-emerald-800" },
  unknown: { label: "Inconnu", className: "bg-gray-100 text-gray-700" },
};

export function getChunkSourceStyle(source: string) {
  return CHUNK_SOURCE_STYLES[(source as ChunkSource) ?? "unknown"] ?? CHUNK_SOURCE_STYLES.unknown;
}
