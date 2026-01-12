#!/bin/bash
# Database System Validation Test
# Tests all database features end-to-end

set -e

echo "=========================================="
echo "Database System Validation Test"
echo "=========================================="
echo ""

# Clean slate
rm -f ~/.lrc/results_test.db

# Test 1: Initialize
echo "[1/8] Testing database initialization..."
python3 analyze/db.py --db ~/.lrc/results_test.db --init > /dev/null 2>&1
if [ -f ~/.lrc/results_test.db ]; then
    echo "✓ Database initialized"
else
    echo "✗ Database initialization failed"
    exit 1
fi

# Test 2: Store with metadata
echo "[2/8] Testing store with metadata..."
python3 analyze/capture_metadata.py --output /tmp/test_meta.json > /dev/null 2>&1
python3 analyze/db.py --db ~/.lrc/results_test.db \
    --store data/anova_test.csv \
    --scenario anova_test \
    --metadata /tmp/test_meta.json \
    --notes "Test experiment" \
    --tags test validation > /dev/null 2>&1
echo "✓ Store with metadata working"

# Test 3: List
echo "[3/8] Testing list experiments..."
count=$(python3 analyze/db.py --db ~/.lrc/results_test.db --list 2>/dev/null | grep -c "anova_test" || true)
if [ "$count" -ge 1 ]; then
    echo "✓ List working"
else
    echo "✗ List failed"
    exit 1
fi

# Test 4: Stats
echo "[4/8] Testing statistics..."
python3 analyze/db.py --db ~/.lrc/results_test.db --stats 1 > /dev/null 2>&1
echo "✓ Statistics working"

# Test 5: Export CSV
echo "[5/8] Testing CSV export..."
python3 analyze/db.py --db ~/.lrc/results_test.db \
    --export 1 --output /tmp/exported.csv > /dev/null 2>&1
if [ -f /tmp/exported.csv ]; then
    lines=$(wc -l < /tmp/exported.csv)
    if [ "$lines" -ge 30 ]; then
        echo "✓ CSV export working ($lines rows)"
    else
        echo "✗ CSV export incomplete"
        exit 1
    fi
else
    echo "✗ CSV export failed"
    exit 1
fi

# Test 6: Export JSON
echo "[6/8] Testing JSON export..."
python3 analyze/db.py --db ~/.lrc/results_test.db \
    --export 1 --output /tmp/exported.json --format json > /dev/null 2>&1
if [ -f /tmp/exported.json ]; then
    echo "✓ JSON export working"
else
    echo "✗ JSON export failed"
    exit 1
fi

# Test 7: Query
echo "[7/8] Testing SQL queries..."
result=$(python3 analyze/db.py --db ~/.lrc/results_test.db \
    --query "SELECT COUNT(*) FROM experiments" 2>/dev/null | tail -1)
if [ "$result" -ge 1 ]; then
    echo "✓ SQL queries working"
else
    echo "✗ SQL queries failed"
    exit 1
fi

# Test 8: CLI Integration
echo "[8/8] Testing CLI integration..."
STORE_DB=true
if ./lrc store anova_test 2>&1 | grep -q "Stored in database"; then
    echo "✓ CLI integration working"
else
    echo "✗ CLI integration failed"
    exit 1
fi

# Cleanup
rm -f ~/.lrc/results_test.db /tmp/test_meta.json /tmp/exported.csv /tmp/exported.json

echo ""
echo "=========================================="
echo "All database features validated! ✓"
echo "=========================================="
echo ""
echo "Database system ready for production use."
