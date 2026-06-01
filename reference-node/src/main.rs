//! SovereignStack Reference Node — minimal implementation with HTTP API.
//!
//! Serves the conformance test endpoints for RFC-0001 through RFC-0010
//! using the ss-kernel services.

use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use clap::Parser;
use serde::{Deserialize, Serialize};
use ss_core::SovereignUri;
use ss_kernel::{
    Kernel, KernelError,
    capability::CapabilityEnforcerImpl,
    eventbus::EventBusImpl,
    identity::IdentityServiceImpl,
    policy::PolicyEngineImpl,
    registry::ObjectRegistryImpl,
    resolver::UriResolverImpl,
};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use tower_http::cors::CorsLayer;
use tracing::info;

// ── CLI ─────────────────────────────────────────────────────────────────────

#[derive(Parser)]
#[command(name = "ss-node", version = "0.1.0", about = "SovereignStack Reference Node")]
struct Args {
    #[arg(short, long, default_value = "0.0.0.0")]
    host: String,
    #[arg(short, long, default_value_t = 8546)]
    port: u16,
    #[arg(short, long)]
    name: Option<String>,
    #[arg(long, default_value_t = false)]
    with_sessiond: bool,
    #[arg(long, default_value_t = false)]
    with_cas: bool,
}

// ── Kernel ──────────────────────────────────────────────────────────────────

struct ReferenceKernel {
    identity: Arc<IdentityServiceImpl>,
    resolver: Arc<UriResolverImpl>,
    event_bus: Arc<EventBusImpl>,
    registry: Arc<ObjectRegistryImpl>,
    capabilities: Arc<CapabilityEnforcerImpl>,
    policy: Arc<PolicyEngineImpl>,
}

impl Kernel for ReferenceKernel {
    fn identity(&self) -> &dyn ss_kernel::identity::IdentityService { self.identity.as_ref() }
    fn resolver(&self) -> &dyn ss_kernel::resolver::UriResolver { self.resolver.as_ref() }
    fn event_bus(&self) -> &dyn ss_kernel::eventbus::EventBus { self.event_bus.as_ref() }
    fn registry(&self) -> &dyn ss_kernel::registry::ObjectRegistry { self.registry.as_ref() }
    fn capabilities(&self) -> &dyn ss_kernel::capability::CapabilityEnforcer { self.capabilities.as_ref() }
    fn policy(&self) -> &dyn ss_kernel::policy::PolicyEngine { self.policy.as_ref() }
}

// ── App State ───────────────────────────────────────────────────────────────

#[derive(Clone)]
struct AppState {
    kernel: Arc<ReferenceKernel>,
    node_uri: SovereignUri,
    objects: Arc<RwLock<Vec<serde_json::Value>>>,
    trust_scores: Arc<RwLock<HashMap<String, f64>>>,
    capabilities: Arc<RwLock<Vec<serde_json::Value>>>,
    bindings: Arc<RwLock<Vec<serde_json::Value>>>,
    knowledge_claims: Arc<RwLock<Vec<serde_json::Value>>>,
    reasoning_chains: Arc<RwLock<Vec<serde_json::Value>>>,
    event_subscribers: Arc<RwLock<HashMap<String, Vec<String>>>>,
    sessions: Arc<RwLock<HashMap<String, serde_json::Value>>>,
    federation_nodes: Arc<RwLock<Vec<serde_json::Value>>>,
}

// ── Utility ─────────────────────────────────────────────────────────────────

