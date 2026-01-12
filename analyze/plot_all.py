#!/usr/bin/env python3
"""
plot_all.py - Automatic visualization generator for all CSV files

Purpose:
  Automatically discovers all CSV files in data/ directory
  Generates appropriate plots based on experiment type
  Saves plots to data/plots/ directory
  
Usage:
  python3 analyze/plot_all.py
  
Output:
  - Individual plots for each experiment
  - Summary dashboard with all experiments
  - PNG format for easy sharing
"""

import sys
import csv
from pathlib import Path
from typing import Dict, List, Tuple
import warnings

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.gridspec import GridSpec
except ImportError:
    print("Error: matplotlib is required for plotting")
    print("Install with: pip3 install matplotlib numpy")
    sys.exit(1)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Plot styling
plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#BC4B51']


class ExperimentPlotter:
    """Base class for experiment-specific plotting."""
    
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.name = csv_path.stem
        self.data = self._load_data()
        
    def _load_data(self) -> List[Dict]:
        """Load CSV data into list of dictionaries."""
        data = []
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    
    def _ms_from_ns(self, ns_value) -> float:
        """Convert nanoseconds to milliseconds."""
        return float(ns_value) / 1_000_000.0
    
    def plot(self, output_dir: Path) -> Path:
        """Generate plot. Returns path to saved file."""
        raise NotImplementedError


