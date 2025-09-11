import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

try:
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    print("✅ Successfully imported UnifiedCitationProcessorV2 from src.unified_citation_processor_v2")
    
    # Test creating an instance
    processor = UnifiedCitationProcessorV2()
    print("✅ Successfully created UnifiedCitationProcessorV2 instance")
    
    # Test a simple method if available
    if hasattr(processor, '_clean_extracted_case_name'):
        result = processor._clean_extracted_case_name("  Test v. Case  ")
        print(f"✅ Tested _clean_extracted_case_name: '{result}'")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Current Python path:", sys.path)
    print("Current working directory:", os.getcwd())
    print("Files in current directory:", os.listdir('.'))
