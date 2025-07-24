from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Read the brief
with open('wa_briefs_text/020_Appellants Brief.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Initialize v2 processor
v2 = UnifiedCitationProcessorV2()

# Process the text
print("=== v2 Processor: What it extracts from the document ===\n")

citations = v2.process_text(text)

print(f"Total citations found: {len(citations)}\n")

# Show the first few citations with their extracted case names and years
for i, citation in enumerate(citations[:5], 1):
    print(f"{i}. Citation: {citation.citation}")
    print(f"   Extracted Case Name: {citation.extracted_case_name}")
    print(f"   Extracted Date: {citation.extracted_date}")
    print(f"   Canonical Name: {citation.canonical_name}")
    print(f"   Canonical Date: {citation.canonical_date}")
    print(f"   Verified: {citation.verified}")
    print(f"   Context: {citation.context[:100]}...")
    print()

print("=== Summary ===")
print("v2 processor extracts case names and years from the ENTIRE document,")
print("not just the ToA section. It looks for citations throughout the text")
print("and extracts context around each citation to find case names.") 