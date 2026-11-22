┌─────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (LLM)                    │
│  Recibe task → decide qué agent usar → evalúa resultado │
└────────────────────────┬────────────────────────────────┘
                         │ JSONL message bus
                         ▼
┌─────────────────────────────────────────────────────────┐
│                     DISPATCHER (script)                  │
│  Lee mensaje → rutea al agent → maneja retries          │
└───┬──────────┬──────────┬──────────┬────────────────────┘
    ▼          ▼          ▼          ▼
┌───────┐ ┌─────────┐ ┌────────┐ ┌──────────┐
│Coder  │ │Researcher│ │Tester  │ │Reviewer  │
│Agent  │ │Agent    │ │Agent   │ │Agent     │
└───────┘ └─────────┘ └────────┘ └──────────┘
    │          │          │          │
    └──────────┴──────────┴──────────┘
                         │
                    Vector Memory
                    (ChromaDB)   
