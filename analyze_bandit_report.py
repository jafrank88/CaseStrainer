#!/usr/bin/env python3
"""
Analyze Bandit security report and provide summary
"""

import json
from collections import Counter

def analyze_bandit_report(report_file):
    """Analyze the Bandit security report."""
    with open(report_file, 'r') as f:
        data = json.load(f)
    
    print("🔒 BANDIT SECURITY REPORT ANALYSIS")
    print("=" * 50)
    
    # Overall statistics
    print(f"Total issues found: {len(data['results'])}")
    print(f"Files with syntax errors: {len(data['errors'])}")
    print(f"Total lines of code: {data['metrics']['_totals']['loc']}")
    
    # Severity breakdown
    high_severity = [r for r in data['results'] if r['issue_severity'] == 'HIGH']
    medium_severity = [r for r in data['results'] if r['issue_severity'] == 'MEDIUM']
    low_severity = [r for r in data['results'] if r['issue_severity'] == 'LOW']
    
    print(f"\nSeverity Breakdown:")
    print(f"  High: {len(high_severity)}")
    print(f"  Medium: {len(medium_severity)}")
    print(f"  Low: {len(low_severity)}")
    
    # Issue types
    issue_types = Counter([r['test_name'] for r in data['results']])
    print(f"\nTop Issue Types:")
    for issue_type, count in issue_types.most_common(10):
        print(f"  {issue_type}: {count}")
    
    # Files with most issues
    file_issues = Counter([r['filename'] for r in data['results']])
    print(f"\nFiles with Most Issues:")
    for filename, count in file_issues.most_common(5):
        print(f"  {filename}: {count}")
    
    # Critical issues (High severity)
    if high_severity:
        print(f"\n🚨 CRITICAL ISSUES (High Severity):")
        for issue in high_severity[:5]:  # Show first 5
            print(f"  {issue['filename']}:{issue['line_number']} - {issue['issue_text']}")
        if len(high_severity) > 5:
            print(f"  ... and {len(high_severity) - 5} more")
    
    # Medium severity issues
    if medium_severity:
        print(f"\n⚠️  MEDIUM SEVERITY ISSUES:")
        for issue in medium_severity[:3]:  # Show first 3
            print(f"  {issue['filename']}:{issue['line_number']} - {issue['issue_text']}")
        if len(medium_severity) > 3:
            print(f"  ... and {len(medium_severity) - 3} more")
    
    # Common patterns
    print(f"\n🔍 COMMON SECURITY PATTERNS:")
    patterns = {
        'pickle': 'Unsafe deserialization',
        'subprocess': 'Command injection risks',
        'requests': 'Missing timeouts',
        'random': 'Weak random generation',
        'sql': 'SQL injection risks',
        'shell': 'Shell command execution'
    }
    
    for pattern, description in patterns.items():
        count = sum(1 for r in data['results'] if pattern in r['test_name'].lower())
        if count > 0:
            print(f"  {description}: {count} instances")

if __name__ == "__main__":
    import sys
    report_file = sys.argv[1] if len(sys.argv) > 1 else 'bandit-report.json'
    analyze_bandit_report(report_file) 