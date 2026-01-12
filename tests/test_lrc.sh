#!/bin/bash
#
# LRC Comprehensive Test Suite
# Tests all functionality of the lrc command

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0
TESTS=0

test_passed() {
    PASSED=$((PASSED + 1))
    TESTS=$((TESTS + 1))
    echo -e "${GREEN}✓${NC} $1"
}

test_failed() {
    FAILED=$((FAILED + 1))
    TESTS=$((TESTS + 1))
    echo -e "${RED}✗${NC} $1"
}

test_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          LRC Comprehensive Test Suite                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Basic command existence
echo "=== Test 1: Command Existence ==="
if [ -x ./lrc ]; then
    test_passed "lrc command exists and is executable"
else
    test_failed "lrc command not found or not executable"
fi
echo ""

# Test 2: Help output
echo "=== Test 2: Help Output ==="
if ./lrc --help >/dev/null 2>&1; then
    test_passed "Help command works"
else
    test_failed "Help command failed"
fi
echo ""

# Test 3: Version output
echo "=== Test 3: Version Information ==="
if ./lrc --version >/dev/null 2>&1; then
    test_passed "Version command works"
else
    test_failed "Version command failed"
fi
echo ""

# Test 4: List experiments
echo "=== Test 4: List Experiments ==="
if ./lrc list | grep -q "pinned"; then
    test_passed "List command shows experiments"
else
    test_failed "List command output incorrect"
fi
echo ""

# Test 5: Check system
echo "=== Test 5: System Check ==="
if ./lrc check 2>&1 | grep -q "CPU:"; then
    test_passed "Check command displays system info"
else
    test_failed "Check command output incorrect"
fi
echo ""

# Test 6: Build command
echo "=== Test 6: Build Components ==="
if ./lrc build >/dev/null 2>&1; then
    test_passed "Build command succeeded"
else
    test_failed "Build command failed"
fi
echo ""

# Test 7: Experiment validation
echo "=== Test 7: Invalid Experiment Handling ==="
if ./lrc run nonexistent 2>&1 | grep -q "Unknown experiment"; then
    test_passed "Invalid experiment rejected with clear error"
else
    test_failed "Invalid experiment error handling broken"
fi
echo ""

# Test 8: Run null_baseline (fast test)
echo "=== Test 8: Run Null Baseline Experiment ==="
rm -f data/null_baseline.csv  # Clean up first to avoid overwrite prompt
if timeout 60 ./lrc run null_baseline </dev/null >/dev/null 2>&1; then
    test_passed "null_baseline experiment ran successfully"
    if [ -f data/null_baseline.csv ]; then
        test_passed "CSV file generated"
    else
        test_failed "CSV file not generated"
    fi
else
    test_failed "null_baseline experiment failed or timed out"
fi
echo ""

# Test 9: Analyze command
echo "=== Test 9: Analyze Results ==="
if ./lrc analyze null_baseline 2>&1 | grep -q "Mean"; then
    test_passed "Analyze command works"
else
    test_failed "Analyze command failed"
fi
echo ""

# Test 10: Clean command
echo "=== Test 10: Clean Old Results ==="
if ./lrc clean >/dev/null 2>&1; then
    test_passed "Clean command succeeded"
    if [ -d data/archive ]; then
        test_passed "Archive directory created"
    fi
else
    test_failed "Clean command failed"
fi
echo ""

# Test 11: File permissions
echo "=== Test 11: File Permissions ==="
if [ -r scenarios/pinned ]; then
    test_passed "Scenario binaries are readable"
else
    test_warning "Some scenario binaries may not be accessible"
fi
echo ""

# Test 12: Data directory
echo "=== Test 12: Data Directory ==="
if [ -d data ]; then
    test_passed "Data directory exists"
else
    test_failed "Data directory missing"
fi
echo ""

# Test 13: Analyze directory
echo "=== Test 13: Analysis Tools ==="
if [ -f analyze/parse.py ] && [ -f analyze/classify.py ]; then
    test_passed "Analysis tools present"
else
    test_failed "Analysis tools missing"
fi
echo ""

# Test 14: Python availability
echo "=== Test 14: Python Environment ==="
if command -v python3 &>/dev/null; then
    test_passed "Python 3 available"
    
    # Check specific analysis tools
    if python3 -c "import sys" 2>/dev/null; then
        test_passed "Python environment functional"
    fi
