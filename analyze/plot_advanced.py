#!/usr/bin/env python3
"""
plot_advanced.py - Advanced visualization with statistical analysis

Purpose:
  Enhanced plotting with statistical overlays, correlation analysis,
  heatmaps, violin plots, confidence intervals, and multi-experiment
  comparisons.
  
Features:
  - Statistical annotations (mean, median, CI)
  - Violin plots with kernel density estimation
  - Correlation matrices and heatmaps
  - Multi-experiment comparison overlays
  - Performance regression analysis
  - CDF and percentile plots
  - Outlier detection visualization
  - Time series decomposition
  
Usage:
  python3 analyze/plot_advanced.py [options]
  
Options:
  --experiments NAMES  Only plot specific experiments (comma-separated)
  --compare            Generate comparison plots across experiments
  --stats              Include statistical annotations
  --all                Generate all advanced plots (default)
"""

import sys
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import warnings

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.gridspec import GridSpec
    from matplotlib.patches import Rectangle
    from scipy import stats
    from scipy.signal import savgol_filter
except ImportError as e:
    print(f"Error: Required package missing: {e}")
    print("Install with: pip3 install matplotlib numpy scipy")
    sys.exit(1)

warnings.filterwarnings('ignore')

# Enhanced styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#BC4B51', '#5E548E', '#E07A5F']
ALPHA = 0.7


