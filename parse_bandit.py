import json

# Load the bandit report
with open('bandit-report-fixed.json', 'r') as f:
    data = json.load(f)

# Print high severity issues
print("HIGH SEVERITY ISSUES:")
print("=" * 80)
high_issues = [r for r in data['results'] if r['issue_severity'] == 'HIGH']
print(f"Total high severity issues: {len(high_issues)}")
for issue in high_issues:
    print(f"\nFile: {issue['filename']}")
    print(f"Line: {issue['line_number']}")
    print(f"Issue: {issue['issue_text']}")
    print(f"Test ID: {issue['test_id']}")
    print("-" * 40)

# Also check metrics
print("\n\nSUMMARY METRICS:")
print("=" * 80)
metrics = data['metrics']['_totals']
print(f"High severity: {metrics['SEVERITY.HIGH']}")
print(f"Medium severity: {metrics['SEVERITY.MEDIUM']}")
print(f"Low severity: {metrics['SEVERITY.LOW']}")
