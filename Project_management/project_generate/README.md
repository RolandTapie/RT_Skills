# `/project:generate` - Code Generation Skill

**Génère le code complet et les tests pour une feature basée sur ses spécifications.**

---

## 📌 Vue d'Ensemble

Cette skill lit les spécifications d'une feature et génère **du code production-ready** avec type hints, docstrings et tests complets.

**Elle crée:**
- Code dans `src/{number}-{name}/` (models, service, repository, API)
- Tests dans `tests/test_{number}_{name}.py` (pytest ou React Testing Library)
- Code immédiatement compilable/exécutable

---

## 🚀 Utilisation

### Commande
```bash
/project:generate 001-member-management
```

### Paramètre
- **Feature**: Numéro + nom de la feature
  - Format : `{number}-{feature-name}`
  - Example: `001-member-management`, `002-event-api`
  - Case-sensitive : respecter la casse exacte

---

## 📋 Prérequis

Avant de générer, s'assurer que :

1. ✅ `project.toml` existe avec `stack = "python"` ou `"react"`
2. ✅ `features/{number}-{feature-name}/` existe
3. ✅ 3 fichiers de spec existent:
   - `requirements.md`
   - `design.md`
   - `plan.md`

### Vérifier les Prérequis
```bash
# Vérifier project.toml
cat project.toml

# Vérifier les specs
ls features/001-member-management/
# Doit montrer: requirements.md, design.md, plan.md
```

---

## 📂 Code Généré - Python

### Structure
```
src/
├── models/
│   ├── __init__.py
│   └── member.py         # Pydantic models pour Member
├── services/
│   ├── __init__.py
│   └── member_service.py # Business logic pour Member
├── repositories/
│   ├── __init__.py
│   └── member_repository.py # Data access pour Member
├── api/
│   ├── __init__.py
│   └── members.py        # FastAPI routes /members
└── __init__.py

tests/
└── test_member_service.py  # Comprehensive tests (pytest)
```

**Important:** Code est centralisé, pas par feature !
- Tous les models dans `src/models/`
- Tous les services dans `src/services/`
- Tous les repositories dans `src/repositories/`
- Toutes les routes dans `src/api/`

### Exemple: src/models/member.py
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MemberIn(BaseModel):
    """Input model for creating a member."""
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    phone: Optional[str] = None