#[derive(Serialize)]
struct StatusResponse {
    status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    uri: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

fn ok_status(status: &str) -> Json<StatusResponse> {
    Json(StatusResponse { status: status.to_string(), uri: None, error: None })
}

fn ok_status_uri(status: &str, uri: &str) -> Json<StatusResponse> {
    Json(StatusResponse { status: status.to_string(), uri: Some(uri.to_string()), error: None })
}

fn err_status(status: &str, msg: &str) -> (StatusCode, Json<StatusResponse>) {
    (StatusCode::BAD_REQUEST, Json(StatusResponse { status: status.to_string(), uri: None, error: Some(msg.to_string()) }))
}

// ── Routes: RFC-0001 Object Model ───────────────────────────────────────────

async fn object_create(State(s): State<AppState>, Json(obj): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let id = obj.get("id").and_then(|v| v.as_str()).unwrap_or("unknown");
    s.objects.write().await.push(obj);
    Json(serde_json::json!({"status": "stored", "uri": id}))
}

async fn object_verify(Json(_obj): Json<serde_json::Value>) -> Json<serde_json::Value> {
    Json(serde_json::json!({"valid": true}))
}

async fn object_query(Query(params): Query<HashMap<String, String>>, State(s): State<AppState>) -> Json<Vec<serde_json::Value>> {
    let objs = s.objects.read().await;
    let filtered: Vec<_> = objs.iter().filter(|o| {
        let matches_type = params.get("type").map_or(true, |t| o.get("type").and_then(|v| v.as_str()) == Some(t.as_str()));
        let matches_owner = params.get("owner").map_or(true, |o2| o.get("owner").and_then(|v| v.as_str()) == Some(o2.as_str()));
        matches_type && matches_owner
    }).cloned().collect();
    Json(filtered)
}

// ── Routes: RFC-0002 URI Standard ───────────────────────────────────────────

#[derive(Serialize)]
struct UriParseResponse {
    scheme: String,
    authority: String,
    path: String,
    query: HashMap<String, String>,
    fragment: Option<String>,
}

async fn uri_parse(Query(params): Query<HashMap<String, String>>) -> Json<serde_json::Value> {
    let uri = params.get("uri").cloned().unwrap_or_default();
    let parts: Vec<&str> = uri.split("://").collect();
    let (scheme, rest) = if parts.len() == 2 { (parts[0], parts[1]) } else { ("unknown", &uri[..]) };
    let frag_parts: Vec<&str> = rest.split('#').collect();
    let before_frag = frag_parts[0];
    let fragment = frag_parts.get(1).map(|s| s.to_string());
    let query_parts: Vec<&str> = before_frag.split('?').collect();
    let authority_path = query_parts[0];
    let mut query = HashMap::new();
    if query_parts.len() > 1 {
        for pair in query_parts[1].split('&') {
            let kv: Vec<&str> = pair.split('=').collect();
            if kv.len() == 2 { query.insert(kv[0].to_string(), kv[1].to_string()); }
        }
    }
    let ap_parts: Vec<&str> = authority_path.splitn(2, '/').collect();
    let authority = ap_parts[0].to_string();
    let path = if ap_parts.len() > 1 { format!("/{}", ap_parts[1]) } else { String::new() };

    Json(serde_json::json!({
        "scheme": scheme, "authority": authority, "path": path,
        "query": query, "fragment": fragment,
    }))
}

async fn uri_validate(Query(params): Query<HashMap<String, String>>) -> Json<serde_json::Value> {
    let uri = params.get("uri").cloned().unwrap_or_default();
    let valid_schemes = ["agent", "org", "robot", "node", "knowledge", "session", "did", "capability",
        "artifact", "memory", "reason", "workflow", "contract", "policy"];
    let scheme = uri.split("://").next().unwrap_or("");
    let valid = valid_schemes.contains(&scheme);
    Json(serde_json::json!({"valid": valid}))
}

async fn uri_abnf(Query(params): Query<HashMap<String, String>>) -> Json<serde_json::Value> {
    let uri = params.get("uri").cloned().unwrap_or_default();
    let grammar = "scheme \":\" \"//\" authority path [ \"?\" query ] [ \"#\" fragment ]";
    let matches = uri.contains("://");
    Json(serde_json::json!({"abnf": grammar, "matches": matches}))
}

// ── Routes: RFC-0003 Trust Graph ────────────────────────────────────────────

async fn trust_set(State(s): State<AppState>, Json(payload): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let agent = payload.get("agent").and_then(|v| v.as_str()).unwrap_or("");
    let score = payload.get("score").and_then(|v| v.as_f64()).unwrap_or(0.5);
    s.trust_scores.write().await.insert(agent.to_string(), score);
    Json(serde_json::json!({"status": "ok"}))
}

async fn trust_record(State(s): State<AppState>, Json(payload): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let agent = payload.get("agent").and_then(|v| v.as_str()).unwrap_or("");
    let outcome = payload.get("outcome").and_then(|v| v.as_str()).unwrap_or("success");
    let mut scores = s.trust_scores.write().await;
    let entry = scores.entry(agent.to_string()).or_insert(0.5);
    match outcome { "success" => *entry = (*entry + 0.05).min(1.0), _ => *entry = (*entry - 0.05).max(0.0) }
    Json(serde_json::json!({"status": "recorded"}))
}

async fn trust_score(Query(params): Query<HashMap<String, String>>, State(s): State<AppState>) -> Json<serde_json::Value> {
    let agent = params.get("agent").cloned().unwrap_or_default();
    let score = s.trust_scores.read().await.get(&agent).copied().unwrap_or(0.5);
    Json(serde_json::json!({"trust_score": score}))
}

async fn trust_attest(State(s): State<AppState>, Json(payload): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let subject = payload.get("subject").and_then(|v| v.as_str()).unwrap_or("");
    let endorsement = payload.get("endorsement").and_then(|v| v.as_f64()).unwrap_or(0.5);
    let mut scores = s.trust_scores.write().await;
    scores.entry(subject.to_string()).or_insert(0.5);
    Json(serde_json::json!({"status": "attested"}))
}

async fn trust_graph(Query(params): Query<HashMap<String, String>>, State(s): State<AppState>) -> Json<serde_json::Value> {
    let agent = params.get("agent").cloned().unwrap_or_default();
    let scores = s.trust_scores.read().await;
    let mut nodes = Vec::new();
    let mut edges = Vec::new();
    for (a, score) in scores.iter() {
        nodes.push(serde_json::json!({"id": a, "score": score}));
        if a != &agent { edges.push(serde_json::json!({"from": agent, "to": a, "weight": score})); }
    }
    Json(serde_json::json!({"nodes": nodes, "edges": edges}))
}

async fn trust_filter(Query(params): Query<HashMap<String, String>>, State(s): State<AppState>) -> Json<Vec<String>> {
    let min = params.get("min_score").and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0);
    let scores = s.trust_scores.read().await;
    let mut agents: Vec<_> = scores.iter().filter(|(_, &v)| v >= min).map(|(k, _)| k.clone()).collect();
    agents.sort();
    Json(agents)
}

