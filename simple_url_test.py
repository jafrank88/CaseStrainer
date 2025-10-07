#!/usr/bin/env python3
"""
Simple test of URL processing and basic citation extraction.
"""

import sys
import os
import re
import json
from typing import List

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Simple test of URL processing capabilities."""
    print("🧪 SIMPLE CASESTRAINER URL TEST")
    print("=" * 50)

    url = "https://www.courthousenews.com/wp-content/uploads/2025/09/g-ross-intelligence-redacted-brief-thomson-reuters-interlocutory-appeal-third-circuit.pdf"

    # Step 1: Extract text
    print("📄 Extracting text from URL...")
    try:
        from document_processing_unified import extract_text_from_url
        text = extract_text_from_url(url)
        text_length = len(text)
        print(f"✅ Extracted {text_length} characters")

        if text_length < 500:
            print("❌ Insufficient text extracted")
            return

        print(f"Sample text: {text[:200].replace(chr(10), ' ').strip()}...")

    except Exception as e:
        print(f"❌ Text extraction failed: {e}")
        return

    # Step 2: Find citations with simple regex
    print("\n🔍 Finding citations...")
    citation_patterns = [
        r'\b\d+\s+[A-Z][a-z]+\.?\s*\d+',  # Basic: 123 F.2d 456
        r'\b\d+\s+[A-Z]+\.?\s*\d+',       # Reporter: 123 US 456
    ]

    citations = []
    for pattern in citation_patterns:
        matches = re.findall(pattern, text)
        citations.extend(matches)

    citations = list(set(citations))  # Remove duplicates
    print(f"✅ Found {len(citations)} unique citations")

    if citations:
        print("Sample citations:")
        for i, cite in enumerate(citations[:5]):
            print(f"  {i+1}. {cite}")

    # Step 3: Basic assessment
    print("\n📊 ASSESSMENT")
    print("-" * 30)

    url_success = text_length > 1000
    citation_success = len(citations) > 0

    print(f"URL Processing: {'✅' if url_success else '❌'} ({text_length} chars)")
    print(f"Citation Finding: {'✅' if citation_success else '❌'} ({len(citations)} found)")

    total_score = (10 if url_success else 0) + (10 if citation_success else 0)
    print(f"\n🏆 TOTAL SCORE: {total_score}/20")

    if total_score >= 15:
        print("🎉 SUCCESS: Core functionality working!")
    elif total_score >= 10:
        print("⚠️ PARTIAL: Basic functionality operational")
    else:
        print("❌ ISSUES: Major problems detected")

    # Save basic results
    results = {
        'url': url,
        'text_length': text_length,
        'citations_found': len(citations),
        'citations': citations[:10],  # First 10
        'score': total_score,
        'url_success': url_success,
        'citation_success': citation_success
    }

    with open('simple_url_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results saved to: simple_url_test_results.json")

if __name__ == "__main__":
    main()
