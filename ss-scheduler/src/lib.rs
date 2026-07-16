//! # ss-scheduler
//!
//! Multi-model aware cognitive scheduler for SovereignStack.
//!
//! Implements AI Fabric Scheduling Protocol (RFC-0064).

use ss_core::uri::SovereignUri;

pub enum ResourceType {
    Compute,
    Memory,
    Bandwidth,
    Storage,
    Energy,
}

pub struct CostConstraints {
    pub max_cost: f64,
    pub currency: String,
}

pub struct ResourceContract {
    pub uri: SovereignUri,
    pub resource_type: ResourceType,
    pub quantity: f64,
    pub constraints: CostConstraints,
}

pub struct HardwareRequirements {
    pub min_vram_gb: u32,
    pub capabilities: Vec<String>,
}

pub struct SchedulingConstraints {
    pub hardware: HardwareRequirements,
    pub trust_domain: Option<String>,
    pub jurisdiction: Option<String>,
}

pub struct SchedulingRequest {
    pub workload: SovereignUri,
    pub session: SovereignUri,
    pub constraints: SchedulingConstraints,
    pub locality_preference: Option<SovereignUri>,
    pub resource_contract: Option<SovereignUri>,
}

pub struct SchedulingResponse {
    pub node: SovereignUri,
    pub estimated_start: String,
    pub allocated_resources: Vec<SovereignUri>,
}

#[async_trait::async_trait]
pub trait CognitiveScheduler: Send + Sync {
    async fn schedule(&self, request: SchedulingRequest) -> Result<SchedulingResponse, String>;
}
