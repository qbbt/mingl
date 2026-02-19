---
name: check-before-refactor
description: Prevents redundant work and enforces architectural patterns during refactors.
---

# Thinking Process: Check Before Refactor

**Trigger**: When asked to refactor or move database logic.

## 1. Discovery Phase
Run a grep for `import duckdb` and `app/repositories/`. Identify where data access currently lives and if there are existing repositories.

## 2. State Analysis
Compare the current file structure against `architecture-law.md` (or the established Repository-Service pattern).

## 3. Redundancy Gate
If a file or logic already exists in `app/repositories/`, you are **FORBIDDEN** from creating a duplicate. You must update the existing one.

## 4. Artifact Check
Read the `plan.md` from the root directory to see what was already completed and ensure alignment with the single source of truth.
