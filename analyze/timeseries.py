#!/usr/bin/env python3
"""
timeseries.py - Time-series analysis for experiment runs

Purpose:
  Detect temporal patterns in experiment runs:
  - Warmup effects (first runs slower)
  - Thermal throttling (later runs slower)
  - Periodic interference
  - Drift over time
"""

import sys
from pathlib import Path
from typing import List, Tuple
import statistics
sys.path.insert(0, str(Path(__file__).parent))
from parse import parse_csv, RunGroup, Metrics


def detect_warmup(runs: List[Metrics], warmup_threshold: int = 3) -> Tuple[bool, float]:
    """
    Detect if first N runs are slower (warmup effect).
    
    Returns:
        (has_warmup, warmup_overhead_pct)
    """
    if len(runs) <= warmup_threshold:
        return (False, 0.0)
    
    warmup_runtimes = [r.runtime_ms for r in runs[:warmup_threshold]]
    steady_runtimes = [r.runtime_ms for r in runs[warmup_threshold:]]
    
    warmup_mean = statistics.mean(warmup_runtimes)
    steady_mean = statistics.mean(steady_runtimes)
    
    # Consider warmup if first runs are >5% slower
    overhead_pct = ((warmup_mean - steady_mean) / steady_mean) * 100
    has_warmup = overhead_pct > 5.0
    
    return (has_warmup, overhead_pct)


def detect_throttling(runs: List[Metrics], window_size: int = 3) -> Tuple[bool, float]:
    """
    Detect if later runs are slower (thermal throttling).
    
    Returns:
        (has_throttling, degradation_pct)
    """
    if len(runs) <= window_size * 2:
        return (False, 0.0)
    
    early_runtimes = [r.runtime_ms for r in runs[:window_size]]
    late_runtimes = [r.runtime_ms for r in runs[-window_size:]]
    
    early_mean = statistics.mean(early_runtimes)
    late_mean = statistics.mean(late_runtimes)
    
    # Consider throttling if last runs are >5% slower
    degradation_pct = ((late_mean - early_mean) / early_mean) * 100
    has_throttling = degradation_pct > 5.0
    
    return (has_throttling, degradation_pct)


def detect_change_point(runs: List[Metrics], min_segment_size: int = 5) -> Tuple[bool, int]:
    """
    Simple change-point detection using median difference.
    
    Looks for a point where the distribution changes significantly.
    More appropriate than trend fitting for regime-based behavior.
    
    Returns:
        (has_change_point, change_index)
    """
    if len(runs) < min_segment_size * 2:
        return (False, -1)
    
    runtimes = [r.runtime_ms for r in runs]
    n = len(runtimes)
    
    # Try each potential split point
    best_split = -1
    max_difference = 0.0
    
    for split in range(min_segment_size, n - min_segment_size):
        segment1 = runtimes[:split]
        segment2 = runtimes[split:]
        
        median1 = statistics.median(segment1)
        median2 = statistics.median(segment2)
        
        # Normalized difference
        avg_median = (median1 + median2) / 2
        if avg_median > 0:
            diff = abs(median1 - median2) / avg_median
            
            if diff > max_difference:
                max_difference = diff
                best_split = split
    
    # Significant change if difference > 10%
    has_change = max_difference > 0.10
    
    return (has_change, best_split if has_change else -1)


def detect_trend(runs: List[Metrics]) -> str:
    """
    Detect overall trend: increasing, decreasing, or stable.
    Uses simple linear regression slope.
    """
    if len(runs) < 4:
        return "insufficient_data"
    
    runtimes = [r.runtime_ms for r in runs]
    n = len(runtimes)
    
    # Simple linear regression
    x_mean = (n - 1) / 2.0
    y_mean = statistics.mean(runtimes)
    
    numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(runtimes))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return "stable"
    
    slope = numerator / denominator
    
    # Slope as percentage of mean per run
    slope_pct_per_run = (slope / y_mean) * 100
    
    if abs(slope_pct_per_run) < 0.5:
        return "stable"
    elif slope_pct_per_run > 0:
        return f"increasing ({slope_pct_per_run:+.2f}%/run)"
    else:
        return f"decreasing ({slope_pct_per_run:+.2f}%/run)"


