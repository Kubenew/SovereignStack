/* file: ss_core_tracer.bpf.c */
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

char LICENSE[] SEC("license") = "GPL";

#define MAX_CAPABILITIES_COUNT 64

// Structure of the event sent to user-space via ring buffer
struct cap_audit_event {
    u64 timestamp_ns;
    u32 pid;
    u32 tgid;
    u64 cgroup_id;
    char comm[16];
    u32 capability_id;
    u32 deviation_class; // 1 = Class I, 2 = Class II, 3 = Class III
    u32 syscall_id;
    bool action_taken;
};

// Map defining the approved capabilities (populated from user-space during node startup)
// Key: cgroup_id + capability_id -> Value: allowed (0/1)
struct policy_key {
    u64 cgroup_id;
    u32 capability_id;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, struct policy_key);
    __type(value, u8);
    __uint(max_entries, 1024);
} oasa_policy_map SEC(".maps");

// Ring Buffer for immediate submission of Class III incidents to the audit daemon
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 22); // 4MB buffer
} audit_ring_buffer SEC(".maps");

SEC("lsm/cred_cap_capable")
int BPF_PROG(bpf_oasa_audit_cap, const struct cred *cred, struct user_namespace *ns, int cap, unsigned int opts, int ret)
{
    u64 cgroup_id = bpf_get_current_cgroup_id();
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;

    struct policy_key key = {};
    key.cgroup_id = cgroup_id;
    key.capability_id = (u32)cap;

    // Look up in the policy map approved by the OASA Manifest
    u8 *policy_allowed = bpf_map_lookup_elem(&oasa_policy_map, &key);

    // Default state: If the record does not exist, the capability is considered NOT ALLOWED
    if (policy_allowed && *policy_allowed == 1) {
        // Class I: Everything is fine, the operation matches the declared state
        return 0;
    }

    // Initialize audit event
    struct cap_audit_event *event;
    event = bpf_ringbuf_reserve(&audit_ring_buffer, sizeof(*event), 0);
    if (!event) {
        return 0; // Buffer full, security failure (detected by user layer)
    }

    event->timestamp_ns = bpf_ktime_get_ns();
    event->pid = pid;
    event->cgroup_id = cgroup_id;
    event->capability_id = cap;
    bpf_get_current_comm(&event->comm, sizeof(event->comm));

    // Key Decision: Was the unauthorized capability only possessed, or already exercised?
    // 'ret' represents the return value of the internal Linux kernel capability check
    if (ret == 0) {
        // The Linux kernel permitted the check (ret=0) and we know it is not in our manifest
        event->deviation_class = 3; // CLASS III: CONTROL FAILED - Active misuse
        event->action_taken = true;
    } else {
        // The kernel would deny the call, or it is a passive status inspection of the process
        event->deviation_class = 2; // CLASS II: PASSIVE DEVIATION - Risk of holding the token
        event->action_taken = false;
    }

    // Send to user-space daemon for immediate WORM log writing and Halt State evaluation
    bpf_ringbuf_submit(event, 0);

    // If we detect Class III, we can intervene directly in the kernel (Inline Mitigation)
    if (event->deviation_class == 3) {
        // OASA Policy: Immediate process isolation by sending SIGKILL directly from eBPF context
        bpf_send_signal(9);
    }

    return 0;
}
