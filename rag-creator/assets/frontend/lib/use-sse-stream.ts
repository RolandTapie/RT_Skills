/**
 * Hook de consommation du flux SSE du backend RAG — voir references/frontend.md §4.
 *
 * Pourquoi fetch() et pas EventSource : EventSource ne supporte que les requêtes GET,
 * alors que la question + les options (collections, historique...) doivent être envoyées
 * dans un corps de requête POST.
 *
 * À ADAPTER : le typage `SSEEvent` doit correspondre exactement au contrat backend
 * (voir ../types/rag-contracts.ts) — tenu manuellement, pas généré.
 */
import { useCallback, useRef, useState } from "react";
import type { CotStepItem, RagStreamResult, SSEEvent } from "../types/rag-contracts";

interface UseSSEStreamOptions {
  url: string;
  getToken: () => string | null;
}

interface UseSSEStreamState {
  loading: boolean;
  cotSteps: CotStepItem[];
  streamedText: string;
  result: RagStreamResult | null;
  error: string | null;
}

export function useSSEStream({ url, getToken }: UseSSEStreamOptions) {
  const [state, setState] = useState<UseSSEStreamState>({
    loading: false,
    cotSteps: [],
    streamedText: "",
    result: null,
    error: null,
  });
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(
    async (payload: Record<string, unknown>) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setState({ loading: true, cotSteps: [], streamedText: "", result: null, error: null });

      const token = getToken();
      const response = await fetch(url, {
        method: "POST",
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      });

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        // La dernière ligne peut être incomplète (coupée entre deux paquets réseau) —
        // la reporter au tour de boucle suivant plutôt que de tenter de la parser.
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (raw === "[DONE]") {
            setState((s) => ({ ...s, loading: false }));
            return;
          }

          const evt = JSON.parse(raw) as SSEEvent;
          if (evt.type === "cot") {
            setState((s) => ({
              ...s,
              cotSteps: [...s.cotSteps.filter((c) => c.stage !== evt.stage), evt],
            }));
          } else if (evt.type === "token") {
            setState((s) => ({ ...s, streamedText: s.streamedText + evt.content }));
          } else if (evt.type === "result") {
            setState((s) => ({ ...s, result: evt.data, loading: false }));
          } else if (evt.type === "error") {
            setState((s) => ({ ...s, error: evt.message, loading: false }));
          }
        }
      }
    },
    [url, getToken]
  );

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setState((s) => ({ ...s, loading: false }));
  }, []);

  return { ...state, send, cancel };
}
