#!/usr/bin/env python3
"""
metadata.py - Experiment metadata tracking

Purpose:
  Capture system configuration and experiment parameters
  for reproducibility tracking.
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def get_system_info() -> Dict[str, Any]:
    """Collect system information."""
    info = {}
    
    # Kernel
    try:
        info['kernel'] = subprocess.check_output(['uname', '-r']).decode().strip()
        info['kernel_full'] = subprocess.check_output(['uname', '-a']).decode().strip()
    except:
        info['kernel'] = 'unknown'
    
    # CPU
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'model name' in line:
                    info['cpu_model'] = line.split(':')[1].strip()
                    break
        
        info['cpu_count'] = os.cpu_count()
    except:
        info['cpu_model'] = 'unknown'
        info['cpu_count'] = 0
    
    # CPU Governor
    try:
        gov_file = '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'
        if os.path.exists(gov_file):
            with open(gov_file, 'r') as f:
                info['cpu_governor'] = f.read().strip()
    except:
        info['cpu_governor'] = 'unknown'
    
    # Load average
    try:
        with open('/proc/loadavg', 'r') as f:
            load = f.read().strip().split()
            info['load_avg'] = {
                '1min': float(load[0]),
                '5min': float(load[1]),
                '15min': float(load[2])
            }
    except:
        info['load_avg'] = {}
    
    # Memory
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = {}
            for line in f:
                if ':' in line:
                    key, value = line.split(':', 1)
                    meminfo[key.strip()] = value.strip()
        
        info['memory_total_kb'] = meminfo.get('MemTotal', 'unknown')
        info['memory_available_kb'] = meminfo.get('MemAvailable', 'unknown')
    except:
        info['memory_total_kb'] = 'unknown'
    
    # ASLR
    try:
        with open('/proc/sys/kernel/randomize_va_space', 'r') as f:
            info['aslr'] = int(f.read().strip())
    except:
        info['aslr'] = 'unknown'
    
    # Swappiness
    try:
        with open('/proc/sys/vm/swappiness', 'r') as f:
            info['swappiness'] = int(f.read().strip())
    except:
        info['swappiness'] = 'unknown'
    
    return info


def create_metadata(experiment_name: str, 
                   iterations: int = None,
                   runs: int = None,
                   additional_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create experiment metadata."""
    metadata = {
        'experiment': {
            'name': experiment_name,
            'timestamp': datetime.now().isoformat(),
            'iterations': iterations,
            'runs': runs,
        },
        'system': get_system_info(),
    }
    
    if additional_params:
        metadata['parameters'] = additional_params
    
    return metadata


def save_metadata(metadata: Dict[str, Any], output_dir: Path):
    """Save metadata to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    exp_name = metadata['experiment']['name']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = output_dir / f"{exp_name}_{timestamp}_metadata.json"
    
    with open(filename, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Metadata saved to: {filename}")
    return filename


def load_metadata(filepath: Path) -> Dict[str, Any]:
    """Load metadata from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def print_metadata(metadata: Dict[str, Any]):
    """Print metadata in human-readable format."""
    print(f"\n{'='*70}")
    print(f"Experiment Metadata")
    print(f"{'='*70}\n")
    
    exp = metadata.get('experiment', {})
    print(f"Experiment:")
    print(f"  Name:       {exp.get('name', 'unknown')}")
    print(f"  Timestamp:  {exp.get('timestamp', 'unknown')}")
    if exp.get('iterations'):
        print(f"  Iterations: {exp.get('iterations')}")
    if exp.get('runs'):
        print(f"  Runs:       {exp.get('runs')}")
    
    sys_info = metadata.get('system', {})
    print(f"\nSystem:")
    print(f"  Kernel:     {sys_info.get('kernel', 'unknown')}")
    print(f"  CPU:        {sys_info.get('cpu_model', 'unknown')}")
    print(f"  Cores:      {sys_info.get('cpu_count', 'unknown')}")
    print(f"  Governor:   {sys_info.get('cpu_governor', 'unknown')}")
    
    if 'load_avg' in sys_info:
        load = sys_info['load_avg']
        print(f"  Load (1m):  {load.get('1min', 'unknown')}")
    
    print(f"  ASLR:       {sys_info.get('aslr', 'unknown')}")
    print(f"  Swappiness: {sys_info.get('swappiness', 'unknown')}")
    
    if 'parameters' in metadata:
        print(f"\nParameters:")
        for key, value in metadata['parameters'].items():
            print(f"  {key}: {value}")
    
    print()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <experiment_name> [output_dir]", file=sys.stderr)
        print(f"\nExample:", file=sys.stderr)
        print(f"  {sys.argv[0]} pinned_test data/", file=sys.stderr)
        sys.exit(1)
    
    exp_name = sys.argv[1]
    output_dir = Path(sys.argv[2] if len(sys.argv) > 2 else 'data')
    
    metadata = create_metadata(exp_name)
    print_metadata(metadata)
    save_metadata(metadata, output_dir)


if __name__ == '__main__':
    main()
