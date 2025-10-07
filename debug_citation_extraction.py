#!/usr/bin/env python3
"""
Debug citation extraction for the user's text.
"""

from src.unified_input_processor import UnifiedInputProcessor

def test_citation_extraction():
    processor = UnifiedInputProcessor()

    text = '''Five Corners Fam. Farmers v. State, 173 Wn.2d
296, 306, 268 P.3d 892 (2011) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150
Wn.2d 674, 682, 80 P.3d 598 (2003)); Bostain v. Food Express, Inc., 159 Wn.2d
700, 716, 153 P.3d 846 (2007) (collecting cases).'''

    print('Testing UnifiedInputProcessor...')
    print('Text length:', len(text))
    print('Text preview:', repr(text[:100] + '...' if len(text) > 100 else text))

    try:
        result = processor.process_any_input(
            input_data=text,
            input_type='text',
            request_id='debug-test'
        )

        print('\nResult analysis:')
        print('- Success:', result.get('success'))
        print('- Citations found:', len(result.get('citations', [])))
        print('- Clusters found:', len(result.get('clusters', [])))
        print('- Message:', result.get('message', 'No message'))

        citations = result.get('citations', [])
        if citations:
            print('\nFirst 3 citations:')
            for i, citation in enumerate(citations[:3]):
                print(f'  {i+1}. {citation.get("citation", "N/A")}')
                print(f'     Case name: {citation.get("extracted_case_name", "N/A")}')
                print(f'     Date: {citation.get("extracted_date", "N/A")}')
        else:
            print('\nNo citations found!')

        return result

    except Exception as e:
        print('Error:', e)
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_citation_extraction()
