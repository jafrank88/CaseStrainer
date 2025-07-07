#!/usr/bin/env python3
import re

sample_text = '''
Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716 (1982)
John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)
John Doe G v. Department of Corrections, 190 Wn.2d 185, 410 P.3d 1156 (2018)
Cohen v. Everett City Council, 85 Wn.2d 385, 388, 535 P.2d 801 (1975)
State v. Waldon, 148 Wn. App. 952, 962-63, 202 P.3d 325 (2009)
Federated Publ'ns v. Kurtz, 94 Wn.2d 51, 64, 615 P.2d 440 (1980)
'''

print("[DEBUG] Raw lines and repr:")
for line in sample_text.splitlines():
    print(repr(line))

# Stepwise pattern: (1) case name, (2) citation(s), (3) year
stepwise_pattern = re.compile(r"^(.+? v\.[^,\n]+), (.+) \((\d{4})\)$", re.MULTILINE)
print(f"\n[DEBUG] Stepwise pattern: {stepwise_pattern.pattern}")
matches = list(stepwise_pattern.finditer(sample_text))
print(f"[DEBUG] Matches found: {len(matches)}")
for m in matches:
    print(f"[DEBUG] Match: {m.group(0)}")
    for i in range(1, m.lastindex+1):
        print(f"  group({i}): {m.group(i)}")

# Very permissive pattern: anything before (year)
permissive_pattern = re.compile(r"(.+?\([0-9]{4}\))")
print(f"\n[DEBUG] Permissive pattern: {permissive_pattern.pattern}")
matches = list(permissive_pattern.finditer(sample_text))
print(f"[DEBUG] Matches found: {len(matches)}")
for m in matches:
    print(f"[DEBUG] Match: {m.group(0)}")

# Patterns from the backend
patterns = [
    re.compile(r"((?:[\w\W]*?\n){0,2})([A-Z][A-Za-z0-9\.'\- ]+? v\. [A-Z][A-Za-z0-9\.'\- ]+?),?\s*([0-9]{1,4} [A-Za-z\. ]+ [0-9]{1,5}(?:, [0-9]{1,4} [A-Za-z\. ]+ [0-9]{1,5})*)\s*\((\d{4})\)"),
    re.compile(r"((?:[\w\W]*?\n){0,2})([A-Z][A-Za-z0-9\.'\- ]+? (?:v\.|v|versus) [A-Z][A-Za-z0-9\.'\- ]+?),?\s*([0-9]{1,4} [A-Za-z\. ]+ [0-9]{1,5}(?:, [0-9]{1,4} [A-Za-z\. ]+ [0-9]{1,5})*)\s*\((\d{4})\)"),
    re.compile(r"([0-9]{1,4} [A-Za-z\. ]+ [0-9]{1,5}(?:, [0-9]{1,4} [A-Za-z\. ]+ [0-9]{1,5})*)\s*\((\d{4})\)")
]

for idx, pattern in enumerate(patterns):
    print(f"\n[DEBUG] Pattern {idx+1}: {pattern.pattern}")
    matches = list(pattern.finditer(sample_text))
    print(f"[DEBUG] Matches found: {len(matches)}")
    for m in matches:
        print(f"[DEBUG] Match: {m.group(0)}")
        for i in range(1, m.lastindex+1):
            print(f"  group({i}): {m.group(i)}")

# Simple pattern: Case Name, Reporter (Year)
simple_pattern = re.compile(r"([A-Z][^,\n]+? v\. [^,\n]+), ([0-9]{1,4} [A-Za-z\. ]+ [0-9]{1,5}(?:, [0-9]{1,4} [A-Za-z\. ]+ [0-9]{1,5})*) \((\d{4})\)")

print(f"[DEBUG] Pattern: {simple_pattern.pattern}")
matches = list(simple_pattern.finditer(sample_text))
print(f"[DEBUG] Matches found: {len(matches)}")
for m in matches:
    print(f"[DEBUG] Match: {m.group(0)}")
    for i in range(1, m.lastindex+1):
        print(f"  group({i}): {m.group(i)}") 