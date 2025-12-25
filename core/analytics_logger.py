import json
import os
from datetime import datetime

ANALYTICS_DIR = "data/analytics"
ANALYTICS_FILE = os.path.join(ANALYTICS_DIR, "interactions.json")

os.makedirs(ANALYTICS_DIR, exist_ok=True)

def log_interaction(question, answer, sources, confidence=None):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer,
        "sources": sources
    }

    if confidence is not None:
        log_entry["confidence"] = confidence

    try:
        with open(ANALYTICS_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append(log_entry)

    with open(ANALYTICS_FILE, "w") as f:
        json.dump(data, f, indent=2)
