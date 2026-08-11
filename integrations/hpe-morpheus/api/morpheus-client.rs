//! Rust reference module for the SovereignStack x HPE Morpheus integration.
//!
//! This file mirrors the runnable Python implementation
//! (`morpheus_client.py`) for teams embedding governance natively in Rust
//! control-plane agents. It is documentation-grade: it is not part of the
//! workspace build, but is kept structurally identical to the Python contract
//! so the wire format and decision flow match exactly.
//!
//! Core contract: identity -> capability -> policy -> decision -> Morpheus ->
//! provenance -> evidence.

use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

pub fn sha256_hex(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hex::encode(hasher.finalize())
}

/// Deterministic canonical JSON bytes (sorted keys, compact separators).
pub fn canonical_json(obj: &Value) -> Vec<u8> {
    to_canonical(obj)
}

fn to_canonical(obj: &Value) -> Vec<u8> {
    let sorted = sort_value(obj);
    serde_json::to_vec(&sorted).expect("canonical serialization")
}

fn sort_value(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut sorted = Map::new();
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            for key in keys {
                sorted.insert(key.clone(), sort_value(&map[key]));
            }
            Value::Object(sorted)
        }
        Value::Array(items) => Value::Array(items.iter().map(sort_value).collect()),
        other => other.clone(),
    }
}

// ─── signing helpers ────────────────────────────────────────────────────────

pub fn sign(payload: &[u8], private_key_hex: &str) -> String {
    let key_bytes = hex::decode(private_key_hex).expect("valid hex private key");
    let signing_key = SigningKey::from_bytes(key_bytes.as_slice().try_into().expect("32 bytes"));
    hex::encode(signing_key.sign(payload).to_bytes())
}

pub fn verify(payload: &[u8], signature_hex: &str, public_key_hex: &str) -> bool {
    let Ok(sig_bytes) = hex::decode(signature_hex) else {
        return false;
    };
    let Ok(key_bytes) = hex::decode(public_key_hex) else {
        return false;
    };
    let Ok(key_bytes): Result<[u8; 32], _> = key_bytes.as_slice().try_into() else {
        return false;
    };
    let Ok(key) = VerifyingKey::from_bytes(&key_bytes) else {
        return false;
    };
    let sig = Signature::from_slice(&sig_bytes).ok();
    match sig {
        Some(sig) => key.verify(payload, &sig).is_ok(),
        None => false,
    }
}

// ─── request / decision types ───────────────────────────────────────────────

#[derive(Clone, Serialize, Deserialize)]
pub struct GovernedRequest {
    pub action: String,
    pub agent_uri: String,
    pub capability: String,
    pub spec: Value,
    pub nonce: String,
    pub environment: Option<String>,
    #[serde(default)]
    pub signature: Option<String>,
}

impl GovernedRequest {
    /// Canonical message an agent signs (never includes the signature).
    pub fn message(&self) -> Value {
        json!({
            "action": self.action,
            "agent_uri": self.agent_uri,
            "capability": self.capability,
            "spec": self.spec,
            "nonce": self.nonce,
            "environment": self.environment,
        })
    }

    pub fn sign(&mut self, private_key_hex: &str) {
        let payload = canonical_json(&self.message());
        self.signature = Some(sign(&payload, private_key_hex));
    }
}

#[derive(Clone, Serialize)]
pub struct GovernedDecision {
    pub decision: String, // ALLOW | DENY
    pub agent_uri: String,
    pub capability: String,
    #[serde(default)]
    pub checks: Vec<Value>,
    #[serde(default)]
    pub reason: Option<String>,
    #[serde(default)]
    pub escalate: bool,
    #[serde(default)]
    pub morpheus_called: bool,
    #[serde(default)]
    pub vm_id: Option<String>,
}

// ─── provenance ─────────────────────────────────────────────────────────────

#[derive(Clone, Serialize)]
pub struct ProvenanceEntry {
    pub seq: u64,
    pub action: String,
    pub agent_uri: String,
    pub object_uri: String,
    pub decision: String,
    pub detail: Value,
    pub prev_hash: Option<String>,
    pub content_hash: String,
    pub signature: Option<String>,
}

impl ProvenanceEntry {
    fn content_bytes(&self) -> Vec<u8> {
        canonical_json(&json!({
            "action": self.action,
            "agent_uri": self.agent_uri,
            "object_uri": self.object_uri,
            "decision": self.decision,
            "detail": self.detail,
        }))
    }

    pub fn new(seq: u64, action: &str, agent_uri: &str, object_uri: &str, decision: &str, detail: Value, prev_hash: Option<String>) -> Self {
        let mut entry = ProvenanceEntry {
            seq,
            action: action.to_string(),
            agent_uri: agent_uri.to_string(),
            object_uri: object_uri.to_string(),
            decision: decision.to_string(),
            detail,
            prev_hash,
            content_hash: String::new(),
            signature: None,
        };
        entry.content_hash = sha256_hex(&entry.content_bytes());
        entry
    }

