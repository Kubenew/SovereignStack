//! ss-kernel: SovereignStack Kernel — core system services.
//!
//! The kernel is the only mandatory component of any SovereignStack node.
//! It provides seven core services: Identity, URI Resolution, Event Bus,
//! Object Registry, Capability Enforcement, Policy Engine, and Provenance.

pub mod identity;
pub mod resolver;
pub mod eventbus;
pub mod registry;
pub mod capability;
pub mod policy;
pub mod provenance;

/// Top-level kernel interface. All subsystems build on top of this.
pub trait Kernel: Send + Sync {
    fn identity(&self) -> &dyn identity::IdentityService;
    fn resolver(&self) -> &dyn resolver::UriResolver;
    fn event_bus(&self) -> &dyn eventbus::EventBus;
    fn registry(&self) -> &dyn registry::ObjectRegistry;
    fn capabilities(&self) -> &dyn capability::CapabilityEnforcer;
    fn policy(&self) -> &dyn policy::PolicyEngine;
    fn provenance(&self) -> &dyn provenance::ProvenanceService;
}

/// Errors that can occur at the kernel level.
#[derive(Debug, thiserror::Error)]
pub enum KernelError {
    #[error("identity error: {0}")]
    Identity(#[from] identity::IdentityError),
    #[error("resolution error: {0}")]
    Resolution(#[from] resolver::ResolutionError),
    #[error("capability denied: {0}")]
    CapabilityDenied(String),
    #[error("policy violation: {0}")]
    PolicyViolation(String),
    #[error("not found: {0}")]
    NotFound(String),
    #[error("internal error: {0}")]
    Internal(String),
}

impl KernelError {
    pub fn code(&self) -> u16 {
        match self {
            Self::NotFound(_) => 404,
            Self::CapabilityDenied(_) => 403,
            Self::PolicyViolation(_) => 403,
            Self::Identity(_) => 401,
            _ => 500,
        }
    }
}

pub type Result<T> = std::result::Result<T, KernelError>;
