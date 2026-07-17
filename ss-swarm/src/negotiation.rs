use std::collections::HashMap;
use std::time::{Duration, Instant};

/// Represents a single capability that an agent offers.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Capability {
    Compute { cpus: u32, memory_mb: u64 },
    Storage { bytes: u64 },
    Networking { bandwidth_mbps: u64 },
    Reasoning { model: String },
    ToolExecution { tool_name: String },
    Custom(String),
}

/// Direction of a negotiation message.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NegotiationRole {
    Initiator,
    Responder,
}

/// The current status of a negotiation session.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NegotiationStatus {
    Pending,
    Accepted,
    Rejected(String),
    CounterOffer(Vec<Capability>),
    TimedOut,
    Committed,
}

/// A negotiation session between two agents.
#[derive(Debug, Clone)]
pub struct NegotiationSession {
    pub session_id: String,
    pub initiator: String,
    pub responder: String,
    pub offered: Vec<Capability>,
    pub status: NegotiationStatus,
    pub started_at: Instant,
    pub audit_uri: Option<String>,
}

/// Dynamic capability negotiator.
pub struct Negotiator {
    local_capabilities: Vec<Capability>,
    timeout: Duration,
    sessions: HashMap<String, NegotiationSession>,
}

impl Negotiator {
    pub fn new(local_capabilities: Vec<Capability>, timeout_secs: u64) -> Self {
        Self {
            local_capabilities,
            timeout: Duration::from_secs(timeout_secs),
            sessions: HashMap::new(),
        }
    }

    pub fn offer(
        &mut self,
        session_id: &str,
        initiator: &str,
        responder: &str,
        offered: Vec<Capability>,
    ) -> NegotiationStatus {
        let session = NegotiationSession {
            session_id: session_id.to_string(),
            initiator: initiator.to_string(),
            responder: responder.to_string(),
            offered,
            status: NegotiationStatus::Pending,
            started_at: Instant::now(),
            audit_uri: Some(format!("policy://{initiator}/negotiation/{session_id}")),
        };
        self.sessions.insert(session_id.to_string(), session);
        NegotiationStatus::Pending
    }

    pub fn evaluate(&self, offered: &[Capability]) -> NegotiationStatus {
        if offered.is_empty() {
            return NegotiationStatus::Rejected("No capabilities offered".into());
        }
        // Accept if we support at least one offered capability
        let supported = offered.iter().any(|c| self.local_capabilities.contains(c));
        if supported {
            NegotiationStatus::Accepted
        } else {
            NegotiationStatus::CounterOffer(self.local_capabilities.clone())
        }
    }

    pub fn accept(&mut self, session_id: &str) -> bool {
        if let Some(session) = self.sessions.get_mut(session_id) {
            if session.status == NegotiationStatus::Pending {
                session.status = NegotiationStatus::Committed;
                return true;
            }
        }
        false
    }

    pub fn reject(&mut self, session_id: &str, reason: &str) -> bool {
        if let Some(session) = self.sessions.get_mut(session_id) {
            session.status = NegotiationStatus::Rejected(reason.to_string());
            true
        } else {
            false
        }
    }

    pub fn check_timeouts(&mut self) -> Vec<String> {
        let now = Instant::now();
        let timed_out: Vec<String> = self.sessions.iter()
            .filter(|(_, s)| s.status == NegotiationStatus::Pending && now.duration_since(s.started_at) > self.timeout)
            .map(|(k, _)| k.clone())
            .collect();
        for id in &timed_out {
            if let Some(s) = self.sessions.get_mut(id) {
                s.status = NegotiationStatus::TimedOut;
            }
        }
        timed_out
    }

    pub fn status(&self, session_id: &str) -> Option<NegotiationStatus> {
        self.sessions.get(session_id).map(|s| s.status.clone())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_capabilities() -> Vec<Capability> {
        vec![
            Capability::Compute { cpus: 4, memory_mb: 8192 },
            Capability::Storage { bytes: 1_000_000_000 },
            Capability::Reasoning { model: "gpt-4".into() },
        ]
    }

    #[test]
    fn test_offer_accept() {
        let local = make_capabilities();
        let mut neg = Negotiator::new(local.clone(), 30);
        neg.offer("session-1", "agent-a", "agent-b", local.clone());
        assert_eq!(neg.evaluate(&local), NegotiationStatus::Accepted);
        assert!(neg.accept("session-1"));
    }

    #[test]
    fn test_reject() {
        let mut neg = Negotiator::new(make_capabilities(), 30);
        neg.offer("session-2", "agent-a", "agent-b", vec![]);
        assert!(neg.reject("session-2", "no capabilities"));
    }

    #[test]
    fn test_counter_offer() {
        let neg = Negotiator::new(make_capabilities(), 30);
        let unknown = vec![Capability::Custom("unknown-tech".into())];
        let status = neg.evaluate(&unknown);
        assert!(matches!(status, NegotiationStatus::CounterOffer(_)));
    }

    #[test]
    fn test_timeout() {
        let mut neg = Negotiator::new(make_capabilities(), 0);
        neg.offer("session-3", "agent-a", "agent-b", make_capabilities());
        std::thread::sleep(Duration::from_millis(10));
        let timed_out = neg.check_timeouts();
        assert!(timed_out.contains(&"session-3".to_string()));
    }

    #[test]
    fn test_audit_uri() {
        let mut neg = Negotiator::new(make_capabilities(), 30);
        neg.offer("session-4", "agent-audit", "agent-b", make_capabilities());
        let s = neg.sessions.get("session-4").unwrap();
        assert!(s.audit_uri.as_ref().unwrap().starts_with("policy://agent-audit"));
    }
}
