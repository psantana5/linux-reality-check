#!/usr/bin/env python3
"""
distributions.py - Distribution analysis and visualization

Purpose:
  Analyze runtime distributions to understand variance sources.
  Identify bimodal patterns, tail latency, outliers.
"""

import sys
from pathlib import Path
from typing import List, Dict
import statistics
sys.path.insert(0, str(Path(__file__).parent))
from parse import parse_csv, RunGroup


def histogram_ascii(values: List[float], bins: int = 10, width: int = 40) -> None:
    """Draw ASCII histogram."""
    if len(values) < 2:
        print("  Insufficient data for histogram")
        return
    
    min_val = min(values)
    max_val = max(values)
    
    if max_val == min_val:
        print(f"  All values identical: {min_val:.2f}")
        return
    
    # Calculate bin edges
    bin_width = (max_val - min_val) / bins
    bins_data = [0] * bins
    
    # Count values in each bin
    for val in values:
        bin_idx = int((val - min_val) / bin_width)
        if bin_idx >= bins:
            bin_idx = bins - 1
        bins_data[bin_idx] += 1
    
    # Find max count for scaling
    max_count = max(bins_data)
    
    # Print histogram
    for i, count in enumerate(bins_data):
        bin_start = min_val + i * bin_width
        bin_end = bin_start + bin_width
        bar_len = int((count / max_count) * width) if max_count > 0 else 0
        bar = "█" * bar_len
        pct = (count / len(values)) * 100
        print(f"  {bin_start:7.1f}-{bin_end:7.1f}: {bar} ({pct:4.1f}%)")


def percentiles(values: List[float]) -> Dict[str, float]:
    """Calculate percentile values."""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    
    return {
        'p1': sorted_vals[int(n * 0.01)],
        'p5': sorted_vals[int(n * 0.05)],
        'p10': sorted_vals[int(n * 0.10)],
        'p25': sorted_vals[int(n * 0.25)],
        'p50': sorted_vals[int(n * 0.50)],
        'p75': sorted_vals[int(n * 0.75)],
        'p90': sorted_vals[int(n * 0.90)],
        'p95': sorted_vals[int(n * 0.95)],
        'p99': sorted_vals[int(n * 0.99)] if n > 100 else sorted_vals[-1],
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


def coefficient_of_variation(values: List[float]) -> float:
    """CV = (stdev / mean) * 100"""
    if len(values) < 2:
        return 0.0
    mean = statistics.mean(values)
    if mean == 0:
        return 0.0
    return (statistics.stdev(values) / mean) * 100


def analyze_distribution(group: RunGroup) -> None:
    """Analyze and visualize distribution for a run group."""
    runtimes = [r.runtime_ms for r in group.runs]
    
    print(f"\n{'='*70}")
    print(f"{group.name}")
    print(f"{'='*70}")
    
    # Basic statistics
    print(f"\nBasic Statistics:")
    print(f"  Count:  {len(runtimes)}")
    print(f"  Mean:   {statistics.mean(runtimes):.2f} ms")
    print(f"  Median: {statistics.median(runtimes):.2f} ms")
    print(f"  Stdev:  {statistics.stdev(runtimes):.2f} ms" if len(runtimes) > 1 else "  Stdev:  N/A")
    print(f"  Min:    {min(runtimes):.2f} ms")
    print(f"  Max:    {max(runtimes):.2f} ms")
    print(f"  Range:  {max(runtimes) - min(runtimes):.2f} ms")
    print(f"  CV:     {coefficient_of_variation(runtimes):.2f}%")
    
    # Percentiles
    percs = percentiles(runtimes)
    print(f"\nPercentiles:")
    print(f"  p1:  {percs['p1']:.2f} ms")
    print(f"  p5:  {percs['p5']:.2f} ms")
    print(f"  p25: {percs['p25']:.2f} ms")
    print(f"  p50: {percs['p50']:.2f} ms (median)")
    print(f"  p75: {percs['p75']:.2f} ms")
    print(f"  p90: {percs['p90']:.2f} ms")
    print(f"  p95: {percs['p95']:.2f} ms")
    print(f"  p99: {percs['p99']:.2f} ms")
    
    # Tail latency
    tail_factor = percs['p99'] / percs['p50']
    print(f"\nTail Latency:")
    print(f"  p99/p50 ratio: {tail_factor:.2f}x")
    if tail_factor > 1.5:
        print(f"  ⚠ Significant tail latency (p99 is {tail_factor:.1f}x median)")
    
    # Bimodal detection
    if detect_bimodal(runtimes):
        print(f"\n⚠ Bimodal distribution detected!")
        print(f"  Likely cause: cache hits vs misses, or intermittent interference")
    
    # Histogram
    print(f"\nDistribution (histogram):")
    histogram_ascii(runtimes, bins=min(10, len(runtimes) // 3 + 1))


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
