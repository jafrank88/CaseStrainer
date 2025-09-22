#!/usr/bin/env python3

def debug_pdf_routing():
    """Debug why the large PDF text is being processed as sync instead of async."""
    
    print("🔍 PDF ROUTING DEBUG")
    print("=" * 50)
    
    # Read the extracted text
    try:
        with open("extracted_pdf_text.txt", "r", encoding="utf-8") as f:
            pdf_text = f.read()
    except FileNotFoundError:
        print("❌ extracted_pdf_text.txt not found. Run extract_pdf_text.py first.")
        return
    
    print(f"📊 Text size: {len(pdf_text):,} characters")
    print()
    
    # Test the routing logic directly
    try:
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        
        print(f"🎯 ROUTING LOGIC TEST:")
        print("-" * 30)
        print(f"   SYNC_THRESHOLD: {service.SYNC_THRESHOLD:,} bytes")
        print(f"   Text size: {len(pdf_text):,} bytes")
        print(f"   Size >= Threshold: {len(pdf_text) >= service.SYNC_THRESHOLD}")
        print()
        
        # Test determine_processing_mode
        mode = service.determine_processing_mode(pdf_text)
        print(f"   determine_processing_mode(): {mode}")
        
        # Test should_process_immediately
        input_data = {'type': 'text', 'text': pdf_text}
        should_sync = service.should_process_immediately(input_data)
        print(f"   should_process_immediately(): {should_sync}")
        
        # Test extract_text_from_input
        extracted_text = service.extract_text_from_input(input_data)
        if extracted_text:
            print(f"   extract_text_from_input(): {len(extracted_text):,} characters")
            extracted_mode = service.determine_processing_mode(extracted_text)
            print(f"   Mode from extracted text: {extracted_mode}")
        else:
            print("   extract_text_from_input(): FAILED")
        
        print()
        
        # Test with a smaller sample to see if citations are found
        sample_text = pdf_text[:5000]  # First 5KB
        print(f"🧪 TESTING SMALLER SAMPLE:")
        print("-" * 30)
        print(f"   Sample size: {len(sample_text):,} characters")
        
        sample_mode = service.determine_processing_mode(sample_text)
        print(f"   Expected mode: {sample_mode}")
        
        # Test citation extraction on sample
        try:
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
            from src.config import get_citation_config
            
            config = get_citation_config()
            processor = UnifiedCitationProcessorV2(config)
            
            print("   Testing citation extraction on sample...")
            citations = processor.extract_citations_from_text(sample_text)
            print(f"   Citations found in sample: {len(citations)}")
            
            if citations:
                print("   First few citations:")
                for i, citation in enumerate(citations[:3]):
                    citation_text = getattr(citation, 'citation', str(citation))
                    print(f"      {i+1}. {citation_text}")
            
        except Exception as e:
            print(f"   Citation extraction error: {e}")
        
        print()
        
        # Check if there's an issue with the full text
        print(f"🔍 FULL TEXT ANALYSIS:")
        print("-" * 30)
        
        # Look for potential issues in the text
        non_printable = sum(1 for c in pdf_text if ord(c) < 32 and c not in '\n\r\t')
        print(f"   Non-printable characters: {non_printable}")
        
        # Check for very long lines that might cause issues
        lines = pdf_text.split('\n')
        max_line_length = max(len(line) for line in lines) if lines else 0
        print(f"   Longest line: {max_line_length:,} characters")
        
        # Check for null bytes or other problematic characters
        null_bytes = pdf_text.count('\x00')
        print(f"   Null bytes: {null_bytes}")
        
        # Show first 200 characters to check format
        print(f"\n   First 200 characters:")
        print(f"   {repr(pdf_text[:200])}")
        
        # Check last 200 characters
        print(f"\n   Last 200 characters:")
        print(f"   {repr(pdf_text[-200:])}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pdf_routing()
