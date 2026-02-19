# Architecture Law: MINGL-1 Unified Data Manager

## 1. Modularity
Final code MUST follow the **Repository-Service-Router** pattern.
- **Repository**: `app/repositories/` (Direct DB access)
- **Service**: `app/services/` (Business logic, orchestration)
- **Router**: `app/routers/` (API endpoints, schema validation)
- **Frontend**: `dashboard.py` (UI only, NO direct DB access)

## 2. Locking Governance (Windows Scale)
Direct DuckDB access from multiple processes is forbidden on Windows. All data access MUST flow through the FastAPI backend API via the `MarketService`.

## 3. Storage Hierarchy
- **Tier 1**: In-memory buffer
- **Tier 2**: DuckDB Warehouse
- **Tier 3**: Parquet Archive (LZO/ZSTD compressed)

## 4. Redundancy Gate
Before creating a new repository or service, you MUST check existing files. Integrating with established patterns is mandatory.
