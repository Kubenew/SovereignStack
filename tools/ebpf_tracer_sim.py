import json

# Simulation of eBPF LSM probe behavior inside SovereignStack kernel
class EBPFCapabilityTracerCore:
    def __init__(self, allowed_manifest_policies):
        # Initialize oasa_policy_map in kernel memory
        self.kernel_policy_map = set(allowed_manifest_policies)
        self.worm_log = []
        self.signals_sent = {}

    def trace_cap_capable_event(self, pid, cgroup_id, cap_name, kernel_auth_result):
        # Create unique key corresponding to 'struct policy_key'
        policy_key = (cgroup_id, cap_name)

        # Check if capability is in the allowed policies map
        is_allowed = policy_key in self.kernel_policy_map

        # Class deviation assignment logic (Section IV Spec)
        if is_allowed:
            deviation_class = 1  # Class I: Within normal limits
            action_taken = False
        else:
            if kernel_auth_result == "GRANTED":
                deviation_class = 3  # Class III: Active unauthorized execution
                action_taken = True
                # Inline Mitigation: Immediate kernel intervention (bpf_send_signal)
                self.signals_sent[pid] = "SIGKILL (9)"
            else:
                deviation_class = 2  # Class II: Passive holding/query, operation did not execute
                action_taken = False

        # Write event to structure corresponding to 'struct cap_audit_event'
        audit_event = {
            "pid": pid,
            "cgroup_id": cgroup_id,
            "capability": cap_name,
            "class": deviation_class,
            "action_taken": action_taken
        }
        self.worm_log.append(audit_event)
        
        return audit_event

if __name__ == "__main__":
    print("=== OASA eBPF Tracing Engine Simulation ===")
    
    # Define approved policy for container 42 (Only port binding allowed)
    oasa_approved_manifest = [(42, "CAP_NET_BIND_SERVICE")]
    
    tracer = EBPFCapabilityTracerCore(allowed_manifest_policies=oasa_approved_manifest)
    
    print("\n--- TEST 1: Legitimate Behavior (Class I) ---")
    ev1 = tracer.trace_cap_capable_event(pid=102, cgroup_id=42, cap_name="CAP_NET_BIND_SERVICE", kernel_auth_result="GRANTED")
    print(f"Event Class: {ev1['class']} | Kill Signal: {tracer.signals_sent.get(102, 'None')}")
    
    print("\n--- TEST 2: Passive Token outside Manifest (Class II) ---")
    ev2 = tracer.trace_cap_capable_event(pid=102, cgroup_id=42, cap_name="CAP_SYS_CHROOT", kernel_auth_result="DENIED")
    print(f"Event Class: {ev2['class']} | Kill Signal: {tracer.signals_sent.get(102, 'None')}")
    
    print("\n--- TEST 3: Active Security Breach / Attack Attempt (Class III) ---")
    ev3 = tracer.trace_cap_capable_event(pid=9012, cgroup_id=42, cap_name="CAP_SYS_RAWIO", kernel_auth_result="GRANTED")
    print(f"Event Class: {ev3['class']} | Kill Signal: {tracer.signals_sent.get(9012, 'None')}")
