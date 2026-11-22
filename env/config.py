from pathlib import Path
import os

BASE = Path(__file__).parent.parent
AGENTS_DIR = BASE / "agents"
CONTEXT_DIR = BASE / "context"
LOG_DIR = CONTEXT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

BUS_FILE = BASE / "bus.jsonl"
ORDERS_FILE = BASE / "orders.jsonl"

GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
EMBED_MODEL = "nomic-embed-text"

def _load_env():
    env_file = Path(__file__).parent / "keys.env"
    if env_file.exists():
        for line in env_file.read_text().strip().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

_load_env()

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