class AdvancedPlotter:
    """Advanced statistical plotting capabilities."""
    
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.name = csv_path.stem
        self.data = self._load_data()
        
    def _load_data(self) -> List[Dict]:
        """Load CSV data."""
        data = []
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    
    def _ms_from_ns(self, ns_value) -> float:
        """Convert nanoseconds to milliseconds."""
        return float(ns_value) / 1_000_000.0
    
    def _calculate_ci(self, data: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval."""
        n = len(data)
        mean = np.mean(data)
        se = stats.sem(data)
        ci = se * stats.t.ppf((1 + confidence) / 2, n - 1)
        return mean - ci, mean + ci
    
    def _detect_outliers_iqr(self, data: np.ndarray) -> np.ndarray:
        """Detect outliers using IQR method."""
        q1, q3 = np.percentile(data, [25, 75])
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return (data < lower) | (data > upper)
    
    def plot_violin_with_stats(self, output_dir: Path) -> Path:
        """Violin plot with statistical annotations."""
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Group data
        grouped = defaultdict(list)
        for row in self.data:
            # Find grouping column
            group_col = None
            for col in row.keys():
                if col not in ['run', 'timestamp_ns', 'runtime_ns', 
                              'voluntary_ctxt_switches', 'nonvoluntary_ctxt_switches',
                              'minor_page_faults', 'major_page_faults', 
                              'start_cpu', 'end_cpu', 'ops_per_sec']:
                    group_col = col
                    break
            
            if group_col:
                grouped[row[group_col]].append(self._ms_from_ns(row['runtime_ns']))
        
        if not grouped:
            # Single group
            grouped['default'] = [self._ms_from_ns(row['runtime_ns']) for row in self.data]
        
        # Prepare data
        labels = list(grouped.keys())
        data_list = [grouped[k] for k in labels]
        
        # Violin plot
        parts = ax.violinplot(data_list, positions=range(len(labels)), 
                             showmeans=True, showmedians=True, widths=0.7)
        
        # Color violin plots
        for i, pc in enumerate(parts['bodies']):
            pc.set_facecolor(COLORS[i % len(COLORS)])
            pc.set_alpha(ALPHA)
        
        # Add statistical annotations
        for i, (label, data) in enumerate(zip(labels, data_list)):
            data_arr = np.array(data)
            mean = np.mean(data_arr)
            median = np.median(data_arr)
            ci_low, ci_high = self._calculate_ci(data_arr)
            std = np.std(data_arr)
            
            # Plot confidence interval
            ax.plot([i, i], [ci_low, ci_high], 'k-', linewidth=2, alpha=0.6)
            ax.plot([i-0.1, i+0.1], [ci_low, ci_low], 'k-', linewidth=2)
            ax.plot([i-0.1, i+0.1], [ci_high, ci_high], 'k-', linewidth=2)
            
            # Annotate statistics
            stats_text = f'μ={mean:.2f}\nσ={std:.2f}\n95%CI'
            ax.text(i, ci_high + 0.05 * (ax.get_ylim()[1] - ax.get_ylim()[0]), 
                   stats_text, ha='center', va='bottom', fontsize=8,
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_ylabel('Runtime (ms)', fontsize=12, fontweight='bold')
        ax.set_title(f'{self.name.replace("_", " ").title()} - Distribution Analysis with Statistics',
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_path = output_dir / f'{self.name}_violin_stats.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path
    
    def plot_cdf_percentiles(self, output_dir: Path) -> Path:
        """Cumulative Distribution Function with percentile markers."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Group data
        grouped = defaultdict(list)
        for row in self.data:
            group_col = None
            for col in row.keys():
                if col not in ['run', 'timestamp_ns', 'runtime_ns', 
                              'voluntary_ctxt_switches', 'nonvoluntary_ctxt_switches',
                              'minor_page_faults', 'major_page_faults', 
                              'start_cpu', 'end_cpu', 'ops_per_sec']:
                    group_col = col
                    break
            
            if group_col:
                grouped[row[group_col]].append(self._ms_from_ns(row['runtime_ns']))
        
        if not grouped:
            grouped['default'] = [self._ms_from_ns(row['runtime_ns']) for row in self.data]
        
        # CDF Plot
        for i, (label, data) in enumerate(grouped.items()):
            sorted_data = np.sort(data)
            cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
            ax1.plot(sorted_data, cdf, label=label, linewidth=2, 
                    color=COLORS[i % len(COLORS)], alpha=ALPHA)
            
            # Mark percentiles
            percentiles = [50, 90, 95, 99]
            for p in percentiles:
                val = np.percentile(data, p)
                ax1.plot(val, p/100, 'o', markersize=8, 
                        color=COLORS[i % len(COLORS)])
                if i == 0:  # Only label once
                    ax1.text(val, p/100, f'p{p}', fontsize=8, 
                            va='bottom', ha='left')
        
        ax1.set_xlabel('Runtime (ms)', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Cumulative Probability', fontsize=11, fontweight='bold')
        ax1.set_title('Cumulative Distribution Function', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Percentile comparison
        percentiles = [50, 75, 90, 95, 99, 99.9]
        x = np.arange(len(percentiles))
        width = 0.8 / len(grouped)
        
        for i, (label, data) in enumerate(grouped.items()):
            values = [np.percentile(data, p) for p in percentiles]
            ax2.bar(x + i * width, values, width, label=label,
                   color=COLORS[i % len(COLORS)], alpha=ALPHA)
        
        ax2.set_xlabel('Percentile', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Runtime (ms)', fontsize=11, fontweight='bold')
        ax2.set_title('Percentile Comparison', fontsize=12, fontweight='bold')
        ax2.set_xticks(x + width * (len(grouped) - 1) / 2)
        ax2.set_xticklabels([f'p{p}' for p in percentiles])
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.suptitle(f'{self.name.replace("_", " ").title()} - Statistical Analysis',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        output_path = output_dir / f'{self.name}_cdf_percentiles.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path
    
    def plot_outlier_detection(self, output_dir: Path) -> Path:
        """Visualize outliers with multiple detection methods."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        runtimes = np.array([self._ms_from_ns(row['runtime_ns']) for row in self.data])
        
        # 1. Box plot with outliers highlighted
        bp = ax1.boxplot(runtimes, vert=True, patch_artist=True, widths=0.5)
        bp['boxes'][0].set_facecolor(COLORS[0])
        bp['boxes'][0].set_alpha(ALPHA)
        
        outliers_iqr = self._detect_outliers_iqr(runtimes)
        ax1.scatter(np.ones(len(runtimes[outliers_iqr])), runtimes[outliers_iqr],
                   color='red', s=50, alpha=0.7, label=f'Outliers: {sum(outliers_iqr)}')
        ax1.set_ylabel('Runtime (ms)', fontsize=11)
        ax1.set_title('IQR Method Outlier Detection', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 2. Z-score method
        z_scores = np.abs(stats.zscore(runtimes))
        outliers_z = z_scores > 3
        
        ax2.scatter(range(len(runtimes)), runtimes, c=['red' if o else 'blue' 
                   for o in outliers_z], alpha=0.6, s=30)
        ax2.axhline(np.mean(runtimes), color='green', linestyle='--', 
                   label=f'Mean: {np.mean(runtimes):.2f}')
        ax2.axhline(np.mean(runtimes) + 3*np.std(runtimes), color='red', 
                   linestyle='--', alpha=0.5, label='±3σ')
        ax2.axhline(np.mean(runtimes) - 3*np.std(runtimes), color='red', 
                   linestyle='--', alpha=0.5)
        ax2.set_xlabel('Run Number', fontsize=11)
        ax2.set_ylabel('Runtime (ms)', fontsize=11)
        ax2.set_title(f'Z-Score Method (Outliers: {sum(outliers_z)})', 
                     fontsize=12, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Moving average with deviation
        if len(runtimes) > 10:
            window = min(20, len(runtimes) // 5)
            moving_avg = np.convolve(runtimes, np.ones(window)/window, mode='valid')
            x_ma = np.arange(window-1, len(runtimes))
            
            ax3.plot(runtimes, alpha=0.5, label='Raw data', color=COLORS[0])
            ax3.plot(x_ma, moving_avg, linewidth=2, label=f'Moving Avg (w={window})',
                    color=COLORS[1])
            
            # Highlight deviations
            threshold = 2 * np.std(runtimes)
            for i, (val, ma) in enumerate(zip(runtimes[window-1:], moving_avg)):
                if abs(val - ma) > threshold:
                    ax3.scatter(i + window - 1, val, color='red', s=50, zorder=5)
            
            ax3.set_xlabel('Run Number', fontsize=11)
            ax3.set_ylabel('Runtime (ms)', fontsize=11)
            ax3.set_title('Moving Average Deviation', fontsize=12, fontweight='bold')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        # 4. Histogram with distribution fit
        ax4.hist(runtimes, bins=30, density=True, alpha=0.6, 
                color=COLORS[0], edgecolor='black', label='Data')
        
        # Fit normal distribution
        mu, sigma = stats.norm.fit(runtimes)
        x = np.linspace(runtimes.min(), runtimes.max(), 100)
        ax4.plot(x, stats.norm.pdf(x, mu, sigma), 'r-', linewidth=2,
                label=f'Normal fit\nμ={mu:.2f}, σ={sigma:.2f}')
        
        # Mark outliers on histogram
        outlier_data = runtimes[outliers_iqr]
        if len(outlier_data) > 0:
            ax4.scatter(outlier_data, [0.001] * len(outlier_data), 
                       color='red', s=50, marker='^', 
                       label='IQR Outliers', zorder=5)
        
        ax4.set_xlabel('Runtime (ms)', fontsize=11)
        ax4.set_ylabel('Density', fontsize=11)
        ax4.set_title('Distribution with Normal Fit', fontsize=12, fontweight='bold')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.suptitle(f'{self.name.replace("_", " ").title()} - Outlier Detection Analysis',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        output_path = output_dir / f'{self.name}_outlier_analysis.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path
    
    def plot_time_series_decomposition(self, output_dir: Path) -> Path:
        """Time series analysis with trend and seasonality."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        runtimes = np.array([self._ms_from_ns(row['runtime_ns']) for row in self.data])
        x = np.arange(len(runtimes))
        
        # 1. Original series
        ax1.plot(x, runtimes, linewidth=1, alpha=0.7, color=COLORS[0])
        ax1.scatter(x, runtimes, s=20, alpha=0.5, color=COLORS[0])
        ax1.set_xlabel('Run Number', fontsize=11)
        ax1.set_ylabel('Runtime (ms)', fontsize=11)
        ax1.set_title('Original Time Series', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # 2. Trend (using polynomial fit)
        if len(runtimes) > 3:
            z = np.polyfit(x, runtimes, 3)
            p = np.poly1d(z)
            trend = p(x)
            
            ax2.plot(x, runtimes, alpha=0.3, label='Data', color=COLORS[0])
            ax2.plot(x, trend, linewidth=2, label='Trend (poly-3)', color=COLORS[1])
            ax2.set_xlabel('Run Number', fontsize=11)
            ax2.set_ylabel('Runtime (ms)', fontsize=11)
            ax2.set_title('Trend Analysis', fontsize=12, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 3. Detrended (residuals)
            detrended = runtimes - trend
            ax3.plot(x, detrended, linewidth=1, color=COLORS[2])
            ax3.axhline(0, color='black', linestyle='--', alpha=0.5)
            ax3.fill_between(x, 0, detrended, alpha=0.3, color=COLORS[2])
            ax3.set_xlabel('Run Number', fontsize=11)
            ax3.set_ylabel('Residual (ms)', fontsize=11)
            ax3.set_title('Detrended Series (Residuals)', fontsize=12, fontweight='bold')
            ax3.grid(True, alpha=0.3)
        
        # 4. Rolling statistics
        if len(runtimes) > 20:
            window = min(20, len(runtimes) // 4)
            rolling_mean = np.convolve(runtimes, np.ones(window)/window, mode='valid')
            rolling_std = np.array([np.std(runtimes[max(0, i-window):i+1]) 
                                   for i in range(len(runtimes))])
            
            ax4_twin = ax4.twinx()
            ax4.plot(x, runtimes, alpha=0.3, label='Data', color=COLORS[0])
            ax4.plot(x[window-1:], rolling_mean, linewidth=2, 
                    label=f'Rolling Mean (w={window})', color=COLORS[1])
            ax4_twin.plot(x, rolling_std, linewidth=2, linestyle='--',
                         label='Rolling Std Dev', color=COLORS[3])
            
            ax4.set_xlabel('Run Number', fontsize=11)
            ax4.set_ylabel('Runtime (ms)', fontsize=11)
            ax4_twin.set_ylabel('Std Dev (ms)', fontsize=11)
            ax4.set_title('Rolling Statistics', fontsize=12, fontweight='bold')
            
            # Combine legends
            lines1, labels1 = ax4.get_legend_handles_labels()
            lines2, labels2 = ax4_twin.get_legend_handles_labels()
            ax4.legend(lines1 + lines2, labels1 + labels2, loc='best')
            ax4.grid(True, alpha=0.3)
        
        plt.suptitle(f'{self.name.replace("_", " ").title()} - Time Series Decomposition',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        output_path = output_dir / f'{self.name}_timeseries_decomposition.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path


def create_correlation_matrix(csv_files: List[Path], output_dir: Path) -> Path:
    """Create correlation matrix across all experiments."""
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Collect data from all experiments
    experiment_data = {}
    for csv_file in csv_files:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            runtimes = []
            for row in reader:
                runtimes.append(float(row['runtime_ns']) / 1_000_000.0)
            if runtimes:
                experiment_data[csv_file.stem] = runtimes
    
    # Align data lengths (use minimum length)
    min_length = min(len(v) for v in experiment_data.values())
    aligned_data = {k: v[:min_length] for k, v in experiment_data.items()}
    
    # Calculate correlation matrix
    names = list(aligned_data.keys())
    n = len(names)
    corr_matrix = np.zeros((n, n))
    
    for i, name1 in enumerate(names):
        for j, name2 in enumerate(names):
            if i == j:
                corr_matrix[i, j] = 1.0
            else:
                corr, _ = stats.pearsonr(aligned_data[name1], aligned_data[name2])
                corr_matrix[i, j] = corr
    
    # Plot heatmap
    im = ax.imshow(corr_matrix, cmap='RdYlGn', vmin=-1, vmax=1, aspect='auto')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Correlation Coefficient', fontsize=11, fontweight='bold')
    
    # Add text annotations
    for i in range(n):
        for j in range(n):
            text = ax.text(j, i, f'{corr_matrix[i, j]:.2f}',
                          ha='center', va='center', 
                          color='white' if abs(corr_matrix[i, j]) > 0.5 else 'black',
                          fontsize=8)
    
    # Set ticks
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels([name.replace('_', '\n') for name in names], 
                       rotation=45, ha='right', fontsize=9)
    ax.set_yticklabels(names, fontsize=9)
    
    ax.set_title('Cross-Experiment Correlation Matrix\n(Runtime Correlations)',
                fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    output_path = output_dir / 'correlation_matrix.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_comparison_dashboard(csv_files: List[Path], output_dir: Path) -> Path:
    """Create comprehensive comparison dashboard."""
    n_experiments = len(csv_files)
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    # Collect all data
    all_data = {}
    for csv_file in csv_files:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            runtimes = [float(row['runtime_ns']) / 1_000_000.0 for row in reader]
            all_data[csv_file.stem] = runtimes
    
    # 1. Box plot comparison (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    labels = list(all_data.keys())
    data_list = [all_data[k] for k in labels]
    bp = ax1.boxplot(data_list, labels=labels, patch_artist=True)
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(COLORS[i % len(COLORS)])
        patch.set_alpha(ALPHA)
    ax1.set_ylabel('Runtime (ms)', fontsize=10)
    ax1.set_title('Runtime Distribution Comparison', fontsize=11, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45, labelsize=8)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. Mean comparison with error bars (top middle)
    ax2 = fig.add_subplot(gs[0, 1])
    means = [np.mean(d) for d in data_list]
    stds = [np.std(d) for d in data_list]
    x = np.arange(len(labels))
    ax2.bar(x, means, yerr=stds, capsize=5, color=COLORS[:len(labels)], 
           alpha=ALPHA, edgecolor='black')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax2.set_ylabel('Mean Runtime (ms)', fontsize=10)
    ax2.set_title('Mean Runtime Comparison', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Coefficient of Variation (top right)
    ax3 = fig.add_subplot(gs[0, 2])
    cvs = [(np.std(d) / np.mean(d)) * 100 for d in data_list]
    ax3.bar(x, cvs, color=COLORS[:len(labels)], alpha=ALPHA, edgecolor='black')
    ax3.axhline(10, color='red', linestyle='--', alpha=0.5, label='10% CV')
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax3.set_ylabel('CV (%)', fontsize=10)
    ax3.set_title('Variability (Coefficient of Variation)', fontsize=11, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. CDF overlay (middle left)
    ax4 = fig.add_subplot(gs[1, 0])
    for i, (label, data) in enumerate(all_data.items()):
        sorted_data = np.sort(data)
        cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
        ax4.plot(sorted_data, cdf, label=label[:15], linewidth=2,
                color=COLORS[i % len(COLORS)], alpha=ALPHA)
    ax4.set_xlabel('Runtime (ms)', fontsize=10)
    ax4.set_ylabel('CDF', fontsize=10)
    ax4.set_title('Cumulative Distribution Overlay', fontsize=11, fontweight='bold')
    ax4.legend(fontsize=7)
    ax4.grid(True, alpha=0.3)
    
    # 5. Percentile comparison (middle middle)
    ax5 = fig.add_subplot(gs[1, 1])
    percentiles = [50, 90, 95, 99]
    x_perc = np.arange(len(percentiles))
    width = 0.8 / len(labels)
    for i, (label, data) in enumerate(all_data.items()):
        values = [np.percentile(data, p) for p in percentiles]
        ax5.bar(x_perc + i * width, values, width, label=label[:10],
               color=COLORS[i % len(COLORS)], alpha=ALPHA)
    ax5.set_xlabel('Percentile', fontsize=10)
    ax5.set_ylabel('Runtime (ms)', fontsize=10)
    ax5.set_title('Tail Latency Comparison', fontsize=11, fontweight='bold')
    ax5.set_xticks(x_perc + width * (len(labels) - 1) / 2)
    ax5.set_xticklabels([f'p{p}' for p in percentiles])
    ax5.legend(fontsize=7, ncol=2)
    ax5.grid(True, alpha=0.3, axis='y')
    
    # 6. Sample size comparison (middle right)
    ax6 = fig.add_subplot(gs[1, 2])
    sample_sizes = [len(d) for d in data_list]
    ax6.bar(x, sample_sizes, color=COLORS[:len(labels)], alpha=ALPHA, edgecolor='black')
    ax6.set_xticks(x)
    ax6.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax6.set_ylabel('Sample Count', fontsize=10)
    ax6.set_title('Sample Size per Experiment', fontsize=11, fontweight='bold')
    ax6.grid(True, alpha=0.3, axis='y')
    
    # 7. Normalized comparison (bottom left)
    ax7 = fig.add_subplot(gs[2, 0])
    baseline = np.mean(data_list[0]) if data_list else 1
    normalized = [(np.mean(d) / baseline) * 100 for d in data_list]
    colors_norm = ['green' if n <= 100 else 'red' for n in normalized]
    ax7.bar(x, normalized, color=colors_norm, alpha=ALPHA, edgecolor='black')
    ax7.axhline(100, color='black', linestyle='--', alpha=0.5, label='Baseline')
    ax7.set_xticks(x)
    ax7.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax7.set_ylabel('Relative Performance (%)', fontsize=10)
    ax7.set_title(f'Normalized to {labels[0]}', fontsize=11, fontweight='bold')
    ax7.legend()
    ax7.grid(True, alpha=0.3, axis='y')
    
    # 8. Min/Max range (bottom middle)
    ax8 = fig.add_subplot(gs[2, 1])
    mins = [np.min(d) for d in data_list]
    maxs = [np.max(d) for d in data_list]
    ranges = [mx - mn for mn, mx in zip(mins, maxs)]
    ax8.bar(x, ranges, color=COLORS[:len(labels)], alpha=ALPHA, edgecolor='black')
    ax8.set_xticks(x)
    ax8.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax8.set_ylabel('Range (ms)', fontsize=10)
    ax8.set_title('Min-Max Range', fontsize=11, fontweight='bold')
    ax8.grid(True, alpha=0.3, axis='y')
    
    # 9. Statistical summary table (bottom right)
    ax9 = fig.add_subplot(gs[2, 2])
    ax9.axis('off')
    
    table_data = []
    for label, data in all_data.items():
        table_data.append([
            label[:12],
            f'{np.mean(data):.2f}',
            f'{np.median(data):.2f}',
            f'{np.std(data):.2f}',
            f'{len(data)}'
        ])
    
    table = ax9.table(cellText=table_data,
                     colLabels=['Experiment', 'Mean', 'Median', 'StdDev', 'N'],
                     cellLoc='center',
                     loc='center',
                     bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 2)
    
    for i in range(len(table_data) + 1):
        for j in range(5):
            cell = table[(i, j)]
            if i == 0:
                cell.set_facecolor('#4472C4')
                cell.set_text_props(weight='bold', color='white')
            else:
                cell.set_facecolor('#E7E6E6' if i % 2 == 0 else 'white')
    
    plt.suptitle('Multi-Experiment Comparison Dashboard',
                fontsize=16, fontweight='bold')
    
    output_path = output_dir / 'comparison_dashboard.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Advanced plotting for LRC experiments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 analyze/plot_advanced.py
  python3 analyze/plot_advanced.py --experiments pinned,cache_hierarchy
  python3 analyze/plot_advanced.py --compare --stats
        """)
    
    parser.add_argument('--experiments', type=str, default=None,
                       help='Comma-separated list of experiments to plot')
    parser.add_argument('--compare', action='store_true',
                       help='Generate comparison plots across experiments')
    parser.add_argument('--stats', action='store_true', default=True,
                       help='Include statistical annotations (default: True)')
    parser.add_argument('--all', action='store_true', default=True,
                       help='Generate all advanced plots (default: True)')
    
    args = parser.parse_args()
    
    # Setup paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    plots_dir = data_dir / 'plots' / 'advanced'
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     LRC Advanced Plotting - Statistical Visualization     ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Create output directory
    plots_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output: {plots_dir}")
    print()
    
    # Discover CSV files
    if args.experiments:
        exp_names = [e.strip() for e in args.experiments.split(',')]
        csv_files = [data_dir / f'{name}.csv' for name in exp_names 
                    if (data_dir / f'{name}.csv').exists()]
    else:
        csv_files = sorted(data_dir.glob('*.csv'))
    
    if not csv_files:
        print("⚠ No CSV files found")
        return 1
    
    print(f"📊 Processing {len(csv_files)} experiment(s)")
    print()
    
    # Generate advanced plots for each experiment
    plot_count = 0
    for i, csv_file in enumerate(csv_files, 1):
        try:
            plotter = AdvancedPlotter(csv_file)
            print(f"[{i}/{len(csv_files)}] {csv_file.stem}")
            
            # Violin plot with statistics
            path = plotter.plot_violin_with_stats(plots_dir)
            print(f"  ✓ Violin + Stats: {path.name}")
            plot_count += 1
            
            # CDF and percentiles
            path = plotter.plot_cdf_percentiles(plots_dir)
            print(f"  ✓ CDF/Percentiles: {path.name}")
            plot_count += 1
            
            # Outlier detection
            path = plotter.plot_outlier_detection(plots_dir)
            print(f"  ✓ Outlier Analysis: {path.name}")
            plot_count += 1
            
            # Time series decomposition
            path = plotter.plot_time_series_decomposition(plots_dir)
            print(f"  ✓ Time Series: {path.name}")
            plot_count += 1
            
            print()
        except Exception as e:
            print(f"  ✗ Error: {e}")
            print()
    
    # Generate comparison plots
    if args.compare and len(csv_files) > 1:
        print("Generating comparison plots...")
        
        # Correlation matrix
        try:
            path = create_correlation_matrix(csv_files, plots_dir)
            print(f"  ✓ Correlation Matrix: {path.name}")
            plot_count += 1
        except Exception as e:
            print(f"  ✗ Correlation Matrix: {e}")
        
        # Comparison dashboard
        try:
            path = create_comparison_dashboard(csv_files, plots_dir)
            print(f"  ✓ Comparison Dashboard: {path.name}")
            plot_count += 1
        except Exception as e:
            print(f"  ✗ Comparison Dashboard: {e}")
        
        print()
    
    print("╔════════════════════════════════════════════════════════════╗")
    print(f"║  ✓ Generated {plot_count} advanced plot(s)")
    print(f"║  📂 {plots_dir}")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
