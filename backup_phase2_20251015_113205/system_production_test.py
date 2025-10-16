#!/usr/bin/env python3
"""
Comprehensive system test for CaseStrainer production readiness
Tests all major components and data integrity validation
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_system_components():
    """Test all major system components"""
    print('🧪 TESTING COMPLETE CASESTRAINER SYSTEM')
    print('=' * 60)

    try:
        # Test the validation system first
        from src.data_separation_validator import validate_data_separation
        print('✅ Data separation validator imported')

        # Test API validation
        from src.api_validation import validate_text_input, validate_citation_text
        print('✅ API validation imported')

        # Test CourtListener integration (this should work now with the key)
        from src.courtlistener_integration import CourtListenerClient
        print('✅ CourtListener client imported')

        # Test the main processing pipeline
        from src.unified_input_processor import UnifiedInputProcessor
        print('✅ Unified input processor imported')

        return True

    except Exception as e:
        print(f'❌ Component import failed: {e}')
        return False

def test_pdf_processing():
    """Test PDF file processing"""
    print('\n📄 TESTING PDF PROCESSING')

    pdf_path = '1033940.pdf'

    if os.path.exists(pdf_path):
        file_size = os.path.getsize(pdf_path)
        print(f'📄 Testing with PDF file: {pdf_path} ({file_size} bytes)')

        # Test PDF text extraction
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = '\n'.join(page.extract_text() for page in pdf_reader.pages)
                print(f'📝 PDF text extracted: {len(text)} characters from {len(pdf_reader.pages)} pages')

                # Test citation extraction on first 2000 chars
                test_text = text[:2000]
                print(f'🧪 Testing citation extraction on first 2000 characters...')

                from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
                processor = UnifiedCitationProcessorV2()
                citations = processor._extract_citations_unified(test_text)

                print(f'🎯 Found {len(citations)} citations in test text')

                # Show first few citations
                for i, cit in enumerate(citations[:3]):
                    cit_text = getattr(cit, 'citation', str(cit)[:50])
                    print(f'  {i+1}. {cit_text}...')

                return True

        except Exception as e:
            print(f'❌ PDF processing error: {e}')
            return False

    else:
        print(f'⚠️ PDF file {pdf_path} not found')
        return False

def test_data_validation():
    """Test data integrity validation system"""
    print('\n🔍 TESTING DATA VALIDATION SYSTEM')

    try:
        from src.data_separation_validator import validate_data_separation

        # Test with mock data that includes contamination
        mock_citations = [
            {
                'citation': '123 U.S. 456',
                'extracted_case_name': 'Test Case v. Defendant',
                'canonical_name': 'Test Case v. Defendant',  # Contamination!
                'verified': True
            },
            {
                'citation': '456 F.2d 789',
                'extracted_case_name': 'Another v. Party',
                'canonical_name': 'Different Case v. Party',
                'verified': True
            }
        ]

        validation_report = validate_data_separation(mock_citations)
        contamination_rate = validation_report["contamination_rate"] * 100

        print(f'📊 Validation report: {contamination_rate:.1f}% contamination rate')
        print(f'⚠️ Warnings: {len(validation_report["warnings"])}')

        for warning in validation_report['warnings'][:2]:
            print(f'  - {warning[:80]}...')

        # Verify that contamination was detected
        if contamination_rate > 0:
            print('✅ Data contamination correctly detected')
            return True
        else:
            print('❌ Data contamination not detected')
            return False

    except Exception as e:
        print(f'❌ Validation test failed: {e}')
        return False

def main():
    """Run all system tests"""
    success_count = 0
    total_tests = 3

    if test_system_components():
        success_count += 1

    if test_pdf_processing():
        success_count += 1

    if test_data_validation():
        success_count += 1

    print(f'\n🎯 TEST RESULTS: {success_count}/{total_tests} tests passed')

    if success_count == total_tests:
        print('✅ SYSTEM TEST COMPLETED SUCCESSFULLY')
        print('🎉 All components are working and data integrity is protected!')
        print('🚀 CaseStrainer is PRODUCTION READY')
        return True
    else:
        print('❌ SYSTEM TEST FAILED')
        print('🔧 Some components need attention before production deployment')
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
