import os
import sys
# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))
from app.data_controller import data_controller

def test_controller():
    print("Testing UnifiedDataController...")
    entity_id = 9999
    metric = "load_test"
    
    # Add data
    data_controller.add_observation(entity_id, metric, 42.0)
    data_controller.add_user_override(entity_id, metric, 99.0)
    
    # Verify layered retrieval
    series = data_controller.get_layered_series(entity_id, metric)
    print(f"Retrieved series: {series}")
    
    if len(series) >= 1:
        print("✅ Data Ingestion Successful")
    else:
        print("❌ Data Ingestion Failed")

if __name__ == "__main__":
    test_controller()
