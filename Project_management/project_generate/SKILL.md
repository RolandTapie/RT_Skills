---
name: project:generate
description: Generate complete, functional code and comprehensive tests for a feature based on its specifications (requirements.md, design.md, plan.md). Creates production-ready code in src/{number}-feature-name/ with proper structure, type hints, and full test coverage. Use this after /project:analyze to implement individual features.
---

# Project Generate

Génère le code complet et les tests pour une feature basée sur ses spécifications.

## Usage

```
/project:generate 001-feature-name
/project:generate 002-feature-name
```

## What to do

1. **Validate prerequisites**:
   - `project.toml` exists with `stack = "python"` or `stack = "react"`
   - `features/{number}-{feature-name}/` exists with all three spec files:
     - `requirements.md`
     - `design.md`
     - `plan.md`

2. **Extract feature number and name** from the argument:
   - Example: `001-user-auth` → number: `001`, name: `user-auth`

3. **Read the specification files**:
   - Parse `requirements.md` - Functional specs
   - Parse `design.md` - Technical design
   - Parse `plan.md` - Implementation plan

4. **Generate complete code** in `src/{number}-{name}/` based on stack:

   **Python (uv)**:
   - `__init__.py` - Module exports
   - `models.py` - Pydantic models
   - `service.py` - Business logic
   - `repository.py` - Data access (if applicable)
   - `api.py` - Routes (if applicable)
   - Type hints throughout
   - Docstrings for public functions

   **React (npm)**:
   - `components/` - React components
   - `hooks/` - Custom hooks
   - `services/` - API calls / business logic
   - `types.ts` - TypeScript interfaces
   - `index.ts` - Barrel export

5. **Generate comprehensive tests** in `tests/`:
   - **Python**: `tests/test_{number}_{name}.py`
     - Unit tests for all business logic
     - Integration tests if applicable
     - Use pytest with fixtures
     - Follow AAA pattern (Arrange, Act, Assert)
   
   - **React**: `tests/{number}-{name}.test.tsx`
     - Component tests with React Testing Library
     - Mock external services

6. **Code quality**:
   - Follow PEP 8 (Python) or ESLint (React)
   - Strict type hints / TypeScript
   - Error handling for edge cases
   - Self-documenting through clear naming
   - No commented code, no TODOs
   - Minimal, focused code

7. **Report**:
   - Show directory structure created
   - List all generated files
   - Confirm ready to test and integrate

## Code Standards

**Python example:**
```python
from pydantic import BaseModel

class UserModel(BaseModel):
    id: int
    name: str
    email: str

class UserService:
    """User management."""
    
    def __init__(self, repository):
        self.repository = repository
    
    def create_user(self, data: UserModel) -> UserModel:
        """Create a new user."""
        # Implementation
        pass
```

**React example:**
```typescript
export interface User {
  id: number;
  name: string;
}

export const UserList: React.FC<{users: User[]}> = ({users}) => {
  return (/* JSX */);
};
```

## Guidelines
- Generate **complete, runnable code** (not stubs)
- Every function does exactly what the spec says
- Tests have good coverage of happy paths and edge cases
- Follow the plan.md for file structure and order
- Each module has one responsibility
