#!/usr/bin/env python3

# Test if the validation fix is actually working in the container
import sys
sys.path.append('/app/src')

from src.unified_extraction_architecture import UnifiedExtractionArchitecture

# Create an instance to test the validation logic
extractor = UnifiedExtractionArchitecture()

# Test the validation logic with a long case name
long_case_name = "Statutory interpretation is also an issue of law we review de novo. Spokane County v. Dep't of Fish & Wildlife"

print("Testing validation logic:")
print(f"Case name length: {len(long_case_name)}")
print(f"Quality score: {extractor._assess_case_name_quality(long_case_name)}")
print(f"Would be accepted: {extractor._assess_case_name_quality(long_case_name) > 0.5}")

# Test with the actual extraction
text = """Certified questions are questions of law that this court reviews de novo and in light
of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183
Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we
review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430
P.3d 655 (2018)."""

result = extractor.extract_case_name_and_year(
    text=text,
    citation="192 Wn.2d 453",
    start_index=323,
    end_index=336,
    debug=True
)

print(f"\nExtraction result: {result}")
print(f"Case name: '{result.get('case_name', 'N/A')}'")
print(f"Year: '{result.get('year', 'N/A')}'")
