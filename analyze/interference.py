#!/usr/bin/env python3
"""
Interference Studies Framework for Linux Reality Check

Orchestrates multi-process experiments to study performance interference
and resource contention. Tests how background workloads affect foreground
performance.

Features:
- Multi-process coordination
- Resource contention measurement
- Isolation analysis
- Automated experiment matrix

Usage:
  # Run cache interference study
  python3 analyze/interference.py --foreground cache_hierarchy \
      --background memory_bandwidth --duration 30

  # Test multiple background loads
  python3 analyze/interference.py --foreground null_baseline \
      --backgrounds cpu_intensive io_intensive --matrix

  # Measure isolation quality
  python3 analyze/interference.py --isolation-test cache_hierarchy \
      --num-neighbors 4
"""

import argparse
import csv
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
DATA_DIR = PROJECT_ROOT / "data"

class InterferenceStudy:
    def __init__(self):
        self.processes = []
        self.results = []
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def cleanup(self):
        """Kill all child processes."""
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                try:
                    proc.kill()
                except:
                    pass
        self.processes.clear()
    
    def run_scenario(self, scenario: str, background: bool = False) -> Optional[subprocess.Popen]:
        """
        Run a scenario as foreground or background process.
        
        Args:
            scenario: Scenario name (e.g., 'cache_hierarchy')
            background: If True, run in background and return process
                       If False, wait for completion
        
        Returns:
            Process object if background, None otherwise
        """
        scenario_path = SCENARIOS_DIR / scenario
        
        if not scenario_path.exists():
            print(f"Error: Scenario not found: {scenario}", file=sys.stderr)
            return None
        
        # Change to project root so scenarios can write to data/
        proc = subprocess.Popen(
            [str(scenario_path)],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        if background:
            self.processes.append(proc)
            return proc
        else:
            proc.wait()
            return None
    
    def measure_baseline(self, scenario: str, iterations: int = 5) -> Dict:
        """
        Measure baseline performance without interference.
        
        Returns:
            dict with mean, std, min, max runtime
        """
        print(f"Measuring baseline for {scenario}...")
        
        runtimes = []
        
        for i in range(iterations):
            start = time.time()
            self.run_scenario(scenario, background=False)
            end = time.time()
            
            runtime = end - start
            runtimes.append(runtime)
            print(f"  Run {i+1}/{iterations}: {runtime:.2f}s")
        
        mean = sum(runtimes) / len(runtimes)
        variance = sum((x - mean) ** 2 for x in runtimes) / (len(runtimes) - 1) if len(runtimes) > 1 else 0
        std = variance ** 0.5
        
        return {
            'mean': mean,
            'std': std,
            'min': min(runtimes),
            'max': max(runtimes),
            'runs': runtimes
        }
    
    def measure_with_interference(self, 
                                   foreground: str,
                                   background: List[str],
                                   iterations: int = 5) -> Dict:
        """
        Measure performance with background interference.
        
        Returns:
            dict with mean, std, min, max runtime under interference
        """
        print(f"Measuring {foreground} with interference from {background}...")
        
        runtimes = []
        
        for i in range(iterations):
            # Start background processes
            for bg in background:
                self.run_scenario(bg, background=True)
            
            # Give background processes time to start
            time.sleep(1)
            
            # Run foreground and measure
            start = time.time()
            self.run_scenario(foreground, background=False)
            end = time.time()
            
            runtime = end - start
            runtimes.append(runtime)
            
            # Kill background processes
            self.cleanup()
            
            print(f"  Run {i+1}/{iterations}: {runtime:.2f}s")
            
            # Cooldown between runs
            time.sleep(2)
        
        mean = sum(runtimes) / len(runtimes)
        variance = sum((x - mean) ** 2 for x in runtimes) / (len(runtimes) - 1) if len(runtimes) > 1 else 0
        std = variance ** 0.5
        
        return {
            'mean': mean,
            'std': std,
            'min': min(runtimes),
            'max': max(runtimes),
            'runs': runtimes
        }
    
    def run_interference_study(self,
                               foreground: str,
                               backgrounds: List[str],
                               output: Path,
                               iterations: int = 5):
        """
        Complete interference study with baseline and multiple backgrounds.
        
        Generates CSV with results.
        """
        results = []
        
        # Baseline measurement (no interference)
        baseline = self.measure_baseline(foreground, iterations)
        results.append({
            'foreground': foreground,
            'background': 'none',
            'mean_runtime': baseline['mean'],
            'std_runtime': baseline['std'],
            'slowdown': 1.0,
            'interference_pct': 0.0
        })
        
        # Measure with each background
        for bg in backgrounds:
            interfered = self.measure_with_interference(foreground, [bg], iterations)
            
            slowdown = interfered['mean'] / baseline['mean']
            interference_pct = (slowdown - 1.0) * 100
            
            results.append({
                'foreground': foreground,
                'background': bg,
                'mean_runtime': interfered['mean'],
                'std_runtime': interfered['std'],
                'slowdown': slowdown,
                'interference_pct': interference_pct
            })
            
            print(f"\n{bg}: {slowdown:.2f}x slowdown ({interference_pct:.1f}% interference)")
        
        # Write results
        with open(output, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'foreground', 'background', 'mean_runtime', 'std_runtime',
                'slowdown', 'interference_pct'
            ])
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\nResults saved to {output}")
        
        return results
    
    def run_isolation_test(self,
                           scenario: str,
                           num_neighbors: int,
                           output: Path,
                           iterations: int = 5):
        """
        Test how well processes are isolated from each other.
        
        Runs multiple copies of the same scenario simultaneously and
        measures interference.
        """
        print(f"Isolation Test: {num_neighbors}x {scenario}")
        print("=" * 60)
        
        # Baseline: single instance
        baseline = self.measure_baseline(scenario, iterations)
        
        # With neighbors: run N copies simultaneously
        print(f"\nRunning {num_neighbors} simultaneous instances...")
        
        neighbor_runtimes = []
        
        for i in range(iterations):
            # Start N-1 neighbors
            for j in range(num_neighbors - 1):
                self.run_scenario(scenario, background=True)
            
            time.sleep(1)
            
            # Run and measure the Nth instance
            start = time.time()
            self.run_scenario(scenario, background=False)
            end = time.time()
            
            runtime = end - start
            neighbor_runtimes.append(runtime)
            
            self.cleanup()
            print(f"  Run {i+1}/{iterations}: {runtime:.2f}s")
            
            time.sleep(2)
        
        mean = sum(neighbor_runtimes) / len(neighbor_runtimes)
        slowdown = mean / baseline['mean']
        
        print(f"\nIsolation Analysis:")
        print(f"  Baseline (1 instance): {baseline['mean']:.2f}s")
        print(f"  With {num_neighbors} instances: {mean:.2f}s")
        print(f"  Slowdown: {slowdown:.2f}x")
        print(f"  Interference: {(slowdown - 1.0) * 100:.1f}%")
        
        # Ideal scaling: no slowdown
        # Reality: some slowdown due to shared resources
        isolation_quality = max(0, (1.0 - (slowdown - 1.0)) * 100)
        print(f"  Isolation Quality: {isolation_quality:.1f}%")
        
        # Write results
        with open(output, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['num_instances', 'mean_runtime', 'slowdown', 'interference_pct', 'isolation_quality'])
            writer.writerow([1, baseline['mean'], 1.0, 0.0, 100.0])
            writer.writerow([num_neighbors, mean, slowdown, (slowdown - 1.0) * 100, isolation_quality])
        
        print(f"\nResults saved to {output}")