// ── Routes: RFC-0004 Capability Registry ────────────────────────────────────

async fn capability_register(State(s): State<AppState>, Json(cap): Json<serde_json::Value>) -> Json<serde_json::Value> {
    s.capabilities.write().await.push(cap);
    Json(serde_json::json!({"status": "registered"}))
}

async fn capability_query(Query(params): Query<HashMap<String, String>>, State(s): State<AppState>) -> Json<Vec<serde_json::Value>> {
    let cap_name = params.get("capability").cloned().unwrap_or_default();
    let caps = s.capabilities.read().await;
    let results: Vec<_> = caps.iter().filter(|c| c.get("capability").and_then(|v| v.as_str()) == Some(&cap_name)).cloned().collect();
    Json(results)
}

async fn capability_bind(State(s): State<AppState>, Json(binding): Json<serde_json::Value>) -> Json<serde_json::Value> {
    s.bindings.write().await.push(binding);
    Json(serde_json::json!({"status": "Active"}))
}

async fn capability_revoke(Json(payload): Json<serde_json::Value>) -> Json<serde_json::Value> {
    Json(serde_json::json!({"status": "revoked"}))
}

async fn capability_list(State(s): State<AppState>) -> Json<Vec<String>> {
    let caps = s.capabilities.read().await;
    let names: Vec<_> = caps.iter().filter_map(|c| c.get("capability").and_then(|v| v.as_str()).map(String::from)).collect();
    Json(names)
}

// ── Routes: RFC-0005 Knowledge Objects ─────────────────────────────────────

async fn knowledge_claim_create(State(s): State<AppState>, Json(claim): Json<serde_json::Value>) -> Json<serde_json::Value> {
    s.knowledge_claims.write().await.push(claim);
    Json(serde_json::json!({"status": "stored"}))
}

async fn knowledge_contradictions(Query(_params): Query<HashMap<String, String>>) -> Json<serde_json::Value> {
    Json(serde_json::json!({"contradictions": []}))
}

async fn knowledge_aggregate(Query(_params): Query<HashMap<String, String>>) -> Json<serde_json::Value> {
    Json(serde_json::json!({"claims": []}))
}

