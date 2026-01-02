import re

pattern = r'^\s*\d{1,3}\s+(?:[A-Za-z\.]+\s*)*[A-Za-z\.0-9]+\s+\d+(?:\s*,\s*\d+)?\s*,?'
tests = ['120 Wn. App. 175, 188,', '20 Wn. App. 175, 188,', '140 Wn.2d 19, 32,']

for test in tests:
    match = re.match(pattern, test)
    print(f'Test: "{test}" -> Match: {bool(match)}')
    if match:
        print(f'  Full match: "{match.group()}"')
    else:
        # Try to debug what's failing
        parts = test.split()
        print(f'  Parts: {parts}')
        if len(parts) >= 3:
            print(f'  Number: "{parts[0]}"')
            print(f'  Reporter: "{parts[1]}"')
            print(f'  Page: "{parts[2]}"')
