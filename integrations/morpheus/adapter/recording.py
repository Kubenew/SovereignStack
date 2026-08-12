import time
import hashlib

class RecordingAdapter:
    """
    Records Morpheus operations as SovereignStack Provenance events.
    """
    def record(self, identity_uri: str, operation: str, infrastructure_facts: dict, previous_hash: str) -> dict:
        event_data = f"{identity_uri}:{operation}:{infrastructure_facts}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        return {
            "event_type": "infrastructure.operation",
            "subject": identity_uri,
            "operation": operation,
            "facts": infrastructure_facts,
            "timestamp": int(time.time()),
            "previous_hash": previous_hash,
            "content_hash": event_hash
        }