def analyze_periodicity(runs: List[Metrics]) -> bool:
    """
    Simple periodic interference detection.
    Looks for alternating fast/slow pattern.
    """
    if len(runs) < 6:
        return False
    
    runtimes = [r.runtime_ms for r in runs]
    
    # Check if even-indexed runs differ significantly from odd-indexed
    even_runtimes = [runtimes[i] for i in range(0, len(runtimes), 2)]
    odd_runtimes = [runtimes[i] for i in range(1, len(runtimes), 2)]
    
    if len(even_runtimes) < 2 or len(odd_runtimes) < 2:
        return False
    
    even_mean = statistics.mean(even_runtimes)
    odd_mean = statistics.mean(odd_runtimes)
    
    diff_pct = abs((even_mean - odd_mean) / statistics.mean(runtimes)) * 100
    
    return diff_pct > 10.0


def draw_sparkline(values: List[float], width: int = 40) -> str:
    """Draw simple ASCII sparkline."""
    if not values or len(values) < 2:
        return ""
    
    min_val = min(values)
    max_val = max(values)
    
    if max_val == min_val:
        return "─" * width
    
    # 8 levels using unicode block characters
    blocks = " ▁▂▃▄▅▆▇█"
    
    sparkline = ""
    for val in values:
        normalized = (val - min_val) / (max_val - min_val)
        block_idx = int(normalized * (len(blocks) - 1))
        sparkline += blocks[block_idx]
    
    return sparkline


def analyze_group(group: RunGroup) -> None:
    """Analyze temporal patterns in a run group."""
    print(f"\n{group.name}:")
    print(f"  Runs: {len(group.runs)}")
    
    # Runtime sparkline
    runtimes = [r.runtime_ms for r in group.runs]
    sparkline = draw_sparkline(runtimes)
    print(f"  Runtime pattern: {sparkline}")
    print(f"  Range: [{min(runtimes):.2f}, {max(runtimes):.2f}] ms")
    
    # Change-point detection (regime-based, not trend-based)
    has_change, change_idx = detect_change_point(group.runs)
    if has_change:
        before_median = statistics.median([r.runtime_ms for r in group.runs[:change_idx]])
        after_median = statistics.median([r.runtime_ms for r in group.runs[change_idx:]])
        change_pct = ((after_median - before_median) / before_median) * 100
        print(f"  [WARNING] Regime change detected at run {change_idx}")
        print(f"     Before: {before_median:.2f} ms (median)")
        print(f"     After:  {after_median:.2f} ms (median, {change_pct:+.1f}%)")
    
    # Warmup detection
    has_warmup, warmup_pct = detect_warmup(group.runs)
    if has_warmup:
        print(f"  [WARNING] Warmup effect detected: first runs {warmup_pct:+.1f}% slower")
    
    # Throttling detection
    has_throttling, throttle_pct = detect_throttling(group.runs)
    if has_throttling:
        print(f"  [WARNING] Throttling detected: last runs {throttle_pct:+.1f}% slower")
    
    # Trend analysis (fallback if no change-point)
    if not has_change:
        trend = detect_trend(group.runs)
        if trend != "stable":
            print(f"  -> Trend: {trend}")
    
    # Periodicity
    if analyze_periodicity(group.runs):
        print(f"  [WARNING] Periodic pattern detected (alternating fast/slow)")
    
    # Context switch pattern
    ctxt_switches = [r.nonvoluntary_ctxt_switches for r in group.runs]
    if max(ctxt_switches) > 0:
        ctxt_sparkline = draw_sparkline([float(c) for c in ctxt_switches])
        print(f"  Context switches: {ctxt_sparkline}")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <data.csv>", file=sys.stderr)
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    groups = parse_csv(filepath)
    
    print(f"=== Time-Series Analysis: {filepath.name} ===")
    
    for name, group in sorted(groups.items()):
        analyze_group(group)
    
    print()


if __name__ == '__main__':
    main()