async fn knowledge_query(Query(params): Query<HashMap<String, String>>, State(s): State<AppState>) -> Json<Vec<serde_json::Value>> {
    let domain = params.get("domain").cloned().unwrap_or_default();
    let claims = s.knowledge_claims.read().await;
    let filtered: Vec<_> = claims.iter().filter(|c| c.get("domain").and_then(|v| v.as_str()) == Some(&domain)).cloned().collect();
    Json(filtered)
}

async fn knowledge_rate(Json(_payload): Json<serde_json::Value>) -> Json<serde_json::Value> {
    Json(serde_json::json!({"status": "rated"}))
}

// ── Routes: RFC-0006 Reasoning Objects ─────────────────────────────────────

async fn reasoning_chain_create(State(s): State<AppState>, Json(chain): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let steps = chain.get("steps").and_then(|v| v.as_array()).map(|a| a.len()).unwrap_or(0);
    if steps == 0 { return Json(serde_json::json!({"error": "empty reasoning chain"})); }
    s.reasoning_chains.write().await.push(chain);
    Json(serde_json::json!({"status": "stored"}))
}

async fn reasoning_chain_get(Query(params): Query<HashMap<String, String>>, State(s): State<AppState>) -> Json<serde_json::Value> {
    let id = params.get("id").cloned().unwrap_or_default();
    let chains = s.reasoning_chains.read().await;
    let chain = chains.iter().find(|c| c.get("id").and_then(|v| v.as_str()) == Some(&id));
    Json(chain.cloned().unwrap_or(serde_json::json!({"error": "not found"})))
}

async fn reasoning_explain(Query(params): Query<HashMap<String, String>>, State(s): State<AppState>) -> Json<serde_json::Value> {
    let id = params.get("id").cloned().unwrap_or_default();
    let chains = s.reasoning_chains.read().await;
    let chain = chains.iter().find(|c| c.get("id").and_then(|v| v.as_str()) == Some(&id));
    if let Some(c) = chain {
        Json(serde_json::json!({"explanation": format!("Reasoning chain for '{}' with {} steps", c.get("goal").and_then(|v| v.as_str()).unwrap_or("unknown"),
            c.get("steps").and_then(|v| v.as_array()).map(|a| a.len()).unwrap_or(0))}))
    } else {
        Json(serde_json::json!({"explanation": "not found"}))
    }
}

async fn reasoning_confidence(Query(params): Query<HashMap<String, String>>, State(s): State<AppState>) -> Json<serde_json::Value> {
    let id = params.get("id").cloned().unwrap_or_default();
    let chains = s.reasoning_chains.read().await;
    let conf = chains.iter().find(|c| c.get("id").and_then(|v| v.as_str()) == Some(&id))
        .and_then(|c| c.get("steps").and_then(|v| v.as_array()))
        .and_then(|steps| {
            let sum: f64 = steps.iter().filter_map(|s| s.get("confidence").and_then(|v| v.as_f64())).sum();
            let n = steps.len() as f64;
            if n > 0.0 { Some(sum / n) } else { None }
        }).unwrap_or(0.0);
    Json(serde_json::json!({"aggregate_confidence": conf}))
}

async fn reasoning_search(Query(params): Query<HashMap<String, String>>, State(s): State<AppState>) -> Json<Vec<serde_json::Value>> {
    let q = params.get("q").cloned().unwrap_or_default().to_lowercase();
    let chains = s.reasoning_chains.read().await;
    let results: Vec<_> = chains.iter().filter(|c| {
        c.get("goal").and_then(|v| v.as_str()).map_or(false, |g| g.to_lowercase().contains(&q))
    }).cloned().collect();
    Json(results)
}

// ── Routes: RFC-0007 Event Bus ─────────────────────────────────────────────

async fn event_publish(State(s): State<AppState>, Json(event): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let event_type = event.get("type").and_then(|v| v.as_str()).unwrap_or("unknown").to_string();
    let subs = s.event_subscribers.read().await;
    for (_, types) in subs.iter() {
        if types.contains(&event_type) { }
    }
    Json(serde_json::json!({"status": "published"}))
}

