#!/usr/bin/env python3
"""
generate_all_plots.py - Generate all analysis plots in one run

Automatically discovers all CSV files in data/ directory and generates
complete analysis with academically rigorous visualizations.

Output:
  - ECDF plots
  - Quantile comparisons
  - Boxplots
  - Tail heaviness charts
  - All organized in plots/ directory
"""

import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent))

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except ImportError:
    print("Error: matplotlib required")
    print("Install with: .venv/bin/pip install matplotlib numpy")
    sys.exit(1)

from plot_robust import generate_all_plots


def find_csv_files(data_dir: Path) -> List[Path]:
    """Find all CSV files in data directory"""
    csv_files = list(data_dir.glob("*.csv"))
    
    # Filter out empty files
    valid_files = []
    for csv_file in csv_files:
        if csv_file.stat().st_size > 0:
            valid_files.append(csv_file)
    
    return sorted(valid_files)


def detect_metric_column(csv_file: Path) -> str:
    """Detect the main metric column in CSV"""
    import csv
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Prefer runtime_ns, then workload_ns, then any *_ns
        if 'runtime_ns' in headers:
            return 'runtime_ns'
        elif 'workload_ns' in headers:
            return 'workload_ns'
        else:
            # Find first column ending in _ns
            for h in headers:
                if h.endswith('_ns'):
                    return h
    
    return None


def detect_group_column(csv_file: Path) -> str:
    """Detect the grouping column in CSV"""
    import csv
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Common grouping columns
        if 'name' in headers:
            return 'name'
        elif 'buffer_size' in headers:
            return 'buffer_size'
        elif 'threads' in headers:
            return 'threads'
        elif 'condition' in headers:
            return 'condition'
        
        # Default: use first non-numeric, non-timestamp column
        for row in reader:
            for h in headers:
                if h in ['run', 'timestamp_ns', 'runtime_ns', 'workload_ns']:
                    continue
                try:
                    float(row[h])
                except:
                    return h
            break
    
    return 'name'


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate all analysis plots from data files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate plots for all CSV files in data/
  python3 generate_all_plots.py

  # Specify different data directory
  python3 generate_all_plots.py --data-dir experiments/

  # Specify output directory
  python3 generate_all_plots.py --output plots/publication/

Output:
  - ECDF plots (no histograms)
  - Quantile comparisons (p50, p90, p95, p99)
  - Boxplots (Tukey method)
  - Tail heaviness (p99/p50 ratio)

All plots are publication-quality (300 DPI, no parametric assumptions).
        """
    )
    
    parser.add_argument('--data-dir', type=Path, default=Path('data'),
                       help='Data directory (default: data/)')
    parser.add_argument('--output', type=Path, default=Path('plots'),
                       help='Output directory (default: plots/)')
    parser.add_argument('--metric', help='Force specific metric column')
    parser.add_argument('--group-by', help='Force specific grouping column')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be processed without generating plots')
    
    args = parser.parse_args()
    
    # Find CSV files
    csv_files = find_csv_files(args.data_dir)
    
    if not csv_files:
        print(f"No CSV files found in {args.data_dir}/")
        return 1
    
    print(f"Found {len(csv_files)} CSV file(s) in {args.data_dir}/")
    print()
    
    # Process each file
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for csv_file in csv_files:
        print(f"Processing: {csv_file.name}")
        
        # Auto-detect metric and grouping
        metric = args.metric or detect_metric_column(csv_file)
        group_by = args.group_by or detect_group_column(csv_file)
        
        if not metric:
            print(f"  [SKIP] No metric column found")
            skip_count += 1
            continue
        
        print(f"  Metric: {metric}")
        print(f"  Group by: {group_by}")
        
        if args.dry_run:
            print(f"  [DRY-RUN] Would generate plots")
            continue
        
        try:
            generate_all_plots(csv_file, metric, group_by, args.output)
            success_count += 1
        except Exception as e:
            print(f"  [ERROR] {e}")
            error_count += 1
        
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Processed: {success_count}")
    print(f"  Skipped:   {skip_count}")
    print(f"  Errors:    {error_count}")
    print()
    
    if success_count > 0:
        print(f"Plots saved to: {args.output}/")
        print()
        print("Generated plot types:")
        print("  - *_ecdf.png       : Empirical CDF")
        print("  - *_quantiles.png  : p50, p90, p95, p99 comparison")
        print("  - *_boxplot.png    : Tukey boxplot")
        print("  - *_tail_ratio.png : Tail heaviness (p99/p50)")
    
    return 0 if error_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
