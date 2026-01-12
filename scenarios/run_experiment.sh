#!/bin/bash
#
# run_experiment.sh - Experiment runner
#
# Usage: ./run_experiment.sh [pinned|nice_levels|cache_hierarchy]

set -e

SCENARIO="${1:-pinned}"
DATA_DIR="../data"
ANALYZE_DIR="../analyze"

mkdir -p "$DATA_DIR"

echo "=== Linux Reality Check ==="
echo "Experiment: $SCENARIO"
echo ""

# System info
echo "System Configuration:"
echo "  Kernel: $(uname -r)"
echo "  CPU: $(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)"
echo "  Cores: $(nproc)"
echo ""

# Check CPU governor
if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
    GOV=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)
    echo "  CPU Governor: $GOV"
    if [ "$GOV" != "performance" ]; then
        echo "  ⚠ Warning: Consider using 'performance' governor for reproducibility"
        echo "    sudo cpupower frequency-set -g performance"
    fi
fi

echo ""
echo "Running experiment..."
echo ""

case "$SCENARIO" in
    pinned)
        ./"$SCENARIO"
        ;;
    nice_levels)
        echo "Note: This may require sudo for nice -10"
        ./"$SCENARIO"
        ;;
    cache_hierarchy)
        ./"$SCENARIO"
        ;;
    *)
        echo "Unknown scenario: $SCENARIO"
        echo "Available: pinned, nice_levels, cache_hierarchy"
        exit 1
        ;;
esac

echo ""
echo "=== Analysis ==="
echo ""

python3 "$ANALYZE_DIR/parse.py" "$DATA_DIR/${SCENARIO}.csv"
echo ""
python3 "$ANALYZE_DIR/classify.py" "$DATA_DIR/${SCENARIO}.csv"
