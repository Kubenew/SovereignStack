//! Digital Twin Session.

use std::sync::Arc;
use tokio::time::{interval, Duration};
use tracing::{info, warn};

use ss_core::uri::SovereignUri;
use ss_eventbus::{Event, EventStream, EventType};
use crate::interface::RealityInterface;

/// A session that manages a physical device or robot.
///
/// It constantly reads from the `RealityInterface` and publishes state
/// to the Sovereign Event Bus, while listening to the Event Bus for
/// commands routed to its specific `robot://` URI.
pub struct TwinSession {
    /// The URI of this physical device (e.g., robot://drone-01).
    pub uri: SovereignUri,
    /// The hardware driver implementing the Reality Interface.
    hardware: Arc<dyn RealityInterface>,
    /// The event bus to publish telemetry to.
    event_bus: Arc<EventStream>,
}

impl TwinSession {
    pub fn new(uri: SovereignUri, hardware: Arc<dyn RealityInterface>, event_bus: Arc<EventStream>) -> Self {
        Self {
            uri,
            hardware,
            event_bus,
        }
    }

    /// Start the telemetry polling loop.
    pub async fn start_telemetry_loop(&self) {
        let hardware = self.hardware.clone();
        let event_bus = self.event_bus.clone();
        let uri = self.uri.clone();

        tokio::spawn(async move {
            info!("Starting telemetry loop for {}", uri);
            let mut ticker = interval(Duration::from_secs(5));

            loop {
                ticker.tick().await;

                match hardware.sense().await {
                    Ok(sensor_data) => {
                        // In a real implementation, serialize sensor_data and publish
                        let payload = serde_json::to_string(&sensor_data).unwrap_or_default();
                        
                        if let Ok(event) = Event::new(
                            uri.clone(), 
                            EventType::Custom("TelemetryUpdate".to_string()), 
                            payload
                        ) {
                            event_bus.append(event).await;
                        }
                    }
                    Err(e) => {
                        warn!("Hardware sensor error on {}: {:?}", uri, e);
                    }
                }
            }
        });
    }
}
