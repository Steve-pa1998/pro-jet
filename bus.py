import json
from datetime import datetime
from env import BUS_FILE, ORDERS_FILE

def publish(agent, estado, problema="", resultado=""):
    msg = {"timestamp": datetime.now().isoformat(), "agent": agent,
           "estado": estado, "problema": problema, "resultado": resultado}
    with open(BUS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")

def read_last(n=20):
    if not BUS_FILE.exists():
        return []
    lines = BUS_FILE.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(l) for l in lines[-n:]]

def publish_order(to, task, priority=2, context=""):
    msg = {"type": "order", "to": to, "task": task, "priority": priority,
           "context": context, "timestamp": datetime.now().isoformat(), "status": "pendiente"}
    with open(ORDERS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")

def read_pending():
    if not ORDERS_FILE.exists():
        return []
    orders, done_ids = [], set()
    for line in ORDERS_FILE.read_text(encoding="utf-8").strip().splitlines():
        msg = json.loads(line)
        if msg.get("type") == "done":
            done_ids.add(msg["order_id"])
    for line in ORDERS_FILE.read_text(encoding="utf-8").strip().splitlines():
        msg = json.loads(line)
        if msg.get("type") == "order" and msg["timestamp"] not in done_ids:
            orders.append(msg)
    orders.sort(key=lambda x: x.get("priority", 2))
    return orders

def mark_done(order_ts, success, output=""):
    msg = {"type": "done", "order_id": order_ts, "success": success,
           "output": output[:500], "timestamp": datetime.now().isoformat()}
    with open(ORDERS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")
