import json
import os

CRED_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')

def load_credentials():
    """Load credentials from JSON file."""
    if not os.path.exists(CRED_FILE):
        return {}
    try:
        with open(CRED_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_credentials(data):
    """Save credentials to JSON file."""
    with open(CRED_FILE, 'w') as f:
        json.dump(data, f, indent=2)
