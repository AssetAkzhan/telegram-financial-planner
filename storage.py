import json
import os

def load_data(user_id):
    path = f"user_{user_id}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"income": 0, "budgets": {}, "expenses": []}

def save_data(user_id, data):
    path = f"user_{user_id}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
