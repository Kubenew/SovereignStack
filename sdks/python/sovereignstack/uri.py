"""URI parsing and scheme registry for SovereignStack objects."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class UriScheme(str, Enum):
    """All registered SovereignStack URI schemes."""
    # Cognitive
    AGENT = "agent"
    SESSION = "session"
    ARTIFACT = "artifact"
    MEMORY = "memory"
    MIND = "mind"
    REASON = "reason"
    GOAL = "goal"
    BELIEF = "belief"
    KNOWLEDGE = "knowledge"
    CAPABILITY = "capability"
    WORKFLOW = "workflow"
    CONTRACT = "contract"
    EVENT = "event"
    CHECKPOINT = "checkpoint"
    EVIDENCE = "evidence"
    # Federation
    ORG = "org"
    NODE = "node"
    GATEWAY = "gateway"
    FABRIC = "fabric"
    TOPOLOGY = "topology"
    ROUTING = "routing"
    # Infrastructure
    COMPUTE = "compute"
    BANDWIDTH = "bandwidth"
    STORAGE = "storage"
    ENERGY = "energy"
    ROBOT = "robot"
    POLICY = "policy"
    # Memory & Cache
    KV = "kv"
    MEM = "mem"
    TEL = "tel"
    PROFILE = "profile"
    MODEL = "model"
    DATASET = "dataset"
    TRAINING = "training"
    EVALUATION = "evaluation"
    # Recovery
    AUDIT_PKG = "audit-pkg"
    CONTINUITY = "continuity"
    RECOVERY = "recovery"
    FAILOVER = "failover"
    PLAYBOOK = "playbook"
    SNAPSHOT = "snapshot"
    MIGRATION = "migration"
    # Meta-cognition
    META = "meta"
    SELF = "self"
    REFLECTION = "reflection"
    IMPROVEMENT = "improvement"
    EXPLANATION = "explanation"
    SUMMARY = "summary"
    TIMELINE = "timeline"
    # Safety & Governance
    SAFEGUARD = "safeguard"
    VALUES = "values"
    PROTOCOL = "protocol"
    OPERATOR = "operator"
    SANDBOX = "sandbox"
    REPLAY = "replay"
    GOVERNANCE = "governance"
    LINEAGE = "lineage"
    LEASE = "lease"
    TWIN = "twin"
    IDENTITY = "identity"
    MESH = "mesh"
    WORLD = "world"
    PLAN = "plan"
    TOOL = "tool"
    TRANSITION = "transition"
    # Cognitive Development
    IDEA = "idea"
    RESEARCH = "research"
    DECISION = "decision"
    ARCHITECTURE = "architecture"
    SPEC = "spec"
    BUILD = "build"
    RELEASE = "release"
    PROJECT = "project"
    FLOW = "flow"
    # Digital Twins
    PERSON = "person"
    COMPANY = "company"
    BANK = "bank"
    HOSPITAL = "hospital"
    PORTFOLIO = "portfolio"
    FUND = "fund"
    BOND = "bond"
    STOCK = "stock"
    FACTORY = "factory"
    VEHICLE = "vehicle"
    CITY = "city"
    # Digital Economy
    ECONOMY = "economy"
    ASSET = "asset"
    PAYMENT = "payment"
    TREASURY = "treasury"
    MARKET = "market"
    RISK = "risk"
    INSURANCE = "insurance"
    SETTLEMENT = "settlement"
    EXCHANGE = "exchange"
    TAX = "tax"
    DERIVATIVE = "derivative"
    ACCOUNT = "account"


@dataclass
class ParsedUri:
    scheme: UriScheme
    authority: str
    path: Optional[str] = None
    raw: str = ""


def parse_uri(uri: str) -> ParsedUri:
    """Parse a SovereignStack URI into its components.

    Example:
        >>> p = parse_uri("payment://cbdc/ecb/pacs008-001")
        >>> p.scheme
        UriScheme.PAYMENT
        >>> p.authority
        'cbdc'
        >>> p.path
        'ecb/pacs008-001'
    """
    if "://" not in uri:
        raise ValueError(f"Invalid URI (missing ://): {uri}")

    scheme_str, rest = uri.split("://", 1)
    try:
        scheme = UriScheme(scheme_str)
    except ValueError:
        raise ValueError(f"Unknown URI scheme: {scheme_str}")

    parts = rest.split("/", 1)
    authority = parts[0]
    path = parts[1] if len(parts) > 1 else None

    return ParsedUri(scheme=scheme, authority=authority, path=path, raw=uri)
