import os
import json
import time
import uuid
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
CONTRACTS_FILE = os.path.join(DATA_DIR, "contracts.json")
TICKETS_FILE = os.path.join(DATA_DIR, "support_tickets.json")
UPDATES_FILE = os.path.join(DATA_DIR, "update_history.json")
RELEASES_FILE = os.getenv("RELEASES_MANIFEST_URL", "https://releases.sovereignstack.ai/manifest.json")
SUPPORT_API_KEY = os.getenv("SUPPORT_API_KEY", "")

app = FastAPI(title="OASA Enterprise Service", version="2026.3")


_TIER_FEATURES = {
    "community": ["basic_support", "community_forum"],
    "standard": ["basic_support", "email_support", "audit_logs", "sla_8h"],
    "enterprise": ["basic_support", "email_support", "phone_support", "audit_logs",
                   "sla_4h", "managed_updates", "deployment_audits", "sso"],
    "enterprise-plus": ["basic_support", "email_support", "phone_support",
                        "dedicated_engineer", "audit_logs", "sla_1h",
                        "managed_updates", "deployment_audits", "sso",
                        "custom_integration", "on_prem_deployment"],
}


def _default_features(tier: str) -> list[str]:
    return _TIER_FEATURES.get(tier, _TIER_FEATURES["standard"])


def _load_json(path: str, default: list | dict):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _save_json(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _require_api_key(auth: Optional[str] = None):
    if SUPPORT_API_KEY:
        if not auth or not hmac.compare_digest(auth, SUPPORT_API_KEY):
            raise HTTPException(401, "Valid Support API key required")


class ContractRequest(BaseModel):
    customer_name: str
    tier: str = "standard"
    start_date: str = ""
    end_date: str = ""
    max_nodes: int = 1
    features: list[str] = []
    sla_response_hours: int = 8


class TicketRequest(BaseModel):
    subject: str
    description: str = ""
    severity: str = "normal"
    customer_name: str = ""
    contact_email: str = ""


class UpdateApplyRequest(BaseModel):
    update_id: str
    confirm: bool = False


@app.get("/health")
def health():
    return {"status": "ok", "service": "enterprise", "version": "2026.3"}


@app.get("/enterprise/contract")
def get_contract():
    contracts = _load_json(CONTRACTS_FILE, [])
    if not contracts:
        return {"active": False, "message": "No active support contract"}
    return {"active": True, "contract": contracts[-1]}


@app.post("/enterprise/contract")
def create_contract(req: ContractRequest):
    contracts = _load_json(CONTRACTS_FILE, [])
    contract = {
        "id": str(uuid.uuid4()),
        "customer_name": req.customer_name,
        "tier": req.tier,
        "start_date": req.start_date or datetime.now(timezone.utc).isoformat(),
        "end_date": req.end_date or "",
        "max_nodes": req.max_nodes,
        "features": req.features or _default_features(req.tier),
        "sla_response_hours": req.sla_response_hours,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    contracts.append(contract)
    _save_json(CONTRACTS_FILE, contracts)
    return {"status": "activated", "contract": contract}


@app.get("/enterprise/sla")
def get_sla():
    contracts = _load_json(CONTRACTS_FILE, [])
    tickets = _load_json(TICKETS_FILE, [])
    if not contracts:
        return {"status": "no_contract"}
    contract = contracts[-1]
    total_tickets = len(tickets)
    resolved = sum(1 for t in tickets if t.get("status") == "resolved")
    sla_breaches = sum(1 for t in tickets if "breach_at" in t)
    return {
        "contract_tier": contract["tier"],
        "sla_response_hours": contract["sla_response_hours"],
        "total_tickets": total_tickets,
        "resolved_tickets": resolved,
        "resolution_rate": round(resolved / total_tickets * 100, 1) if total_tickets else 100.0,
        "sla_breaches": sla_breaches,
        "sla_compliance": f"{round((1 - sla_breaches / max(total_tickets, 1)) * 100, 1)}%",
    }


@app.post("/enterprise/ticket")
def create_ticket(req: TicketRequest):
    tickets = _load_json(TICKETS_FILE, [])
    now = datetime.now(timezone.utc)
    ticket = {
        "id": str(uuid.uuid4()),
        "subject": req.subject,
        "description": req.description,
        "severity": req.severity,
        "customer_name": req.customer_name,
        "contact_email": req.contact_email,
        "status": "open",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    contracts = _load_json(CONTRACTS_FILE, [])
    if contracts:
        sla_hours = contracts[-1].get("sla_response_hours", 8)
        ticket["sla_deadline"] = datetime.fromtimestamp(time.time() + sla_hours * 3600, tz=timezone.utc).isoformat()
    tickets.append(ticket)
    _save_json(TICKETS_FILE, tickets)
    return {"status": "created", "ticket": ticket}


@app.get("/enterprise/tickets")
def list_tickets(status: Optional[str] = None):
    tickets = _load_json(TICKETS_FILE, [])
    if status:
        tickets = [t for t in tickets if t.get("status") == status]
    return {"tickets": tickets, "count": len(tickets)}


@app.get("/enterprise/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    tickets = _load_json(TICKETS_FILE, [])
    for t in tickets:
        if t["id"] == ticket_id:
            return {"ticket": t}
    raise HTTPException(404, "Ticket not found")


@app.post("/enterprise/tickets/{ticket_id}/resolve")
def resolve_ticket(ticket_id: str):
    tickets = _load_json(TICKETS_FILE, [])
    for t in tickets:
        if t["id"] == ticket_id:
            t["status"] = "resolved"
            t["resolved_at"] = datetime.now(timezone.utc).isoformat()
            _save_json(TICKETS_FILE, tickets)
            return {"status": "resolved", "ticket": t}
    raise HTTPException(404, "Ticket not found")


@app.get("/enterprise/updates/check")
def check_updates():
    history = _load_json(UPDATES_FILE, [])
    return {
        "current_version": "2026.3",
        "latest_version": "2026.3",
        "updates_available": False,
        "update_history": history[-5:] if history else [],
    }


@app.post("/enterprise/updates/apply")
def apply_update(req: UpdateApplyRequest):
    if not req.confirm:
        return {"status": "confirmation_required"}
    history = _load_json(UPDATES_FILE, [])
    entry = {
        "update_id": req.update_id,
        "version": "2026.3",
        "status": "applied",
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }
    history.append(entry)
    _save_json(UPDATES_FILE, history)
    return {"status": "update_applied", "update": entry}


@app.get("/enterprise/license")
def get_license():
    contracts = _load_json(CONTRACTS_FILE, [])
    if not contracts:
        return {"licensed": False}
    contract = contracts[-1]
    return {
        "licensed": True,
        "tier": contract["tier"],
        "customer": contract["customer_name"],
        "max_nodes": contract["max_nodes"],
        "features": contract["features"],
        "expires": contract.get("end_date", "perpetual"),
    }
