import os
import sys
import subprocess
import time

def check_environment():
    print("[SENTINEL] Checking environment health...")
    
    # 1. Check Python Path
    print(f"[SENTINEL] Python Executable: {sys.executable}")
    
    # 2. Check for 20 GB DuckDB reachability
    db_path = "backend/data_store/warehouse.duckdb"
    if os.path.exists(db_path):
        size_gb = os.path.getsize(db_path) / (1024**3)
        print(f"[SENTINEL] Database found: {db_path} ({size_gb:.2f} GB)")
    else:
        print("[SENTINEL] WARNING: DuckDB warehouse not found at expected path.")

    # 3. Check for Port 8000 availability
    # (Simple socket check could go here)
    
    # 4. NumPy Version Conflict Check
    try:
        import numpy
        print(f"[SENTINEL] NumPy Version: {numpy.__version__}")
        if numpy.__version__.startswith("2"):
            print("[SENTINEL] CAUTION: NumPy 2.x detected. Ensure all C-extensions are compatible.")
    except Exception as e:
        print(f"[SENTINEL] ERROR: NumPy import failure: {e}")

if __name__ == "__main__":
    check_environment()
