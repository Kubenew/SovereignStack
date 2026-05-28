import os
import json
import shutil
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

app = FastAPI(title="Sovereign Marketplace Service")

MARKETPLACE_DATA_DIR = os.getenv("MARKETPLACE_DATA_DIR", "/app/data/marketplace")
os.makedirs(MARKETPLACE_DATA_DIR, exist_ok=True)

class BundleMetadata(BaseModel):
    bundle_id: str
    name: str
    version: str
    author: str
    type: str
    description: Optional[str] = None

@app.post("/v1/marketplace/publish")
async def publish_bundle(
    metadata: str = Form(...),
    payload: UploadFile = File(None)
):
    """
    Publish an agent bundle to the local marketplace registry.
    """
    try:
        meta_dict = json.loads(metadata)
        bundle_meta = BundleMetadata(**meta_dict)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid metadata format: {exc}")
        
    # Validate bundle ID format (author/plugin-name)
    if "/" not in bundle_meta.bundle_id:
        raise HTTPException(status_code=400, detail="bundle_id must be in format 'author/plugin-name'")
        
    bundle_dir = os.path.join(MARKETPLACE_DATA_DIR, bundle_meta.bundle_id.replace("/", "_"))
    os.makedirs(bundle_dir, exist_ok=True)
    
    version_dir = os.path.join(bundle_dir, bundle_meta.version)
    if os.path.exists(version_dir):
        raise HTTPException(status_code=409, detail=f"Version {bundle_meta.version} already exists")
    os.makedirs(version_dir)
    
    # Save metadata
    with open(os.path.join(version_dir, "metadata.json"), "w") as f:
        json.dump(meta_dict, f, indent=2)
        
    # Save payload (tarball/zip) if provided
    if payload:
        file_path = os.path.join(version_dir, payload.filename or "payload.tar.gz")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(payload.file, buffer)
            
    return {"status": "published", "bundle_id": bundle_meta.bundle_id, "version": bundle_meta.version}

@app.get("/v1/marketplace/search")
async def search_bundles(query: str = "", author: str = ""):
    """
    Search the local marketplace registry.
    """
    results = []
    for bundle_name in os.listdir(MARKETPLACE_DATA_DIR):
        bundle_dir = os.path.join(MARKETPLACE_DATA_DIR, bundle_name)
        if not os.path.isdir(bundle_dir):
            continue
            
        # Get the latest version
        versions = sorted(os.listdir(bundle_dir), reverse=True)
        if not versions:
            continue
            
        latest = versions[0]
        meta_path = os.path.join(bundle_dir, latest, "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
                
            if query and query.lower() not in meta.get("name", "").lower() and query.lower() not in meta.get("description", "").lower():
                continue
            if author and author != meta.get("author"):
                continue
                
            results.append(meta)
            
    return {"results": results}

@app.get("/v1/marketplace/download/{bundle_author}/{bundle_name}/{version}")
async def download_bundle(bundle_author: str, bundle_name: str, version: str):
    """
    Download a bundle payload.
    In a real implementation, this would return a FileResponse.
    """
    bundle_id_safe = f"{bundle_author}_{bundle_name}"
    version_dir = os.path.join(MARKETPLACE_DATA_DIR, bundle_id_safe, version)
    
    if not os.path.exists(version_dir):
        raise HTTPException(status_code=404, detail="Bundle version not found")
        
    payload_files = [f for f in os.listdir(version_dir) if f != "metadata.json"]
    if not payload_files:
        return {"status": "no_payload", "metadata": json.load(open(os.path.join(version_dir, "metadata.json")))}
        
    # Simulated download URL for now
    return {"download_url": f"/static/marketplace/{bundle_id_safe}/{version}/{payload_files[0]}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)
