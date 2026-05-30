//! Event streams and subscriptions.

use std::collections::VecDeque;
use std::sync::Arc;
use tokio::sync::{broadcast, RwLock};

use crate::event::{Event, EventType};

/// An append-only stream of events.
///
/// In a full implementation, this would be backed by persistent storage
/// like Kafka, NATS, or a local append-only log. For this scaffolding,
/// it's an in-memory queue with broadcast capabilities.
#[derive(Clone)]
pub struct EventStream {
    /// In-memory storage of events.
    events: Arc<RwLock<VecDeque<Event>>>,
    /// Broadcast channel for real-time subscribers.
    sender: broadcast::Sender<Event>,
}

impl EventStream {
    /// Create a new event stream.
    pub fn new() -> Self {
        let (sender, _) = broadcast::channel(1024);
        Self {
            events: Arc::new(RwLock::new(VecDeque::new())),
            sender,
        }
    }

    /// Append an event to the stream.
    pub async fn append(&self, event: Event) {
        let mut events = self.events.write().await;
        events.push_back(event.clone());
        // Ignore send errors if there are no subscribers
        let _ = self.sender.send(event);
    }

    /// Subscribe to all future events.
    pub fn subscribe(&self) -> EventSubscription {
        EventSubscription {
            receiver: self.sender.subscribe(),
            filter: None,
        }
    }

    /// Subscribe to specific event types.
    pub fn subscribe_to(&self, event_type: EventType) -> EventSubscription {
        EventSubscription {
            receiver: self.sender.subscribe(),
            filter: Some(event_type),
        }
    }

    /// Retrieve historical events (simplified pagination).
    pub async fn history(&self, limit: usize) -> Vec<Event> {
        let events = self.events.read().await;
        events.iter().rev().take(limit).cloned().collect()
    }
}

impl Default for EventStream {
    fn default() -> Self {
        Self::new()
    }
}

/// A subscription to the event stream.
pub struct EventSubscription {
    receiver: broadcast::Receiver<Event>,
    filter: Option<EventType>,
}

impl EventSubscription {
    /// Receive the next matching event.
    pub async fn next(&mut self) -> Result<Event, broadcast::error::RecvError> {
        loop {
            let event = self.receiver.recv().await?;
            
            // Apply filter if one exists
            if let Some(ref filter_type) = self.filter {
                if &event.event_type == filter_type {
                    return Ok(event);
                }
            } else {
                return Ok(event);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ss_core::uri::{SovereignUri, UriScheme};

    #[tokio::test]
    async fn append_and_subscribe() {
        let stream = EventStream::new();
        let mut sub = stream.subscribe();
        
        let uri = SovereignUri::new(UriScheme::Agent, "test");
        let event = Event::new(uri, EventType::SessionCreated, "").unwrap();
        
        stream.append(event.clone()).await;
        
        let received = sub.next().await.unwrap();
        assert_eq!(received.id, event.id);
    }

    #[tokio::test]
    async fn filtered_subscription() {
        let stream = EventStream::new();
        let mut sub = stream.subscribe_to(EventType::ArtifactPublished);
        
        let uri = SovereignUri::new(UriScheme::Agent, "test");
        
        // This one should be ignored
        stream.append(Event::new(uri.clone(), EventType::SessionCreated, "").unwrap()).await;
        
        // This one should be received
        stream.append(Event::new(uri.clone(), EventType::ArtifactPublished, "").unwrap()).await;
        
        let received = sub.next().await.unwrap();
        assert_eq!(received.event_type, EventType::ArtifactPublished);
    }
}
