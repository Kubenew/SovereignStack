//! Event Bus — publish/subscribe with immutable, signed events.

use ss_core::{SovereignUri, Timestamp};
use std::sync::Arc;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Event {
    pub id: String,
    pub timestamp: Timestamp,
    pub source: SovereignUri,
    pub event_type: String,
    pub payload: serde_json::Value,
    pub signature: Option<String>,
}

pub trait EventBus: Send + Sync {
    fn publish(&self, event: Event);
    fn subscribe(&self, event_type: &str) -> tokio::sync::broadcast::Receiver<Event>;
    fn replay(&self, event_type: &str, from: Timestamp) -> Vec<Event>;
}

pub struct EventBusImpl {
    tx: tokio::sync::broadcast::Sender<Event>,
    history: Arc<dashmap::DashMap<String, Vec<Event>>>,
}

impl EventBusImpl {
    pub fn new(capacity: usize) -> Self {
        let (tx, _) = tokio::sync::broadcast::channel(capacity);
        Self {
            tx,
            history: Arc::new(dashmap::DashMap::new()),
        }
    }
}

impl EventBus for EventBusImpl {
    fn publish(&self, event: Event) {
        self.history
            .entry(event.event_type.clone())
            .or_default()
            .push(event.clone());
        let _ = self.tx.send(event);
    }

    fn subscribe(&self, _event_type: &str) -> tokio::sync::broadcast::Receiver<Event> {
        self.tx.subscribe()
    }

    fn replay(&self, event_type: &str, _from: Timestamp) -> Vec<Event> {
        self.history
            .get(event_type)
            .map(|e| e.value().clone())
            .unwrap_or_default()
    }
}
