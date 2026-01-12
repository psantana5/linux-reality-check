# Troubleshooting Guide

## Common Problems and Solutions

### High Variance (>10% CV)

**Symptoms:**
```
StdDev: 156.32 ms
CV:     12.41%
```

**Causes:**
1. CPU frequency scaling
2. Thermal throttling
3. Background processes
4. Scheduler interference

**Solutions:**

```bash
# 1. Check CPU governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# If not "performance":
sudo scripts/setup_environment.sh --setup

# 2. Check system load
uptime
# Load should be < 1.0 for idle system

# 3. Check temperature
sensors  # Install: sudo apt install lm-sensors
# Look for throttling or >80°C

# 4. Stop background services
sudo systemctl stop cron
sudo systemctl stop apt-daily.timer
```

---

### Performance Counter Errors

**Symptoms:**
```
Warning: perf counters not available
```

**Causes:**
- `perf_event_paranoid` too restrictive
- Missing `CAP_PERFMON` capability
- Kernel not compiled with perf support

**Solutions:**

```bash
# Check current setting
cat /proc/sys/kernel/perf_event_paranoid
# Values: 2 (restricted), 1 (some access), 0 (all access), -1 (no restriction)

# Temporarily allow user access
sudo sysctl kernel.perf_event_paranoid=1

# Permanently (add to /etc/sysctl.conf)
echo "kernel.perf_event_paranoid=1" | sudo tee -a /etc/sysctl.conf

# Alternative: Give capability
sudo setcap cap_perfmon=+ep ./cache_analysis
```

---

### CPU Migrations Despite Pinning

**Symptoms:**
```
Migrations: 10/10 runs
Even when pinned
```

**Causes:**
- Permission denied (need CAP_SYS_NICE or root)
- IRQs moving thread
- CPU hotplug

**Solutions:**

```bash
# Run with sudo
sudo ./pinned

# Or give capability
sudo setcap cap_sys_nice=+ep ./pinned

# Verify pinning worked
# In scenario code, check start_cpu == end_cpu

# Check if IRQs are interfering
cat /proc/interrupts
# Look for high IRQ counts on your pinned CPU
```

---

### NUMA Locality Test Fails

**Symptoms:**
```
NUMA not available on this system
```

**Causes:**
- Single-socket system (UMA, not NUMA)
- VM without NUMA emulation
- Kernel not detecting topology

**Solutions:**

```bash
# Check NUMA availability
numactl --hardware
# Or
ls /sys/devices/system/node/

# If no NUMA:
- This is expected on single-socket systems
- Experiment is not applicable
- Skip or run on multi-socket hardware
```

---

### eBPF Tracer Fails

**Symptoms:**
```
Error: BCC not installed
RuntimeError: Failed to load BPF program
```

**Causes:**
- BCC not installed
- Insufficient permissions
- Kernel too old

**Solutions:**

```bash
# Install BCC
sudo apt install python3-bpfcc

# Run with root
sudo python3 analyze/ebpf_tracer.py <pid>

# Check kernel version (need 4.1+)
uname -r

# If still fails, check dmesg for BPF errors
dmesg | tail
```

---

### Build Errors

**Symptoms:**
```
undefined reference to `pthread_create'
```

**Causes:**
- Missing `-lpthread` flag
- Incorrect link order

**Solutions:**

```bash
# For lock_scaling scenario
# Make sure pthread is linked last
gcc ... -lpthread -lrt

