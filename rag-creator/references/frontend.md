# Frontend de chat RAG

## 1. Organisation par panels plats

Un panel = un fichier par grande fonctionnalité (chat, monitoring, gestion des documents, gestion des jobs d'ingestion, administration des utilisateurs...), montés/démontés selon l'onglet actif et le rôle de l'utilisateur — pas besoin de sur-découper en sous-dossiers par feature tant qu'un panel reste lisible en un seul fichier. N'extraire un sous-dossier que pour un panel qui a vraiment plusieurs sous-composants réutilisés ailleurs (ex. des info-bulles utilisées à la fois dans le chat et dans le monitoring).

Un seul composant "détail de chunk" (dialog générique affichant le contenu et les métadonnées d'un chunk source) mérite d'être partagé entre le panel de chat (clic sur une source citée) et le panel de monitoring (clic sur un chunk récupéré) — extraire ce composant dès qu'un deuxième panel en a besoin.

## 2. Rendu de la trace de raisonnement (chain-of-thought)

Ne pas construire un composant séparé pour chaque contexte d'affichage de la trace — trois rendus différents du même type de données (liste d'étapes avec stage/message/durée/statut terminé) suffisent :
- une timeline animée pendant le streaming (icône + spinner tant que l'étape n'est pas terminée, coche une fois faite) ;
- une version repliable dans une bulle de réponse terminée ;
- une version compacte dans une info-bulle de survol.

Centraliser la traduction du nom technique de stage en libellé lisible dans un seul module, avec une correspondance tolérante (recherche de sous-chaîne insensible à la casse plutôt qu'une énumération stricte) pour rester robuste si le backend renomme légèrement un stage :

```ts
export function getStageLabel(stage: string): string {
  const s = stage.toLowerCase();
  if (s.includes('cache')) return 'Vérification du cache';
  if (s.includes('guardrail') || s.includes('filtr')) return 'Analyse de la question';
  if (s.includes('retriev') || s.includes('recher')) return 'Recherche du contexte';
  if (s.includes('synth') || s.includes('generat')) return 'Rédaction de la réponse';
  return stage;
}
```

**Éviter la duplication de style** : le mapping des couleurs/icônes de badge par source de chunk (lexical/vectoriel/graphe) est un piège classique de duplication — dès qu'un deuxième composant (ex. le panel de monitoring en plus du chat) a besoin du même badge, extraire un seul module partagé plutôt que de recopier le dictionnaire de styles.

## 3. Panel de monitoring (si la couche monitoring backend existe)

Organiser en onglets séparés plutôt qu'une vue unique surchargée : statistiques agrégées (moyenne/médiane/p95 par stage, calculées côté client à partir des données déjà chargées plutôt que via un endpoint séparé), liste des exécutions individuelles (filtrable, avec détail au clic : question/réponse, chunks retenus, couches exécutées, feedback associé), table des exceptions/erreurs, et une vue de configuration des paramètres LLM par couche si le pattern config-as-data (voir `references/architecture-overview.md`) est utilisé.

Ne jamais coder en dur côté frontend la liste des stages ou des modèles disponibles — la construire dynamiquement depuis la table de configuration, pour que l'UI reste synchronisée automatiquement avec la configuration backend sans nécessiter de déploiement frontend à chaque changement de couche.

## 4. Consommer le flux SSE côté client

`EventSource` ne supporte que les requêtes GET — si l'endpoint de streaming attend un corps de requête POST (question, historique, options), consommer le flux via `fetch` + lecture manuelle du flux de réponse, avec parsing des frames `data: ...\n\n` :

```ts
const response = await fetch(`${API_URL}/rag/stream`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify(payload),
});
const reader = response.body!.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n');
  buffer = lines.pop() ?? '';  // ligne potentiellement incomplète, reportée au tour suivant

  for (const line of lines) {
    if (!line.startsWith('data: ')) continue;
    const payload = line.slice(6).trim();
    if (payload === '[DONE]') return;
    const evt = JSON.parse(payload) as SSEEvent;
    // dispatcher selon evt.type : 'cot' | 'token' | 'result' | 'error'
  }
}
```

Typer le contrat d'événements côté frontend en miroir exact des modèles backend (union discriminée sur le champ `type`) — c'est un contrat manuel à maintenir des deux côtés (pas de génération automatique depuis un schéma), donc à documenter comme un fichier à mettre à jour systématiquement en même temps que tout changement du contrat backend :

```ts
export type SSEEvent =
  | { type: 'cot'; stage: string; message: string; elapsed_s: number; done: boolean }
  | { type: 'token'; content: string }
  | { type: 'result'; data: RagStreamResult }
  | { type: 'error'; message: string };
```

Si le projet grossit, extraire cette logique de parsing dans un hook dédié (`useSSEStream`) plutôt que de la garder inline dans le composant de chat — plus facile à tester isolément.

## 5. Stores d'état (Zustand ou équivalent)

Découper par responsabilité plutôt qu'un store global unique : session d'authentification, configuration RAG globale (modèle, seuils), état volatile de la session de chat en cours (sources actives, collections sélectionnées), historique/mémoire conversationnelle, configuration des couches LLM si le pattern config-as-data est utilisé.

Le store de mémoire conversationnelle mérite une attention particulière si une persistance backend fire-and-forget est utilisée en parallèle d'un cache local : à l'initialisation, fusionner les deux sources en gardant la version la plus récente par identifiant de conversation (comparer un horodatage de mise à jour), car l'écriture backend fire-and-forget peut ne pas avoir abouti au moment où l'utilisateur revient sur l'app :

```ts
const merged = new Map<string, Memory>();
for (const m of remoteMemories) merged.set(m.conversation_id, m);
for (const m of localMemories) {
  const existing = merged.get(m.conversation_id);
  if (!existing || m.updated_at > existing.updated_at) merged.set(m.conversation_id, m);
}
```

## 6. Affichage différencié par rôle

Le filtrage des onglets/contrôles visibles selon le rôle est un confort d'affichage, pas une mesure de sécurité — factoriser dans une seule configuration déclarative (ex. `{admin: [...tabs], user: [...tabs]}`) importée à la fois par la navigation et par le composant de routage des vues, plutôt que dupliquer la même logique conditionnelle à deux endroits qui pourraient diverger. La vérification de sécurité réelle reste entièrement côté backend (voir `references/rbac-auth.md`) — un contrôle visible mais désactivé (`disabled`) pour un rôle donné est un raffinement d'ergonomie, pas une protection.

Revalider le rôle courant à chaque montage de l'application (pas seulement au login) pour refléter un changement de droits sans exiger une reconnexion.

## 7. Feedback utilisateur lié à l'exécution

Générer côté client un identifiant de tâche à l'envoi de la requête, le faire circuler jusqu'au résultat final (le backend le renvoie tel quel ou l'utilise comme identifiant de l'exécution persistée côté monitoring), et l'attacher à tout feedback (pouce haut/bas, commentaire) pour permettre la jointure entre un feedback et l'exécution monitoring correspondante :

```ts
const taskId = `task_${Date.now()}`;
// ... envoyé dans la requête, reçu dans la réponse, stocké sur le message affiché ...
await submitFeedback({ message_id: msg.id, task_id: msg.taskId, feedback_type: 'positive' });
```

Prévoir un plan de repli pour la jointure (par exemple utilisateur + texte de la question) au cas où l'identifiant de tâche serait absent sur d'anciens enregistrements — mais documenter clairement que ce plan de repli est moins fiable (une même question posée deux fois par le même utilisateur devient ambiguë), et s'assurer que l'identifiant transmis par le frontend correspond bien à l'identifiant que le backend utilise pour persister l'exécution, sinon la jointure casse silencieusement.

## Où aller ensuite

- Contrat des événements SSE côté backend → `references/orchestrator.md` §5
- Comment `allowed_collections` détermine ce qu'un rôle donné peut voir → `references/rbac-auth.md`
