#!/usr/bin/env python3
"""
JSON Export Tool for LRC

Exports experiment results to JSON format for:
- Machine-readable access
- Programmatic analysis
- Integration with other tools
- Web dashboards
"""

import json
import csv
import sys
from pathlib import Path

def csv_to_json(csv_file, output_file=None, include_metadata=True):
    """Convert CSV results to JSON format"""
    
    # Read CSV data
    rows = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            # Convert numeric fields
            converted_row = {}
            for key, value in row.items():
                try:
                    # Try to convert to number
                    if '.' in value:
                        converted_row[key] = float(value)
                    else:
                        converted_row[key] = int(value)
                except (ValueError, AttributeError):
                    converted_row[key] = value
            
            rows.append(converted_row)
    
    # Build JSON structure
    result = {
        'format_version': '1.0',
        'source_file': str(csv_file),
        'row_count': len(rows),
        'columns': fieldnames,
        'data': rows
    }
    
    # Add metadata if available
    if include_metadata:
        metadata_file = Path(csv_file).parent / f"{Path(csv_file).stem}_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                result['metadata'] = json.load(f)
    
    # Calculate summary statistics
    if rows:
        result['summary'] = calculate_summary(rows)
    
    # Write output
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        return output_file
    else:
        return json.dumps(result, indent=2)

def calculate_summary(rows):
    """Calculate summary statistics for numeric columns"""
    summary = {}
    
    # Find numeric columns
    if not rows:
        return summary
    
    numeric_cols = []
    for key, value in rows[0].items():
        if isinstance(value, (int, float)):
            numeric_cols.append(key)
    
    # Calculate stats for each numeric column
    for col in numeric_cols:
        values = [row[col] for row in rows if col in row and isinstance(row[col], (int, float))]
        
        if values:
            summary[col] = {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': sum(values) / len(values),
                'sum': sum(values)
            }
            
            # Calculate median and std if we have enough data
            if len(values) >= 2:
                sorted_vals = sorted(values)
                mid = len(values) // 2
                if len(values) % 2 == 0:
                    summary[col]['median'] = (sorted_vals[mid-1] + sorted_vals[mid]) / 2
                else:
                    summary[col]['median'] = sorted_vals[mid]
                
                # Standard deviation
                mean_val = summary[col]['mean']
                variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
                summary[col]['std'] = variance ** 0.5
                summary[col]['cv'] = (summary[col]['std'] / summary[col]['mean']) * 100 if summary[col]['mean'] != 0 else 0
    
    return summary

def export_multiple_csv_to_json(csv_files, output_file):
    """Export multiple CSV files to a single JSON"""
    results = []
    
    for csv_file in csv_files:
        try:
            data = json.loads(csv_to_json(csv_file, output_file=None, include_metadata=True))
            results.append(data)
        except Exception as e:
            print(f"Warning: Could not process {csv_file}: {e}", file=sys.stderr)
    
    combined = {
        'format_version': '1.0',
        'experiments': results,
        'total_experiments': len(results)
    }
    
    with open(output_file, 'w') as f:
        json.dump(combined, f, indent=2)
    
    return output_file

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Export LRC results to JSON')
    parser.add_argument('csv_files', nargs='+', help='CSV file(s) to export')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--no-metadata', action='store_true', help='Exclude metadata')
    parser.add_argument('--pretty', '-p', action='store_true', help='Pretty print to stdout')
    parser.add_argument('--combine', '-c', action='store_true', help='Combine multiple CSVs into one JSON')
    
    args = parser.parse_args()
    
    try:
        if args.combine and len(args.csv_files) > 1:
            # Combine multiple CSVs
            if not args.output:
                print("Error: --output required when combining multiple files", file=sys.stderr)
                sys.exit(1)
            
            output = export_multiple_csv_to_json(args.csv_files, args.output)
            print(f"Exported {len(args.csv_files)} files to: {output}")
            
        elif len(args.csv_files) == 1:
            # Single CSV export
            if args.output:
                csv_to_json(args.csv_files[0], args.output, include_metadata=not args.no_metadata)
                print(f"Exported to: {args.output}")
            else:
                # Print to stdout
                json_output = csv_to_json(args.csv_files[0], include_metadata=not args.no_metadata)
                print(json_output)
        else:
            print("Error: Specify --combine to export multiple CSVs, or provide single CSV", file=sys.stderr)
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
