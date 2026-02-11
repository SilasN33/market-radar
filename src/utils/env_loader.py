"""Load environment variables from .env file."""
from pathlib import Path


def load_env():
    """Load environment variables from .env file if it exists."""
    # Path adjustment: src/utils/env_loader.py -> parents[2] is root
    env_file = Path(__file__).resolve().parents[2] / ".env"
    
    if not env_file.exists():
        return
    
    import os
    
    with env_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()
