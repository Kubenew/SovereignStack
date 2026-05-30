//! The Reality Interface for physical devices.

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use ss_core::timestamp::Timestamp;

/// Standardized telemetry and sensor data from a physical device.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SensorData {
    /// GPS or local coordinate tracking.
    Telemetry {
        latitude: f64,
        longitude: f64,
        altitude: f64,
        heading: f64,
    },
    /// Environmental data.
    Environmental {
        temperature_c: f64,
        humidity_percent: f64,
    },
    /// Status of internal systems (battery, motors).
    SystemStatus {
        battery_percent: f64,
        is_charging: bool,
        error_codes: Vec<String>,
    },
}

/// A command sent to a physical actuator.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ActuatorCommand {
    /// Move to a target location.
    NavigateTo {
        latitude: f64,
        longitude: f64,
    },
    /// Halt all physical movement immediately.
    EmergencyStop,
    /// Custom command payload.
    Custom {
        command: String,
        payload: String,
    },
}

/// The core interface that any physical device driver must implement
/// to integrate with SovereignStack.
#[async_trait]
pub trait RealityInterface: Send + Sync {
    /// Read the latest state from the physical sensors.
    async fn sense(&self) -> Result<Vec<SensorData>, ss_core::error::Error>;
    
    /// Send a command to the physical actuators.
    async fn act(&self, command: ActuatorCommand) -> Result<(), ss_core::error::Error>;
    
    /// Take a rich observation (e.g., an image from a camera) and return a reference hash.
    /// In a real implementation, this would upload to CAS and return the ContentHash.
    async fn observe(&self) -> Result<String, ss_core::error::Error>;
}
