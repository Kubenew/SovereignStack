from fastapi import FastAPI, UploadFile, File
import hashlib, os, uuid, json

app = FastAPI(title="OASA Ingest Service", version="2026.1")

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
INGEST_DIR = os.path.join(DATA_DIR, "ingest")

@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    doc_id = str(uuid.uuid4())
    raw = await file.read()
    sha = hashlib.sha256(raw).hexdigest()

    text = raw.decode("utf-8", errors="ignore")

    result = {
        "doc_id": doc_id,
        "source_filename": file.filename,
        "sha256": sha,
        "pages": [{"page": 1, "text": text}]
    }

    os.makedirs(INGEST_DIR, exist_ok=True)
    out_path = os.path.join(INGEST_DIR, f"{doc_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return {"doc_id": doc_id, "sha256": sha, "output": out_path}

@app.get("/health")
def health():
    return {"status":"ok","service":"ingest"}
