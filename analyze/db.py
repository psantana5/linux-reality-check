#!/usr/bin/env python3
"""
SQLite Result Database for Linux Reality Check
Provides persistent storage for all experimental results with full metadata.

Schema Design:
- systems: Hardware/software configuration fingerprints
- experiments: High-level experiment metadata (scenario, parameters, timestamp)
- runs: Individual measurement runs (raw data)
- metadata: Extended metadata (git, environment, etc.)

Features:
- Automatic experiment tracking
- Historical data queries
- Cross-experiment comparison
- Metadata linking
- Export to CSV/JSON

Usage:
  # Initialize database
  python3 analyze/db.py --init

  # Store experiment results
  python3 analyze/db.py --store data/experiment.csv --scenario test --metadata metadata.json

  # Query experiments
  python3 analyze/db.py --query "SELECT * FROM experiments WHERE scenario='cache_hierarchy'"

  # Export experiment
  python3 analyze/db.py --export 123 --output exported.csv

  # List all experiments
  python3 analyze/db.py --list

  # Compare experiments
  python3 analyze/db.py --compare 123 124 --metric runtime_ns
"""

import argparse
import csv
import json
import sqlite3
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Default database location
DEFAULT_DB_PATH = Path.home() / '.lrc' / 'results.db'

# Schema version for migrations
SCHEMA_VERSION = 1


