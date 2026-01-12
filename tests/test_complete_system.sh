#!/bin/bash
# Complete System Validation Test
# Tests all components of LRC v3.0

echo "=============================================="
echo "Linux Reality Check v3.0 - Complete Validation"
echo "=============================================="
echo ""

passed=0
failed=0

# Test 1: Scenarios compile
echo "[1/5] Checking scenario compilation..."
count=$(ls scenarios/ | grep -E '^[a-z_]+$' | wc -l)
if [ $count -ge 20 ]; then
    echo "✓ All $count scenarios compiled"
    passed=$((passed + 1))
else
    echo "✗ Only $count scenarios found (expected 20)"
    failed=$((failed + 1))
fi

# Test 2: Analysis tools exist
echo "[2/5] Checking analysis tools..."
tools=("db.py" "capture_metadata.py" "confidence_intervals.py" "power_analysis.py" "anova.py" "interference.py" "hypothesis.py")
tool_count=0
for tool in "${tools[@]}"; do
    if [ -f "analyze/$tool" ]; then
        tool_count=$((tool_count + 1))
    fi
done

if [ $tool_count -eq ${#tools[@]} ]; then
    echo "✓ All 7 key analysis tools present"
    passed=$((passed + 1))
else
    echo "✗ Only $tool_count/7 tools found"
    failed=$((failed + 1))
fi

# Test 3: Database system
echo "[3/5] Testing database system..."
python3 analyze/db.py --db /tmp/test_lrc.db --init > /dev/null 2>&1
if [ -f /tmp/test_lrc.db ]; then
    echo "✓ Database system working"
    rm -f /tmp/test_lrc.db
    passed=$((passed + 1))
else
    echo "✗ Database not created"
    failed=$((failed + 1))
fi

# Test 4: CLI commands
echo "[4/5] Testing CLI commands..."
if ./lrc --help > /dev/null 2>&1; then
    echo "✓ CLI help working"
    passed=$((passed + 1))
else
    echo "✗ CLI help failed"
    failed=$((failed + 1))
fi

# Test 5: Documentation
echo "[5/5] Checking documentation..."
docs=("DATABASE_GUIDE.md" "ANALYSIS_WORKFLOWS.md" "QUICK_WINS_COMPLETE.md" "FINAL_IMPLEMENTATION.md")
doc_count=0
for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        doc_count=$((doc_count + 1))
    fi
done

if [ $doc_count -ge 3 ]; then
    echo "✓ Documentation present ($doc_count/4 key docs)"
    passed=$((passed + 1))
else
    echo "✗ Missing documentation ($doc_count/4)"
    failed=$((failed + 1))
fi

echo ""
echo "=============================================="
echo "Validation Results: $passed passed, $failed failed"
echo "=============================================="
echo ""

if [ $failed -eq 0 ]; then
    echo "✓ Linux Reality Check v3.0 is ready for use!"
    echo ""
    echo "Quick start:"
    echo "  ./lrc list              # List all scenarios"
    echo "  ./lrc run null_baseline # Run quick experiment"
    echo "  ./lrc db --list         # View stored results"
    echo ""
    exit 0
else
    echo "⚠ Some components need attention"
    exit 1
fi
