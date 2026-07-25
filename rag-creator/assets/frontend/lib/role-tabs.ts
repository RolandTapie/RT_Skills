/**
 * Configuration déclarative unique des onglets visibles par rôle — voir references/frontend.md §6.
 *
 * Module volontairement isolé : dans les projets similaires, la même logique de filtrage
 * par rôle a été dupliquée entre le composant de navigation et le composant de routage des
 * vues, ce qui les fait facilement diverger. Importer ROLE_TABS des deux côtés plutôt que
 * de recopier une condition if/else par rôle à deux endroits.
 *
 * RAPPEL : ce filtrage est un confort d'affichage, pas une mesure de sécurité — la
 * vérification réelle des droits reste entièrement côté backend (voir references/rbac-auth.md).
 *
 * À ADAPTER : la liste des onglets et des rôles selon les besoins réels du projet.
 */

export type Role = "admin" | "user" | "evaluator" | "unknown";

export const ROLE_TABS: Record<Role, string[]> = {
  admin: ["chat", "monitoring", "documents", "jobs", "evaluation", "users", "settings"],
  evaluator: ["chat", "evaluation"],
  user: ["chat", "documents"],
  unknown: ["chat"],
};

export function tabsForRole(role: string | undefined | null): string[] {
  return ROLE_TABS[(role as Role) ?? "unknown"] ?? ROLE_TABS.unknown;
}
