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
    txs: Arc<dashmap::DashMap<String, tokio::sync::broadcast::Sender<Event>>>,
    history: Arc<dashmap::DashMap<String, Vec<Event>>>,
    capacity: usize,
}

impl EventBusImpl {
    pub fn new(capacity: usize) -> Self {
        Self {
            txs: Arc::new(dashmap::DashMap::new()),
            history: Arc::new(dashmap::DashMap::new()),
            capacity,
        }
    }
}

impl EventBus for EventBusImpl {
    fn publish(&self, event: Event) {
        let etype = event.event_type.clone();
        self.history
            .entry(etype.clone())
            .or_default()
            .push(event.clone());
        if let Some(tx) = self.txs.get(&etype) {
            let _ = tx.send(event);
        }
    }

    fn subscribe(&self, event_type: &str) -> tokio::sync::broadcast::Receiver<Event> {
        self.txs
            .entry(event_type.to_string())
            .or_insert_with(|| tokio::sync::broadcast::channel(self.capacity).0)
            .subscribe()
    }

    fn replay(&self, event_type: &str, from: Timestamp) -> Vec<Event> {
        self.history
            .get(event_type)
            .map(|e| {
                e.value()
                    .iter()
                    .filter(|ev| ev.timestamp >= from)
                    .cloned()
                    .collect()
            })
            .unwrap_or_default()
    }
}
