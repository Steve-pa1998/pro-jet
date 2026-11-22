import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import time
import requests

from env import GROQ_KEY, GROQ_URL, GROQ_MODEL, BASE

SYSTEM = "Eres un desarrollador senior experto en C++ y Python. Escribe codigo limpio con comentarios en espanol. Si la tarea es ambigua haz suposiciones razonables y documentalas. Siempre devuelves el codigo completo no fragmentos."

def main():
    data = json.loads(sys.stdin.read())
    task = data["task"]
    context = data.get("context", "")

    r = requests.post(
        GROQ_URL,
        headers={"Authorization": "Bearer " + GROQ_KEY},
        json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": "Tarea: " + task + "\n\nContexto: " + context},
            ],
            "temperature": 0.2,
            "max_tokens": 8192,
        },
        timeout=120,
    )
    r.raise_for_status()
    codigo = r.json()["choices"][0]["message"]["content"]

    output_dir = BASE / "context" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / ("codi_" + str(int(time.time())) + ".md")
    out_file.write_text(codigo, encoding="utf-8")

    print(json.dumps({"success": True, "file": str(out_file), "length": len(codigo)}))

if __name__ == "__main__":
    main()