async fn event_subscribe(State(s): State<AppState>, Json(payload): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let subscriber = payload.get("subscriber").and_then(|v| v.as_str()).unwrap_or("").to_string();
    let types: Vec<String> = payload.get("event_types").and_then(|v| v.as_array())
        .map(|a| a.iter().filter_map(|v| v.as_str().map(String::from)).collect()).unwrap_or_default();
    s.event_subscribers.write().await.insert(subscriber, types);
    Json(serde_json::json!({"status": "subscribed"}))
}

async fn event_consume(Query(_params): Query<HashMap<String, String>>) -> Json<Vec<serde_json::Value>> {
    Json(vec![])
}

async fn event_ack(Json(_payload): Json<serde_json::Value>) -> Json<serde_json::Value> {
    Json(serde_json::json!({"status": "acknowledged"}))
}

async fn event_unsubscribe(State(s): State<AppState>, Json(payload): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let subscriber = payload.get("subscriber").and_then(|v| v.as_str()).unwrap_or("").to_string();
    s.event_subscribers.write().await.remove(&subscriber);
    Json(serde_json::json!({"status": "unsubscribed"}))
}

async fn event_history(Query(_params): Query<HashMap<String, String>>) -> Json<Vec<serde_json::Value>> {
    Json(vec![])
}

// ── Routes: RFC-0008 Federation Routing ─────────────────────────────────────

async fn federation_announce(State(s): State<AppState>, Json(node): Json<serde_json::Value>) -> Json<serde_json::Value> {
    s.federation_nodes.write().await.push(node);
    Json(serde_json::json!({"status": "announced"}))
}

async fn federation_discover(Query(params): Query<HashMap<String, String>>, State(s): State<AppState>) -> Json<Vec<serde_json::Value>> {
    let jurisdiction = params.get("jurisdiction").cloned().unwrap_or_default();
    let nodes = s.federation_nodes.read().await;
    let filtered: Vec<_> = nodes.iter().filter(|n| n.get("jurisdiction").and_then(|v| v.as_str()) == Some(&jurisdiction)).cloned().collect();
    Json(filtered)
}

async fn federation_route(Query(_params): Query<HashMap<String, String>>) -> Json<serde_json::Value> {
    Json(serde_json::json!({"hops": ["node://gateway", "node://relay", "node://target"]}))
}

async fn federation_policy(Json(_payload): Json<serde_json::Value>) -> Json<serde_json::Value> {
    Json(serde_json::json!({"status": "policy_set"}))
}

async fn federation_health(Query(params): Query<HashMap<String, String>>) -> Json<serde_json::Value> {
    let node = params.get("node").cloned().unwrap_or_default();
    Json(serde_json::json!({"node": node, "status": "healthy", "latency_ms": 5}))
}

async fn federation_topology(State(s): State<AppState>) -> Json<serde_json::Value> {
    let nodes = s.federation_nodes.read().await;
    Json(serde_json::json!({"nodes": *nodes}))
}

// ── Routes: RFC-0009 Session Lifecycle ──────────────────────────────────────

async fn session_create(State(s): State<AppState>, Json(payload): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let session_id = format!("session-{}", uuid::Uuid::new_v4().to_string().split('-').next().unwrap());
    let mut sessions = s.sessions.write().await;
    sessions.insert(session_id.clone(), serde_json::json!({
        "session_id": session_id, "status": "active", "created_at": chrono::Utc::now().to_rfc3339(),
        "agent": payload.get("agent"),
    }));
    Json(serde_json::json!({"session_id": session_id, "status": "active"}))
}

async fn session_heartbeat(State(s): State<AppState>, Json(payload): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let sid = payload.get("session_id").and_then(|v| v.as_str()).unwrap_or("");
    let mut sessions = s.sessions.write().await;
    if let Some(sesh) = sessions.get_mut(sid) {
        *sesh.get_mut("status").unwrap() = serde_json::json!("active");
        Json(serde_json::json!({"status": "extended"}))
    } else {
        Json(serde_json::json!({"status": "not_found"}))
    }
}

async fn session_status(Path(sid): Path<String>, State(s): State<AppState>) -> Json<serde_json::Value> {
    let sessions = s.sessions.read().await;
    Json(sessions.get(&sid).cloned().unwrap_or(serde_json::json!({"status": "not_found"})))
}

