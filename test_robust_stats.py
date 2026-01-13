#!/usr/bin/env python3
"""Integration test for robust statistics refactoring."""

import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'analyze'))

from robust_stats import (
    describe_robust,
    quantile,
    median,
    iqr,
    mad,
    bootstrap_ci_quantile,
    quantile_difference_ci,
    hodges_lehmann_estimator,
    tukey_fences
)

def test_basic_stats():
    """Test basic robust statistics."""
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # One extreme value
    
    stats = describe_robust(data)
    
    # Median should be between 4 and 6
    assert 4 <= stats['median'] <= 6, f"Expected median ~5.5, got {stats['median']}"
    
    # IQR should be positive
    assert stats['iqr'] > 0, f"IQR should be positive, got {stats['iqr']}"
    assert stats['n'] == 10
    
    # Tail ratio should be high due to extreme value
    assert stats['tail_ratio'] > 2.0, f"Expected heavy tail, got ratio {stats['tail_ratio']}"
    
    print("✓ Basic statistics")

def test_quantiles():
    """Test quantile calculations."""
    data = list(range(1, 101))  # 1-100
    
    p50 = quantile(data, 0.50)
    p90 = quantile(data, 0.90)
    p99 = quantile(data, 0.99)
    
    assert 48 <= p50 <= 52, f"p50 should be ~50, got {p50}"
    assert 86 <= p90 <= 92, f"p90 should be ~90, got {p90}"
    assert 95 <= p99 <= 100, f"p99 should be ~99, got {p99}"
    
    print("✓ Quantile calculation")

def test_bootstrap_ci():
    """Test bootstrap confidence intervals."""
    random.seed(42)
    data = [random.gauss(10, 2) for _ in range(100)]
    
    p50_est, lower, upper = bootstrap_ci_quantile(data, 0.50, n_bootstrap=1000)
    
    # CI should contain the estimate
    assert lower <= p50_est <= upper
    
    # CI should be reasonably sized (not degenerate)
    assert upper - lower > 0
    
    print("✓ Bootstrap confidence intervals")

def test_comparison():
    """Test comparison between two groups."""
    baseline = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    treatment = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]  # ~2 units faster
    
    # Hodges-Lehmann
    hl = hodges_lehmann_estimator(baseline, treatment)
    assert hl > 0, f"Baseline should be slower, HL = {hl}"
    
    # Quantile difference
    diff, lower, upper = quantile_difference_ci(
        baseline, treatment, 0.50, n_bootstrap=1000
    )
    
    assert diff > 0, f"Baseline should have higher median, diff = {diff}"
    
    print("✓ Group comparison")

def test_outlier_detection():
    """Test outlier flagging."""
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # Clear outlier
    
    lower, upper, flagged = tukey_fences(data, k=1.5)
    
    assert len(flagged) > 0, "Should flag at least one outlier"
    assert 9 in flagged, "Should flag the extreme value (index 9)"
    
    print("✓ Outlier detection")

def test_tail_heaviness():
    """Test tail heaviness metric."""
    # Light tails
    light = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    stats_light = describe_robust(light)
    assert stats_light['tail_ratio'] < 1.5
    
    # Heavy tails
    heavy = [10] * 90 + [50, 60, 70, 80, 90, 100, 110, 120, 130, 140]
    stats_heavy = describe_robust(heavy)
    assert stats_heavy['tail_ratio'] > 2.0
    
    print("✓ Tail heaviness detection")

def main():
    print("Testing robust statistics module...\n")
    
    test_basic_stats()
    test_quantiles()
    test_bootstrap_ci()
    test_comparison()
    test_outlier_detection()
    test_tail_heaviness()
    
    print("\n✓✓✓ All tests passed!\n")
    print("The statistical refactoring is working correctly.")
    print("Ready for academic use.")

if __name__ == '__main__':
    main()