def get_db_path(custom_path: Optional[str] = None) -> Path:
    """Get database path, creating directory if needed."""
    if custom_path:
        db_path = Path(custom_path)
    else:
        db_path = DEFAULT_DB_PATH
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_database(db_path: Path) -> sqlite3.Connection:
    """
    Initialize database with schema.
    Creates all tables if they don't exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Schema version tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # System configurations (hardware/software fingerprints)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS systems (
            system_id INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint TEXT UNIQUE NOT NULL,
            cpu_model TEXT,
            cpu_cores INTEGER,
            memory_gb REAL,
            kernel_version TEXT,
            architecture TEXT,
            numa_nodes INTEGER,
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Experiments (high-level runs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS experiments (
            experiment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_id INTEGER NOT NULL,
            scenario TEXT NOT NULL,
            git_commit TEXT,
            git_branch TEXT,
            git_dirty BOOLEAN,
            num_samples INTEGER,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (system_id) REFERENCES systems(system_id)
        )
    ''')
    
    # Individual runs (raw measurements)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            run_number INTEGER NOT NULL,
            workload_type TEXT,
            timestamp_ns BIGINT,
            runtime_ns BIGINT,
            voluntary_ctxt_switches INTEGER,
            nonvoluntary_ctxt_switches INTEGER,
            minor_page_faults INTEGER,
            major_page_faults INTEGER,
            start_cpu INTEGER,
            end_cpu INTEGER,
            custom_metrics TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        )
    ''')
    
    # Extended metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        )
    ''')
    
    # Tags for organization
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        )
    ''')
    
    # Indices for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_experiments_scenario ON experiments(scenario)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_experiments_started_at ON experiments(started_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_runs_experiment ON runs(experiment_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_runs_workload ON runs(workload_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_experiment ON tags(experiment_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag)')
    
    # Insert schema version
    cursor.execute('INSERT OR IGNORE INTO schema_version (version) VALUES (?)', (SCHEMA_VERSION,))
    
    conn.commit()
    return conn


def get_or_create_system(conn: sqlite3.Connection, metadata: Dict[str, Any]) -> int:
    """
    Get system_id for current system, creating entry if needed.
    Uses fingerprint to identify unique systems.
    """
    cursor = conn.cursor()
    
    # Extract system info from metadata
    system_info = metadata.get('system', {})
    cpu_info = metadata.get('cpu', {})
    memory_info = metadata.get('memory', {})
    kernel_info = metadata.get('kernel', {})
    numa_info = metadata.get('numa', {})
    
    # Create fingerprint
    fingerprint_data = f"{cpu_info.get('model', '')}-{cpu_info.get('physical_cores', 0)}-{memory_info.get('total_gb', 0)}-{kernel_info.get('version', '')}"
    fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    # Check if system exists
    cursor.execute('SELECT system_id FROM systems WHERE fingerprint = ?', (fingerprint,))
    row = cursor.fetchone()
    
    if row:
        return row[0]
    
    # Create new system entry
    cursor.execute('''
        INSERT INTO systems 
        (fingerprint, cpu_model, cpu_cores, memory_gb, kernel_version, 
         architecture, numa_nodes, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        fingerprint,
        cpu_info.get('model'),
        cpu_info.get('physical_cores'),
        memory_info.get('total_gb'),
        kernel_info.get('version'),
        system_info.get('architecture'),
        numa_info.get('nodes'),
        json.dumps(metadata)
    ))
    
    conn.commit()
    return cursor.lastrowid


def store_experiment(conn: sqlite3.Connection, 
                     csv_path: Path, 
                     scenario: str,
                     metadata: Optional[Dict] = None,
                     notes: Optional[str] = None,
                     tags: Optional[List[str]] = None) -> int:
    """
    Store experiment results from CSV file.
    Returns experiment_id.
    """
    cursor = conn.cursor()
    
    # Load metadata if not provided
    if metadata is None:
        metadata_path = csv_path.parent / f"{csv_path.stem}_metadata.json"
        if metadata_path.exists():
            with open(metadata_path) as f:
                metadata = json.load(f)
        else:
            metadata = {}
    
    # Get or create system
    system_id = get_or_create_system(conn, metadata)
    
    # Extract git info
    git_info = metadata.get('git', {})
    
    # Create experiment entry
    started_at = metadata.get('timestamp', datetime.utcnow().isoformat())
    
    cursor.execute('''
        INSERT INTO experiments 
        (system_id, scenario, git_commit, git_branch, git_dirty, 
         started_at, completed_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        system_id,
        scenario,
        git_info.get('commit'),
        git_info.get('branch'),
        git_info.get('has_uncommitted_changes', False),
        started_at,
        started_at,  # completed_at same as started for imported data
        notes
    ))
    
    experiment_id = cursor.lastrowid
    
    # Store runs from CSV
    num_samples = 0
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle optional custom metrics
            custom_metrics = {}
            for key in row.keys():
                if key not in ['run', 'workload_type', 'timestamp_ns', 'runtime_ns',
                             'voluntary_ctxt_switches', 'nonvoluntary_ctxt_switches',
                             'minor_page_faults', 'major_page_faults', 'start_cpu', 'end_cpu']:
                    custom_metrics[key] = row[key]
            
            cursor.execute('''
                INSERT INTO runs 
                (experiment_id, run_number, workload_type, timestamp_ns, runtime_ns,
                 voluntary_ctxt_switches, nonvoluntary_ctxt_switches,
                 minor_page_faults, major_page_faults, start_cpu, end_cpu, custom_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                experiment_id,
                int(row.get('run', num_samples)),
                row.get('workload_type'),
                int(row['timestamp_ns']) if row.get('timestamp_ns') else None,
                int(row['runtime_ns']) if row.get('runtime_ns') else None,
                int(row.get('voluntary_ctxt_switches', 0)),
                int(row.get('nonvoluntary_ctxt_switches', 0)),
                int(row.get('minor_page_faults', 0)),
                int(row.get('major_page_faults', 0)),
                int(row.get('start_cpu', -1)),
                int(row.get('end_cpu', -1)),
                json.dumps(custom_metrics) if custom_metrics else None
            ))
            num_samples += 1
    
    # Update sample count
    cursor.execute('UPDATE experiments SET num_samples = ? WHERE experiment_id = ?',
                  (num_samples, experiment_id))
    
    # Store extended metadata
    for key, value in metadata.items():
        if key not in ['system', 'cpu', 'memory', 'kernel', 'numa', 'git', 'timestamp']:
            cursor.execute('''
                INSERT INTO metadata (experiment_id, key, value)
                VALUES (?, ?, ?)
            ''', (experiment_id, key, json.dumps(value)))
    
    # Store tags
    if tags:
        for tag in tags:
            cursor.execute('''
                INSERT INTO tags (experiment_id, tag)
                VALUES (?, ?)
            ''', (experiment_id, tag))
    
    conn.commit()
    return experiment_id


def list_experiments(conn: sqlite3.Connection, 
                     scenario: Optional[str] = None,
                     limit: int = 20) -> List[Dict]:
    """List recent experiments with summary info."""
    cursor = conn.cursor()
    
    query = '''
        SELECT 
            e.experiment_id,
            e.scenario,
            e.num_samples,
            e.started_at,
            e.git_commit,
            s.cpu_model,
            s.kernel_version
        FROM experiments e
        JOIN systems s ON e.system_id = s.system_id
    '''
    
    params = []
    if scenario:
        query += ' WHERE e.scenario = ?'
        params.append(scenario)
    
    query += ' ORDER BY e.started_at DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'experiment_id': row[0],
            'scenario': row[1],
            'num_samples': row[2],
            'started_at': row[3],
            'git_commit': row[4],
            'cpu_model': row[5],
            'kernel_version': row[6]
        })
    
    return results


def export_experiment(conn: sqlite3.Connection, 
                      experiment_id: int,
                      output_path: Path,
                      format: str = 'csv') -> bool:
    """Export experiment to CSV or JSON."""
    cursor = conn.cursor()
    
    # Get runs
    cursor.execute('''
        SELECT run_number, workload_type, timestamp_ns, runtime_ns,
               voluntary_ctxt_switches, nonvoluntary_ctxt_switches,
               minor_page_faults, major_page_faults, start_cpu, end_cpu,
               custom_metrics
        FROM runs
        WHERE experiment_id = ?
        ORDER BY run_number
    ''', (experiment_id,))
    
    rows = cursor.fetchall()
    if not rows:
        return False
    
    if format == 'csv':
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['run', 'workload_type', 'timestamp_ns', 'runtime_ns',
                           'voluntary_ctxt_switches', 'nonvoluntary_ctxt_switches',
                           'minor_page_faults', 'major_page_faults', 'start_cpu', 'end_cpu'])
            
            for row in rows:
                writer.writerow(row[:10])  # Exclude custom_metrics for now
    
    elif format == 'json':
        data = {
            'experiment_id': experiment_id,
            'runs': []
        }
        
        for row in rows:
            run_data = {
                'run': row[0],
                'workload_type': row[1],
                'timestamp_ns': row[2],
                'runtime_ns': row[3],
                'voluntary_ctxt_switches': row[4],
                'nonvoluntary_ctxt_switches': row[5],
                'minor_page_faults': row[6],
                'major_page_faults': row[7],
                'start_cpu': row[8],
                'end_cpu': row[9]
            }
            
            if row[10]:  # custom_metrics
                run_data['custom_metrics'] = json.loads(row[10])
            
            data['runs'].append(run_data)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    return True


def print_experiments_table(experiments: List[Dict]):
    """Print experiments in formatted table."""
    if not experiments:
        print("No experiments found.")
        return
    
    print()
    print("=" * 100)
    print(f"{'ID':<8} {'Scenario':<25} {'Samples':<10} {'Date':<20} {'Git Commit':<12}")
    print("=" * 100)
    
    for exp in experiments:
        exp_id = exp['experiment_id']
        scenario = exp['scenario'][:24]
        samples = exp['num_samples'] or 0
        date = exp['started_at'][:19] if exp['started_at'] else 'N/A'
        commit = (exp['git_commit'][:10] if exp['git_commit'] else 'N/A')
        
        print(f"{exp_id:<8} {scenario:<25} {samples:<10} {date:<20} {commit:<12}")
    
    print("=" * 100)
    print()


def get_experiment_stats(conn: sqlite3.Connection, experiment_id: int) -> Optional[Dict]:
    """Get summary statistics for an experiment."""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            workload_type,
            COUNT(*) as count,
            AVG(runtime_ns) as mean_ns,
            MIN(runtime_ns) as min_ns,
            MAX(runtime_ns) as max_ns
        FROM runs
        WHERE experiment_id = ?
        GROUP BY workload_type
    ''', (experiment_id,))
    
    results = {}
    for row in cursor.fetchall():
        results[row[0]] = {
            'count': row[1],
            'mean_ns': row[2],
            'min_ns': row[3],
            'max_ns': row[4]
        }
    
    return results if results else None


def main():
    parser = argparse.ArgumentParser(
        description="SQLite Result Database for Linux Reality Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database
  python3 db.py --init

  # Store experiment
  python3 db.py --store data/experiment.csv --scenario cache_test

  # List recent experiments
  python3 db.py --list

  # Export experiment
  python3 db.py --export 123 --output exported.csv

  # Query database
  python3 db.py --query "SELECT * FROM experiments WHERE scenario='null_baseline'"
        """
    )
    
    parser.add_argument('--db', help='Database path (default: ~/.lrc/results.db)')
    parser.add_argument('--init', action='store_true', help='Initialize database')
    parser.add_argument('--store', help='Store CSV results in database')
    parser.add_argument('--scenario', help='Scenario name (required with --store)')
    parser.add_argument('--metadata', help='Metadata JSON file')
    parser.add_argument('--notes', help='Experiment notes')
    parser.add_argument('--tags', nargs='+', help='Tags for experiment')
    parser.add_argument('--list', action='store_true', help='List recent experiments')
    parser.add_argument('--list-scenario', help='List experiments for specific scenario')
    parser.add_argument('--limit', type=int, default=20, help='Limit for --list')
    parser.add_argument('--export', type=int, help='Export experiment ID')
    parser.add_argument('--output', help='Output file for export')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                       help='Export format (default: csv)')
    parser.add_argument('--query', help='Execute SQL query')
    parser.add_argument('--stats', type=int, help='Show statistics for experiment ID')
    
    args = parser.parse_args()
    
    # Get database connection
    db_path = get_db_path(args.db)
    
    if args.init:
        conn = init_database(db_path)
        print(f"Database initialized: {db_path}")
        conn.close()
        return 0
    
    # Open database
    if not db_path.exists():
        print(f"Error: Database not found: {db_path}", file=sys.stderr)
        print("Run with --init to create database", file=sys.stderr)
        return 1
    
    conn = sqlite3.connect(db_path)
    
    try:
        if args.store:
            if not args.scenario:
                print("Error: --scenario required with --store", file=sys.stderr)
                return 1
            
            csv_path = Path(args.store)
            if not csv_path.exists():
                print(f"Error: File not found: {csv_path}", file=sys.stderr)
                return 1
            
            # Load metadata if provided
            metadata = None
            if args.metadata:
                with open(args.metadata) as f:
                    metadata = json.load(f)
            
            exp_id = store_experiment(conn, csv_path, args.scenario, 
                                     metadata, args.notes, args.tags)
            print(f"Stored experiment {exp_id}: {args.scenario}")
            print(f"Database: {db_path}")
        
        elif args.list or args.list_scenario:
            experiments = list_experiments(conn, args.list_scenario, args.limit)
            print_experiments_table(experiments)
        
        elif args.export:
            if not args.output:
                print("Error: --output required with --export", file=sys.stderr)
                return 1
            
            output_path = Path(args.output)
            success = export_experiment(conn, args.export, output_path, args.format)
            
            if success:
                print(f"Exported experiment {args.export} to {output_path}")
            else:
                print(f"Error: Experiment {args.export} not found", file=sys.stderr)
                return 1
        
        elif args.stats:
            stats = get_experiment_stats(conn, args.stats)
            if stats:
                print(f"\nStatistics for experiment {args.stats}:")
                print("-" * 70)
                for workload, data in stats.items():
                    print(f"\n{workload}:")
                    print(f"  Samples: {data['count']}")
                    print(f"  Mean: {data['mean_ns']:.0f} ns")
                    print(f"  Range: [{data['min_ns']:.0f}, {data['max_ns']:.0f}] ns")
            else:
                print(f"Error: Experiment {args.stats} not found", file=sys.stderr)
                return 1
        
        elif args.query:
            cursor = conn.cursor()
            cursor.execute(args.query)
            
            rows = cursor.fetchall()
            if rows:
                # Print column names
                col_names = [desc[0] for desc in cursor.description]
                print('\t'.join(col_names))
                
                # Print rows
                for row in rows:
                    print('\t'.join(str(x) for x in row))
            else:
                print("No results.")
        
        else:
            parser.print_help()
    
    finally:
        conn.close()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
