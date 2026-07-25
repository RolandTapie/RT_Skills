# RBAC et authentification

## 1. Modèle de données — une seule source de vérité par concept

Deux tables suffisent dans la grande majorité des cas :

```sql
CREATE TABLE roles (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                 TEXT NOT NULL UNIQUE,          -- ex: 'admin', 'user', 'evaluator'
  allowed_collections  TEXT[] NOT NULL DEFAULT '{}',  -- collections logiques accessibles par défaut pour ce rôle
  description          TEXT
);

CREATE TABLE user_profiles (
  id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,  -- FK vers la table d'auth du provider
  role_id     UUID REFERENCES roles(id),
  full_name   TEXT NOT NULL DEFAULT '',
  -- Optionnel : surcharge individuelle si un utilisateur a besoin de droits différents de son rôle par défaut
  allowed_collections_override TEXT[]
);
```

**Anti-pattern à ne pas reproduire** : ne pas créer une seconde table "applicative" parallèle à la table de profil officielle (par exemple parce qu'une fonctionnalité plus ancienne du projet référence un id utilisateur différent). Cette duplication crée deux sources de vérité pour la même notion de droits, qui peuvent diverger silencieusement (l'une mise à jour, l'autre oubliée). Si une contrainte historique impose de garder une table legacy, migrer les autres tables qui la référencent vers `user_profiles` plutôt que de maintenir la duplication indéfiniment.

**RLS (Row Level Security) : ne pas se fier à des policies permissives comme mesure de sécurité réelle.** Si l'API accède à la base avec une clé de service qui bypass RLS de toute façon (cas courant), une policy `USING (true)` ne protège rien — la sécurité réelle repose entièrement sur les dépendances d'authentification côté API (section 3). Documenter ce choix explicitement dans la migration SQL elle-même (commentaire), pour qu'un futur lecteur ne croie pas à tort que RLS filtre quoi que ce soit ici.

## 2. Vérification du JWT (cas Supabase Auth / OIDC générique)

Pattern robuste à privilégier : validation via les clés publiques du provider (JWKS), avec repli sur un appel direct à l'API du provider si les clés ne sont pas joignables :

```python
_jwks_cache: dict | None = None
_jwks_cached_at: float = 0.0
_JWKS_TTL = 3600

async def _validate_via_jwks(token: str) -> tuple[str, str]:
    global _jwks_cache, _jwks_cached_at
    if _jwks_cache is None or time.time() - _jwks_cached_at > _JWKS_TTL:
        _jwks_cache = await _fetch_jwks()
        _jwks_cached_at = time.time()
    header = jwt.get_unverified_header(token)
    key = _jwks_cache[header["kid"]]
    payload = jwt.decode(token, key=key, algorithms=["RS256", "ES256", "EdDSA"],
                          options={"verify_aud": False})  # le provider peut émettre le même aud pour tous les projets
    return payload["sub"], payload.get("email", "")

async def _validate_via_supabase_api(token: str) -> tuple[str, str]:
    # Repli si les clés JWKS ne sont pas joignables (rotation trop rapide, panne réseau) :
    # interroge directement l'API d'auth du provider avec le token.
    ...
```

Mettre les clés publiques en cache avec une durée de vie raisonnable (pas de fetch réseau à chaque requête), et gérer la rotation de clé via l'identifiant `kid` présent dans l'en-tête du JWT plutôt que de figer une seule clé en dur.

## 3. Dépendances imbriquées : valider puis autoriser

Séparer strictement la validation du token (authentification) de la vérification du rôle (autorisation), en chaînant deux dépendances :

```python
async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not credentials:
        raise HTTPException(401, "Authentification requise")
    try:
        auth_user_id, email = await _validate_via_jwks(credentials.credentials)
    except ExpiredSignatureError:
        raise HTTPException(401, "Token expiré")
    except Exception:
        auth_user_id, email = await _validate_via_supabase_api(credentials.credentials)

    profile = _load_profile(auth_user_id)   # jointure user_profiles + roles
    if not profile:
        raise HTTPException(403, "Profil introuvable — contacter l'administrateur")
    return {
        "id": auth_user_id, "email": email, "role": profile["role_name"],
        "allowed_collections": profile["allowed_collections"],
    }

async def require_admin(current_user: dict = Depends(require_auth)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(403, "Accès réservé aux administrateurs")
    return current_user
```

Usage sur une route :
```python
@router.get("/users")
async def list_users(admin: dict = Depends(require_admin)):
    ...
```

**Point de sécurité le plus important de cette section** : cette protection est posée route par route, explicitement, via `Depends(...)`. Ne pas s'appuyer sur un middleware global "qui protégerait tout par défaut" à moins de l'avoir vraiment enregistré et testé — un middleware défini dans le code mais jamais enregistré sur l'application est un piège fréquent (le code existe, rassure en lecture, mais ne protège rien). Après avoir écrit `require_auth`/`require_admin`, vérifier systématiquement qu'aucune route sensible n'a été oubliée sans sa dépendance.

`allowed_collections=None` doit conventionnellement signifier "pas de restriction" (rôle admin) et `allowed_collections=[]` doit signifier "aucun accès" — cette distinction doit être respectée jusque dans le filtrage du vector store (voir `references/vector-store.md` §4) ; une confusion entre les deux est la source la plus probable d'une fuite de données entre utilisateurs ou, à l'inverse, d'un blocage total d'un utilisateur légitime.

## 4. Clé de service — usage et sécurisation

Une clé "service role" (droits élevés, bypass RLS) est nécessaire pour les opérations d'administration (créer/lister/supprimer des comptes utilisateurs via l'API d'administration du provider d'auth) que la clé publique ne peut pas effectuer.

