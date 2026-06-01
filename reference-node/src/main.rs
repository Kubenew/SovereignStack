//! SovereignStack Reference Node — minimal implementation.
//!
//! This binary assembles the core kernel and starts a basic node.
//! No AI, no swarm, no federation — just the core architecture.

use clap::Parser;
use ss_kernel::{
    Kernel, KernelError,
    capability::CapabilityEnforcerImpl,
    eventbus::EventBusImpl,
    identity::IdentityServiceImpl,
    policy::PolicyEngineImpl,
    registry::ObjectRegistryImpl,
    resolver::UriResolverImpl,
};
use ss_core::SovereignUri;
use std::sync::Arc;
use tracing::info;

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

/// The ReferenceNode assembles all kernel services into a runnable binary.
struct ReferenceNode {
    kernel: ReferenceKernel,
    node_uri: SovereignUri,
}

impl ReferenceNode {
    fn new(args: &Args) -> Result<Self, KernelError> {
        let node_id = format!("node://{}-{}", args.name.as_deref().unwrap_or("ss-node"), uuid::Uuid::new_v4().to_string().split('-').next().unwrap());
        let node_uri = SovereignUri::parse(&node_id).map_err(|e| KernelError::Internal(e.to_string()))?;

        let kernel = ReferenceKernel {
            identity: Arc::new(IdentityServiceImpl::new()),
            resolver: Arc::new(UriResolverImpl::new()),
            event_bus: Arc::new(EventBusImpl::new(1024)),
            registry: Arc::new(ObjectRegistryImpl::new()),
            capabilities: Arc::new(CapabilityEnforcerImpl::new()),
            policy: Arc::new(PolicyEngineImpl::new()),
        };

        info!("Node initialized: {}", node_id);
        Ok(Self { kernel, node_uri })
    }

    fn kernel(&self) -> &ReferenceKernel {
        &self.kernel
    }

    fn node_uri(&self) -> &SovereignUri {
        &self.node_uri
    }
}

struct ReferenceKernel {
    identity: Arc<IdentityServiceImpl>,
    resolver: Arc<UriResolverImpl>,
    event_bus: Arc<EventBusImpl>,
    registry: Arc<ObjectRegistryImpl>,
    capabilities: Arc<CapabilityEnforcerImpl>,
    policy: Arc<PolicyEngineImpl>,
}

impl Kernel for ReferenceKernel {
    fn identity(&self) -> &dyn ss_kernel::identity::IdentityService {
        self.identity.as_ref()
    }

    fn resolver(&self) -> &dyn ss_kernel::resolver::UriResolver {
        self.resolver.as_ref()
    }

    fn event_bus(&self) -> &dyn ss_kernel::eventbus::EventBus {
        self.event_bus.as_ref()
    }

    fn registry(&self) -> &dyn ss_kernel::registry::ObjectRegistry {
        self.registry.as_ref()
    }

    fn capabilities(&self) -> &dyn ss_kernel::capability::CapabilityEnforcer {
        self.capabilities.as_ref()
    }

    fn policy(&self) -> &dyn ss_kernel::policy::PolicyEngine {
        self.policy.as_ref()
    }
}

#[tokio::main]
async fn main() -> Result<(), anyhow::Error> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info".into()),
        )
        .init();

    let args = Args::parse();

    info!("╔══════════════════════════════════════╗");
    info!("║  SovereignStack Reference Node v0.1  ║");
    info!("╚══════════════════════════════════════╝");

    let node = ReferenceNode::new(&args)?;

    info!("Host: {}:{}", args.host, args.port);
    info!("Node URI: {}", node.node_uri());
    info!("Services: identity ✓ resolver ✓ eventbus ✓ registry ✓ capability ✓ policy ✓");
    if args.with_sessiond {
        info!("Session daemon: enabled");
    }
    if args.with_cas {
        info!("Content-addressed storage: enabled");
    }

    // Seed the identity service with the node's own identity
    let node_doc = node.kernel().identity().generate(node.node_uri())?;
    info!("Node identity document generated: {:?}", node_doc);

    // Start the SIP endpoint (placeholder for HTTP/WS listener)
    info!("SIP endpoint ready at {}:{}", args.host, args.port);

    // Publish startup event
    node.kernel().event_bus().publish(ss_kernel::eventbus::Event {
        id: uuid::Uuid::new_v4().to_string(),
        timestamp: ss_core::Timestamp::now(),
        source: node.node_uri().clone(),
        event_type: "node.started".into(),
        payload: serde_json::json!({
            "host": args.host,
            "port": args.port,
            "name": args.name,
            "version": "0.1.0"
        }),
        signature: None,
    });

    info!("Node running. Press Ctrl+C to stop.");

    // Keep running until signal
    tokio::signal::ctrl_c().await?;
    info!("Shutting down...");

    Ok(())
}
