#!/usr/bin/env python3
"""
Power Analysis Calculator for Linux Reality Check
Helps researchers determine adequate sample sizes and detect achievable effect sizes.

Statistical Power Concepts:
- Power (1 - β): Probability of detecting a true effect
- Alpha (α): Type I error rate (false positive)
- Beta (β): Type II error rate (false negative)
- Effect Size: Standardized measure of difference (Cohen's d, eta-squared)

Standard Values:
- Power: 0.8 (80% chance of detecting effect)
- Alpha: 0.05 (5% false positive rate)
- Two-tailed tests for bidirectional hypotheses

Usage:
  # Calculate required sample size for given effect size
  python3 power_analysis.py --effect-size 0.5 --power 0.8

  # Estimate effect size from pilot data
  python3 power_analysis.py --pilot data/pilot1.csv data/pilot2.csv --metric runtime_ns

  # Calculate minimum detectable effect given sample size
  python3 power_analysis.py --sample-size 30 --power 0.8

  # Full analysis from existing results
  python3 power_analysis.py --analyze data/exp1.csv data/exp2.csv --metric runtime_ns
"""

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Try to import scipy for accurate power calculations
try:
    from scipy import stats
    from scipy.special import ndtri
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("Warning: scipy not available. Using approximations for power calculations.", file=sys.stderr)
    print("Install with: pip install scipy", file=sys.stderr)


def cohens_d(mean1: float, mean2: float, std1: float, std2: float, n1: int, n2: int) -> float:
    """
    Calculate Cohen's d effect size.
    
    Cohen's d = (mean1 - mean2) / pooled_std
    
    Interpretation (Cohen, 1988):
    - 0.2: Small effect
    - 0.5: Medium effect
    - 0.8: Large effect
    """
    pooled_std = math.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return abs(mean1 - mean2) / pooled_std


def interpret_effect_size(d: float) -> str:
    """Interpret Cohen's d according to standard conventions."""
    if d < 0.2:
        return "negligible"
    elif d < 0.5:
        return "small"
    elif d < 0.8:
        return "medium"
    else:
        return "large"


def sample_size_two_sample_ttest(effect_size: float, power: float = 0.8, alpha: float = 0.05) -> int:
    """
    Calculate required sample size per group for two-sample t-test.
    
    Uses approximation when scipy unavailable.
    For exact calculations, requires scipy.
    """
    if effect_size <= 0:
        print("Error: Effect size must be positive", file=sys.stderr)
        return -1
    
    if SCIPY_AVAILABLE:
        # Accurate calculation using scipy
        z_alpha = stats.norm.ppf(1 - alpha/2)  # Two-tailed
        z_beta = stats.norm.ppf(power)
        
        n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
        return math.ceil(n)
    else:
        # Approximation without scipy
        # For α=0.05 (two-tailed): z_α/2 ≈ 1.96
        # For power=0.80: z_β ≈ 0.84
        z_alpha = 1.96 if alpha == 0.05 else 2.576  # Rough approximation
        z_beta = 0.84 if power == 0.8 else (1.28 if power == 0.9 else 0.52)
        
        n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
        return math.ceil(n)


def minimum_detectable_effect(n: int, power: float = 0.8, alpha: float = 0.05) -> float:
    """
    Calculate minimum detectable effect size given sample size.
    
    This is the smallest effect that can be reliably detected with given n and power.
    """
    if n <= 2:
        return float('inf')
    
    if SCIPY_AVAILABLE:
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = stats.norm.ppf(power)
        
        effect_size = (z_alpha + z_beta) * math.sqrt(2 / n)
        return effect_size
    else:
        # Approximation
        z_alpha = 1.96 if alpha == 0.05 else 2.576
        z_beta = 0.84 if power == 0.8 else (1.28 if power == 0.9 else 0.52)
        
        effect_size = (z_alpha + z_beta) * math.sqrt(2 / n)
        return effect_size


def actual_power(n: int, effect_size: float, alpha: float = 0.05) -> float:
    """
    Calculate actual statistical power given sample size and effect size.
    
    Returns probability of detecting the effect.
    """
    if n <= 2 or effect_size <= 0:
        return 0.0
    
    if SCIPY_AVAILABLE:
        z_alpha = stats.norm.ppf(1 - alpha/2)
        noncentrality = effect_size * math.sqrt(n / 2)
        power = stats.norm.cdf(noncentrality - z_alpha)
        return max(0.0, min(1.0, power))
    else:
        # Approximation
        z_alpha = 1.96 if alpha == 0.05 else 2.576
        noncentrality = effect_size * math.sqrt(n / 2)
        
        # Rough approximation using normal CDF
        # This is less accurate but gives reasonable estimates
        if noncentrality <= z_alpha:
            return 0.05  # Barely above alpha
        else:
            # Linear approximation in the middle range
            power = 0.5 + 0.4 * ((noncentrality - z_alpha) / (3.0 - z_alpha))
            return max(0.0, min(1.0, power))


