-- Migration RBAC de base — voir references/rbac-auth.md §1.
-- À ADAPTER : adapter la référence `auth.users` au schéma réel du provider d'auth utilisé
-- (ce nom est celui de Supabase Auth ; un autre provider peut avoir un schéma différent).

CREATE TABLE IF NOT EXISTS roles (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                 TEXT NOT NULL UNIQUE,           -- ex: 'admin', 'user'
  display_name         TEXT NOT NULL,
  allowed_collections  TEXT[] NOT NULL DEFAULT '{}',
  description          TEXT,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_profiles (
  id            UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  role_id       UUID REFERENCES roles(id),
  full_name     TEXT NOT NULL DEFAULT '',
  -- Surcharge individuelle optionnelle : si non nulle, prévaut sur les valeurs par défaut du rôle.
  -- Une seule table de profil porte cette notion — ne pas créer de table parallèle qui
  -- dupliquerait ce concept (voir references/rbac-auth.md §1, anti-pattern documenté).
  allowed_collections_override TEXT[],
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO roles (name, display_name, allowed_collections, description) VALUES
  ('admin', 'Administrateur', '{}', 'Accès à toutes les collections (allowed_collections=None applicatif)'),
  ('user',  'Utilisateur',    '{}', 'Accès restreint aux collections listées ici ou en surcharge du profil')
ON CONFLICT (name) DO NOTHING;

ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- RLS activée par convention, mais la sécurité réelle repose sur les dépendances FastAPI
-- require_auth/require_admin (l'API accède via une clé de service qui bypass RLS) — voir
-- assets/backend/auth/dependencies.py et references/rbac-auth.md §1.
CREATE POLICY service_role_all_roles ON roles FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_role_all_profiles ON user_profiles FOR ALL TO service_role USING (true) WITH CHECK (true);
