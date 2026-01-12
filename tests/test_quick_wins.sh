#!/bin/bash
# Quick Wins Feature Validation Test
# Tests all 5 analysis tools with the anova_test dataset

set -e

echo "=========================================="
echo "Quick Wins Feature Validation Test"
echo "=========================================="
echo ""

# Test 1: Metadata Capture
echo "[1/5] Testing metadata capture..."
python3 analyze/capture_metadata.py --summary > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Metadata capture working"
else
    echo "✗ Metadata capture failed"
    exit 1
fi

# Test 2: Confidence Intervals
echo "[2/5] Testing confidence intervals..."
python3 analyze/confidence_intervals.py data/anova_test.csv \
    --metric runtime_ns --group workload_type > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Confidence intervals working"
else
    echo "✗ Confidence intervals failed"
    exit 1
fi

# Test 3: JSON Export
echo "[3/5] Testing JSON export..."
python3 analyze/export_json.py data/anova_test.csv \
    --output /tmp/lrc_test_export.json > /dev/null 2>&1
if [ $? -eq 0 ] && [ -f /tmp/lrc_test_export.json ]; then
    echo "✓ JSON export working"
    rm -f /tmp/lrc_test_export.json
else
    echo "✗ JSON export failed"
    exit 1
fi

# Test 4: Power Analysis
echo "[4/5] Testing power analysis..."
python3 analyze/power_analysis.py --effect-size 0.5 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Power analysis working"
else
    echo "✗ Power analysis failed"
    exit 1
fi

# Test 5: ANOVA
echo "[5/5] Testing ANOVA..."
python3 analyze/anova.py data/anova_test.csv \
    --metric runtime_ns --group workload_type > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ ANOVA working"
else
    echo "✗ ANOVA failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "All Quick Wins features validated! ✓"
echo "=========================================="
echo ""
echo "Available tools:"
echo "  - analyze/capture_metadata.py"
echo "  - analyze/confidence_intervals.py"
echo "  - analyze/export_json.py"
echo "  - analyze/power_analysis.py"
echo "  - analyze/anova.py"
echo ""
echo "Run './lrc' for main experiments"
echo "Run 'python3 analyze/<tool>.py --help' for usage"
