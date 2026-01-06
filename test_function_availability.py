#!/usr/bin/env python3
"""
Test if the function is available
"""

try:
    from src.citation_clustering import _is_citation_contained_in_any
    print(f"Function imported: {_is_citation_contained_in_any}")
    print(f"Type: {type(_is_citation_contained_in_any)}")
except ImportError as e:
    print(f"ImportError: {e}")
    
# Check the import in the processor
print("\nChecking in processor:")
from src.unified_citation_processor_v2 import _is_citation_contained_in_any as func
print(f"In processor: {func}")

if func is None:
    print("Function is None in processor!")
else:
    print("Function is available in processor")
