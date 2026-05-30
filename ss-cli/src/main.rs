//! SovereignStack Command Line Interface.
//!
//! The `ss` command is the primary user interface for interacting with
//! the local SovereignStack node and the broader intelligence network.

use clap::{Parser, Subcommand};
use tracing::{info, Level};

/// SovereignStack CLI - The distributed operating system for intelligence
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,

    /// Set verbosity level
    #[arg(short, long, default_value_t = false)]
    verbose: bool,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Initialize a new Sovereign node
    Init {
        /// Name of the node
        #[arg(short, long)]
        name: String,
    },
    
    /// Agent management commands
    Agent {
        #[command(subcommand)]
        cmd: AgentCommands,
    },

    /// Capability network commands
    Capability {
        #[command(subcommand)]
        cmd: CapabilityCommands,
    },

    /// Show node status
    Status,
}

#[derive(Subcommand, Debug)]
enum AgentCommands {
    /// Create a new Universal Agent Identity
    Create {
        /// Name of the agent
        name: String,
    },
    
    /// Launch an agent session in the daemon
    Start {
        /// URI of the agent (e.g., agent://researcher-1)
        uri: String,
    },
    
    /// List active agent sessions
    List,
}

#[derive(Subcommand, Debug)]
enum CapabilityCommands {
    /// Query the network for a capability
    Query {
        /// The capability name to search for (e.g., contract_review)
        capability: String,
        
        /// Required language (optional)
        #[arg(short, long)]
        lang: Option<String>,
        
        /// Minimum accuracy required (0.0 to 1.0)
        #[arg(short, long)]
        min_accuracy: Option<f64>,
    },
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    // Initialize logging
    let log_level = if cli.verbose { Level::DEBUG } else { Level::INFO };
    tracing_subscriber::fmt()
        .with_max_level(log_level)
        .init();

    match &cli.command {
        Commands::Init { name } => {
            println!("🚀 Initializing SovereignStack node: {}", name);
            // In a real impl, this generates the node's Ed25519 identity and config files
            println!("Node identity generated: node://{}", name);
            println!("Run `ss-sessiond` to start the daemon.");
        }
        Commands::Agent { cmd } => match cmd {
            AgentCommands::Create { name } => {
                println!("Creating new Universal Agent Identity: {}", name);
                println!("URI: agent://{}", name);
                println!("Public Key: ed25519:...(generated)...");
            }
            AgentCommands::Start { uri } => {
                println!("Starting session for agent: {}", uri);
                // Real impl makes HTTP/JSON request to daemon
                println!("Session started successfully.");
            }
            AgentCommands::List => {
                println!("Active Sessions:");
                println!("  agent://researcher-1 [Running]");
                println!("  agent://legal-expert [Suspended]");
            }
        },
        Commands::Capability { cmd } => match cmd {
            CapabilityCommands::Query { capability, lang, min_accuracy } => {
                println!("🔍 Querying network for capability: {}", capability);
                if let Some(l) = lang {
                    println!("   Language: {}", l);
                }
                if let Some(a) = min_accuracy {
                    println!("   Min Accuracy: {}", a);
                }
                println!("\nTop Matches:");
                println!("  1. agent://expert-reviewer (Score: 0.94)");
                println!("  2. agent://fast-reviewer (Score: 0.88)");
            }
        },
        Commands::Status => {
            println!("SovereignStack Node Status");
            println!("--------------------------");
            println!("Identity: node://homelab-alpha");
            println!("Daemon:   Running (pid 4242)");
            println!("Peers:    14 connected");
            println!("Sessions: 2 active");
        }
    }

    Ok(())
}
