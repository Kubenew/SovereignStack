//! # ss-twin
//!
//! Digital Twin Framework for SovereignStack.
//!
//! Bridges physical devices, IoT sensors, and robotics into the Sovereign
//! Intelligence Network. A physical device is represented as a `robot://`
//! session that publishes telemetry to the Event Bus and accepts commands.

pub mod interface;
pub mod session;

pub use interface::{RealityInterface, SensorData, ActuatorCommand};
pub use session::TwinSession;