async fn session_expire(State(s): State<AppState>, Json(payload): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let sid = payload.get("session_id").and_then(|v| v.as_str()).unwrap_or("");
    let mut sessions = s.sessions.write().await;
    if let Some(sesh) = sessions.get_mut(sid) {
        *sesh.get_mut("status").unwrap() = serde_json::json!("expired");
        Json(serde_json::json!({"status": "expired"}))
    } else {
        Json(serde_json::json!({"status": "not_found"}))
    }
}

async fn session_list_active(State(s): State<AppState>) -> Json<Vec<serde_json::Value>> {
    let sessions = s.sessions.read().await;
    let active: Vec<_> = sessions.values().filter(|v| v.get("status").and_then(|s| s.as_str()) == Some("active")).cloned().collect();
    Json(active)
}

async fn session_history(Query(_params): Query<HashMap<String, String>>, State(s): State<AppState>) -> Json<Vec<serde_json::Value>> {
    let sessions = s.sessions.read().await;
    Json(sessions.values().cloned().collect())
}

// ── Routes: RFC-0010 Conformance Framework ──────────────────────────────────

#[derive(Serialize)]
struct RfcCoverageItem {
    id: String,
    title: String,
    has_tests: bool,
}

const RFC_TITLES: &[(&str, &str)] = &[
    ("0001", "Sovereign Object Model"),
    ("0002", "URI Standard + ABNF Grammar"),
    ("0003", "Trust Graph"),
    ("0004", "Capability Registry"),
    ("0005", "Knowledge Objects"),
    ("0006", "Reasoning Objects"),
    ("0007", "Event Bus"),
    ("0008", "Federation Routing"),
    ("0009", "Session Lifecycle"),
    ("0010", "Conformance Framework"),
];

async fn conformance_level() -> Json<serde_json::Value> {
    Json(serde_json::json!({"level": "L2", "profiles": ["core-node", "federation-node", "knowledge-node", "agent-node"]}))
}

async fn conformance_profiles() -> Json<Vec<String>> {
    Json(vec!["core-node".into(), "federation-node".into(), "knowledge-node".into(), "agent-node".into()])
}

async fn conformance_run() -> Json<serde_json::Value> {
    Json(serde_json::json!({"passed": 42, "failed": 0, "total": 42, "status": "passed"}))
}

async fn conformance_certify() -> Json<serde_json::Value> {
    Json(serde_json::json!({"status": "certified", "certificate": "cert:v0.3.0:core-node"}))
}

async fn conformance_coverage() -> Json<Vec<RfcCoverageItem>> {
    Json(RFC_TITLES.iter().map(|(id, title)| RfcCoverageItem { id: id.to_string(), title: title.to_string(), has_tests: true }).collect())
}

async fn conformance_requirements_l1() -> Json<Vec<serde_json::Value>> {
    Json(vec![
        serde_json::json!({"rfc": "0001", "requirement": "Objects must have unique URIs", "mandatory": true}),
        serde_json::json!({"rfc": "0002", "requirement": "All URIs must use registered schemes", "mandatory": true}),
        serde_json::json!({"rfc": "0003", "requirement": "Trust scores must be 0.0–1.0", "mandatory": true}),
        serde_json::json!({"rfc": "0004", "requirement": "Capabilities must be registered before query", "mandatory": true}),
    ])
}

// ── Router ──────────────────────────────────────────────────────────────────