class NullBaselinePlotter(ExperimentPlotter):
    """Plot null baseline experiment - measurement overhead."""
    
    def plot(self, output_dir: Path) -> Path:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        runtimes = [self._ms_from_ns(row['runtime_ns']) for row in self.data]
        
        # Time series
        ax1.plot(runtimes, marker='o', markersize=3, linewidth=1, color=COLORS[0], alpha=0.7)
        ax1.set_xlabel('Run Number', fontsize=11)
        ax1.set_ylabel('Runtime (ms)', fontsize=11)
        ax1.set_title('Measurement Overhead Over Time', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Distribution
        ax2.hist(runtimes, bins=30, color=COLORS[1], alpha=0.7, edgecolor='black')
        ax2.axvline(np.median(runtimes), color='red', linestyle='--', 
                   label=f'Median: {np.median(runtimes):.4f} ms')
        ax2.set_xlabel('Runtime (ms)', fontsize=11)
        ax2.set_ylabel('Frequency', fontsize=11)
        ax2.set_title('Runtime Distribution', fontsize=12, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.suptitle('Null Baseline Experiment - Measurement Overhead', 
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        output_path = output_dir / f'{self.name}.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path


class PinnedPlotter(ExperimentPlotter):
    """Plot CPU affinity experiment."""
    
    def plot(self, output_dir: Path) -> Path:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Group by affinity
        grouped = {}
        for row in self.data:
            affinity = row['affinity']
            if affinity not in grouped:
                grouped[affinity] = []
            grouped[affinity].append(self._ms_from_ns(row['runtime_ns']))
        
        # Box plot
        labels = list(grouped.keys())
        data_for_box = [grouped[k] for k in labels]
        bp = ax1.boxplot(data_for_box, labels=labels, patch_artist=True)
        for patch, color in zip(bp['boxes'], COLORS):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax1.set_ylabel('Runtime (ms)', fontsize=11)
        ax1.set_title('Runtime by CPU Affinity', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Migration analysis
        migrations = {}
        for row in self.data:
            affinity = row['affinity']
            if affinity not in migrations:
                migrations[affinity] = {'migrated': 0, 'not_migrated': 0}
            if row['start_cpu'] != row['end_cpu']:
                migrations[affinity]['migrated'] += 1
            else:
                migrations[affinity]['not_migrated'] += 1
        
        x = np.arange(len(labels))
        width = 0.35
        migrated = [migrations[k]['migrated'] for k in labels]
        not_migrated = [migrations[k]['not_migrated'] for k in labels]
        
        ax2.bar(x - width/2, not_migrated, width, label='No Migration', 
               color=COLORS[4], alpha=0.7)
        ax2.bar(x + width/2, migrated, width, label='Migrated', 
               color=COLORS[5], alpha=0.7)
        ax2.set_xlabel('CPU Affinity', fontsize=11)
        ax2.set_ylabel('Count', fontsize=11)
        ax2.set_title('CPU Migration Analysis', fontsize=12, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels)
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.suptitle('CPU Affinity Impact on Performance', 
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        output_path = output_dir / f'{self.name}.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path


class CacheHierarchyPlotter(ExperimentPlotter):
    """Plot cache hierarchy latency experiment."""
    
    def plot(self, output_dir: Path) -> Path:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Group by buffer size
        grouped = {}
        for row in self.data:
            size = row['buffer_size']
            if size not in grouped:
                grouped[size] = []
            grouped[size].append(self._ms_from_ns(row['runtime_ns']))
        
        # Sort by size (extract numeric value)
        def size_key(s):
            if 'KB' in s:
                return float(s.split('KB')[0].split('_')[-1])
            elif 'MB' in s:
                return float(s.split('MB')[0].split('_')[-1]) * 1024
            return 0
        
        sorted_sizes = sorted(grouped.keys(), key=size_key)
        
        # Plot with error bars
        means = [np.mean(grouped[s]) for s in sorted_sizes]
        stds = [np.std(grouped[s]) for s in sorted_sizes]
        
        x = np.arange(len(sorted_sizes))
        ax.bar(x, means, yerr=stds, capsize=5, color=COLORS[2], 
              alpha=0.7, edgecolor='black', linewidth=1.2)
        
        ax.set_xlabel('Buffer Size (Cache Level)', fontsize=11)
        ax.set_ylabel('Latency (ms)', fontsize=11)
        ax.set_title('Memory Hierarchy Latency Analysis', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(sorted_sizes, rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        output_path = output_dir / f'{self.name}.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path


class LockScalingPlotter(ExperimentPlotter):
    """Plot lock contention scaling experiment."""
    
    def plot(self, output_dir: Path) -> Path:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Group by lock type and threads
        grouped = {}
        for row in self.data:
            key = (row['lock_type'], int(row['threads']))
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(float(row['ops_per_sec']))
        
        # Get unique lock types and thread counts
        lock_types = sorted(set(k[0] for k in grouped.keys()))
        thread_counts = sorted(set(k[1] for k in grouped.keys()))
        
        # Throughput by thread count
        for i, lock_type in enumerate(lock_types):
            throughputs = []
            for threads in thread_counts:
                key = (lock_type, threads)
                if key in grouped:
                    throughputs.append(np.mean(grouped[key]) / 1_000_000)  # M ops/sec
                else:
                    throughputs.append(0)
            ax1.plot(thread_counts, throughputs, marker='o', linewidth=2, 
                    label=lock_type, color=COLORS[i % len(COLORS)])
        
        ax1.set_xlabel('Thread Count', fontsize=11)
        ax1.set_ylabel('Throughput (M ops/sec)', fontsize=11)
        ax1.set_title('Lock Throughput Scaling', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Runtime comparison (1/throughput)
        for threads in thread_counts:
            data = []
            labels = []
            for lock_type in lock_types:
                key = (lock_type, threads)
                if key in grouped:
                    data.append(1000.0 / (np.mean(grouped[key]) / 1_000_000))  # ns per op
                    labels.append(lock_type)
            
            if data:
                x = np.arange(len(labels))
                ax2.bar(x + threads * 0.2, data, 0.2, 
                       label=f'{threads} thread(s)', alpha=0.7)
        
        ax2.set_xlabel('Lock Type', fontsize=11)
        ax2.set_ylabel('Time per Operation (ns)', fontsize=11)
        ax2.set_title('Lock Operation Latency', fontsize=12, fontweight='bold')
        ax2.set_xticks(x + 0.3)
        ax2.set_xticklabels(labels)
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.suptitle('Lock Contention Analysis', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        output_path = output_dir / f'{self.name}.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path


class GenericPlotter(ExperimentPlotter):
    """Generic plotter for other experiments."""
    
    def plot(self, output_dir: Path) -> Path:
        # Determine grouping column (first non-run, non-timestamp column)
        group_col = None
        for col in self.data[0].keys():
            if col not in ['run', 'timestamp_ns', 'runtime_ns', 
                          'voluntary_ctxt_switches', 'nonvoluntary_ctxt_switches',
                          'minor_page_faults', 'major_page_faults', 
                          'start_cpu', 'end_cpu']:
                group_col = col
                break
        
        if not group_col:
            # Simple time series
            fig, ax = plt.subplots(figsize=(12, 6))
            runtimes = [self._ms_from_ns(row['runtime_ns']) for row in self.data]
            ax.plot(runtimes, marker='o', markersize=3, linewidth=1, color=COLORS[0])
            ax.set_xlabel('Run Number', fontsize=11)
            ax.set_ylabel('Runtime (ms)', fontsize=11)
            ax.set_title(f'{self.name.replace("_", " ").title()} - Runtime', 
                        fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
        else:
            # Grouped plot
            fig, ax = plt.subplots(figsize=(12, 6))
            
            grouped = {}
            for row in self.data:
                key = row[group_col]
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(self._ms_from_ns(row['runtime_ns']))
            
            labels = list(grouped.keys())
            data_for_box = [grouped[k] for k in labels]
            bp = ax.boxplot(data_for_box, labels=labels, patch_artist=True)
            for patch, color in zip(bp['boxes'], COLORS):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            ax.set_xlabel(group_col.replace('_', ' ').title(), fontsize=11)
            ax.set_ylabel('Runtime (ms)', fontsize=11)
            ax.set_title(f'{self.name.replace("_", " ").title()} - Performance', 
                        fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        output_path = output_dir / f'{self.name}.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path


def get_plotter(csv_path: Path) -> ExperimentPlotter:
    """Factory function to get appropriate plotter for experiment."""
    name = csv_path.stem
    
    if name == 'null_baseline':
        return NullBaselinePlotter(csv_path)
    elif name == 'pinned':
        return PinnedPlotter(csv_path)
    elif name == 'cache_hierarchy':
        return CacheHierarchyPlotter(csv_path)
    elif name == 'lock_scaling':
        return LockScalingPlotter(csv_path)
    else:
        return GenericPlotter(csv_path)


def create_summary_dashboard(plot_paths: List[Path], output_dir: Path):
    """Create a summary dashboard with thumbnails of all plots."""
    n_plots = len(plot_paths)
    if n_plots == 0:
        return
    
    # Calculate grid size
    n_cols = min(3, n_plots)
    n_rows = (n_plots + n_cols - 1) // n_cols
    
    fig = plt.figure(figsize=(18, 6 * n_rows))
    gs = GridSpec(n_rows, n_cols, figure=fig, hspace=0.3, wspace=0.3)
    
    for idx, plot_path in enumerate(plot_paths):
        row = idx // n_cols
        col = idx % n_cols
        ax = fig.add_subplot(gs[row, col])
        
        # Load and display image
        img = plt.imread(plot_path)
        ax.imshow(img)
        ax.axis('off')
        ax.set_title(plot_path.stem.replace('_', ' ').title(), 
                    fontsize=10, fontweight='bold')
    
    plt.suptitle('Linux Reality Check - Experiment Results Summary', 
                fontsize=16, fontweight='bold')
    
    dashboard_path = output_dir / 'summary_dashboard.png'
    plt.savefig(dashboard_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    print(f"\n✓ Summary dashboard: {dashboard_path}")


def main():
    """Main function to discover and plot all CSV files."""
    
    # Setup paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    plots_dir = data_dir / 'plots'
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     Linux Reality Check - Automatic Plot Generator        ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Create plots directory
    plots_dir.mkdir(exist_ok=True)
    print(f"Output directory: {plots_dir}")
    print()
    
    # Discover CSV files
    csv_files = sorted(data_dir.glob('*.csv'))
    
    if not csv_files:
        print("No CSV files found in data/ directory")
        print("  Run experiments first: ./lrc quick")
        return 1
    
    print(f"Found {len(csv_files)} experiment(s):")
    for csv_file in csv_files:
        print(f"   • {csv_file.name}")
    print()
    
    # Generate plots
    print("Generating plots...")
    plot_paths = []
    
    for i, csv_file in enumerate(csv_files, 1):
        try:
            plotter = get_plotter(csv_file)
            output_path = plotter.plot(plots_dir)
            plot_paths.append(output_path)
            print(f"  [{i}/{len(csv_files)}] ✓ {csv_file.stem:25s} → {output_path.name}")
        except Exception as e:
            print(f"  [{i}/{len(csv_files)}] ✗ {csv_file.stem:25s} → Error: {e}")
    
    print()
    
    # Create summary dashboard
    if plot_paths:
        print("Creating summary dashboard...")
        create_summary_dashboard(plot_paths, plots_dir)
    
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print(f"║  ✓ Generated {len(plot_paths)} plot(s) successfully")
    print(f"║    Location: {plots_dir}")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    print("View plots:")
    print(f"  Open {plots_dir}")
    print(f"  View summary: {plots_dir / 'summary_dashboard.png'}")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
