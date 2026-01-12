#!/usr/bin/env python3
"""
visualize.py - ASCII visualization for experiment results

Purpose:
  Generate simple ASCII charts from metrics.
  No dependencies beyond standard library.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'analyze'))
from parse import parse_csv, RunGroup


def draw_bar_chart(data: dict[str, float], title: str, width: int = 60) -> None:
    """Draw horizontal bar chart."""
    print(f"\n{title}")
    print("=" * width)
    
    max_val = max(data.values())
    
    for name, value in sorted(data.items(), key=lambda x: x[1]):
        bar_len = int((value / max_val) * (width - 30))
        bar = "█" * bar_len
        print(f"{name:15s} {bar} {value:8.2f}")


def draw_comparison(groups: dict[str, RunGroup]) -> None:
    """Draw comparative visualizations."""
    
    # Runtime comparison
    runtime_data = {name: g.mean_runtime_ms for name, g in groups.items()}
    draw_bar_chart(runtime_data, "Mean Runtime (ms)")
    
    # Variance comparison
    variance_data = {name: g.stdev_runtime_ms for name, g in groups.items()}
    draw_bar_chart(variance_data, "Runtime Standard Deviation (ms)")
    
    # Context switch comparison
    ctxt_data = {
        name: g.total_nonvoluntary_ctxt / len(g.runs)
        for name, g in groups.items()
    }
    draw_bar_chart(ctxt_data, "Involuntary Context Switches (avg)")
    
    # Migration comparison
    migration_data = {
        name: (g.total_migrations / len(g.runs)) * 100
        for name, g in groups.items()
    }
    draw_bar_chart(migration_data, "CPU Migration Rate (%)")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <data.csv>", file=sys.stderr)
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    groups = parse_csv(filepath)
    
    print(f"=== Visualization: {filepath.name} ===")
    draw_comparison(groups)
    print()


if __name__ == '__main__':
    main()
