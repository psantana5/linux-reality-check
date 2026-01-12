#!/usr/bin/env python3
"""
outliers.py - Statistical outlier detection

Purpose:
  Identify anomalous runs that may indicate interference.
  Uses IQR (Interquartile Range) method - robust to distribution.
"""

import sys
from pathlib import Path
from typing import List, Tuple
import statistics
sys.path.insert(0, str(Path(__file__).parent))
from parse import parse_csv, RunGroup, Metrics


def detect_outliers_iqr(values: List[float], k: float = 1.5) -> Tuple[List[int], float, float]:
    """
    Detect outliers using IQR method.
    
    Returns:
        (outlier_indices, lower_bound, upper_bound)
    """
    if len(values) < 4:
        return ([], 0, 0)
    
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    
    q1 = sorted_vals[n // 4]
    q3 = sorted_vals[3 * n // 4]
    iqr = q3 - q1
    
    lower_bound = q1 - k * iqr
    upper_bound = q3 + k * iqr
    
    outliers = [i for i, v in enumerate(values) if v < lower_bound or v > upper_bound]
    
    return (outliers, lower_bound, upper_bound)


def analyze_outliers(group: RunGroup) -> None:
    """Analyze outliers in a run group."""
    runtimes = [m.runtime_ms for m in group.runs]
    outlier_indices, lower, upper = detect_outliers_iqr(runtimes)
    
    print(f"\n{group.name}:")
    print(f"  Samples: {len(group.runs)}")
    print(f"  Range: [{min(runtimes):.2f}, {max(runtimes):.2f}] ms")
    print(f"  Expected range (IQR): [{lower:.2f}, {upper:.2f}] ms")
    
    if outlier_indices:
        print(f"  ⚠ Outliers detected: {len(outlier_indices)}/{len(group.runs)}")
        for idx in outlier_indices:
            m = group.runs[idx]
            deviation = ((m.runtime_ms - group.median_runtime_ms) / group.median_runtime_ms) * 100
            print(f"    Run {idx}: {m.runtime_ms:.2f} ms ({deviation:+.1f}% from median)")
            
            if m.migrated:
                print(f"      → CPU migration: {m.start_cpu} → {m.end_cpu}")
            if m.nonvoluntary_ctxt_switches > 0:
                print(f"      → {m.nonvoluntary_ctxt_switches} involuntary context switches")
            if m.major_page_faults > 0:
                print(f"      → {m.major_page_faults} major page faults")
    else:
        print(f"  ✓ No outliers (all within expected range)")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <data.csv>", file=sys.stderr)
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    groups = parse_csv(filepath)
    
    print(f"=== Outlier Analysis: {filepath.name} ===")
    
    for name, group in sorted(groups.items()):
        analyze_outliers(group)


if __name__ == '__main__':
    main()
