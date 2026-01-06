#!/usr/bin/env python3
"""
Test the actual normalization in the function
"""

import re

def normalize_citation(cite):
    """Normalize citation text for consistent matching."""
    if not cite or not isinstance(cite, str):
        return ""
    # Remove any non-alphanumeric characters except spaces, dots, and numbers
    normalized = re.sub(r"[^a-z0-9\s.]", " ", cite.lower())
    # Collapse multiple spaces and standardize variations
    normalized = re.sub(r"\s+", " ", normalized).strip()
    # Standardize variations
    normalized = normalized.replace("pacific", "p").replace("pacific reporter", "p")
    normalized = normalized.replace("washington", "wash").replace("wn ", "wash ").replace("wn. ", "wash. ")
    # Handle cases like 'Wn. App. 2d' -> 'wash app 2d' (must be before general app pattern)
    normalized = re.sub(r"wash\.?\s+app\.?\s+(\d*)d", r"wash app \1d", normalized)
    # Handle cases like 'Wn. App.' -> 'wash app'
    normalized = re.sub(r"wash(?:ington)?\s+app(?:\.?\s*\w*)?", "wash app", normalized)
    # Handle cases like 'Wash.2d' -> 'wash2d'
    normalized = re.sub(r"wash(?:ington)?\.?\s*(\d*)d", r"wash\1d", normalized)
    # Handle cases like 'Wn.2d' -> 'wash2d'
    normalized = re.sub(r"wn\.?\s*(\d*)d", r"wash\1d", normalized)
    # Handle cases like 'P.3d' -> 'p3d'
    normalized = re.sub(r"p\.?\s*(\d*)d", r"p\1d", normalized)
    return normalized

# Test
cite = "24 Wn. App. 2d 377"
print(f"Original: '{cite}'")
result = normalize_citation(cite)
print(f"Normalized: '{result}'")

# The issue is that after replacing 'wn. ' with 'wash. ', we get 'wash. app. 2d'
# But the pattern expects 'wash app 2d' without the dots!
# Let's trace:
step1 = re.sub(r"[^a-z0-9\s.]", " ", cite.lower())
print(f"Step 1: '{step1}'")

step2 = re.sub(r"\s+", " ", step1).strip()
print(f"Step 2: '{step2}'")

step3 = step2.replace("washington", "wash").replace("wn ", "wash ").replace("wn. ", "wash. ")
print(f"Step 3: '{step3}'")

# Now apply the wash app 2d pattern
step4 = re.sub(r"wash\.?\s+app\.?\s+(\d*)d", r"wash app \1d", step3)
print(f"Step 4: '{step4}'")
