#!/usr/bin/env python3
"""
plot_robust.py - Academically rigorous visualization for systems data

Generates publication-quality plots using non-parametric methods:
- ECDF (no histograms)
- Quantile plots (no mean-based comparisons)
- Boxplots (Tukey method, no violin plots with KDE)
- No normal distribution overlays
"""

import sys
import csv
from pathlib import Path
from typing import Dict, List
import argparse

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("Error: matplotlib required. Install with: pip3 install matplotlib numpy")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))
from robust_stats import describe_robust, ecdf_values, quantile

# Publication-quality styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#6A994E', '#BC4B51']


def load_csv(csv_path: Path, metric: str, group_by: str = 'name') -> Dict[str, List[float]]:
    """Load CSV and group by column."""
    data = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            group = row.get(group_by, 'default')
            if group not in data:
                data[group] = []
            
            value = float(row[metric])
            if metric.endswith('_ns'):
                value = value / 1_000_000  # ns to ms
            
            data[group].append(value)
    
    return data


def plot_ecdf(data_dict: Dict[str, List[float]], output_path: Path, title: str = "ECDF"):
    """
    Plot Empirical CDF (academically correct).
    
    No binning, no smoothing, shows all data.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for i, (name, values) in enumerate(sorted(data_dict.items())):
        x, y = ecdf_values(values, num_points=1000)
        color = COLORS[i % len(COLORS)]
        ax.plot(x, y, label=name, color=color, linewidth=2)
    
    ax.set_xlabel('Value (ms)', fontsize=12)
    ax.set_ylabel('Cumulative Probability', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Add reference lines for key percentiles
    for p, label in [(0.5, 'p50'), (0.9, 'p90'), (0.99, 'p99')]:
        ax.axhline(p, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
        ax.text(ax.get_xlim()[1] * 0.02, p + 0.01, label, fontsize=9, color='gray')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved ECDF plot: {output_path}")


def plot_quantiles(data_dict: Dict[str, List[float]], output_path: Path, title: str = "Quantiles"):
    """
    Plot quantile comparison (academically correct).
    
    Shows p50, p90, p95, p99 across groups.
    """
    quantiles = [0.50, 0.90, 0.95, 0.99]
    q_labels = ['p50\n(median)', 'p90', 'p95', 'p99']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x_positions = np.arange(len(quantiles))
    width = 0.8 / len(data_dict)
    
    for i, (name, values) in enumerate(sorted(data_dict.items())):
        q_values = [quantile(values, q) for q in quantiles]
        color = COLORS[i % len(COLORS)]
        
        offset = (i - len(data_dict)/2 + 0.5) * width
        ax.bar(x_positions + offset, q_values, width, label=name, color=color, alpha=0.8)
    
    ax.set_xlabel('Percentile', fontsize=12)
    ax.set_ylabel('Value (ms)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(x_positions)
    ax.set_xticklabels(q_labels, fontsize=10)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved quantile plot: {output_path}")


def plot_boxplot(data_dict: Dict[str, List[float]], output_path: Path, title: str = "Boxplot"):
    """
    Plot boxplot (Tukey method, academically correct).
    
    Shows median, IQR, and flagged extremes.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    names = sorted(data_dict.keys())
    data_list = [data_dict[name] for name in names]
    
    bp = ax.boxplot(data_list, labels=names, patch_artist=True,
                    showfliers=True, # Show flagged extremes
                    boxprops=dict(facecolor='lightblue', alpha=0.7),
                    medianprops=dict(color='red', linewidth=2),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5),
                    flierprops=dict(marker='o', markerfacecolor='red', markersize=6, alpha=0.5))
    
    ax.set_ylabel('Value (ms)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Rotate labels if many groups
    if len(names) > 5:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved boxplot: {output_path}")


def plot_tail_ratio(data_dict: Dict[str, List[float]], output_path: Path, title: str = "Tail Heaviness"):
    """
    Plot tail heaviness (p99/p50 ratio).
    
    Shows how heavy-tailed each distribution is.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    names = []
    ratios = []
    
    for name in sorted(data_dict.keys()):
        stats = describe_robust(data_dict[name])
        names.append(name)
        ratios.append(stats['tail_ratio'])
    
    colors = [COLORS[i % len(COLORS)] for i in range(len(names))]
    bars = ax.bar(names, ratios, color=colors, alpha=0.8)
    
    # Add reference lines
    ax.axhline(1.5, color='green', linestyle='--', alpha=0.5, linewidth=1, label='Light tails (<1.5x)')
    ax.axhline(3.0, color='orange', linestyle='--', alpha=0.5, linewidth=1, label='Heavy tails (>3.0x)')
    
    ax.set_ylabel('p99/p50 Ratio', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Rotate labels if many groups
    if len(names) > 5:
        plt.xticks(rotation=45, ha='right')
    
    # Annotate bars
    for bar, ratio in zip(bars, ratios):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{ratio:.2f}x', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved tail ratio plot: {output_path}")


def generate_all_plots(csv_path: Path, metric: str, group_by: str, output_dir: Path):
    """Generate all academically correct plots."""
    output_dir.mkdir(exist_ok=True)
    
    # Load data
    data = load_csv(csv_path, metric, group_by)
    
    if not data:
        print(f"Error: No data found for metric '{metric}'")
        return
    
    print(f"\nGenerating robust plots for {csv_path.name}")
    print(f"  Metric: {metric}")
    print(f"  Groups: {len(data)}")
    print()
    
    base_name = csv_path.stem
    
    # Generate plots
    plot_ecdf(data, output_dir / f"{base_name}_ecdf.png", 
              f"ECDF: {metric}")
    
    plot_quantiles(data, output_dir / f"{base_name}_quantiles.png",
                   f"Quantiles: {metric}")
    
    plot_boxplot(data, output_dir / f"{base_name}_boxplot.png",
                 f"Boxplot: {metric}")
    
    plot_tail_ratio(data, output_dir / f"{base_name}_tail_ratio.png",
                    f"Tail Heaviness: {metric}")
    
    print()
    print("✓ All plots generated successfully!")
    print(f"  Output directory: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate academically rigorous plots for systems data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all plots
  python3 plot_robust.py data/results.csv --metric runtime_ns
  
  # Specify output directory
  python3 plot_robust.py data/cache_hierarchy.csv --metric workload_ns \\
      --output plots/cache/
  
  # Custom grouping column
  python3 plot_robust.py data/exp.csv --metric latency_ns --group-by condition

Academic Note:
  These plots use non-parametric methods appropriate for heavy-tailed
  systems data. No normal distribution overlays. No KDE smoothing.
        """
    )
    
    parser.add_argument('csv_file', type=Path, help='CSV file with results')
    parser.add_argument('--metric', '-m', required=True, help='Metric column to plot')
    parser.add_argument('--group-by', '-g', default='name', help='Column to group by (default: name)')
    parser.add_argument('--output', '-o', type=Path, default=Path('plots'),
                       help='Output directory (default: plots/)')
    
    args = parser.parse_args()
    
    if not args.csv_file.exists():
        print(f"Error: File not found: {args.csv_file}", file=sys.stderr)
        return 1
    
    generate_all_plots(args.csv_file, args.metric, args.group_by, args.output)
    return 0


if __name__ == '__main__':
    sys.exit(main())
