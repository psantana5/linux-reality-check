#!/usr/bin/env python3
"""
Metadata Capture System for LRC

Captures complete system information for reproducibility.
Includes: kernel, CPU, timestamp, git commit, environment.
"""

import json
import subprocess
import sys
import os
import platform
import datetime
from pathlib import Path

def get_git_info(repo_path="."):
    """Get git commit hash and status"""
    try:
        os.chdir(repo_path)
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], 
                                        stderr=subprocess.DEVNULL).decode().strip()
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                        stderr=subprocess.DEVNULL).decode().strip()
        
        # Check if working tree is clean
        status = subprocess.check_output(['git', 'status', '--porcelain'],
                                        stderr=subprocess.DEVNULL).decode().strip()
        is_clean = len(status) == 0
        
        return {
            'commit': commit,
            'commit_short': commit[:8],
            'branch': branch,
            'clean': is_clean,
            'uncommitted_changes': not is_clean
        }
    except:
        return {
            'commit': None,
            'commit_short': None,
            'branch': None,
            'clean': None,
            'uncommitted_changes': None
        }

def get_cpu_info():
    """Get detailed CPU information"""
    info = {}
    
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'model name' in line:
                    info['model'] = line.split(':')[1].strip()
                    break
        
        # CPU count
        info['cores'] = os.cpu_count()
        
        # CPU frequency
        if os.path.exists('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'):
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq') as f:
                freq_khz = int(f.read().strip())
                info['frequency_mhz'] = freq_khz / 1000
        
        # CPU governor
        if os.path.exists('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'):
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor') as f:
                info['governor'] = f.read().strip()
                
    except Exception as e:
        info['error'] = str(e)
    
    return info

def get_memory_info():
    """Get memory information"""
    info = {}
    
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemTotal' in line:
                    kb = int(line.split()[1])
                    info['total_mb'] = kb // 1024
                    info['total_gb'] = kb // (1024 * 1024)
                    break
    except Exception as e:
        info['error'] = str(e)
    
    return info

def get_numa_info():
    """Get NUMA topology information"""
    info = {
        'available': False,
        'nodes': 0
    }
    
    try:
        import glob
        nodes = glob.glob('/sys/devices/system/node/node*')
        if len(nodes) > 1:
            info['available'] = True
            info['nodes'] = len(nodes)
    except:
        pass
    
    return info

def get_kernel_info():
    """Get kernel information"""
    return {
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine()
    }

def get_perf_info():
    """Get perf configuration"""
    info = {}
    
    try:
        if os.path.exists('/proc/sys/kernel/perf_event_paranoid'):
            with open('/proc/sys/kernel/perf_event_paranoid') as f:
                info['paranoid_level'] = int(f.read().strip())
    except:
        pass
    
    return info

def get_environment_info():
    """Get relevant environment variables"""
    relevant_vars = [
        'USER', 'HOSTNAME', 'SHELL', 'TERM',
        'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
        'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'
    ]
    
    return {var: os.environ.get(var) for var in relevant_vars if var in os.environ}

def capture_metadata(experiment_name=None, extra_info=None):
    """Capture complete system metadata"""
    
    metadata = {
        'lrc_version': '2.0',
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
        'timestamp_unix': int(datetime.datetime.utcnow().timestamp()),
        
        'experiment': {
            'name': experiment_name,
            'extra': extra_info or {}
        },
        
        'system': {
            'hostname': platform.node(),
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor()
        },
        
        'kernel': get_kernel_info(),
        'cpu': get_cpu_info(),
        'memory': get_memory_info(),
        'numa': get_numa_info(),
        'perf': get_perf_info(),
        
        'git': get_git_info(),
        'environment': get_environment_info(),
        
        'python': {
            'version': platform.python_version(),
            'implementation': platform.python_implementation()
        }
    }
    
    return metadata

def save_metadata(metadata, filename):
    """Save metadata to JSON file"""
    with open(filename, 'w') as f:
        json.dump(metadata, f, indent=2)

def load_metadata(filename):
    """Load metadata from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)

def print_metadata_summary(metadata):
    """Print human-readable metadata summary"""
    print("═" * 70)
    print("EXPERIMENT METADATA")
    print("═" * 70)
    print()
    
    if metadata['experiment']['name']:
        print(f"Experiment: {metadata['experiment']['name']}")
    print(f"Timestamp:  {metadata['timestamp']}")
    print()
    
    print("System:")
    print(f"  Hostname:   {metadata['system']['hostname']}")
    print(f"  Platform:   {metadata['system']['platform']} {metadata['system']['platform_release']}")
    print(f"  Arch:       {metadata['system']['architecture']}")
    print()
    
    print("Kernel:")
    print(f"  Release:    {metadata['kernel']['release']}")
    print()
    
    cpu = metadata['cpu']
    print("CPU:")
    if 'model' in cpu:
        print(f"  Model:      {cpu['model']}")
    print(f"  Cores:      {cpu.get('cores', 'unknown')}")
    if 'governor' in cpu:
        print(f"  Governor:   {cpu['governor']}")
    if 'frequency_mhz' in cpu:
        print(f"  Frequency:  {cpu['frequency_mhz']:.0f} MHz")
    print()
    
    mem = metadata['memory']
    if 'total_gb' in mem:
        print(f"Memory:     {mem['total_gb']} GB")
        print()
    
    numa = metadata['numa']
    if numa['available']:
        print(f"NUMA:       {numa['nodes']} nodes")
        print()
    
    git = metadata['git']
    if git['commit']:
        print("Git:")
        print(f"  Commit:     {git['commit_short']} ({git['branch']})")
        if not git['clean']:
            print(f"  Status:     ⚠ Uncommitted changes")
        else:
            print(f"  Status:     ✓ Clean")
        print()
    
    print(f"LRC Version: {metadata['lrc_version']}")
    print("═" * 70)

def fingerprint_system():
    """Generate unique system fingerprint"""
    metadata = capture_metadata()
    
    # Create fingerprint from key system characteristics
    fingerprint_data = {
        'cpu_model': metadata['cpu'].get('model', ''),
        'cpu_cores': metadata['cpu'].get('cores', 0),
        'memory_gb': metadata['memory'].get('total_gb', 0),
        'kernel_release': metadata['kernel']['release'],
        'architecture': metadata['system']['architecture']
    }
    
    # Simple hash-based fingerprint
    import hashlib
    fp_string = json.dumps(fingerprint_data, sort_keys=True)
    fingerprint = hashlib.sha256(fp_string.encode()).hexdigest()[:16]
    
    return fingerprint, fingerprint_data

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Capture system metadata for reproducibility')
    parser.add_argument('--experiment', '-e', help='Experiment name')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--fingerprint', '-f', action='store_true', help='Show system fingerprint')
    parser.add_argument('--summary', '-s', action='store_true', help='Show summary only')
    
    args = parser.parse_args()
    
    if args.fingerprint:
        fingerprint, fp_data = fingerprint_system()
        print(f"System Fingerprint: {fingerprint}")
        print()
        print("Based on:")
        for key, value in fp_data.items():
            print(f"  {key}: {value}")
        sys.exit(0)
    
    metadata = capture_metadata(experiment_name=args.experiment)
    
    if args.summary:
        print_metadata_summary(metadata)
    else:
        print(json.dumps(metadata, indent=2))
    
    if args.output:
        save_metadata(metadata, args.output)
        print(f"\nMetadata saved to: {args.output}", file=sys.stderr)
