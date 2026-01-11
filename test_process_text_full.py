"""
Test to catch where the clean pipeline fails in process_text
"""

import sys
import asyncio
import logging
sys.path.insert(0, 'D:/dev/casestrainer/src')

# Set up logging to capture everything
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

# Add a handler to capture errors specifically
error_handler = logging.FileHandler('process_text_errors.log')
error_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
error_handler.setFormatter(formatter)

# Get the root logger and add our handler
root_logger = logging.getLogger()
root_logger.addHandler(error_handler)

async def test_full_process_text():
    """Run full process_text with error logging"""
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    print("Creating processor...")
    processor = UnifiedCitationProcessorV2()
    
    test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."
    
    print("\nRunning process_text...")
    print("=" * 80)
    
    try:
        result = await processor.process_text(test_text)
        
        print("\nResults:")
        print(f"  Citations found: {len(result.get('citations', []))}")
        
        citations = result.get('citations', [])
        print("\nCitations after processing:")
        for i, cit in enumerate(citations):
            print(f"\n{i+1}. Citation: {cit.citation}")
            print(f"   Extracted case name: {cit.extracted_case_name}")
            if hasattr(cit, 'metadata') and cit.metadata:
                print(f"   Metadata: {cit.metadata}")
        
        # Check if clean pipeline was used
        if citations and citations[0].method == 'clean_pipeline_v1':
            print("\n✓ Clean pipeline was used!")
        else:
            print("\n✗ Clean pipeline was NOT used - fallback occurred")
            
    except Exception as e:
        print(f"\nProcess text failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Check error log
    print("\n" + "=" * 80)
    print("CHECKING ERROR LOG:")
    try:
        with open('process_text_errors.log', 'r') as f:
            errors = f.read()
            if errors:
                print("Errors found in log:")
                print(errors)
            else:
                print("No errors logged")
    except:
        print("No error log file found")

# Run the test
asyncio.run(test_full_process_text())