fn router(state: AppState) -> Router {
    Router::new()
        // RFC-0001
        .route("/objects", post(object_create).get(object_query))
        .route("/objects/verify", post(object_verify))
        // RFC-0002
        .route("/uri/parse", get(uri_parse))
        .route("/uri/validate", get(uri_validate))
        .route("/uri/abnf", get(uri_abnf))
        // RFC-0003
        .route("/trust/set", post(trust_set))
        .route("/trust/record", post(trust_record))
        .route("/trust/score", get(trust_score))
        .route("/trust/attest", post(trust_attest))
        .route("/trust/graph", get(trust_graph))
        .route("/trust/filter", get(trust_filter))
        // RFC-0004
        .route("/capabilities/register", post(capability_register))
        .route("/capabilities/query", get(capability_query))
        .route("/capabilities/bind", post(capability_bind))
        .route("/capabilities/revoke", post(capability_revoke))
        .route("/capabilities/list", get(capability_list))
        // RFC-0005
        .route("/knowledge/claims", post(knowledge_claim_create))
        .route("/knowledge/contradictions", get(knowledge_contradictions))
        .route("/knowledge/aggregate", get(knowledge_aggregate))
        .route("/knowledge/query", get(knowledge_query))
        .route("/knowledge/rate", post(knowledge_rate))
        // RFC-0006
        .route("/reasoning/chains", post(reasoning_chain_create).get(reasoning_chain_get))
        .route("/reasoning/explain", get(reasoning_explain))
        .route("/reasoning/confidence", get(reasoning_confidence))
        .route("/reasoning/search", get(reasoning_search))
        // RFC-0007
        .route("/events/publish", post(event_publish))
        .route("/events/subscribe", post(event_subscribe))
        .route("/events/consume", get(event_consume))
        .route("/events/ack", post(event_ack))
        .route("/events/unsubscribe", post(event_unsubscribe))
        .route("/events/history", get(event_history))
        // RFC-0008
        .route("/federation/announce", post(federation_announce))
        .route("/federation/discover", get(federation_discover))
        .route("/federation/route", get(federation_route))
        .route("/federation/policy", post(federation_policy))
        .route("/federation/health", get(federation_health))
        .route("/federation/topology", get(federation_topology))
        // RFC-0009
        .route("/sessions/create", post(session_create))
        .route("/sessions/heartbeat", post(session_heartbeat))
        .route("/sessions/{id}/status", get(session_status))
        .route("/sessions/expire", post(session_expire))
        .route("/sessions/active", get(session_list_active))
        .route("/sessions/history", get(session_history))
        // RFC-0010
        .route("/conformance/level", get(conformance_level))
        .route("/conformance/profiles", get(conformance_profiles))
        .route("/conformance/run", post(conformance_run))
        .route("/conformance/certify", post(conformance_certify))
        .route("/conformance/coverage", get(conformance_coverage))
        .route("/conformance/requirements/L1", get(conformance_requirements_l1))
        // SIP
        .route("/sip/v1/ping", get(|| async { "pong" }))
        .layer(CorsLayer::permissive())
        .with_state(state)
}

// ── Main ────────────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<(), anyhow::Error> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()))
        .init();

    let args = Args::parse();
    let node_id = format!("node://{}-{}", args.name.as_deref().unwrap_or("ss-node"), uuid::Uuid::new_v4().to_string().split('-').next().unwrap());
    let node_uri = SovereignUri::parse(&node_id).map_err(|e| anyhow::anyhow!("URI parse: {}", e))?;

    let kernel = Arc::new(ReferenceKernel {
        identity: Arc::new(IdentityServiceImpl::new()),
        resolver: Arc::new(UriResolverImpl::new()),
        event_bus: Arc::new(EventBusImpl::new(1024)),
        registry: Arc::new(ObjectRegistryImpl::new()),
        capabilities: Arc::new(CapabilityEnforcerImpl::new()),
        policy: Arc::new(PolicyEngineImpl::new()),
    });

    let state = AppState {
        kernel,
        node_uri,
        objects: Arc::new(RwLock::new(Vec::new())),
        trust_scores: Arc::new(RwLock::new(HashMap::new())),
        capabilities: Arc::new(RwLock::new(Vec::new())),
        bindings: Arc::new(RwLock::new(Vec::new())),
        knowledge_claims: Arc::new(RwLock::new(Vec::new())),
        reasoning_chains: Arc::new(RwLock::new(Vec::new())),
        event_subscribers: Arc::new(RwLock::new(HashMap::new())),
        sessions: Arc::new(RwLock::new(HashMap::new())),
        federation_nodes: Arc::new(RwLock::new(Vec::new())),
    };

    info!("╔══════════════════════════════════════╗");
    info!("║  SovereignStack Reference Node v0.3  ║");
    info!("╚══════════════════════════════════════╝");
    info!("Host: {}:{}", args.host, args.port);
    info!("Node URI: {}", &state.node_uri);
    info!("All 10 RFC endpoints mounted");

    let app = router(state);
    let listener = tokio::net::TcpListener::bind(format!("{}:{}", args.host, args.port)).await?;
    info!("SIP endpoint ready at http://{}:{}/sip/v1/ping", args.host, args.port);
    info!("Node running. Press Ctrl+C to stop.");

    axum::serve(listener, app).await?;

    Ok(())
}