    /// Payload that is actually signed (excludes the signature field itself).
    pub fn signature_payload(&self) -> Vec<u8> {
        canonical_json(&json!({
            "seq": self.seq,
            "content_hash": self.content_hash,
            "prev_hash": self.prev_hash,
            "action": self.action,
            "agent_uri": self.agent_uri,
            "object_uri": self.object_uri,
            "decision": self.decision,
            "detail": self.detail,
        }))
    }

    /// Linkage hash covers the signature, so tampering any field breaks the chain.
    pub fn hash(&self) -> String {
        let payload = canonical_json(&json!({
            "seq": self.seq,
            "content_hash": self.content_hash,
            "prev_hash": self.prev_hash,
            "signature": self.signature,
            "action": self.action,
            "agent_uri": self.agent_uri,
            "object_uri": self.object_uri,
            "decision": self.decision,
            "detail": self.detail,
        }));
        sha256_hex(&payload)
    }

    pub fn sign(&mut self, private_key_hex: &str) {
        let payload = self.signature_payload();
        self.signature = Some(sign(&payload, private_key_hex));
    }
}

#[derive(Default)]
pub struct ProvenanceChain {
    pub target: String,
    pub entries: Vec<ProvenanceEntry>,
}

impl ProvenanceChain {
    pub fn append(&mut self, mut entry: ProvenanceEntry, private_key_hex: Option<&str>) {
        let expected = self.entries.last().map(|e| e.hash());
        if entry.prev_hash != expected {
            panic!("linkage broken: expected prev_hash {expected:?}, found {:?}", entry.prev_hash);
        }
        if let Some(key) = private_key_hex {
            entry.sign(key);
        }
        self.entries.push(entry);
    }

    pub fn verify(&self, public_keys: &std::collections::HashMap<String, String>, node_public_key: &str) -> (bool, Vec<String>) {
        let mut reasons = Vec::new();
        let mut expected: Option<String> = None;
        for entry in &self.entries {
            if entry.prev_hash != expected {
                reasons.push(format!("entry {}: broken linkage", entry.seq));
                return (false, reasons);
            }
            if entry.content_hash != sha256_hex(&entry.content_bytes()) {
                reasons.push(format!("entry {}: content tampered", entry.seq));
                return (false, reasons);
            }
            let signature = entry.signature.as_deref().unwrap_or("");
            let agent_key = public_keys.get(&entry.agent_uri).map(String::as_str);
            let node_key = Some(node_public_key);
            let keys: Vec<&str> = [agent_key, node_key].into_iter().flatten().collect();
            if !keys.iter().any(|k| verify(&entry.signature_payload(), signature, k)) {
                reasons.push(format!("entry {}: invalid signature", entry.seq));
                return (false, reasons);
            }
            expected = Some(entry.hash());
        }
        reasons.push(format!("chain verified: {} entries", self.entries.len()));
        (true, reasons)
    }
}

// ─── governed client ────────────────────────────────────────────────────────

pub struct GovernedClient {
    pub endpoint: String,
    pub identity: std::collections::HashMap<String, String>, // agent_uri -> public_key
    pub capabilities: std::collections::HashMap<String, Vec<String>>, // agent_uri -> capability grants
    pub chain: ProvenanceChain,
    pub node_public_key_hex: String,
    pub node_private_key_hex: String,
    seen_nonces: std::collections::HashSet<String>,
}

impl GovernedClient {
    pub fn new(
        endpoint: &str,
        identity: std::collections::HashMap<String, String>,
        capabilities: std::collections::HashMap<String, Vec<String>>,
        chain: ProvenanceChain,
        node_public_key_hex: &str,
        node_private_key_hex: &str,
    ) -> Self {
        GovernedClient {
            endpoint: endpoint.to_string(),
            identity,
            capabilities,
            chain,
            node_public_key_hex: node_public_key_hex.to_string(),
            node_private_key_hex: node_private_key_hex.to_string(),
            seen_nonces: std::collections::HashSet::new(),
        }
    }

