import json
import time
import sys
from datetime import datetime
from pathlib import Path

import requests
import pyttsx3
import chromadb
from duckduckgo_search import DDGS
from mss import mss
import mss.tools

from env import BASE, GROQ_KEY, GROQ_URL, GROQ_MODEL, LOG_DIR

SCREENSHOT_DIR = BASE / "context" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR = BASE / "chroma"

tts = pyttsx3.init()
tts.setProperty("rate", 170)

def log(msg):
    line = "[" + datetime.now().strftime("%H:%M:%S") + "] " + msg
    print(line)
    with open(LOG_DIR / "asiste.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")

def pensar(messages, tools=None):
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 2048,
    }
    if tools:
        payload["tools"] = tools
    r = requests.post(
        GROQ_URL,
        headers={"Authorization": "Bearer " + GROQ_KEY},
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]

def leer_archivo(path):
    p = BASE / path
    if p.exists():
        return p.read_text(encoding="utf-8")[:5000]
    return "No existe: " + path

def escribir_archivo(path, content):
    p = BASE / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return "Escrito: " + path + " (" + str(len(content)) + " chars)"

def buscar_web(query):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
    if not results:
        return "Sin resultados."
    return "\n".join("- " + r["title"] + ": " + r["body"][:200] for r in results)

def buscar_memoria(query):
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        col = client.get_collection("memoria")
        res = col.query(query_texts=[query], n_results=5)
        if res["documents"][0]:
            return "\n".join(res["documents"][0])
        return "Sin resultados."
    except Exception:
        return "Memoria vacia."

def guardar_memoria(content, tags=""):
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection("memoria")
    doc_id = "mem_" + str(int(time.time()*1000))
    col.add(documents=[content], metadatas=[{"tags": tags}], ids=[doc_id])
    return "Guardado."

def navegador(action, url="", selector="", text=""):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(headless=False)
        page = br.new_page(viewport={"width": 1280, "height": 800})
        if action == "navigate":
            page.goto(url, wait_until="domcontentloaded")
            result = "Navegado: " + page.title()
        elif action == "click":
            page.goto(url or "about:blank", wait_until="domcontentloaded")
            page.click(selector)
            result = "Clic: " + selector
        elif action == "type":
            page.goto(url or "about:blank", wait_until="domcontentloaded")
            page.fill(selector, text)
            result = "Escribi: " + text
        elif action == "snapshot":
            if url:
                page.goto(url, wait_until="domcontentloaded")
            result = "Titulo: " + page.title() + "\n" + page.content()[:3000]
        elif action == "screenshot":
            if url:
                page.goto(url, wait_until="domcontentloaded")
            path = SCREENSHOT_DIR / ("br_" + datetime.now().strftime("%H%M%S") + ".png")
            page.screenshot(path=str(path))
            result = "Screenshot: " + str(path)
        else:
            result = "Accion desconocida: " + action
        br.close()
        return result

def capturar_pantalla():
    path = SCREENSHOT_DIR / ("screen_" + datetime.now().strftime("%H%M%S") + ".png")
    with mss() as sct:
        img = sct.grab(sct.monitors[1])
        mss.tools.to_png(img.rgb, img.size, output=str(path))
    return str(path)

def hablar(texto):
    log("VOZ: " + texto)
    tts.say(texto)
    tts.runAndWait()
    return "Dicho."

TOOLS = [
    {"type": "function", "function": {
        "name": "leer_archivo",
        "description": "Lee un archivo y devuelve su contenido.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
    }},
    {"type": "function", "function": {
        "name": "escribir_archivo",
        "description": "Crea o sobrescribe un archivo.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}
    }},
    {"type": "function", "function": {
        "name": "buscar_web",
        "description": "Busca en internet (DuckDuckGo).",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    }},
    {"type": "function", "function": {
        "name": "buscar_memoria",
        "description": "Busca en la memoria vectorial.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    }},
    {"type": "function", "function": {
        "name": "guardar_memoria",
        "description": "Guarda algo en la memoria persistente.",
        "parameters": {"type": "object", "properties": {"content": {"type": "string"}, "tags": {"type": "string"}}, "required": ["content"]}
    }},
    {"type": "function", "function": {
        "name": "navegador",
        "description": "Controla el navegador. Acciones: navigate, click, type, snapshot, screenshot.",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["navigate", "click", "type", "snapshot", "screenshot"]},
            "url": {"type": "string"}, "selector": {"type": "string"}, "text": {"type": "string"}
        }, "required": ["action"]}
    }},
    {"type": "function", "function": {
        "name": "capturar_pantalla",
        "description": "Toma screenshot del escritorio completo.",
        "parameters": {"type": "object", "properties": {}}
    }},
    {"type": "function", "function": {
        "name": "hablar",
        "description": "Habla un texto por voz al usuario.",
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}
    }},
]

TOOL_MAP = {
    "leer_archivo": leer_archivo,
    "escribir_archivo": escribir_archivo,
    "buscar_web": buscar_web,
    "buscar_memoria": buscar_memoria,
    "guardar_memoria": guardar_memoria,
    "navegador": navegador,
    "capturar_pantalla": capturar_pantalla,
    "hablar": hablar,
}

SYSTEM = "Eres Asiste, el asistente personal de Steve (CDMX, 29 anos). Puedes ver su pantalla, escucharlo, buscar en la web, controlar el navegador, leer/escribir archivos, y hablar por voz. Reglas: Espanol mexicano tono casual. Si necesitas una herramienta usala. Respuestas cortas usar hablar. Maximo 2 herramientas por turno. Si no sabes di que no sabes."

def listen():
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            print("  MIC: Escuchando... (o presiona Enter para texto)")
            audio = r.listen(source, timeout=8, phrase_time_limit=30)
            return r.recognize_google(audio, language="es-MX")
    except Exception:
        return input("  > ")

def chat_loop():
    messages = [{"role": "system", "content": SYSTEM}]
    print("")
    print("=" * 50)
    print("  ASISTE - Listo. Di algo. 'salir' para terminar.")
    print("=" * 50)
    print("")

    while True:
        user_input = listen()
        if user_input.lower().strip() in ("salir", "adios", "chao", "bye"):
            hablar("Hasta luego, Steve.")
            break
        if not user_input.strip():
            continue

        log("Oido: " + user_input)
        messages.append({"role": "user", "content": user_input})

        try:
            msg = pensar(messages, TOOLS)

            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    fn = TOOL_MAP.get(tc["function"]["name"])
                    args = tc["function"]["arguments"]
                    log("TOOL: " + tc["function"]["name"] + "(" + str(args) + ")")
                    result = fn(**args) if fn else "No encontrada."
                    log("RESULT: " + str(result)[:150])
                    messages.append({"role": "assistant", "content": msg.get("content", ""), "tool_calls": [tc]})
                    messages.append({"role": "tool", "content": str(result), "name": tc["function"]["name"]})
                msg = pensar(messages)

            reply = msg.get("content", "")
            if reply:
                log("RESP: " + reply)
                if len(reply) < 120 and "\n" not in reply:
                    hablar(reply)
            messages.append({"role": "assistant", "content": reply})

            if len(messages) > 22:
                messages = [messages[0]] + messages[-20:]

        except Exception as e:
            log("ERROR: " + str(e))
            hablar("Hubo un error.")
            messages.append({"role": "assistant", "content": "Error."})

if __name__ == "__main__":
    chat_loop()
