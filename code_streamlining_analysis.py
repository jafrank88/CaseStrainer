"""
ANALYSIS: Code Deprecation and Streamlining Opportunities
"""

print("=" * 70)
print("CODE DEPRECATION AND STREAMLINING ANALYSIS")
print("=" * 70)

print("\n1. DEPRECATED MODULES IDENTIFIED:")
print("-" * 50)

deprecated_files = [
    ("src/clean_extraction_pipeline.py", "Still used but marked as DEPRECATED"),
    ("archive_2025_10_22/", "Old diagnostic files from Oct 2022"),
    ("archive_2025_12_11/", "Old config files from Dec 2025"),
    ("extraction_results/", "Old extraction test results"),
    ("nginx/", "Custom nginx configs - may not be needed"),
    ("docker-test/", "Old docker test directories"),
    ("docker-test2/", "Another old docker test directory"),
    ("docker-backup/", "Backup docker configs"),
]

for file_path, reason in deprecated_files:
    print(f"  {file_path}")
    print(f"    Reason: {reason}")

print("\n2. REDUNDANT CODE PATTERNS:")
print("-" * 50)

redundancies = [
    ("Multiple citation processors", 
     "unified_citation_processor_v2.py, clean_extraction_pipeline.py, unified_case_extraction_master.py"),
    ("Duplicate docket detection", 
     "Added to case_name_validator.py but issue is in strict_context_isolator.py"),
    ("Multiple extraction methods", 
     "extract_citations, extract_citations_clean, process_document_citations"),
    ("Repeated validation logic", 
     "is_valid_case_name exists in multiple places"),
    ("Duplicate regex patterns", 
     "Similar patterns defined across multiple files"),
]

for title, details in redundancies:
    print(f"  {title}:")
    print(f"    {details}")

print("\n3. STREAMLINING OPPORTUNITIES:")
print("-" * 50)

opportunities = [
    {
        "Area": "Citation Extraction",
        "Current": "3 different processors",
        "Suggested": "Consolidate to unified_case_extraction_master.py",
        "Impact": "Reduce complexity, improve maintainability"
    },
    {
        "Area": "Validation Logic",
        "Current": "Scattered across files",
        "Suggested": "Centralize in case_name_validator.py",
        "Impact": "Single source of truth for validation"
    },
    {
        "Area": "Configuration",
        "Current": "Multiple config files",
        "Suggested": "Use single config.py with environment overrides",
        "Impact": "Simpler deployment and debugging"
    },
    {
        "Area": "Docker Setup",
        "Current": "5+ docker directories",
        "Suggested": "Keep only docker/ and docker-windows/",
        "Impact": "Cleaner repository, less confusion"
    },
    {
        "Area": "Test Files",
        "Current": "Scattered test_*.py files in root",
        "Suggested": "Organize in tests/ directory",
        "Impact": "Better test organization"
    }
]

for opp in opportunities:
    print(f"\n  {opp['Area']}:")
    print(f"    Current: {opp['Current']}")
    print(f"    Suggested: {opp['Suggested']}")
    print(f"    Impact: {opp['Impact']}")

print("\n4. IMMEDIATE ACTIONS RECOMMENDED:")
print("-" * 50)

actions = [
    "1. Migrate clean_extraction_pipeline.py users to unified_case_extraction_master.py",
    "2. Remove archive directories (create git tag first for preservation)",
    "3. Consolidate docker configurations",
    "4. Create tests/ directory and move test files",
    "5. Document the deprecation path for clean_extraction_pipeline.py",
    "6. Remove duplicate regex patterns - create patterns.py module",
    "7. Centralize all validation in case_name_validator.py",
]

for action in actions:
    print(f"  {action}")

print("\n5. FILES TO KEEP (ACTIVE):")
print("-" * 50)

active_files = [
    "src/unified_case_extraction_master.py",
    "src/unified_citation_processor_v2.py",
    "src/case_name_validator.py",
    "src/strict_context_isolator.py",
    "docker/",
    "src/",
    "config/",
    "docs/",
]

for file_path in active_files:
    print(f"  {file_path}")

print("\n" + "=" * 70)
print("RECOMMENDATION: Gradual deprecation with clear migration path")
print("=" * 70)
