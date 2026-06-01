//! Capability Enforcer — intercept all operations, verify capabilities.

use ss_core::{SovereignUri, Timestamp};
use std::sync::Arc;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Capability {
    pub uri: SovereignUri,
    pub granted_by: SovereignUri,
    pub granted_to: SovereignUri,
    pub permissions: Vec<String>,
    pub target: SovereignUri,
    pub conditions: CapabilityConditions,
    pub signature: Option<String>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct CapabilityConditions {
    pub max_uses: Option<u32>,
    pub expires_at: Option<Timestamp>,
}

pub trait CapabilityEnforcer: Send + Sync {
    fn grant(&self, capability: Capability);
    fn revoke(&self, uri: &SovereignUri);
    fn check(&self, caller: &SovereignUri, permission: &str, target: &SovereignUri) -> bool;
    fn list_for(&self, identity: &SovereignUri) -> Vec<Capability>;
}

pub struct CapabilityEnforcerImpl {
    capabilities: Arc<dashmap::DashMap<String, Capability>>,
    revoked: Arc<dashmap::DashSet<String>>,
    use_counts: Arc<dashmap::DashMap<String, u32>>,
}

impl CapabilityEnforcerImpl {
    pub fn new() -> Self {
        Self {
            capabilities: Arc::new(dashmap::DashMap::new()),
            revoked: Arc::new(dashmap::DashSet::new()),
            use_counts: Arc::new(dashmap::DashMap::new()),
        }
    }
}

impl CapabilityEnforcer for CapabilityEnforcerImpl {
    fn grant(&self, capability: Capability) {
        self.capabilities
            .insert(capability.uri.to_string(), capability);
    }

    fn revoke(&self, uri: &SovereignUri) {
        self.revoked.insert(uri.to_string());
    }

    fn check(&self, caller: &SovereignUri, permission: &str, target: &SovereignUri) -> bool {
        for entry in self.capabilities.iter() {
            let cap = entry.value();
            if cap.granted_to == *caller
                && cap.permissions.contains(&permission.to_string())
                && cap.target == *target
            {
                if self.revoked.contains(&cap.uri.to_string()) {
                    return false;
                }
                if let Some(expires) = cap.conditions.expires_at {
                    if Timestamp::now() > expires {
                        return false;
                    }
                }
                if let Some(max) = cap.conditions.max_uses {
                    let count = self
                        .use_counts
                        .entry(cap.uri.to_string())
                        .or_insert(0);
                    *count += 1;
                    if *count > max {
                        return false;
                    }
                }
                return true;
            }
        }
        false
    }

    fn list_for(&self, identity: &SovereignUri) -> Vec<Capability> {
        self.capabilities
            .iter()
            .filter(|e| e.value().granted_to == *identity)
            .map(|e| e.value().clone())
            .collect()
    }
}
