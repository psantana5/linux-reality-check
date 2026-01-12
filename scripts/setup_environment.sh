#!/bin/bash
#
# setup_environment.sh - Configure system for reproducible experiments
#
# Purpose:
#   Set optimal system state for performance measurement.
#   Save current state and provide restore function.

set -e

STATE_FILE="/tmp/lrc_saved_state.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script needs root privileges"
        log_info "Run with: sudo $0 $1"
        exit 1
    fi
}

save_state() {
    log_info "Saving current system state..."
    
    > "$STATE_FILE"
    
    # CPU governor
    if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
        GOV=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)
        echo "GOVERNOR=$GOV" >> "$STATE_FILE"
    fi
    
    # ASLR
    if [ -f /proc/sys/kernel/randomize_va_space ]; then
        ASLR=$(cat /proc/sys/kernel/randomize_va_space)
        echo "ASLR=$ASLR" >> "$STATE_FILE"
    fi
    
    # Swappiness
    if [ -f /proc/sys/vm/swappiness ]; then
        SWAP=$(cat /proc/sys/vm/swappiness)
        echo "SWAPPINESS=$SWAP" >> "$STATE_FILE"
    fi
    
    log_info "State saved to $STATE_FILE"
}

restore_state() {
    if [ ! -f "$STATE_FILE" ]; then
        log_error "No saved state found at $STATE_FILE"
        exit 1
    fi
    
    log_info "Restoring system state..."
    
    source "$STATE_FILE"
    
    # Restore CPU governor
    if [ -n "$GOVERNOR" ]; then
        log_info "Restoring CPU governor to: $GOVERNOR"
        for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
            [ -f "$cpu" ] && echo "$GOVERNOR" > "$cpu" 2>/dev/null || true
        done
    fi
    
    # Restore ASLR
    if [ -n "$ASLR" ]; then
        log_info "Restoring ASLR to: $ASLR"
        echo "$ASLR" > /proc/sys/kernel/randomize_va_space
    fi
    
    # Restore swappiness
    if [ -n "$SWAPPINESS" ]; then
        log_info "Restoring swappiness to: $SWAPPINESS"
        echo "$SWAPPINESS" > /proc/sys/vm/swappiness
    fi
    
    rm "$STATE_FILE"
    log_info "State restored"
}

configure_system() {
    check_root
    save_state
    
    log_info "Configuring system for performance measurement..."
    
    # Set CPU governor to performance
    if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
        log_info "Setting CPU governor to 'performance'..."
        for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
            [ -f "$cpu" ] && echo "performance" > "$cpu" 2>/dev/null || true
        done
        log_info "✓ CPU governor set"
    else
        log_warn "CPU frequency scaling not available"
    fi
    
    # Disable ASLR
    if [ -f /proc/sys/kernel/randomize_va_space ]; then
        log_info "Disabling ASLR..."
        echo 0 > /proc/sys/kernel/randomize_va_space
        log_info "✓ ASLR disabled"
    fi
    
    # Reduce swappiness
    if [ -f /proc/sys/vm/swappiness ]; then
        log_info "Setting swappiness to 1..."
        echo 1 > /proc/sys/vm/swappiness
        log_info "✓ Swappiness reduced"
    fi
    
    echo ""
    log_info "System configured. Run: sudo $0 --restore when done"
}

print_status() {
    echo "=== System Status ==="
    echo "Kernel: $(uname -r)"
    echo "CPU: $(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)"
    echo "Cores: $(nproc)"
    
    if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
        echo "Governor: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
    fi
    
    if [ -f /proc/sys/kernel/randomize_va_space ]; then
        echo "ASLR: $(cat /proc/sys/kernel/randomize_va_space)"
    fi
    
    echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
}

case "${1:---status}" in
    --setup) configure_system ;;
    --restore) check_root; restore_state ;;
    --status) print_status ;;
    *) 
        echo "Usage: $0 [--setup|--restore|--status]"
        exit 1
        ;;
esac
