#!/usr/bin/env python3
"""
compare.py - Multi-experiment comparison tool

Purpose:
  Load multiple experiment results and generate
  side-by-side comparison tables.
  
  Useful for:
  - Before/after changes
  - Different system configurations
  - Regression detection
"""

import sys
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
sys.path.insert(0, str(Path(__file__).parent))
from parse import parse_csv, RunGroup


@dataclass
class Comparison:
    """Comparison between two run groups."""
    name: str
    baseline: RunGroup
    current: RunGroup
    
    @property
    def runtime_change_pct(self) -> float:
        """Percentage change in mean runtime."""
        return ((self.current.mean_runtime_ms - self.baseline.mean_runtime_ms) 
                / self.baseline.mean_runtime_ms) * 100
    
    @property
    def variance_change_pct(self) -> float:
        """Percentage change in standard deviation."""
        if self.baseline.stdev_runtime_ms == 0:
            return 0.0
        return ((self.current.stdev_runtime_ms - self.baseline.stdev_runtime_ms) 
                / self.baseline.stdev_runtime_ms) * 100
    
    @property
    def is_regression(self) -> bool:
        """Heuristic: >5% slowdown or >50% variance increase."""
        return (self.runtime_change_pct > 5.0 or 
                self.variance_change_pct > 50.0)


def load_experiments(files: List[Path]) -> Dict[str, Dict[str, RunGroup]]:
    """Load multiple experiment files."""
    experiments = {}
    
    for filepath in files:
        if not filepath.exists():
            print(f"Warning: {filepath} not found, skipping", file=sys.stderr)
            continue
        
        experiments[filepath.name] = parse_csv(filepath)
    
    return experiments


def compare_experiments(baseline_file: Path, current_file: Path) -> List[Comparison]:
    """Compare two experiments."""
    baseline_groups = parse_csv(baseline_file)
    current_groups = parse_csv(current_file)
    
    comparisons = []
    
    # Find common groups
    common_keys = set(baseline_groups.keys()) & set(current_groups.keys())
    
    for key in sorted(common_keys):
        comparisons.append(Comparison(
            name=key,
            baseline=baseline_groups[key],
            current=current_groups[key]
        ))
    
    return comparisons


def print_comparison_table(comparisons: List[Comparison], 
                          baseline_name: str, 
                          current_name: str) -> None:
    """Print side-by-side comparison table."""
    print(f"\n{'='*80}")
    print(f"Comparing: {baseline_name} (baseline) vs {current_name} (current)")
    print(f"{'='*80}\n")
    
    print(f"{'Group':<15} {'Baseline':>12} {'Current':>12} {'Change':>10} {'Verdict':>10}")
    print("-" * 80)
    
    for comp in comparisons:
        verdict = "⚠ REGRESS" if comp.is_regression else "✓ OK"
        print(f"{comp.name:<15} "
              f"{comp.baseline.mean_runtime_ms:>10.2f}ms "
              f"{comp.current.mean_runtime_ms:>10.2f}ms "
              f"{comp.runtime_change_pct:>9.1f}% "
              f"{verdict:>10}")


def print_detailed_comparison(comparisons: List[Comparison]) -> None:
    """Print detailed metrics comparison."""
    print(f"\n{'='*80}")
    print("Detailed Metrics")
    print(f"{'='*80}\n")
    
    for comp in comparisons:
        print(f"{comp.name}:")
        print(f"  Runtime:")
        print(f"    Baseline: {comp.baseline.mean_runtime_ms:.2f} ± "
              f"{comp.baseline.stdev_runtime_ms:.2f} ms")
        print(f"    Current:  {comp.current.mean_runtime_ms:.2f} ± "
              f"{comp.current.stdev_runtime_ms:.2f} ms")
        print(f"    Change:   {comp.runtime_change_pct:+.1f}%")
        
        print(f"  Context Switches (involuntary):")
        baseline_invol = comp.baseline.total_nonvoluntary_ctxt / len(comp.baseline.runs)
        current_invol = comp.current.total_nonvoluntary_ctxt / len(comp.current.runs)
        print(f"    Baseline: {baseline_invol:.1f} per run")
        print(f"    Current:  {current_invol:.1f} per run")
        
        print(f"  Migrations:")
        baseline_migr_rate = (comp.baseline.total_migrations / len(comp.baseline.runs)) * 100
        current_migr_rate = (comp.current.total_migrations / len(comp.current.runs)) * 100
        print(f"    Baseline: {baseline_migr_rate:.1f}%")
        print(f"    Current:  {current_migr_rate:.1f}%")
        
        print()


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <baseline.csv> <current.csv> [additional.csv ...]", 
              file=sys.stderr)
        print("\nExamples:", file=sys.stderr)
        print("  # Compare before/after", file=sys.stderr)
        print("  python3 compare.py pinned_before.csv pinned_after.csv", file=sys.stderr)
        print("\n  # Multiple experiments", file=sys.stderr)
        print("  python3 compare.py exp1.csv exp2.csv exp3.csv", file=sys.stderr)
        sys.exit(1)
    
    files = [Path(f) for f in sys.argv[1:]]
    
    if len(files) == 2:
        # Simple comparison mode
        comparisons = compare_experiments(files[0], files[1])
        print_comparison_table(comparisons, files[0].stem, files[1].stem)
        print_detailed_comparison(comparisons)
        
        # Check for regressions
        regressions = [c for c in comparisons if c.is_regression]
        if regressions:
            print(f"\n⚠ WARNING: {len(regressions)} regression(s) detected")
            sys.exit(1)
        else:
            print(f"\n✓ No regressions detected")
            sys.exit(0)
    else:
        # Multi-experiment overview mode
        experiments = load_experiments(files)
        
        print(f"\n{'='*80}")
        print(f"Multi-Experiment Overview ({len(experiments)} experiments)")
        print(f"{'='*80}\n")
        
        for exp_name, groups in experiments.items():
            print(f"\n{exp_name}:")
            for group_name, group in sorted(groups.items()):
                print(f"  {group_name:<20} {group.mean_runtime_ms:>10.2f} ms "
                      f"(±{group.stdev_runtime_ms:.2f})")


if __name__ == '__main__':
    main()