class MemberOut(MemberIn):
    """Output model for member data."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Exemple: src/services/member_service.py
```python
from typing import List
from ..models.member import MemberIn, MemberOut
from ..repositories.member_repository import MemberRepository

class MemberService:
    """Service for managing members."""
    
    def __init__(self, repository: MemberRepository):
        """Initialize with dependency injection."""
        self.repository = repository
    
    def create_member(self, data: MemberIn) -> MemberOut:
        """Create a new member.
        
        Args:
            data: Member input data
            
        Returns:
            Created member with ID
            
        Raises:
            ValueError: If email already exists
        """
        # Check if email exists
        existing = self.repository.get_by_email(data.email)
        if existing:
            raise ValueError(f"Email {data.email} already registered")
        
        # Create and return
        return self.repository.create(data)
    
    def list_members(self, skip: int = 0, limit: int = 100) -> List[MemberOut]:
        """List all members with pagination."""
        return self.repository.list(skip=skip, limit=limit)
    
    def get_member(self, member_id: int) -> MemberOut:
        """Get a specific member by ID."""
        member = self.repository.get(member_id)
        if not member:
            raise ValueError(f"Member {member_id} not found")
        return member
```

### Exemple: src/api/members.py
```python
from fastapi import APIRouter, HTTPException
from typing import List
from ..models.member import MemberIn, MemberOut
from ..services.member_service import MemberService

router = APIRouter(prefix="/members", tags=["members"])
service = MemberService()  # ou via dependency injection

@router.post("/", response_model=MemberOut, status_code=201)
async def create_member(data: MemberIn):
    """Create a new member.
    
    Args:
        data: Member information
        
    Returns:
        Created member
        
    Raises:
        HTTPException: 400 if email already exists
    """
    try:
        return service.create_member(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[MemberOut])
async def list_members(skip: int = 0, limit: int = 100):
    """List all members with pagination."""
    return service.list_members(skip=skip, limit=limit)

@router.get("/{member_id}", response_model=MemberOut)
async def get_member(member_id: int):
    """Get a specific member by ID."""
    try:
        return service.get_member(member_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### Exemple: tests/test_member_service.py
```python
import pytest
from datetime import datetime
from src.models.member import MemberIn, MemberOut
from src.services.member_service import MemberService
from src.repositories.member_repository import MemberRepository

# Fixtures
@pytest.fixture
def mock_repository():
    """Mock repository for testing."""
    class MockRepository:
        def __init__(self):
            self.members = {}
            self.next_id = 1
        
        def create(self, data: MemberIn) -> MemberOut:
            member_id = self.next_id
            self.next_id += 1
            member = MemberOut(**data.dict(), id=member_id, created_at=datetime.now())
            self.members[member_id] = member
            return member
        
        def get(self, member_id: int):
            return self.members.get(member_id)
        
        def list(self, skip=0, limit=100):
            return list(self.members.values())[skip:skip+limit]
        
        def get_by_email(self, email):
            for member in self.members.values():
                if member.email == email:
                    return member
            return None
    
    return MockRepository()

@pytest.fixture
def service(mock_repository):
    """Create service with mock repository."""
    return MemberService(mock_repository)

# Tests
class TestMemberService:
    def test_create_member(self, service):
        """Test creating a new member."""
        # Arrange
        data = MemberIn(name="John Doe", email="john@example.com")
        
        # Act
        result = service.create_member(data)
        
        # Assert
        assert result.id == 1
        assert result.name == "John Doe"
        assert result.email == "john@example.com"
    
    def test_create_duplicate_email(self, service):
        """Test that duplicate email raises error."""
        # Arrange
        data = MemberIn(name="John", email="john@example.com")
        service.create_member(data)
        
        # Act & Assert
        with pytest.raises(ValueError, match="already registered"):
            service.create_member(data)
    
    def test_get_member(self, service):
        """Test getting a member by ID."""
        # Arrange
        data = MemberIn(name="John", email="john@example.com")
        created = service.create_member(data)
        
        # Act
        result = service.get_member(created.id)
        
        # Assert
        assert result.id == created.id
        assert result.name == "John"
```

**Note:** Tests sont dans `tests/test_member_service.py`, pas distribués par feature.

---

## 📂 Code Généré - React

### Structure
```
src/
├── components/                   # Tous les composants
│   ├── MemberList.tsx
│   ├── MemberForm.tsx
│   ├── MemberDetail.tsx
│   ├── EventCard.tsx
│   └── ...
├── hooks/                        # Tous les custom hooks
│   ├── useMember.ts
│   ├── useEvent.ts
│   └── ...
├── services/                     # Tous les services API
│   ├── memberApi.ts
│   ├── eventApi.ts
│   └── ...
├── pages/                        # Toutes les pages
│   ├── MembersPage.tsx
│   ├── EventsPage.tsx
│   └── ...
├── types.ts                      # Tous les interfaces TypeScript
├── utils/                        # Utilitaires partagés
│   └── helpers.ts
└── App.tsx

tests/
├── test_member_service.test.tsx
├── test_event_service.test.tsx
└── ...
```

**Important:** Code est centralisé et partagé !
- Tous les components dans `src/components/`
- Tous les hooks dans `src/hooks/`
- Tous les API services dans `src/services/`

### Exemple: src/types.ts
```typescript
export interface Member {
  id: number;
  name: string;
  email: string;
  phone?: string;
  createdAt: string;
}

export interface MemberCreate {
  name: string;
  email: string;
  phone?: string;
}
```

### Exemple: src/services/memberApi.ts
```typescript
import axios from 'axios';
import { Member, MemberCreate } from '../types';

const API_BASE = '/api/members';

export const memberApi = {
  create: async (data: MemberCreate): Promise<Member> => {
    const response = await axios.post(API_BASE, data);
    return response.data;
  },
  
  list: async (): Promise<Member[]> => {
    const response = await axios.get(API_BASE);
    return response.data;
  },
  
  get: async (id: number): Promise<Member> => {
    const response = await axios.get(`${API_BASE}/${id}`);
    return response.data;
  },
};
```

### Exemple: src/hooks/useMember.ts
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { memberApi } from '../services/memberApi';
import { Member, MemberCreate } from '../types';

export const useMemberList = () => {
  return useQuery({
    queryKey: ['members'],
    queryFn: memberApi.list,
  });
};

export const useCreateMember = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: memberApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members'] });
    },
  });
};
```

### Exemple: src/components/MemberList.tsx
```typescript
import React from 'react';
import { useMemberList } from '../hooks/useMember';
import { Member } from '../types';

export const MemberList: React.FC = () => {
  const { data: members = [], isLoading, error } = useMemberList();
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading members</div>;
  
  return (
    <div className="member-list">
      <h2>Members</h2>
      <ul>
        {members.map((member: Member) => (
          <li key={member.id}>
            <h3>{member.name}</h3>
            <p>{member.email}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};
```

---

## ✨ Caractéristiques du Code Généré

### Qualité
- ✅ Type hints complets (Python) / TypeScript strict
- ✅ Docstrings claires avec Args, Returns, Raises
- ✅ Error handling approprié
- ✅ Pas de code commenté
- ✅ Pas de TODOs
- ✅ Code self-documenting (bons noms)

### Tests
- ✅ Coverage de la logique métier
- ✅ Happy path + edge cases
- ✅ Mocks pour dépendances externes
- ✅ Pattern AAA (Arrange, Act, Assert)
- ✅ Tests indépendants et rapides

### Standards
- ✅ PEP 8 (Python) / ESLint (React)
- ✅ Single responsibility principle
- ✅ Dependency injection
- ✅ Modular structure

---

## 🔄 Workflow

```
/project:setup
/project:analyze
        ↓
features/001-member-management/ créé (specs)
        ↓
/project:generate 001-member-management
        ↓
src/001-member-management/ créé (code)
tests/test_001_member_management.py créé (tests)
        ↓
Tests passent ? → Oui
        ↓
/project:generate 002-next-feature
        ↓
...
```

---

## ⚠️ Important

### Une Feature à la Fois
Ne pas générer plusieurs features simultanément. Générer et intégrer feature par feature :
```bash
/project:generate 001-xxx
# Test & integrate 001

/project:generate 002-yyy
# Test & integrate 002
```

### Vérifier le Code
Après génération :
```bash
# Python
python -m pytest tests/test_001_*.py -v

# React
npm test
```

### Corriger les Spécifications
Si besoin avant de générer :
1. Édite les fichiers dans `features/{number}-{name}/`
2. Relance `/project:generate {number}-{name}`
3. Le nouveau code remplace l'ancien

---

## 💡 Tips

### 1. Intégration Progressive
Génère → Teste → Intègre → Répète
Ne pas attendre que tout soit fait avant de tester.

### 2. Imports Entre Features
Si feature 002 dépend de 001 :
```python
# Dans feature 002
from src.001_member_management import MemberService
```
C'est automatique, pas besoin de configurer.

### 3. Tester Immédiatement
```bash
# Après chaque /project:generate
pytest tests/ -v
# ou
npm test
```

### 4. Modifier & Régénérer
Si tu dois modifier une feature :
1. Modifie les specs
2. Relance `/project:generate`
Le code est remplacé, tes modifications perdues.

→ Mieux : modifie le code directement après génération, laisse les specs comme référence.

---

## ❓ FAQ

**Q: Puis-je modifier le code généré ?**
R: Oui ! C'est un point de départ. Une fois généré, c'est ton code.

**Q: Et si je veux régénérer une feature ?**
R: Modifie les specs et relance `/project:generate`. Ça remplace tout.

**Q: Combien de temps prend la génération ?**
R: Dépend de la complexité : Simple (5-10 min), Medium (15-25 min), Complex (30+ min).

**Q: Le code généré est prêt pour la production ?**
R: Prêt pour développement. À adapter pour production (config, secrets, monitoring, etc.).

**Q: Que faire avec le code généré ?**
R: Intégrer à ton projet, modifier si besoin, déployer.

---

**Version:** 1.0  
**Prérequis:** `/project:setup` + `/project:analyze` doivent être fait d'abord
