#!/usr/bin/env python3
"""
Quick test for PDF file
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🧪 Quick PDF Test")
    print("=" * 30)
    
    # Check if file exists
    pdf_path = "gov.uscourts.wyd.64014.141.0_1.pdf"
    if os.path.exists(pdf_path):
        print(f"✅ File exists: {pdf_path}")
        print(f"📁 File size: {os.path.getsize(pdf_path)} bytes")
    else:
        print(f"❌ File not found: {pdf_path}")
        return
    
    # Try to import and test extraction
    try:
        print("\n📖 Testing imports...")
        from file_utils import extract_text_from_file
        print("✅ file_utils imported successfully")
        
        from citation_utils import extract_all_citations
        print("✅ citation_utils imported successfully")
        
        print("\n📖 Extracting text from PDF...")
        text = extract_text_from_file(pdf_path)
        
        if text:
            print(f"✅ Text extraction successful!")
            print(f"📝 Text length: {len(text)} characters")
            print(f"📄 First 200 characters:")
            print("-" * 40)
            print(text[:200])
            print("-" * 40)
            
            print("\n🔍 Extracting citations...")
            citations = extract_all_citations(text)
            print(f"📚 Found {len(citations)} citations")
            
            if citations:
                print("\n📋 Citations found:")
                for i, citation in enumerate(citations[:5], 1):  # Show first 5
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
