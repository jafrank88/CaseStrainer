# CORE EXTRACTION TEST - Test Basic Functionality

"""
Test the core extraction functionality directly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_enhanced_extraction_utils():
    """Test enhanced extraction utils directly"""
    
    test_text = """
    Smith v. Jones, 123 Wn.2d 456, 789 P.3d 123 (2020). This case involved...
    """
    
    test_citation = "123 Wn.2d 456"
    
    print("=== TESTING ENHANCED EXTRACTION UTILS ===")
    
    try:
        # Import the module directly
        import enhanced_extraction_utils
        
        # Test the function
        result = enhanced_extraction_utils.extract_case_info_enhanced(test_text, test_citation)
        print(f"Result: {result}")
        
        if result.get('case_name'):
            print("✅ Case name extracted successfully!")
            print(f"   Case name: {result['case_name']}")
        else:
            print("❌ No case name extracted")
            
        if result.get('date'):
            print("✅ Date extracted successfully!")
            print(f"   Date: {result['date']}")
        else:
            print("❌ No date extracted")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_case_name_extraction_core():
    """Test case name extraction core directly"""
    
    test_text = """
    Certified questions are questions of law we review de novo. 
    Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011).
    """
    
    test_citation = "171 Wn.2d 486"
    
    print("\n=== TESTING CASE NAME EXTRACTION CORE ===")
    
    try:
        # Import the module directly
        import case_name_extraction_core
        
        # Test the function
        result = case_name_extraction_core.extract_case_name_triple_comprehensive(test_text, test_citation)
        print(f"Result: {result}")
        
        if result.get('case_name') and result['case_name'] != 'N/A':
            print("✅ Case name extracted successfully!")
            print(f"   Case name: {result['case_name']}")
        else:
            print("❌ No case name extracted")
            
        if result.get('extracted_date') and result['extracted_date'] != 'N/A':
            print("✅ Date extracted successfully!")
            print(f"   Date: {result['extracted_date']}")
        else:
            print("❌ No date extracted")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_unified_citation_processor():
    """Test unified citation processor directly"""
    
    test_text = """
    Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).
    """
    
    print("\n=== TESTING UNIFIED CITATION PROCESSOR ===")
    
    try:
        # Import the module directly
        import unified_citation_processor
        
        # Create processor instance
        processor = unified_citation_processor.UnifiedCitationProcessor()
        
        # Test extraction
        citations = processor.extract_regex_citations(test_text)
        print(f"Found {len(citations)} citations:")
        
        for citation in citations:
            print(f"Citation: {citation.citation}")
            print(f"  extracted_case_name: {citation.extracted_case_name}")
            print(f"  extracted_date: {citation.extracted_date}")
            
            if citation.extracted_case_name and citation.extracted_case_name != 'N/A':
                print("  ✅ Case name extracted!")
            else:
                print("  ❌ No case name extracted")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_document_processing():
    """Test document processing directly"""
    
    test_text = """
    Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). 
    Certified questions are questions of law we review de novo. 
    Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011).
    """
    
    print("\n=== TESTING DOCUMENT PROCESSING ===")
    
    try:
        # Import the module directly
        import document_processing
        
        # Test the function
        result = document_processing.process_document(content=test_text, extract_case_names=True)
        
        print(f"Success: {result.get('success')}")
        print(f"Citations found: {len(result.get('citations', []))}")
        
        for citation in result.get('citations', []):
            print(f"\nCitation: {citation.get('citation')}")
            print(f"  extracted_case_name: {citation.get('extracted_case_name', 'N/A')}")
            print(f"  canonical_name: {citation.get('canonical_name', 'N/A')}")
            print(f"  extracted_date: {citation.get('extracted_date', 'N/A')}")
            
            if citation.get('extracted_case_name') and citation.get('extracted_case_name') != 'N/A':
                print("  ✅ Case name extracted!")
            else:
                print("  ❌ No case name extracted")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def run_core_tests():
    """Run all core tests"""
    
    print("🔍 CORE EXTRACTION TESTING")
    print("=" * 50)
    
    test_enhanced_extraction_utils()
    test_case_name_extraction_core()
    test_unified_citation_processor()
    test_document_processing()
    
    print("\n" + "=" * 50)
    print("📋 CORE TESTING SUMMARY:")
    print("1. Tests core extraction functions directly")
    print("2. Avoids circular import issues")
    print("3. Identifies specific extraction problems")

if __name__ == "__main__":
    run_core_tests() 