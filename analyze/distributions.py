#!/usr/bin/env python3
"""
distributions.py - Non-parametric distribution analysis

Purpose:
  Academically rigorous analysis of runtime distributions using
  non-parametric methods appropriate for heavy-tailed systems data.

Academic Rationale:
  - Uses ECDF instead of histograms/KDE (no binning/smoothing artifacts)
  - Reports median/IQR instead of mean/std (robust to heavy tails)
  - Quantile-based summaries (p50-p99.9) for tail latency
  - No parametric assumptions (no normal fits)
  - Outliers are retained and explained (meaningful tail behavior)
"""

import sys
from pathlib import Path
from typing import List, Dict
import statistics
sys.path.insert(0, str(Path(__file__).parent))
from parse import parse_csv, RunGroup
from robust_stats import (
    describe_robust,
    ecdf_values,
    tukey_fences,
    quantile,
    median,
    iqr,
    mad,
    tail_heaviness_ratio
)


def ecdf_ascii(values: List[float], points: int = 20, width: int = 40) -> None:
    """
    Draw ASCII ECDF (Empirical Cumulative Distribution Function).
    
    ECDF is superior to histograms for systems data because:
    - No arbitrary binning decisions
    - Shows all data without information loss
    - Clearly reveals tail behavior
    """
    if len(values) < 2:
        print("  Insufficient data for ECDF")
        return
    
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    min_val = sorted_vals[0]
    max_val = sorted_vals[-1]
    
    if max_val == min_val:
        print(f"  All values identical: {min_val:.2f}")
        return
    
    # Sample ECDF at regular intervals
    print("  ECDF (cumulative probability):")
    for i in range(points):
        # Value at this percentile
        percentile = i / (points - 1)
        val = sorted_vals[int(percentile * (n - 1))]
        
        # Draw bar
        bar_len = int(percentile * width)
        bar = "█" * bar_len
        
        # Show key percentiles with labels
        if i == 0:
            label = "min"
        elif abs(percentile - 0.25) < 0.02:
            label = "p25"
        elif abs(percentile - 0.50) < 0.02:
            label = "p50"
        elif abs(percentile - 0.75) < 0.02:
            label = "p75"
        elif abs(percentile - 0.90) < 0.02:
            label = "p90"
        elif abs(percentile - 0.99) < 0.02:
            label = "p99"
        elif i == points - 1:
            label = "max"
        else:
            label = ""
        
        print(f"  {val:7.1f} {bar} {label}")


def percentiles(values: List[float]) -> Dict[str, float]:
    """Calculate percentile values using robust quantile function."""
    if not values:
        return {}
    
    from robust_stats import quantile
    
    return {
        'p1': quantile(values, 0.01),
        'p5': quantile(values, 0.05),
        'p10': quantile(values, 0.10),
        'p25': quantile(values, 0.25),
        'p50': quantile(values, 0.50),
        'p75': quantile(values, 0.75),
        'p90': quantile(values, 0.90),
        'p95': quantile(values, 0.95),
        'p99': quantile(values, 0.99),
        'p99.9': quantile(values, 0.999) if len(values) >= 1000 else quantile(values, 0.99),
    }


def detect_bimodal(values: List[float]) -> bool:
    """
    Simple bimodal detection using gap analysis.
    Looks for significant gap in sorted values.
    """
    if len(values) < 10:
        return False
    
    sorted_vals = sorted(values)
    gaps = [sorted_vals[i+1] - sorted_vals[i] for i in range(len(sorted_vals) - 1)]
    
    mean_gap = statistics.mean(gaps)
    max_gap = max(gaps)
    
    # If largest gap is >3x mean, likely bimodal
    return max_gap > 3 * mean_gap


def coefficient_of_variation_robust(values: List[float]) -> float:
    """
    Robust coefficient of variation using MAD.
    
    Traditional CV uses (std/mean), which is unreliable for heavy tails.
    This uses (MAD/median) * 1.4826 for consistency with normal distribution.
    """
    if len(values) < 2:
        return 0.0
    
    from robust_stats import median, mad
    
    med = median(values)
    if med == 0:
        return 0.0
    
    mad_val = mad(values)
    # Scale MAD to match std for normal distribution
    return (mad_val * 1.4826 / med) * 100