def load_csv_metric(csv_path: Path, metric: str) -> List[float]:
    """Load numeric values for a specific metric from CSV."""
    values = []
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            
            if metric not in reader.fieldnames:
                print(f"Error: Metric '{metric}' not found in {csv_path}", file=sys.stderr)
                print(f"Available metrics: {', '.join(reader.fieldnames)}", file=sys.stderr)
                return []
            
            for row in reader:
                try:
                    values.append(float(row[metric]))
                except (ValueError, KeyError):
                    continue
    except Exception as e:
        print(f"Error reading {csv_path}: {e}", file=sys.stderr)
        return []
    
    return values


def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """Calculate mean and standard deviation."""
    if not values:
        return {'mean': 0.0, 'std': 0.0, 'n': 0}
    
    n = len(values)
    mean = sum(values) / n
    
    if n < 2:
        return {'mean': mean, 'std': 0.0, 'n': n}
    
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std = math.sqrt(variance)
    
    return {'mean': mean, 'std': std, 'n': n}


def estimate_effect_from_pilot(csv1: Path, csv2: Path, metric: str) -> Optional[Tuple[float, Dict]]:
    """
    Estimate effect size from pilot data.
    
    Returns (effect_size, details_dict) or None on error.
    """
    values1 = load_csv_metric(csv1, metric)
    values2 = load_csv_metric(csv2, metric)
    
    if not values1 or not values2:
        return None
    
    stats1 = calculate_statistics(values1)
    stats2 = calculate_statistics(values2)
    
    effect = cohens_d(
        stats1['mean'], stats2['mean'],
        stats1['std'], stats2['std'],
        stats1['n'], stats2['n']
    )
    
    details = {
        'group1': {'file': csv1.name, **stats1},
        'group2': {'file': csv2.name, **stats2},
        'effect_size': effect,
        'interpretation': interpret_effect_size(effect)
    }
    
    return effect, details


def print_sample_size_report(effect_size: float, power: float = 0.8, alpha: float = 0.05):
    """Print formatted sample size requirements."""
    n = sample_size_two_sample_ttest(effect_size, power, alpha)
    
    if n < 0:
        return
    
    print("=" * 70)
    print("SAMPLE SIZE CALCULATION")
    print("=" * 70)
    print(f"Effect Size (Cohen's d): {effect_size:.3f} ({interpret_effect_size(effect_size)})")
    print(f"Desired Power: {power:.2f} ({int(power*100)}%)")
    print(f"Significance Level (α): {alpha:.3f}")
    print(f"Test Type: Two-sample t-test (two-tailed)")
    print()
    print(f"Required Sample Size: n = {n} per group")
    print(f"Total Observations: {n * 2}")
    print()
    
    # Show what actual power would be with this n
    actual = actual_power(n, effect_size, alpha)
    print(f"Actual Power: {actual:.3f} ({int(actual*100)}%)")
    print()
    
    # Show alternative scenarios
    print("Alternative Scenarios:")
    print("-" * 70)
    for pwr in [0.7, 0.8, 0.9]:
        n_alt = sample_size_two_sample_ttest(effect_size, pwr, alpha)
        print(f"  Power = {pwr:.1f}: n = {n_alt} per group (total {n_alt*2})")
    print()


def print_effect_size_report(n: int, power: float = 0.8, alpha: float = 0.05):
    """Print minimum detectable effect given sample size."""
    mde = minimum_detectable_effect(n, power, alpha)
    
    if mde == float('inf'):
        print("Error: Sample size too small (n must be > 2)", file=sys.stderr)
        return
    
    print("=" * 70)
    print("MINIMUM DETECTABLE EFFECT")
    print("=" * 70)
    print(f"Sample Size: n = {n} per group")
    print(f"Desired Power: {power:.2f} ({int(power*100)}%)")
    print(f"Significance Level (α): {alpha:.3f}")
    print()
    print(f"Minimum Detectable Effect: d = {mde:.3f} ({interpret_effect_size(mde)})")
    print()
    print("Interpretation:")
    print(f"  With {n} samples per group, you can reliably detect effects of")
    print(f"  size {mde:.3f} or larger with {int(power*100)}% power.")
    print()
    
    # Show what smaller/larger sample sizes could detect
    print("Alternative Sample Sizes:")
    print("-" * 70)
    for n_alt in [10, 20, 30, 50, 100]:
        if n_alt == n:
            continue
        mde_alt = minimum_detectable_effect(n_alt, power, alpha)
        print(f"  n = {n_alt}: minimum detectable effect = {mde_alt:.3f} ({interpret_effect_size(mde_alt)})")
    print()