    /// Run the full governance pipeline for one action.
    pub fn govern(&mut self, request: &mut GovernedRequest) -> GovernedDecision {
        let mut checks: Vec<Value> = Vec::new();
        let mut decision = GovernedDecision {
            decision: "DENY".to_string(),
            agent_uri: request.agent_uri.clone(),
            capability: request.capability.clone(),
            checks: Vec::new(),
            reason: None,
            escalate: false,
            morpheus_called: false,
            vm_id: None,
        };

        // Replay protection
        if self.seen_nonces.contains(&request.nonce) {
            decision.reason = Some("REPLAY_DETECTED".to_string());
            decision.checks = vec![json!({"check": "nonce", "result": "FAIL", "detail": "nonce reused"})];
            return decision;
        }
        self.seen_nonces.insert(request.nonce.clone());

        // 1. Identity
        let payload = canonical_json(&request.message());
        let valid = match (&request.signature, self.identity.get(&request.agent_uri)) {
            (Some(sig), Some(pub_key)) => verify(&payload, sig, pub_key),
            _ => false,
        };
        checks.push(json!({"check": "identity", "result": if valid { "PASS" } else { "FAIL" }}));
        if !valid {
            decision.reason = Some("IDENTITY_VIOLATION".to_string());
            decision.checks = checks;
            return decision;
        }

        // 2. Capability
        let has_capability = self
            .capabilities
            .get(&request.agent_uri)
            .map(|caps| caps.contains(&request.capability))
            .unwrap_or(false);
        checks.push(json!({"check": "capability", "result": if has_capability { "PASS" } else { "FAIL" }}));
        if !has_capability {
            decision.reason = Some("CAPABILITY_VIOLATION".to_string());
            decision.checks = checks;
            return decision;
        }

        // 3. Policy — RFC-0075 safe halt: no explicit allow rules => deny.
        let policy_ok = self.evaluate_policy(request);
        checks.push(json!({"check": "policy", "result": if policy_ok { "ALLOW" } else { "DENY" }}));
        if !policy_ok {
            decision.reason = Some("POLICY_VIOLATION".to_string());
            decision.checks = checks;
            return decision;
        }

        // 4. Execute against Morpheus
        let vm_id = self.call_morpheus(&request.spec);
        decision.decision = "ALLOW".to_string();
        decision.morpheus_called = true;
        decision.vm_id = Some(vm_id.clone());
        decision.checks = checks;

        // 5. Provenance
        self.record(&request, &decision, &vm_id);
        decision
    }

    fn evaluate_policy(&self, _request: &GovernedRequest) -> bool {
        // Reference: policy rules are evaluated by the Python engine. In this
        // module the policy set is left to the embedding agent; the shape of the
        // decision flow is what must match the wire contract.
        true
    }

    fn call_morpheus(&self, _spec: &Value) -> String {
        // Reference: HTTP POST {endpoint}/api/vms with Authorization bearer
        // token. Returns the created VM id. Mirrors morpheus_client.py.
        "vm-reference-1001".to_string()
    }

    fn record(&mut self, request: &GovernedRequest, decision: &GovernedDecision, vm_id: &str) {
        let object_uri = format!("vm://morpheus/{vm_id}");
        let prev_hash = self.chain.entries.last().map(|e| e.hash());
        let mut entry = ProvenanceEntry::new(
            (self.chain.entries.len() + 1) as u64,
            &request.action,
            &request.agent_uri,
            &object_uri,
            &decision.decision,
            json!({"vm_id": vm_id, "checks": decision.checks}),
            prev_hash,
        );
        entry.sign(&self.node_private_key_hex);
        self.chain.append(entry, None);
    }

    pub fn audit_verification(&self) -> (bool, Vec<String>) {
        self.chain.verify(&self.identity, &self.node_public_key_hex)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    fn keypair() -> (String, String) {
        let signing_key = SigningKey::from_bytes(&[0x42u8; 32]);
        let public_key = signing_key.verifying_key();
        (
            hex::encode(signing_key.to_bytes()),
            hex::encode(public_key.to_bytes()),
        )
    }

    #[test]
    fn signed_request_verifies_roundtrip() {
        let (private, public) = keypair();
        let mut request = GovernedRequest {
            action: "provision-vm".into(),
            agent_uri: "agent://ml-platform".into(),
            capability: "capability://compute/provision".into(),
            spec: json!({"cpu": 8}),
            nonce: "n1".into(),
            environment: Some("production".into()),
            signature: None,
        };
        request.sign(&private);
        let payload = canonical_json(&request.message());
        assert!(verify(&payload, request.signature.as_deref().unwrap(), &public));
    }

    #[test]
    fn tamper_detection_breaks_chain() {
        let (private, public) = keypair();
        let mut chain = ProvenanceChain { target: "chain://morpheus/test".into(), entries: vec![] };
        let mut entry = ProvenanceEntry::new(
            1, "provision-vm", "agent://ml-platform", "vm://morpheus/vm-1", "ALLOW",
            json!({"memory_gb": 32}), None,
        );
        entry.sign(&private);
        chain.entries.push(entry);
        chain.entries[0].detail = json!({"memory_gb": 512});
        let (ok, reasons) = chain.verify(&HashMap::new(), &public);
        assert!(!ok);
        assert!(reasons.iter().any(|r| r.contains("tampered")));
    }
}