def main():
    parser = argparse.ArgumentParser(
        description="Interference Studies Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single interference test
  python3 interference.py --foreground cache_hierarchy \\
      --background lock_scaling

  # Multiple backgrounds
  python3 interference.py --foreground null_baseline \\
      --backgrounds lock_scaling syscall_overhead realistic_patterns

  # Isolation test
  python3 interference.py --isolation-test cache_hierarchy \\
      --num-neighbors 4

  # Full study with output
  python3 interference.py --foreground cache_hierarchy \\
      --backgrounds lock_scaling syscall_overhead \\
      --output interference_results.csv
        """
    )
    
    parser.add_argument('--foreground', help='Foreground scenario to measure')
    parser.add_argument('--background', help='Single background scenario')
    parser.add_argument('--backgrounds', nargs='+', help='Multiple background scenarios')
    parser.add_argument('--isolation-test', help='Run isolation test for scenario')
    parser.add_argument('--num-neighbors', type=int, default=4,
                       help='Number of simultaneous instances for isolation test')
    parser.add_argument('--iterations', type=int, default=5,
                       help='Number of iterations per test')
    parser.add_argument('--output', help='Output CSV file')
    
    args = parser.parse_args()
    
    # Determine output file
    if args.output:
        output = Path(args.output)
    else:
        output = DATA_DIR / "interference_results.csv"
    
    with InterferenceStudy() as study:
        if args.isolation_test:
            # Isolation test
            study.run_isolation_test(
                args.isolation_test,
                args.num_neighbors,
                output,
                args.iterations
            )
        
        elif args.foreground:
            # Interference study
            backgrounds = []
            if args.background:
                backgrounds.append(args.background)
            if args.backgrounds:
                backgrounds.extend(args.backgrounds)
            
            if not backgrounds:
                print("Error: Need --background or --backgrounds", file=sys.stderr)
                return 1
            
            study.run_interference_study(
                args.foreground,
                backgrounds,
                output,
                args.iterations
            )
        
        else:
            parser.print_help()
            return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
