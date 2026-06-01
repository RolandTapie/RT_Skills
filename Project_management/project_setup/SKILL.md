---
name: project:setup
description: Initialize a new project structure with the chosen development stack (Python with uv or React with npm). Creates project.toml, pyproject.toml or package.json, and base directories (src/, tests/, features/). Use this when starting a new project or setting up project configuration.
---

# Project Setup

Initialise la structure de base d'un projet avec le stack choisi.

## Usage

```
/project:setup --stack python
/project:setup --stack react
```

## What to do

1. **Validate the stack choice**: Must be "python" or "react"

2. **Check if project.toml exists** at the root of the current directory
   - If it exists: update only the `[project]` section
   - If it doesn't exist: create it

3. **Create project.toml** with:
   ```toml
   [project]
   stack = "python"  # or "react"
   ```

4. **Create project configuration files** based on stack:
   - **Python**: Create `pyproject.toml` if it doesn't exist
   - **React**: Create `package.json` if it doesn't exist

5. **Create base directories** (if they don't exist):
   - `src/` - Source code
   - `tests/` - Tests
   - `features/` - Feature specifications

6. **Report** what was created and show the directory structure

## Notes
- Don't overwrite existing files (warn the user instead)
- project.toml is minimal — only stores the stack choice
- Don't install dependencies yet
