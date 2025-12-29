import json
import os
from datetime import datetime
from typing import List, Dict, Optional


# -----------------------------
# Configuration
# -----------------------------

ANALYTICS_DIR = "data/analytics"
ANALYTICS_FILE = os.path.join(ANALYTICS_DIR, "interactions.json")

os.makedirs(ANALYTICS_DIR, exist_ok=True)


# -----------------------------
# Logger Function
# -----------------------------

def log_interaction(
    question: str,
    answer: str,
    sources: List[Dict],
    confidence: Optional[float] = None
) -> None:
    """
    Logs user interactions safely into a JSON file.
    """

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "answer": answer,
        "sources": sources,
    }

    if confidence is not None:
        log_entry["confidence"] = round(float(confidence), 4)

    try:
        # Load existing logs safely
        if os.path.exists(ANALYTICS_FILE):
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
        else:
            data = []
            

        data.append(log_entry)

        # Atomic write (prevents corruption)
        temp_file = ANALYTICS_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        os.replace(temp_file, ANALYTICS_FILE)

    except Exception as e:
        # Logging must NEVER crash the app
        print(f"[LOGGER ERROR] {e}")