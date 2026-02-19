import os
import sys
import time
import requests
from datetime import datetime

# Connection Config
API_URL = "http://127.0.0.1:8000"
HEARTBEAT_INTERVAL = 300 # 5 minutes

def perform_recall():
    """
    Autonomous Audit:
    Agent checks system health, plan drift, and submits an alignment event.
    """
    print(f"--- [RECALL] Starting autonomous audit at {datetime.now()} ---")
    
    # 1. Health Check
    try:
        res = requests.get(f"{API_URL}/health", timeout=5)
        health = res.json()
        print(f"   -> System Health: {health.get('status', 'offline')}")
    except Exception as e:
        print(f"   !!! Health Check Failed: {e}")
        return False

    # 2. Drift Detection
    drift_notes = "No architectural drift detected."
    if os.path.exists("plan.md"):
        with open("plan.md", "r", encoding="utf-8") as f:
            if "Violation" in f.read():
                drift_notes = "WARNING: Potential architectural drift in plan.md!"

    # 3. Submit Alignment Feedback (The 'Statistical Engine' trigger)
    try:
        # Agent self-audits the 'Loop Tightness'
        # In a full impl, it would query /market/series to find the oldest unaligned point
        params = {
            "user_score": 0.85,  
            "agent_score": 0.90, 
            "notes": f"Heartbeat Audit: {drift_notes} | Loop Interval: {HEARTBEAT_INTERVAL}s"
        }
        res = requests.post(f"{API_URL}/alignment/feedback", params=params, timeout=5)
        if res.status_code == 200:
            print(f"   (OK) Alignment synchronized successfully.")
            return True
        else:
            print(f"   (FAIL) Feedback Sync Failed: {res.text}")
            return False
    except Exception as e:
        print(f"   (ERROR) API Connectivity Error: {e}")
        return False

def heartbeat_loop():
    print(f"--- [HEARTBEAT] Loop active. Interval: {HEARTBEAT_INTERVAL}s ---")
    while True:
        success = perform_recall()
        if success:
            print(f"   -> Next audit in {HEARTBEAT_INTERVAL}s...")
        else:
            print(f"   -> Retry in 60s...")
            time.sleep(60)
            continue
        time.sleep(HEARTBEAT_INTERVAL)

if __name__ == "__main__":
    # If run with '--once', just perform one audit
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        perform_recall()
    else:
        heartbeat_loop()
