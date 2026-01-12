#!/usr/bin/env python3
"""
classify.py - Performance bottleneck classifier

Purpose:
  Apply rule-based classification to identify
  dominant bottleneck from raw metrics.
  
  NOT machine learning. NOT guessing.
  Pure signal-based categorization.
"""

import sys
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass
from parse import parse_csv, RunGroup


@dataclass
class Observation:
    """Single observation about workload behavior."""
    category: str
    severity: str  # 'low', 'medium', 'high'
    evidence: str
    
    def __str__(self) -> str:
        marker = {'low': '·', 'medium': '→', 'high': '⚠'}[self.severity]
        return f"  {marker} [{self.category}] {self.evidence}"


def classify_group(group: RunGroup) -> List[Observation]:
    """
    Classify a group of runs based on metrics.
    
    Rules are explicit and documented.
    Thresholds are based on expected baseline behavior.
    """
    observations = []
    
    # Rule 1: CPU migrations indicate scheduler interference
    migration_rate = group.total_migrations / len(group.runs)
    if migration_rate > 0.5:
        observations.append(Observation(
            category='Scheduler',
            severity='high',
            evidence=f'{migration_rate:.1%} of runs migrated CPUs'
        ))
    elif migration_rate > 0.1:
        observations.append(Observation(
            category='Scheduler',
            severity='medium',
            evidence=f'{migration_rate:.1%} of runs migrated CPUs'
        ))
    
    # Rule 2: Involuntary context switches suggest preemption
    avg_invol = group.total_nonvoluntary_ctxt / len(group.runs)
    if avg_invol > 100:
        observations.append(Observation(
            category='Scheduler',
            severity='high',
            evidence=f'{avg_invol:.0f} involuntary context switches per run'
        ))
    elif avg_invol > 10:
        observations.append(Observation(
            category='Scheduler',
            severity='medium',
            evidence=f'{avg_invol:.0f} involuntary context switches per run'
        ))
    
    # Rule 3: High variance indicates system interference
    cv = (group.stdev_runtime_ms / group.mean_runtime_ms) * 100  # coefficient of variation
    if cv > 10:
        observations.append(Observation(
            category='Variance',
            severity='high',
            evidence=f'{cv:.1f}% coefficient of variation'
        ))
    elif cv > 5:
        observations.append(Observation(
            category='Variance',
            severity='medium',
            evidence=f'{cv:.1f}% coefficient of variation'
        ))
    
    # Rule 4: Major page faults indicate memory pressure
    avg_major_pf = sum(m.major_page_faults for m in group.runs) / len(group.runs)
    if avg_major_pf > 10:
        observations.append(Observation(
            category='Memory',
            severity='high',
            evidence=f'{avg_major_pf:.0f} major page faults per run'
        ))
    elif avg_major_pf > 1:
        observations.append(Observation(
            category='Memory',
            severity='medium',
            evidence=f'{avg_major_pf:.1f} major page faults per run'
        ))
    
    # Rule 5: Clean behavior (baseline)
    if not observations:
        observations.append(Observation(
            category='Baseline',
            severity='low',
            evidence='No significant interference detected'
        ))
    
    return observations


def compare_groups(groups: List[Tuple[str, RunGroup]]) -> None:
    """
    Compare multiple groups to identify relative differences.
    """
    print("\n=== Comparative Analysis ===\n")
    
    # Sort by mean runtime
    sorted_groups = sorted(groups, key=lambda x: x[1].mean_runtime_ms)
    
    baseline_runtime = sorted_groups[0][1].mean_runtime_ms
    
    for name, group in sorted_groups:
        overhead = ((group.mean_runtime_ms - baseline_runtime) / baseline_runtime) * 100
        print(f"{name}:")
        print(f"  Runtime: {group.mean_runtime_ms:.2f} ms (baseline +{overhead:.1f}%)")
        print(f"  Observations:")
        
        for obs in classify_group(group):
            print(f"    {obs}")
        print()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <data.csv>", file=sys.stderr)
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    groups = parse_csv(filepath)
    
    print(f"=== Classification: {filepath.name} ===\n")
    
    compare_groups(list(groups.items()))


if __name__ == '__main__':
    main()
