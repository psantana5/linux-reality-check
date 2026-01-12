#!/usr/bin/env python3
"""
correlate.py - Correlation analysis between metrics

Purpose:
  Discover relationships between metrics automatically.
  Identify strongest correlations.
  Guide bottleneck analysis.
"""

import sys
from pathlib import Path
from typing import List, Tuple, Dict
import statistics
sys.path.insert(0, str(Path(__file__).parent))
from parse import parse_csv, RunGroup, Metrics


def pearson_correlation(x: List[float], y: List[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    
    n = len(x)
    mean_x = statistics.mean(x)
    mean_y = statistics.mean(y)
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    
    sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(n))
    
    if sum_sq_x == 0 or sum_sq_y == 0:
        return 0.0
    
    denominator = (sum_sq_x * sum_sq_y) ** 0.5
    
    return numerator / denominator


def extract_metrics(group: RunGroup) -> Dict[str, List[float]]:
    """Extract all metrics as lists."""
    return {
        'runtime_ms': [m.runtime_ms for m in group.runs],
        'voluntary_ctxt': [float(m.voluntary_ctxt_switches) for m in group.runs],
        'involuntary_ctxt': [float(m.nonvoluntary_ctxt_switches) for m in group.runs],
        'minor_pf': [float(m.minor_page_faults) for m in group.runs],
        'major_pf': [float(m.major_page_faults) for m in group.runs],
        'migrations': [1.0 if m.migrated else 0.0 for m in group.runs],
    }


def correlation_matrix(group: RunGroup) -> List[Tuple[str, str, float]]:
    """Calculate correlation matrix for all metric pairs."""
    metrics = extract_metrics(group)
    correlations = []
    
    metric_names = list(metrics.keys())
    
    for i, name1 in enumerate(metric_names):
        for name2 in metric_names[i+1:]:
            corr = pearson_correlation(metrics[name1], metrics[name2])
            correlations.append((name1, name2, corr))
    
    # Sort by absolute correlation strength
    correlations.sort(key=lambda x: abs(x[2]), reverse=True)
    
    return correlations


def interpret_correlation(corr: float) -> str:
    """Interpret correlation strength."""
    abs_corr = abs(corr)
    
    if abs_corr >= 0.8:
        strength = "very strong"
    elif abs_corr >= 0.6:
        strength = "strong"
    elif abs_corr >= 0.4:
        strength = "moderate"
    elif abs_corr >= 0.2:
        strength = "weak"
    else:
        strength = "negligible"
    
    direction = "positive" if corr > 0 else "negative"
    
    return f"{strength} {direction}"


def analyze_correlations(group: RunGroup) -> None:
    """Analyze and print correlations."""
    print(f"\n{'='*70}")
    print(f"{group.name}")
    print(f"{'='*70}")
    
    correlations = correlation_matrix(group)
    
    print(f"\nCorrelation Matrix (sorted by strength):\n")
    print(f"{'Metric 1':<20} {'Metric 2':<20} {'r':>8} {'Interpretation'}")
    print("-" * 70)
    
    for name1, name2, corr in correlations:
        if abs(corr) < 0.1:  # Skip negligible correlations
            continue
        
        interp = interpret_correlation(corr)
        print(f"{name1:<20} {name2:<20} {corr:>8.3f} {interp}")
    
    # Highlight strongest correlations
    print(f"\nKey Findings:")
    
    significant = [(n1, n2, c) for n1, n2, c in correlations if abs(c) >= 0.6]
    
    if not significant:
        print("  • No strong correlations detected")
        print("  • Metrics appear independent")
    else:
        for name1, name2, corr in significant:
            if corr > 0:
                print(f"  • {name1} and {name2} are strongly correlated (r={corr:.3f})")
                print(f"    → When {name1} increases, {name2} tends to increase")
            else:
                print(f"  • {name1} and {name2} are negatively correlated (r={corr:.3f})")
                print(f"    → When {name1} increases, {name2} tends to decrease")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <data.csv>", file=sys.stderr)
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    groups = parse_csv(filepath)
    
    print(f"=== Correlation Analysis: {filepath.name} ===")
    
    for name, group in sorted(groups.items()):
        if len(group.runs) < 3:
            print(f"\n{name}: Insufficient data for correlation (need 3+ runs)")
            continue
        
        analyze_correlations(group)
    
    print()


if __name__ == '__main__':
    main()
