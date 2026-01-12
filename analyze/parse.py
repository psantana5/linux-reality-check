#!/usr/bin/env python3
"""
parse.py - Raw data parser

Purpose:
  Read CSV files produced by C experiments.
  Perform basic statistical aggregation.
  No interpretation, just normalization.
"""

import sys
import csv
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
import statistics


@dataclass
class Metrics:
    """Raw metrics from a single workload run."""
    timestamp_ns: int
    runtime_ns: int
    voluntary_ctxt_switches: int
    nonvoluntary_ctxt_switches: int
    minor_page_faults: int
    major_page_faults: int
    start_cpu: int
    end_cpu: int
    
    @property
    def migrated(self) -> bool:
        """Did the task migrate between CPUs?"""
        return self.start_cpu != self.end_cpu
    
    @property
    def runtime_ms(self) -> float:
        """Runtime in milliseconds."""
        return self.runtime_ns / 1_000_000.0


@dataclass
class RunGroup:
    """Grouped metrics for statistical analysis."""
    name: str
    runs: List[Metrics]
    
    @property
    def mean_runtime_ms(self) -> float:
        return statistics.mean(m.runtime_ms for m in self.runs)
    
    @property
    def stdev_runtime_ms(self) -> float:
        if len(self.runs) < 2:
            return 0.0
        return statistics.stdev(m.runtime_ms for m in self.runs)
    
    @property
    def median_runtime_ms(self) -> float:
        return statistics.median(m.runtime_ms for m in self.runs)
    
    @property
    def total_migrations(self) -> int:
        return sum(1 for m in self.runs if m.migrated)
    
    @property
    def total_voluntary_ctxt(self) -> int:
        return sum(m.voluntary_ctxt_switches for m in self.runs)
    
    @property
    def total_nonvoluntary_ctxt(self) -> int:
        return sum(m.nonvoluntary_ctxt_switches for m in self.runs)


def parse_csv(filepath: Path) -> Dict[str, RunGroup]:
    """
    Parse experiment CSV file into grouped metrics.
    
    Returns:
        Dictionary mapping group name to RunGroup
    """
    groups: Dict[str, List[Metrics]] = {}
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Determine group key (depends on experiment type)
            if 'affinity' in row:
                group_key = row['affinity']
            elif 'nice_level' in row:
                group_key = row['nice_level']
            elif 'buffer_size' in row:
                group_key = row['buffer_size']
            else:
                group_key = 'default'
            
            metrics = Metrics(
                timestamp_ns=int(row['timestamp_ns']),
                runtime_ns=int(row['runtime_ns']),
                voluntary_ctxt_switches=int(row['voluntary_ctxt_switches']),
                nonvoluntary_ctxt_switches=int(row['nonvoluntary_ctxt_switches']),
                minor_page_faults=int(row['minor_page_faults']),
                major_page_faults=int(row['major_page_faults']),
                start_cpu=int(row['start_cpu']),
                end_cpu=int(row['end_cpu'])
            )
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(metrics)
    
    return {name: RunGroup(name, runs) for name, runs in groups.items()}


def print_summary(groups: Dict[str, RunGroup]) -> None:
    """Print statistical summary of parsed data."""
    print(f"{'Group':<15} {'Runs':>5} {'Mean (ms)':>12} {'StdDev':>10} {'Median':>10} {'Migr':>6} {'Vol':>8} {'Invol':>8}")
    print("-" * 90)
    
    for name, group in sorted(groups.items()):
        print(f"{name:<15} {len(group.runs):>5} "
              f"{group.mean_runtime_ms:>12.2f} "
              f"{group.stdev_runtime_ms:>10.2f} "
              f"{group.median_runtime_ms:>10.2f} "
              f"{group.total_migrations:>6} "
              f"{group.total_voluntary_ctxt:>8} "
              f"{group.total_nonvoluntary_ctxt:>8}")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <data.csv>", file=sys.stderr)
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: {filepath} does not exist", file=sys.stderr)
        sys.exit(1)
    
    groups = parse_csv(filepath)
    print_summary(groups)


if __name__ == '__main__':
    main()
