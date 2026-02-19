# Architectural Law: sofa-scale-guide
**Status: ALWAYS ON**

## 1. Layered Separation (The Cake Pattern)
All code MUST be partitioned into three distinct layers. No layer may skip its neighbor.

- **Routers (`app/routers/`)**: 
    - *Job*: Front Desk. Handles HTTP requests/responses, auth, and validation.
    - *Constraint*: No direct database imports (DuckDB/SQLAlchemy). Calls Services.
- **Services (`app/services/`)**: 
    - *Job*: The Brain. Handles business logic, mathematical models (Gumbel, etc.).
    - *Constraint*: Environment agnostic. Calls Repositories for data.
- **Repositories (`app/repositories/`)**: 
    - *Job*: The Librarian. The ONLY place `import duckdb` or `sqlite3` is allowed.
    - *Constraint*: Returns Pydantic models or clean DataFrames.

## 2. Async First
- Every route (`async def`) and every database call must be asynchronous.
- Use `run_in_executor` or `anyio` for blocking DuckDB calls to prevent thread starvation on the 20 GB file.

## 3. Data Hardening
- Every entity and data point MUST have a **Pydantic V2** schema.
- Strict typing is mandatory. No `Any`.

## 4. Observability
- Every major component must have structured logging: `[COMPONENT_NAME] Message`.
- A `/health` endpoint must exist to verify DuckDB reachability and lock status.
