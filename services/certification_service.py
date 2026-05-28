import os
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
REGISTRY_FILE = os.path.join(DATA_DIR, "certification_registry.json")

app = FastAPI(title="OASA Certification Service", version="2026.3")

CERT_PROGRAMS = {
    "node": {
        "description": "Certified Node — server, edge, personal appliance",
        "levels": ["L1", "L2", "L3"],
        "requirements_l1": "Data ingestion, deterministic extraction, content hashing",
        "requirements_l2": "Memory isolation, local KV, vector store, encryption at rest",
        "requirements_l3": "Runtime AWQ/INT4, TEE-gated execution, rate-limited inference",
    },
    "runtime": {
        "description": "Certified Runtime — inference engine, gateway, memory, ingestion",
        "levels": ["L1", "L2", "L3"],
        "requirements_l1": "OASA-compatible API, compliance lock, audit log",
        "requirements_l2": "JWT auth, OPA policy engine, Merkle-tree audit, hardware binding",
        "requirements_l3": "TEE attestation, enclave-gated inference, runtime shield",
    },
    "federation": {
        "description": "Certified Federation — mesh node, relay, aggregator",
        "levels": ["L1", "L2", "L3"],
        "requirements_l1": "CRDT sync, event log, node identity",
        "requirements_l2": "Jurisdictional gating, signed events, peer health tracking",
        "requirements_l3": "Weight federation, cross-node inference, audit provenance",
    },
}


def _load_registry():
    try:
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"entries": [], "authorities": []}


def _save_registry(data):
    os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


class RegisterRequest(BaseModel):
    subject_name: str
    subject_version: str = "1.0.0"
    program: str
    level: str = "L1"
    contact: str = ""
    homepage: str = ""
    evidence_security_audit: str = ""
    evidence_sbom: str = ""
    evidence_conformance_report: str = ""
    hardware_tpm_version: str = ""
    hardware_gpu_models: list[str] = []
    hardware_confidential_compute: bool = False


class UpdateStatusRequest(BaseModel):
    status: str


class AuthorityRegisterRequest(BaseModel):
    name: str
    public_key_pem: str = ""


@app.get("/health")
def health():
    return {"status": "ok", "service": "certification", "version": "2026.3"}


@app.get("/certification/programs")
def list_programs():
    return {"programs": CERT_PROGRAMS}


@app.get("/certification/programs/{program}")
def get_program(program: str):
    if program not in CERT_PROGRAMS:
        raise HTTPException(404, f"Unknown certification program: {program}")
    return {"program": program, **CERT_PROGRAMS[program]}


@app.get("/certification/registry")
def list_registry(
    program: Optional[str] = None,
    level: Optional[str] = None,
    status: Optional[str] = None,
):
    reg = _load_registry()
    entries = reg["entries"]
    if program:
        entries = [e for e in entries if e.get("program") == program]
    if level:
        entries = [e for e in entries if e.get("level") == level]
    if status:
        entries = [e for e in entries if e.get("status") == status]
    return {"count": len(entries), "entries": entries}


@app.get("/certification/registry/{entry_id}")
def get_entry(entry_id: str):
    reg = _load_registry()
    for e in reg["entries"]:
        if e["id"] == entry_id:
            return e
    raise HTTPException(404, "Certification entry not found")


@app.post("/certification/registry")
def register_certification(req: RegisterRequest):
    if req.program not in CERT_PROGRAMS:
        raise HTTPException(400, f"Unknown program: {req.program}. Valid: {list(CERT_PROGRAMS.keys())}")
    prog = CERT_PROGRAMS[req.program]
    if req.level not in prog["levels"]:
        raise HTTPException(400, f"Invalid level {req.level} for {req.program}. Valid: {prog['levels']}")

    reg = _load_registry()
    now = datetime.now(timezone.utc)
    entry_id = str(uuid.uuid4())
    entry = {
        "id": entry_id,
        "subject_name": req.subject_name,
        "subject_version": req.subject_version,
        "program": req.program,
        "level": req.level,
        "status": "active",
        "issued": now.isoformat(),
        "expires": datetime.fromtimestamp(time.time() + 365 * 86400, tz=timezone.utc).isoformat(),
        "contact": req.contact,
        "homepage": req.homepage,
        "evidence": {
            "security_audit": req.evidence_security_audit,
            "sbom": req.evidence_sbom,
            "conformance_report": req.evidence_conformance_report,
        },
        "hardware": {
            "tpm_version": req.hardware_tpm_version,
            "gpu_models": req.hardware_gpu_models,
            "confidential_compute": req.hardware_confidential_compute,
        },
    }
    reg["entries"].append(entry)
    _save_registry(reg)
    return {"status": "registered", "entry": entry}


@app.post("/certification/registry/{entry_id}/status")
def update_entry_status(entry_id: str, req: UpdateStatusRequest):
    if req.status not in ("active", "expired", "revoked", "suspended"):
        raise HTTPException(400, "Status must be: active, expired, revoked, suspended")
    reg = _load_registry()
    for e in reg["entries"]:
        if e["id"] == entry_id:
            e["status"] = req.status
            e["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save_registry(reg)
            return {"status": "updated", "entry": e}
    raise HTTPException(404, "Entry not found")


@app.get("/certification/verify/{entry_id}")
def verify_entry(entry_id: str):
    reg = _load_registry()
    for e in reg["entries"]:
        if e["id"] == entry_id:
            now = datetime.now(timezone.utc)
            expires = datetime.fromisoformat(e["expires"])
            result = {
                "id": e["id"],
                "subject_name": e["subject_name"],
                "program": e["program"],
                "level": e["level"],
                "status": e["status"],
                "expired": now > expires,
                "valid": e["status"] == "active" and now <= expires,
                "issued": e["issued"],
                "expires": e["expires"],
            }
            return result
    raise HTTPException(404, "Entry not found")
