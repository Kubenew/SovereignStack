from fastapi import FastAPI
from pydantic import BaseModel
import os, json, uuid

app = FastAPI(title="OASA Memory Service", version="2026.1")

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
MEMORY_DIR = os.path.join(DATA_DIR, "memory")
os.makedirs(MEMORY_DIR, exist_ok=True)

class EmbedRequest(BaseModel):
    doc_id: str
    text: str
    org_id: str = "default"

class QueryRequest(BaseModel):
    query: str
    org_id: str = "default"
    top_k: int = 3

@app.post("/embed")
def embed(req: EmbedRequest):
    item_id = str(uuid.uuid4())
    record = {"id": item_id, "doc_id": req.doc_id, "org_id": req.org_id, "text": req.text}

    with open(os.path.join(MEMORY_DIR, f"{item_id}.json"), "w", encoding="utf-8") as f:
        json.dump(record, f)

    return {"status": "stored", "id": item_id}

@app.post("/query")
def query(req: QueryRequest):
    matches = []
    for fn in os.listdir(MEMORY_DIR):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(MEMORY_DIR, fn), "r", encoding="utf-8") as f:
            rec = json.load(f)
        if rec.get("org_id") != req.org_id:
            continue
        if req.query.lower() in rec.get("text","").lower():
            matches.append(rec)

    matches = matches[:req.top_k]
    context = "\n\n".join([m["text"] for m in matches])

    return {"matches": matches, "context": context}

@app.get("/health")
def health():
    return {"status":"ok","service":"memory"}
