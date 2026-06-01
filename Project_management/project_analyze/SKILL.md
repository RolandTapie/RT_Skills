---
name: project:analyze
description: Parse a project description and generate feature specifications. Identifies distinct features, creates requirements.md, design.md, and plan.md for each feature in a numbered directory structure (001-feature-name/, 002-feature-name/, etc.). Use this when you have a project description and need to break it down into actionable feature specifications.
---

# Project Analyze

Analyse un descriptif de projet et génère les spécifications pour chaque feature identifiée.

## Usage

```
/project:analyze "Description complète du projet..."
```

## What to do

1. **Read the project description** provided by the user

2. **Analyze and identify distinct features**:
   - Parse the description carefully
   - Extract independent, cohesive features
   - Create clear kebab-case names (ex: "user-authentication", "email-notifications")

3. **Check existing features** in `features/` directory to determine the next number:
   - If `001-user-auth/` exists, start new features from `002-`
   - Number sequentially: `001-`, `002-`, `003-`, etc. (always 3 digits)

4. **For each feature**, create `features/{number}-{feature-name}/` with three files:

   **requirements.md** - Functional specification
   ```markdown
   # Requirements: {Feature Name}
   
   ## Description
   [What does this feature do?]
   
   ## User Stories
   - As a [user], I want [action], so that [benefit]
   
   ## Acceptance Criteria
   - [ ] Criterion 1
   - [ ] Criterion 2
   
   ## Dependencies
   - Other features (if any)
   ```

   **design.md** - Technical design
   ```markdown
   # Design: {Feature Name}
   
   ## Overview
   [Architecture overview]
   
   ## Components/Modules
   - List of modules and their purposes
   
   ## Data Models
   [Pydantic models, schemas, or TypeScript interfaces]
   
   ## API Endpoints / Functions
   [Method signatures, endpoints]
   
   ## External Dependencies
   [Libraries, services needed]

   ## Business Schema
    - draw the schema on the requirement
   ```

   **plan.md** - Implementation plan
   ```markdown
   # Implementation Plan: {Feature Name}
   
   ## Files to Create
   - src/{number}-feature-name/__init__.py
   - src/{number}-feature-name}/models.py
   - src/{number}-feature-name}/service.py
   - tests/test_{number}_feature_name.py
   
   ## Implementation Steps
   1. Create data models
   2. Implement business logic
   3. Create API endpoints (if applicable)
   4. Write tests
   5. Document public functions
   
   ## Testing Strategy
   - Unit tests for: [functions/components]
   - Integration tests for: [workflows]
   
   ## Complexity
   - Simple / Medium / Complex
   ```

5. **Summary**:
   - List all created features with numbers and names
   - Show directory structure
   - Confirm ready for `/project:generate`

## Guidelines
- Be thorough but concise
- Make specs actionable (ready for `/project:generate`)
- Number sequentially starting from 001
- Check existing features to avoid duplicate numbering
- If requirements are ambiguous, state assumptions clearly
- l'analyse des toutes les fonctionnalité doit être cohérente
