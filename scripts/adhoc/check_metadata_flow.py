"""
Check where metadata is being lost
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import CleanExtractionPipeline
from src.models import CitationResult
from eyecite import get_citations

text = "Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686 (1954)."

print("CHECKING METADATA PRESERVATION")
print("=" * 60)

# Step 1: Check eyecite citations
eyecite_citations = get_citations(text)
print("\n1. Eyecite citations:")
for i, cit in enumerate(eyecite_citations):
    if hasattr(cit, 'metadata'):
        print(f"   {i+1}. {cit}")
        print(f"      Plaintiff: {getattr(cit.metadata, 'plaintiff', None)}")
        print(f"      Defendant: {getattr(cit.metadata, 'defendant', None)}")
        print(f"      Extra: {getattr(cit.metadata, 'extra', None)}")

# Step 2: Check after CleanExtractionPipeline.extract_citations
pipeline = CleanExtractionPipeline()
citations = pipeline.extract_citations(text)
print("\n2. After extract_citations:")
for i, cit in enumerate(citations):
    print(f"   {i+1}. {cit.citation}")
    print(f"      Plaintiff: {cit.metadata.get('plaintiff') if cit.metadata else None}")
    print(f"      Defendant: {cit.metadata.get('defendant') if cit.metadata else None}")
    print(f"      Extra: {cit.metadata.get('extra') if cit.metadata else None}")

# Step 3: Check after _extract_all_case_names
print("\n3. Before _extract_all_case_names:")
for i, cit in enumerate(citations):
    print(f"   {i+1}. {cit.citation}")
    print(f"      Plaintiff: {cit.metadata.get('plaintiff') if cit.metadata else None}")
    print(f"      Defendant: {cit.metadata.get('defendant') if cit.metadata else None}")

pipeline._extract_all_case_names(text, citations)

print("\n4. After _extract_all_case_names:")
for i, cit in enumerate(citations):
    print(f"   {i+1}. {cit.citation}")
    print(f"      Case name: '{cit.extracted_case_name}'")
    print(f"      Plaintiff: {cit.metadata.get('plaintiff') if cit.metadata else None}")
    print(f"      Defendant: {cit.metadata.get('defendant') if cit.metadata else None}")
    print(f"      Is parallel: {cit.metadata.get('is_parallel_citation') if cit.metadata else None}")
    print(f"      Is series: {cit.metadata.get('is_series_citation') if cit.metadata else None}")
