"""Dépendances FastAPI d'authentification/autorisation — voir references/rbac-auth.md §2-3.

À ADAPTER avant usage :
- `_fetch_jwks`/`_validate_via_provider_api` doivent pointer vers le provider d'auth réel
  (Supabase, Auth0, un IdP OIDC maison...).
- `_load_profile` doit interroger le schéma réel du projet (jointure user_profiles + roles).

RAPPEL DE SÉCURITÉ : cette protection est posée route par route via Depends(...). Il n'y a
pas de middleware global qui protégerait automatiquement les routes non annotées — vérifie
systématiquement qu'aucune route sensible n'a été oubliée sans sa dépendance.
"""
from __future__ import annotations

import time
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)

_jwks_cache: Optional[dict] = None
_jwks_cached_at: float = 0.0
_JWKS_TTL = 3600


async def _fetch_jwks() -> dict:
    raise NotImplementedError("Récupérer les clés publiques JWKS du provider d'auth réel du projet")


async def _validate_via_jwks(token: str) -> tuple[str, str]:
    global _jwks_cache, _jwks_cached_at
    if _jwks_cache is None or time.time() - _jwks_cached_at > _JWKS_TTL:
        _jwks_cache = await _fetch_jwks()
        _jwks_cached_at = time.time()
    header = jwt.get_unverified_header(token)
    key = _jwks_cache[header["kid"]]
    payload = jwt.decode(token, key=key, algorithms=["RS256", "ES256", "EdDSA"], options={"verify_aud": False})
    return payload["sub"], payload.get("email", "")


async def _validate_via_provider_api(token: str) -> tuple[str, str]:
    raise NotImplementedError("Repli : valider le token via l'API du provider d'auth si JWKS indisponible")


def _load_profile(auth_user_id: str) -> Optional[dict]:
    raise NotImplementedError(
        "Charger user_profiles + roles pour auth_user_id, retourner "
        "{'full_name', 'role_name', 'allowed_collections'} ou None si profil introuvable"
    )


async def require_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentification requise — token manquant")

    token = credentials.credentials
    try:
        try:
            auth_user_id, email = await _validate_via_jwks(token)
        except jwt.ExpiredSignatureError:
            raise
        except Exception:
            auth_user_id, email = await _validate_via_provider_api(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"Token invalide : {exc}")

    profile = _load_profile(auth_user_id)
    if not profile:
        raise HTTPException(status_code=403, detail="Profil utilisateur introuvable — contacter l'administrateur")

    return {
        "id": auth_user_id,
        "email": email,
        "full_name": profile["full_name"],
        "role": profile["role_name"],
        # None = pas de restriction (admin), [] = aucun accès. Ne jamais confondre les deux
        # (voir references/rbac-auth.md §3 et references/vector-store.md §4).
        "allowed_collections": profile["allowed_collections"],
    }


async def require_admin(current_user: dict = Depends(require_auth)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    return current_user
