#!/usr/bin/env python3
"""
ebpf_tracer.py - eBPF-based kernel tracing

Purpose:
  Use BPF to trace scheduler events during workload execution.
  Provides kernel-level visibility into scheduler decisions.

Requires:
  - Python bcc library (apt install python3-bpfcc)
  - Root privileges or CAP_BPF
  - Kernel with eBPF support (4.1+)

Usage:
  sudo python3 ebpf_tracer.py <pid>
"""

import sys
import os
from pathlib import Path

# Check if BCC is available
try:
    from bcc import BPF
    HAS_BCC = True
except ImportError:
    HAS_BCC = False
    print("Warning: BCC not available. Install with: apt install python3-bpfcc", 
          file=sys.stderr)

# eBPF program for tracing scheduler events
BPF_PROGRAM = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

struct sched_switch_event {
    u64 ts;
    u32 prev_pid;
    u32 next_pid;
    u32 prev_cpu;
    u32 next_cpu;
};

struct sched_migrate_event {
    u64 ts;
    u32 pid;
    u32 orig_cpu;
    u32 dest_cpu;
};

BPF_PERF_OUTPUT(sched_switches);
BPF_PERF_OUTPUT(sched_migrates);

// Trace context switches
TRACEPOINT_PROBE(sched, sched_switch) {
    u32 target_pid = TARGET_PID;
    
    if (args->prev_pid == target_pid || args->next_pid == target_pid) {
        struct sched_switch_event event = {};
        event.ts = bpf_ktime_get_ns();
        event.prev_pid = args->prev_pid;
        event.next_pid = args->next_pid;
        event.prev_cpu = bpf_get_smp_processor_id();
        event.next_cpu = bpf_get_smp_processor_id();
        
        sched_switches.perf_submit(args, &event, sizeof(event));
    }
    
    return 0;
}

// Trace CPU migrations
TRACEPOINT_PROBE(sched, sched_migrate_task) {
    u32 target_pid = TARGET_PID;
    
    if (args->pid == target_pid) {
        struct sched_migrate_event event = {};
        event.ts = bpf_ktime_get_ns();
        event.pid = args->pid;
        event.orig_cpu = args->orig_cpu;
        event.dest_cpu = args->dest_cpu;
        
        sched_migrates.perf_submit(args, &event, sizeof(event));
    }
    
    return 0;
}
"""


class SchedulerTracer:
    """eBPF-based scheduler event tracer."""
    
    def __init__(self, target_pid: int):
        if not HAS_BCC:
            raise RuntimeError("BCC library not available")
        
        self.target_pid = target_pid
        self.switch_count = 0
        self.migrate_count = 0
        self.events = []
        
        # Replace TARGET_PID in BPF program
        program = BPF_PROGRAM.replace('TARGET_PID', str(target_pid))
        
        try:
            self.bpf = BPF(text=program)
        except Exception as e:
            raise RuntimeError(f"Failed to load BPF program: {e}")
        
        # Attach callbacks
        self.bpf["sched_switches"].open_perf_buffer(self._handle_switch)
        self.bpf["sched_migrates"].open_perf_buffer(self._handle_migrate)
    
    def _handle_switch(self, cpu, data, size):
        """Handle context switch event."""
        event = self.bpf["sched_switches"].event(data)
        self.switch_count += 1
        self.events.append({
            'type': 'switch',
            'ts': event.ts,
            'prev_pid': event.prev_pid,
            'next_pid': event.next_pid,
            'cpu': event.prev_cpu
        })
    
    def _handle_migrate(self, cpu, data, size):
        """Handle migration event."""
        event = self.bpf["sched_migrates"].event(data)
        self.migrate_count += 1
        self.events.append({
            'type': 'migrate',
            'ts': event.ts,
            'pid': event.pid,
            'from_cpu': event.orig_cpu,
            'to_cpu': event.dest_cpu
        })
    
    def poll(self, timeout_ms: int = 100):
        """Poll for events."""
        self.bpf.perf_buffer_poll(timeout=timeout_ms)
    
    def report(self):
        """Print summary report."""
        print(f"\nScheduler Events for PID {self.target_pid}:")
        print(f"  Context switches: {self.switch_count}")
        print(f"  CPU migrations: {self.migrate_count}")
        
        if self.events:
            print(f"\nFirst 10 events:")
            for event in self.events[:10]:
                if event['type'] == 'switch':
                    print(f"  [{event['ts']}] SWITCH on CPU {event['cpu']}: "
                          f"{event['prev_pid']} → {event['next_pid']}")
                else:
                    print(f"  [{event['ts']}] MIGRATE: "
                          f"CPU {event['from_cpu']} → {event['to_cpu']}")


def main():
    if not HAS_BCC:
        print("Error: BCC not installed", file=sys.stderr)
        print("Install: sudo apt install python3-bpfcc", file=sys.stderr)
        sys.exit(1)
    
    if os.geteuid() != 0:
        print("Error: This script requires root privileges", file=sys.stderr)
        print("Run: sudo python3 ebpf_tracer.py <pid>", file=sys.stderr)
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print(f"Usage: sudo {sys.argv[0]} <pid>", file=sys.stderr)
        print("\nExample:", file=sys.stderr)
        print("  Terminal 1: ./pinned &", file=sys.stderr)
        print("  Terminal 2: sudo python3 ebpf_tracer.py $!", file=sys.stderr)
        sys.exit(1)
    
    target_pid = int(sys.argv[1])
    
    print(f"Tracing scheduler events for PID {target_pid}...")
    print("Press Ctrl+C to stop\n")
    
    try:
        tracer = SchedulerTracer(target_pid)
        
        while True:
            tracer.poll()
    
    except KeyboardInterrupt:
        pass
    
    tracer.report()


if __name__ == '__main__':
    main()
