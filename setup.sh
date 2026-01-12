#!/bin/bash
#
# Linux Reality Check - One-Step Setup Script
#
# This script builds LRC and optionally configures your system for optimal measurement quality.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   Linux Reality Check (LRC) - Setup Script${NC}"
echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Build everything
echo -e "${BOLD}[1/3] Building LRC Components${NC}"
echo ""

echo "Building core library..."
cd core
make -j$(nproc) || {
    echo "❌ Core build failed"
    exit 1
}
echo -e "${GREEN}✓${NC} Core library built"

echo "Building scenarios..."
cd ../scenarios
make -j$(nproc) || {
    echo "❌ Scenarios build failed"
    exit 1
}
echo -e "${GREEN}✓${NC} All 10 scenarios built"

cd "$PROJECT_ROOT"
echo ""

# Step 2: Check Python dependencies
echo -e "${BOLD}[2/3] Checking Python Dependencies${NC}"
echo ""

PYTHON_OK=true
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found"
    PYTHON_OK=false
else
    echo -e "${GREEN}✓${NC} python3 found: $(python3 --version)"
fi

# Check for numpy (optional but recommended)
if python3 -c "import numpy" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} numpy available (for advanced analysis)"
else
    echo -e "${YELLOW}⚠${NC} numpy not found (optional, install with: pip3 install numpy)"
fi

# Check for scipy (optional)
if python3 -c "import scipy" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} scipy available (for hypothesis testing)"
else
    echo -e "${YELLOW}⚠${NC} scipy not found (optional, install with: pip3 install scipy)"
fi

echo ""

# Step 3: System configuration check
echo -e "${BOLD}[3/3] System Configuration Check${NC}"
echo ""

HAS_ROOT=false
if [ "$EUID" -eq 0 ]; then
    HAS_ROOT=true
fi

# CPU Governor
if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
    GOV=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)
    echo "Current CPU governor: $GOV"
    
    if [ "$GOV" != "performance" ]; then
        echo -e "${YELLOW}⚠${NC} Recommend 'performance' governor for reproducibility"
        
        if $HAS_ROOT; then
            read -p "Set CPU governor to 'performance'? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                if command -v cpupower &> /dev/null; then
                    cpupower frequency-set -g performance
                    echo -e "${GREEN}✓${NC} CPU governor set to 'performance'"
                else
                    echo -e "${YELLOW}⚠${NC} cpupower not found, skipping"
                fi
            fi
        else
            echo "  To fix: sudo cpupower frequency-set -g performance"
        fi
    else
        echo -e "${GREEN}✓${NC} CPU governor already set to 'performance'"
    fi
else
    echo "CPU frequency scaling not available"
fi

echo ""

# perf_event_paranoid
if [ -f /proc/sys/kernel/perf_event_paranoid ]; then
    PARANOID=$(cat /proc/sys/kernel/perf_event_paranoid)
    echo "Current perf_event_paranoid: $PARANOID"
    
    if [ "$PARANOID" -gt 1 ]; then
        echo -e "${YELLOW}⚠${NC} perf hardware counters may be restricted (recommend: ≤1)"
        
        if $HAS_ROOT; then
            read -p "Allow perf hardware counters? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sysctl -w kernel.perf_event_paranoid=1
                echo -e "${GREEN}✓${NC} perf_event_paranoid set to 1"
            fi
        else
            echo "  To fix: sudo sysctl -w kernel.perf_event_paranoid=1"
        fi
    else
        echo -e "${GREEN}✓${NC} perf hardware counters accessible"
    fi
fi

echo ""

# ASLR (optional)
if [ -f /proc/sys/kernel/randomize_va_space ]; then
    ASLR=$(cat /proc/sys/kernel/randomize_va_space)
    if [ "$ASLR" -ne 0 ]; then
        echo "Address space randomization: enabled"
        echo -e "${YELLOW}ℹ${NC} Optional: Disable ASLR for more reproducible results"
        echo "  To disable: echo 0 | sudo tee /proc/sys/kernel/randomize_va_space"
    else
        echo -e "${GREEN}✓${NC} Address space randomization disabled"
    fi
fi

echo ""
echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}   Setup Complete!${NC}"
echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo ""
echo "  ${BOLD}Quick start:${NC}"
echo "    ./lrc quick              # Run 3 fast experiments (~30s)"
echo ""
echo "  ${BOLD}Interactive menu:${NC}"
echo "    ./lrc                    # Browse and select experiments"
echo ""
echo "  ${BOLD}Run specific experiment:${NC}"
echo "    ./lrc run pinned         # Test CPU affinity impact"
echo ""
echo "  ${BOLD}Check system:${NC}"
echo "    ./lrc check              # Verify configuration"
echo ""
echo "  ${BOLD}Read documentation:${NC}"
echo "    cat QUICKSTART.md        # 5-minute guide"
echo "    cat README.md            # Full documentation"
echo ""
echo "Results will be saved in: ${BLUE}data/${NC}"
echo ""
