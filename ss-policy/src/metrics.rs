use lazy_static::lazy_static;
use prometheus::{Encoder, IntCounterVec, Opts, Registry, TextEncoder};
use std::sync::atomic::{AtomicU64, Ordering};

pub static TOTAL_ZK_VERIFICATIONS: AtomicU64 = AtomicU64::new(0);
pub static TOTAL_ZK_FAILURES: AtomicU64 = AtomicU64::new(0);

lazy_static! {
    pub static ref REGISTRY: Registry = Registry::new();

    pub static ref ALIGNMENT_FAILURES_COUNTER: IntCounterVec = IntCounterVec::new(
        Opts::new("sovereignstack_policy_zk_failures_total", "Total count of zero-knowledge alignment proof failures."),
        &["values_uri", "agent_uri"]
    ).unwrap();
}

pub fn initialize_metrics() {
    REGISTRY.register(Box::new(ALIGNMENT_FAILURES_COUNTER.clone())).unwrap();
}

pub fn record_alignment_breach(values_uri: &str, agent_uri: &str) {
    TOTAL_ZK_FAILURES.fetch_add(1, Ordering::SeqCst);
    ALIGNMENT_FAILURES_COUNTER.with_label_values(&[values_uri, agent_uri]).inc();
}

pub fn scrape_metrics_to_string() -> String {
    let mut buffer = Vec::new();
    let encoder = TextEncoder::new();

    let metric_families = REGISTRY.gather();
    encoder.encode(&metric_families, &mut buffer).unwrap();

    let raw_failures = format!(
        "sovereignstack_policy_zk_failures_raw {}\nsovereignstack_policy_zk_verifications_raw {}\n",
        TOTAL_ZK_FAILURES.load(Ordering::SeqCst),
        TOTAL_ZK_VERIFICATIONS.load(Ordering::SeqCst)
    );

    String::from_utf8(buffer).unwrap() + &raw_failures
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_metrics_serialization_format() {
        initialize_metrics();
        record_alignment_breach("values://org/ethics-charter", "agent://rogue-01");

        let scrape_output = scrape_metrics_to_string();
        assert!(scrape_output.contains("sovereignstack_policy_zk_failures_total"));
        assert!(scrape_output.contains("values_uri=\"values://org/ethics-charter\""));
    }
}
