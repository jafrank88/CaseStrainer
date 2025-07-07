#!/usr/bin/env python3
"""
Simple manual test - run this directly
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

def main():
    print("🧪 Simple Manual Test")
    print("=" * 30)
    
    # Check file
    pdf_path = "gov.uscourts.wyd.64014.141.0_1.pdf"
    if os.path.exists(pdf_path):
        print(f"✅ File exists: {pdf_path}")
        print(f"📁 File size: {os.path.getsize(pdf_path)} bytes")
    else:
        print(f"❌ File not found: {pdf_path}")
        return
    
    # Test imports
    try:
        print("\n📖 Testing imports...")
        from file_utils import extract_text_from_file
        print("✅ file_utils imported")
        
        from citation_utils import extract_all_citations
        print("✅ citation_utils imported")
        
        # Test extraction
        print("\n📖 Extracting text...")
        text = extract_text_from_file(pdf_path)
        
        if text:
            print(f"✅ Text extracted: {len(text)} characters")
            print(f"📄 Preview: {text[:200]}...")
            
            # Test citations
            print("\n🔍 Extracting citations...")
            citations = extract_all_citations(text)
            print(f"📚 Found {len(citations)} citations")
            
            if citations:
                print("\n📋 Citations:")
                for i, citation in enumerate(citations[:5], 1):
                    print(f"  {i}. {citation}")
                if len(citations) > 5:
                    print(f"  ... and {len(citations) - 5} more")
            else:
                print("📚 No citations found")
        else:
            print("❌ No text extracted")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 