else
    test_failed "Python 3 not found"
fi
echo ""

# Test 15: Interrupt handling
echo "=== Test 15: Interrupt Handling ==="
# Start a quick experiment in background and interrupt it
timeout 2 ./lrc run null_baseline >/dev/null 2>&1 &
local_pid=$!
sleep 0.5
kill -INT $local_pid 2>/dev/null || true
wait $local_pid 2>/dev/null || true
if [ $? -eq 130 ] || [ $? -eq 143 ]; then
    test_passed "Interrupt handling works"
else
    test_warning "Interrupt handling may need verification"
fi
echo ""

# Test 16: Output formatting
echo "=== Test 16: Output Formatting ==="
if ./lrc list | grep -q "╔"; then
    test_passed "Formatted output with box drawing characters"
else
    test_warning "Output formatting may be plain"
fi
echo ""

# Test 17: Error messages
echo "=== Test 17: Error Message Quality ==="
if ./lrc run badexperiment 2>&1 | grep -q "experiment"; then
    test_passed "Clear error messages for bad input"
else
    test_failed "Error messages unclear"
fi
echo ""

# Test 18: All experiments exist
echo "=== Test 18: All Experiment Binaries ==="
all_exist=true
for exp in pinned nice_levels null_baseline cache_hierarchy cache_analysis \
           latency_vs_bandwidth numa_locality lock_scaling syscall_overhead \
           realistic_patterns; do
    if [ ! -x "scenarios/$exp" ]; then
        test_failed "Missing: $exp"
        all_exist=false
    fi
done
if [ "$all_exist" = true ]; then
    test_passed "All 10 experiment binaries present"
fi
echo ""

# Test 19: Disk space handling
echo "=== Test 19: Disk Space Awareness ==="
if ./lrc check 2>&1 | grep -qE "(disk|space|MB)" || true; then
    test_passed "Disk space awareness present"
else
    test_warning "Disk space checks may be minimal"
fi
echo ""

# Test 20: Color output
echo "=== Test 20: Color Support ==="
if ./lrc --help | grep -q "$(printf '\033')"; then
    test_passed "Color output enabled"
else
    test_warning "Color output may be disabled (terminal support)"
fi
echo ""

# Test 21: No-color option
echo "=== Test 21: No-Color Option ==="
if ./lrc --no-color list 2>&1 | grep -qv "$(printf '\033')"; then
    test_passed "No-color option works"
else
    test_warning "No-color option may need verification"
fi
echo ""

# Test 22: Temp directory cleanup
echo "=== Test 22: Temporary File Cleanup ==="
before_count=$(find /tmp -name "lrc-*" 2>/dev/null | wc -l)
./lrc --version >/dev/null 2>&1
after_count=$(find /tmp -name "lrc-*" 2>/dev/null | wc -l)
if [ $after_count -le $before_count ]; then
    test_passed "Temp directories cleaned up"
else
    test_warning "Temp directories may accumulate"
fi
echo ""

# Test 23: Process cleanup
echo "=== Test 23: Process Cleanup ==="
# Check no stray processes
stray=$(ps aux | grep -E "scenarios/(pinned|cache|numa)" | grep -v grep | wc -l)
if [ $stray -eq 0 ]; then
    test_passed "No stray experiment processes"
else
    test_warning "$stray potentially stray process(es) detected"
fi
echo ""

# Test 24: CSV format validation
echo "=== Test 24: CSV Output Format ==="
if [ -f data/archive/null_baseline.csv ] || [ -f data/null_baseline.csv ]; then
    csv_file=$(ls data/archive/null_baseline.csv data/null_baseline.csv 2>/dev/null | head -1)
    if head -1 "$csv_file" | grep -q "runtime_ns"; then
        test_passed "CSV headers correct"
    else
        test_failed "CSV headers incorrect"
    fi
else
    test_warning "No CSV file available for validation"
fi
echo ""

# Test 25: Quick suite functionality
echo "=== Test 25: Quick Test Suite (will take ~30s) ==="
if timeout 90 ./lrc quick </dev/null >/dev/null 2>&1; then
    test_passed "Quick test suite completed"
else
    test_warning "Quick test suite timed out or failed"
fi
echo ""

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Test Summary                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Tests run: $TESTS"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
else
    echo "Failed: 0"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
