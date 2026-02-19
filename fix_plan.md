# 🛠️ Night Watchman: Fix Plan - 2026-02-18 23:11

Architectural Drift detected. The following violations must be reconciled:

- [ ] **Direct DB Import** in `analytics.py`: Router imports from 'sqlalchemy' - Violation of 3-Layer Cake.
- [ ] **Direct DB Import** in `analytics.py`: Router imports from 'sqlalchemy.orm' - Violation of 3-Layer Cake.

## Proposed Action: Refactor routers to use the Service layer exclusively.