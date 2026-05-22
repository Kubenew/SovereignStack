from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI(title="OASA Compute Service", version="2026.1")

LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "llama3")

class CompletionRequest(BaseModel):
    model: str
    prompt: str
    context: str = ""

@app.post("/completion")
def completion(req: CompletionRequest):
    if req.context:
        response = f"[{LOCAL_MODEL_NAME}] Context-aware answer: {req.prompt}\n\nContext:\n{req.context[:1000]}"
    else:
        response = f"[{LOCAL_MODEL_NAME}] Answer: {req.prompt}"
    return {"response": response}

@app.get("/health")
def health():
    return {"status":"ok","service":"compute"}
