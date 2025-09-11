#!/usr/bin/env python3
"""Compare security scan results before and after fixes."""

import json

def main():
    # Load before and after results
    with open('security_scan_results.json', 'r') as f:
        before = json.load(f)
    
    with open('security_scan_after_fixes.json', 'r') as f:
        after = json.load(f)
    
    # Calculate improvements
    before_count = len(before['results'])
    after_count = len(after['results'])
    improvement = before_count - after_count
    reduction_percent = round((improvement / before_count) * 100, 1)
    
    print("🔒 SECURITY SCAN COMPARISON")
    print("=" * 40)
    print(f"BEFORE - Total Issues: {before_count}")
    print(f"AFTER - Total Issues: {after_count}")
    print(f"IMPROVEMENT: {improvement} issues fixed")
    print(f"REDUCTION: {reduction_percent}%")
    
    # Show severity breakdown
    print("\n📊 SEVERITY BREAKDOWN:")
    print("-" * 20)
    
    for severity in ['HIGH', 'MEDIUM', 'LOW']:
        before_sev = sum(1 for r in before['results'] if r['issue_severity'] == severity)
        after_sev = sum(1 for r in after['results'] if r['issue_severity'] == severity)
        sev_improvement = before_sev - after_sev
        print(f"{severity}: {before_sev} → {after_sev} ({sev_improvement:+d})")

if __name__ == "__main__":
    main()
