def analyze_distribution(group: RunGroup) -> None:
    """
    Analyze distribution using academically rigorous non-parametric methods.
    
    Reports:
    - Median and IQR (not mean and std)
    - Full quantile summary (p1-p99.9)
    - Tail heaviness ratio
    - ECDF visualization (not histogram)
    - Flagged extreme values (retained, not removed)
    """
    runtimes = [r.runtime_ms for r in group.runs]
    
    print(f"\n{'='*70}")
    print(f"{group.name}")
    print(f"{'='*70}")
    
    # Robust summary statistics
    stats = describe_robust(runtimes)
    
    print(f"\nRobust Statistics (non-parametric):")
    print(f"  Count:  {stats['n']}")
    print(f"  Median: {stats['median']:.2f} ms  [robust central tendency]")
    print(f"  IQR:    {stats['iqr']:.2f} ms  [robust spread, Q3-Q1]")
    print(f"  MAD:    {stats['mad']:.2f} ms  [median absolute deviation]")
    print(f"  Range:  [{stats['min']:.2f}, {stats['max']:.2f}] ms")
    
    # Optional: show mean/std for comparison (but note unreliability)
    mean_val = statistics.mean(runtimes)
    std_val = statistics.stdev(runtimes) if len(runtimes) > 1 else 0.0
    print(f"\n  Reference (parametric, unreliable for heavy tails):")
    print(f"    Mean:  {mean_val:.2f} ms")
    print(f"    Stdev: {std_val:.2f} ms")
    
    # Quantiles (key for systems research)
    print(f"\nQuantiles (percentiles):")
    percs = percentiles(runtimes)
    for key in ['p1', 'p5', 'p25', 'p50', 'p75', 'p90', 'p95', 'p99']:
        if key in percs:
            label = "(median)" if key == 'p50' else ""
            print(f"  {key}: {percs[key]:.2f} ms {label}")
    
    if 'p99.9' in percs:
        print(f"  p99.9: {percs['p99.9']:.2f} ms")
    
    # Tail latency analysis
    tail_ratio = stats['tail_ratio']
    print(f"\nTail Latency Analysis:")
    print(f"  p99/p50 ratio: {tail_ratio:.2f}x")
    
    if tail_ratio < 1.5:
        print(f"  ✓ Light tails (good performance consistency)")
    elif tail_ratio < 3.0:
        print(f"  ⚠ Moderate tails (typical for systems workloads)")
    else:
        print(f"  ⚠⚠ Heavy tails (significant tail latency issue)")
        print(f"     p99 is {tail_ratio:.1f}x worse than median")
    
    # Bimodal detection (state-based analysis)
    if detect_bimodal(runtimes):
        print(f"\n⚠ Bimodal distribution detected!")
        print(f"  Likely cause: multiple performance regimes")
        print(f"  (e.g., cache hits vs misses, CPU frequency scaling)")
    
    # ECDF visualization (academically preferred over histogram)
    print(f"\nEmpirical CDF (no binning artifacts):")
    ecdf_ascii(runtimes, points=15)
    
    # Flag extreme values (but retain them)
    lower_fence, upper_fence, flagged = tukey_fences(runtimes, k=1.5)
    
    if flagged:
        print(f"\nExtreme values flagged (Tukey fences, k=1.5):")
        print(f"  Fences: [{lower_fence:.2f}, {upper_fence:.2f}] ms")
        print(f"  Flagged: {len(flagged)}/{len(runtimes)} values")
        print(f"  NOTE: These are RETAINED as meaningful tail behavior")
        
        for idx in flagged[:5]:  # Show first 5
            print(f"    Run {idx}: {runtimes[idx]:.2f} ms")
        
        if len(flagged) > 5:
            print(f"    ... and {len(flagged) - 5} more")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <data.csv>", file=sys.stderr)
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    groups = parse_csv(filepath)
    
    print(f"=== Distribution Analysis: {filepath.name} ===")
    
    for name, group in sorted(groups.items()):
        analyze_distribution(group)
    
    print()


if __name__ == '__main__':
    main()