# Clean and rebuild
make clean
make
```

---

### Results Don't Match Expectations

**Symptoms:**
```
Expected: Pinned faster
Actual: Unpinned faster
```

**This is NOT a bug!**

**Explanation:**
- Real system behavior doesn't always match theory
- This is the POINT of the tool - discover reality
- Possible reasons:
  - Your CPU is mostly idle (migration doesn't hurt)
  - Pinned CPU is busy with IRQs
  - Scheduler is smarter than expected

**Action:**
1. Document what you observed
2. Investigate why (use eBPF tracer, perf counters)
3. Update your mental model

---

### No Data Generated

**Symptoms:**
```
data/*.csv files are empty or missing
```

**Causes:**
- Experiment crashed
- Permission to write to data/
- Disk full

**Solutions:**

```bash
# Check if data directory exists
ls -ld data/
mkdir -p data

# Check permissions
ls -l data/

# Check disk space
df -h

# Run with verbose output
./pinned 2>&1 | tee output.log
```

---

### Outliers Every Run

**Symptoms:**
```
⚠ Outliers detected: 10/10
All runs are outliers
```

**Causes:**
- First run is always slower (cache cold)
- Workload too short (overhead dominates)
- System very noisy

**Solutions:**

```bash
# Add warmup runs (discard first few)
# Modify scenario:
# for (int warmup = 0; warmup < 3; warmup++) {
#     cpu_spin(ITERATIONS);
# }
# // Now start measuring

# Increase iterations
# Make workload longer relative to overhead

# Check if system is idle
top
htop
```

---

### Bimodal Distributions

**Symptoms:**
```
⚠ Bimodal distribution detected!
```

**Explanation:**
This is often REAL behavior, not a problem:
- Cache hits vs misses
- NUMA local vs remote
- CPU frequency transitions
- Periodic interference (cron, background tasks)

**Investigation:**

```bash
# Use time-series analysis
python3 analyze/timeseries.py data/experiment.csv

# Look for pattern
# Use eBPF tracer to see what happened
sudo python3 analyze/ebpf_tracer.py <pid>

# Check system events
dmesg | tail -100
```

---

### Docker Container Issues

**Symptoms:**
```
perf counters don't work in container
```

**Causes:**
- Container doesn't have privileges
- No access to host perf infrastructure

**Solutions:**

```bash
# Run with --privileged
docker run --privileged ...

# Or use docker-compose.yml (already configured)
docker-compose up lrc

# Note: Some features may not work in containers
# Run on bare metal for full functionality
```

---

### Thermal Throttling

**Symptoms:**
```
Later runs slower than early runs
p99/p50 ratio: 2.5x
```

**Detection:**

```bash
# Monitor temperature during test
watch -n 1 sensors

# Check dmesg for throttling messages
dmesg | grep -i thermal

# Time-series analysis will detect this
python3 analyze/timeseries.py data/experiment.csv
# Look for "⚠ Throttling detected"
```

**Solutions:**

```bash
# Improve cooling
# Run shorter experiments
# Reduce CPU frequency
sudo cpupower frequency-set -u 2.4GHz

# Wait between runs
# Add sleep in scenarios:
# sleep(5);  // Cool down
```

---

### Memory Allocation Fails

**Symptoms:**
```
Failed to allocate 67108864 bytes
```

**Causes:**
- Not enough RAM
- ulimit restrictions
- Memory fragmentation

**Solutions:**

```bash
# Check available memory
free -h

# Check ulimits
ulimit -a

# Try smaller buffer sizes
# Edit scenario, reduce BUFFER_SIZE

# For huge allocations, may need huge pages
# (Advanced - see Performance Tuning Guide)
```

---

## Getting Help

If problem persists:

1. **Check documentation:**
   - docs/methodology.md
   - docs/limitations.md
   - IMPROVEMENTS.md

2. **Gather information:**
   ```bash
   uname -a
   lscpu
   cat /proc/cpuinfo
   free -h
   uptime
   ```

3. **Check logs:**
   ```bash
   dmesg | tail -100
   journalctl -xe
   ```

4. **Minimal reproducer:**
   - Which scenario fails?
   - What's different about your system?
   - Can you reproduce on another machine?

5. **Remember:**
   - Unexpected results are DATA, not bugs
   - The tool shows reality, not theory
   - Document and investigate
