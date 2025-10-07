import sys
sys.path.insert(0, '/app')

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

print('Testing enhancements...')
processor = UnifiedCitationProcessorV2()
print(f'Has _repair_truncated_case_name: {hasattr(processor, "_repair_truncated_case_name")}')

# Test the repair function
if hasattr(processor, '_repair_truncated_case_name'):
    test_name = "Inc. v. Robins"
    test_text = "Spokeo, Inc. v. Robins, 136 S. Ct. 1540"
    repaired = processor._repair_truncated_case_name(test_name, test_text, 20)
    print(f'Test repair: "{test_name}" -> "{repaired}"')
else:
    print('ERROR: _repair_truncated_case_name method not found!')
