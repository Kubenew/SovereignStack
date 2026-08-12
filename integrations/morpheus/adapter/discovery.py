from .client import MorpheusClient

class DiscoveryAdapter:
    """Maps Morpheus workload metadata to a SovereignStack Identity."""
    def __init__(self, client: MorpheusClient):
        self.client = client

    def discover(self, vm_id: str) -> dict:
        morpheus_data = self.client.get_workload(vm_id)
        
        # Mapping to SovereignStack Identity
        return {
            "identity_uri": f"agent://morpheus/{morpheus_data['name']}",
            "morpheus_id": morpheus_data["id"],
            "labels": morpheus_data["labels"],
            "status": morpheus_data["status"]
        }
