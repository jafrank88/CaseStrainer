import json
import re

# Check remaining name_mismatch_verified issues for abbreviation patterns
report = json.load(open('batch_report.json', encoding='utf-8'))
nmv_issues = [i for i in report['all_issues'] if i['type'] == 'name_mismatch_verified']

print('Analyzing remaining name_mismatch_verified issues for abbreviation patterns:')
print('=' * 70)

for iss in nmv_issues:
    detail = iss.get('detail', '')
    doc = iss.get('doc', '')
    
    # Extract submitted and canonical names
    if 'submitted=' in detail and 'canonical=' in detail:
        parts = detail.split(' | ')
        submitted = parts[0].replace("submitted=", "").strip("'\"")
        canonical = parts[1].replace("canonical=", "").strip("'\"")
        
        print(f'\nDocument: {doc}')
        print(f'Submitted: {submitted}')
        print(f'Canonical: {canonical}')
        
        # Look for common abbreviation patterns
        # Check for I. N. S vs INS pattern
        if 'I. N. S' in submitted and 'I.N.S.' in canonical:
            print('→ Pattern: I. N. S vs I.N.S. (spacing issue)')
        
        # Check for Comm'n vs Commission
        if 'Comm\'n' in canonical:
            print('→ Pattern: Comm\'n should expand to Commission')
        
        # Check for Dep't vs Department
        if 'Dep\'t' in canonical:
            print('→ Pattern: Dep\'t should expand to Department')
        
        # Check for AFL-CIO vs full union name
        if 'Afl-cio' in submitted and 'Union of Needletrades' in canonical:
            print('→ Pattern: Different unions (not same case)')
        
        # Check for FCC vs Federal Communications Commission
        if 'Fcc' in submitted and 'Communications' in canonical:
            print('→ Pattern: FCC abbreviation missing')
        
        # Check for truncated names
        if len(submitted) < len(canonical) * 0.5:
            print('→ Pattern: Severely truncated name')
