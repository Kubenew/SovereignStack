use std::collections::HashMap;
use std::time::{Duration, Instant};

/// Circuit breaker states.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BreakerState {
    Closed,
    Open,
    HalfOpen,
}

/// A resource lease tracked by the circuit breaker.
#[derive(Debug, Clone)]
pub struct ResourceLease {
    pub lease_uri: String,
    pub container_id: String,
    pub ttl: Duration,
    pub created_at: Instant,
    pub renewed_at: Instant,
    pub revoked: bool,
}

impl ResourceLease {
    pub fn is_expired(&self) -> bool {
        Instant::now() > self.renewed_at + self.ttl
    }
}

/// Circuit breaker that tracks leases and can signal container termination.
pub struct CircuitBreaker {
    state: BreakerState,
    leases: HashMap<String, ResourceLease>,
    failure_count: u64,
    max_failures: u64,
    cooldown: Duration,
    last_trip: Option<Instant>,
}

impl CircuitBreaker {
    pub fn new(max_failures: u64, cooldown_secs: u64) -> Self {
        Self {
            state: BreakerState::Closed,
            leases: HashMap::new(),
            failure_count: 0,
            max_failures,
            cooldown: Duration::from_secs(cooldown_secs),
            last_trip: None,
        }
    }

    pub fn register_lease(&mut self, lease_uri: &str, container_id: &str, ttl_secs: u64) {
        self.leases.insert(lease_uri.to_string(), ResourceLease {
            lease_uri: lease_uri.to_string(),
            container_id: container_id.to_string(),
            ttl: Duration::from_secs(ttl_secs),
            created_at: Instant::now(),
            renewed_at: Instant::now(),
            revoked: false,
        });
    }

    pub fn renew_lease(&mut self, lease_uri: &str) -> bool {
        if let Some(lease) = self.leases.get_mut(lease_uri) {
            lease.renewed_at = Instant::now();
            true
        } else {
            false
        }
    }

    pub fn check_lease(&mut self, lease_uri: &str) -> bool {
        let expired = self.leases.get(lease_uri).map(|l| l.is_expired()).unwrap_or(true);
        if expired {
            self.state = BreakerState::Open;
            self.failure_count += 1;
            self.last_trip = Some(Instant::now());
            return false;
        }
        true
    }

    pub fn trip(&mut self) {
        self.state = BreakerState::Open;
        self.failure_count += 1;
        self.last_trip = Some(Instant::now());
    }

    pub fn reset(&mut self) {
        self.state = BreakerState::Closed;
        self.failure_count = 0;
        self.last_trip = None;
    }

    pub fn attempt_reset(&mut self) -> bool {
        if let Some(trip_time) = self.last_trip {
            if trip_time.elapsed() >= self.cooldown {
                self.state = BreakerState::HalfOpen;
                true
            } else {
                false
            }
        } else {
            false
        }
    }

    pub fn state(&self) -> BreakerState {
        self.state
    }

    pub fn collect_expired(&mut self) -> Vec<String> {
        let expired: Vec<String> = self.leases.iter()
            .filter(|(_, l)| l.is_expired() && !l.revoked)
            .map(|(k, _)| k.clone())
            .collect();
        for uri in &expired {
            if let Some(lease) = self.leases.get_mut(uri) {
                lease.revoked = true;
            }
        }
        expired
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;

    #[test]
    fn test_closed_by_default() {
        let cb = CircuitBreaker::new(3, 60);
        assert_eq!(cb.state(), BreakerState::Closed);
    }

    #[test]
    fn test_trip() {
        let mut cb = CircuitBreaker::new(3, 60);
        cb.trip();
        assert_eq!(cb.state(), BreakerState::Open);
    }

    #[test]
    fn test_lease_expiry() {
        let mut cb = CircuitBreaker::new(3, 60);
        cb.register_lease("lease://agent/test", "container-1", 0);
        thread::sleep(Duration::from_millis(10));
        assert!(!cb.check_lease("lease://agent/test"));
    }

    #[test]
    fn test_lease_renew() {
        let mut cb = CircuitBreaker::new(3, 60);
        cb.register_lease("lease://agent/test", "container-1", 60);
        assert!(cb.check_lease("lease://agent/test"));
        cb.renew_lease("lease://agent/test");
    }

    #[test]
    fn test_cooldown() {
        let mut cb = CircuitBreaker::new(3, 0);
        cb.trip();
        thread::sleep(Duration::from_millis(10));
        assert!(cb.attempt_reset());
        assert_eq!(cb.state(), BreakerState::HalfOpen);
    }

    #[test]
    fn test_collect_expired() {
        let mut cb = CircuitBreaker::new(3, 60);
        cb.register_lease("lease://expired", "container-e", 0);
        cb.register_lease("lease://valid", "container-v", 60);
        let expired = cb.collect_expired();
        assert!(expired.contains(&"lease://expired".to_string()));
        assert!(!expired.contains(&"lease://valid".to_string()));
    }
}
