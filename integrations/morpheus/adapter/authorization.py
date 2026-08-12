class AuthorizationAdapter:
    """
    Gates Morpheus API actions behind SovereignStack Policy evaluation.
    Translates intent into a SovereignStack Capability check.
    """
    def authorize(self, identity_uri: str, operation: str, context: dict) -> dict:
        # Mock policy evaluation based on operation
        if operation == "morpheus:provision":
            if "secure" in context.get("labels", []):
                return {"decision": "allow", "policy_ref": "policy://provision-secure"}
            return {"decision": "deny", "reason": "Missing secure label"}
        
        if operation == "morpheus:network_egress":
            return {"decision": "deny", "reason": "Egress not permitted"}
            
        return {"decision": "deny", "reason": "Unknown operation"}