```python
def _service_key() -> str:
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    if not key:
        raise HTTPException(500, "SUPABASE_SERVICE_KEY non configuré")
    return key
```

Règles à respecter strictement :
- jamais exposée côté client (uniquement lue depuis une variable d'environnement backend) ;
- jamais renvoyée dans une réponse API, même à un administrateur ;
- son absence doit lever une erreur explicite (500) plutôt qu'un repli silencieux vers un comportement dégradé qui masquerait le problème de configuration.

## 5. Routes admin CRUD utilisateurs — pattern type

| Méthode | Route | Effet |
|---|---|---|
| GET | `/auth/users` | Liste les profils (jointure rôle), enrichis avec les emails via l'API admin du provider |
| POST | `/auth/users` | Crée le compte via l'API admin du provider, résout le rôle, insère le profil |
| PATCH | `/auth/users/{id}` | Met à jour rôle/collections/profil |
| DELETE | `/auth/users/{id}` | Supprime via l'API admin (la suppression du profil suit par `ON DELETE CASCADE`) |

Toutes protégées par `Depends(require_admin)`. Prévoir aussi un logging des connexions (table d'accès, consultable par un admin) si une traçabilité des connexions est un besoin du projet.

## RBAC côté frontend

Le filtrage des onglets/vues visibles selon le rôle est purement déclaratif côté client (confort d'affichage, pas une mesure de sécurité) — le rôle vient d'un appel serveur au login (`/auth/me` ou équivalent) et doit être revérifié à chaque montage de l'app pour refléter un changement de rôle sans attendre une reconnexion complète. La sécurité réelle est revalidée indépendamment par chaque endpoint backend via `require_auth`/`require_admin` — ne jamais considérer le filtrage d'affichage frontend comme suffisant en soi. Voir `references/frontend.md` §6 pour le détail du pattern d'affichage par rôle.

## Où aller ensuite

- Comment `allowed_collections` filtre effectivement le retrieval → `references/vector-store.md` §4
- Restriction d'accès aux routes d'évaluation (également réservées aux admins) → `references/evaluation.md`
