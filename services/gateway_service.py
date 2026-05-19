from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, requests, uuid, json
from datetime import datetime

app = FastAPI(title="OASA Gateway Service", version="2026.1")

COMPUTE_URL = os.getenv("COMPUTE_URL", "http://compute:8083")
MEMORY_URL = os.getenv("MEMORY_URL", "http://memory:8082")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
AUDIT_PATH = os.path.join(DATA_DIR, "audit.log")

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list
    oasa_compliance_lock: bool = False
    use_rag: bool = True

def audit(event: dict):
    event["ts"] = datetime.utcnow().isoformat()
    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

@app.post("/v1/chat/completions")
def chat(payload: ChatCompletionRequest):
    request_id = str(uuid.uuid4())
    user_prompt = payload.messages[-1].get("content", "")

    audit({"type":"request","id":request_id,"model":payload.model,"prompt":user_prompt})

    context = ""
    if payload.use_rag:
        try:
            r = requests.post(f"{MEMORY_URL}/query", json={"query": user_prompt})
            if r.status_code == 200:
                context = r.json().get("context","")
        except Exception:
            context = ""

    r = requests.post(f"{COMPUTE_URL}/completion", json={"model":payload.model,"prompt":user_prompt,"context":context})
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail="Compute backend failure")

    answer = r.json().get("response","")
    audit({"type":"response","id":request_id,"response":answer})

    return {
        "id": request_id,
        "object": "chat.completion",
        "model": payload.model,
        "choices": [{"index":0,"message":{"role":"assistant","content":answer}}]
    }

@app.get("/health")
def health():
    return {"status":"ok","service":"gateway"}