def print_pilot_analysis(csv1: Path, csv2: Path, metric: str, power: float = 0.8, alpha: float = 0.05):
    """Analyze pilot data and recommend sample size."""
    result = estimate_effect_from_pilot(csv1, csv2, metric)
    
    if not result:
        print("Error: Could not analyze pilot data", file=sys.stderr)
        return
    
    effect_size, details = result
    
    print("=" * 70)
    print("PILOT DATA ANALYSIS")
    print("=" * 70)
    print(f"Metric: {metric}")
    print()
    
    # Group statistics
    for group_name in ['group1', 'group2']:
        g = details[group_name]
        print(f"{group_name.upper()}: {g['file']}")
        print(f"  Sample Size: n = {g['n']}")
        print(f"  Mean: {g['mean']:.2f}")
        print(f"  Std Dev: {g['std']:.2f}")
        print()
    
    # Effect size
    print(f"Observed Effect Size: d = {effect_size:.3f} ({details['interpretation']})")
    print()
    
    if effect_size < 0.01:
        print("Warning: Effect size is negligible. Consider:")
        print("  - Increasing treatment strength")
        print("  - Using more sensitive measurements")
        print("  - Verifying experimental setup")
        print()
        return
    
    # Recommended sample size
    n = sample_size_two_sample_ttest(effect_size, power, alpha)
    print(f"Recommended Sample Size: n = {n} per group (total {n*2})")
    print(f"This provides {int(power*100)}% power to detect the observed effect.")
    print()
    
    # Current power
    current_n = min(details['group1']['n'], details['group2']['n'])
    current_power = actual_power(current_n, effect_size, alpha)
    print(f"Current Power (pilot): {current_power:.3f} ({int(current_power*100)}%)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Power Analysis Calculator for Linux Reality Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate required sample size for medium effect
  python3 power_analysis.py --effect-size 0.5

  # Estimate effect from pilot data
  python3 power_analysis.py --pilot data/baseline.csv data/optimized.csv --metric runtime_ns

  # Find minimum detectable effect
  python3 power_analysis.py --sample-size 30

  # Full analysis with custom power
  python3 power_analysis.py --pilot data/exp1.csv data/exp2.csv --metric runtime_ns --power 0.9
        """
    )
    
    parser.add_argument('--effect-size', type=float,
                       help='Expected effect size (Cohen\'s d) to detect')
    parser.add_argument('--sample-size', type=int,
                       help='Sample size per group (calculate minimum detectable effect)')
    parser.add_argument('--pilot', nargs=2, metavar='CSV',
                       help='Two CSV files with pilot data for effect size estimation')
    parser.add_argument('--metric', type=str, default='runtime_ns',
                       help='Metric column name for pilot analysis (default: runtime_ns)')
    parser.add_argument('--power', type=float, default=0.8,
                       help='Desired statistical power (default: 0.8)')
    parser.add_argument('--alpha', type=float, default=0.05,
                       help='Significance level (default: 0.05)')
    
    args = parser.parse_args()
    
    # Validate power and alpha
    if not (0 < args.power < 1):
        print("Error: Power must be between 0 and 1", file=sys.stderr)
        return 1
    
    if not (0 < args.alpha < 1):
        print("Error: Alpha must be between 0 and 1", file=sys.stderr)
        return 1
    
    # Determine mode
    if args.pilot:
        # Pilot data analysis
        csv1, csv2 = Path(args.pilot[0]), Path(args.pilot[1])
        if not csv1.exists() or not csv2.exists():
            print(f"Error: Pilot data files not found", file=sys.stderr)
            return 1
        print_pilot_analysis(csv1, csv2, args.metric, args.power, args.alpha)
    
    elif args.effect_size is not None:
        # Sample size calculation
        if args.effect_size <= 0:
            print("Error: Effect size must be positive", file=sys.stderr)
            return 1
        print_sample_size_report(args.effect_size, args.power, args.alpha)
    
    elif args.sample_size is not None:
        # Minimum detectable effect
        if args.sample_size <= 2:
            print("Error: Sample size must be > 2", file=sys.stderr)
            return 1
        print_effect_size_report(args.sample_size, args.power, args.alpha)
    
    else:
        # Default: show examples for common scenarios
        print("=" * 70)
        print("POWER ANALYSIS QUICK REFERENCE")
        print("=" * 70)
        print()
        print("Sample sizes required for different effect sizes (power=0.8, α=0.05):")
        print("-" * 70)
        for d in [0.2, 0.3, 0.5, 0.8, 1.0]:
            n = sample_size_two_sample_ttest(d, 0.8, 0.05)
            print(f"  d = {d:.1f} ({interpret_effect_size(d):>10}): n = {n:>3} per group")
        print()
        print("Use --help for usage examples")
        print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
