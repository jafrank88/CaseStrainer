#!/usr/bin/env python3
"""
Focused test of case name extraction and citation clustering using the PDF URL.
"""

import sys
import os
import json
from typing import Dict, List, Any

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def focused_url_test(url: str):
    """Focused test that avoids problematic components."""
    print("=" * 70)
    print("FOCUSED CASESTRAINER URL TEST")
    print("=" * 70)
    print(f"Testing URL: {url}")
    print()

    try:
        # Step 1: Extract text (should work quickly)
        print("📄 Extracting text from URL...")
        from document_processing_unified import extract_text_from_url

        text = extract_text_from_url(url)
        print(f"✅ Extracted {len(text)} characters")

        if len(text) < 500:
            print("❌ Insufficient text extracted")
            return

        print(f"Preview: {text[:300].replace(chr(10), ' ').strip()}...")
        print()

        # Step 2: Find citations using simple regex (avoid complex processor)
        print("🔍 Finding citations with regex...")
        import re

        # Simple citation patterns
        citation_patterns = [
            r'\b\d+\s+[A-Z][a-z]+\.?\s*\d+',  # Basic format: 123 F.2d 456
            r'\b\d+\s+[A-Z]+\.?\s*\d+',       # Reporter abbreviations
            r'\b\d+\s+[A-Z][a-z]+\s+\d+',    # Full reporter names
        ]

        citations_found = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, text)
            citations_found.extend(matches)

        # Remove duplicates and clean
        citations_found = list(set(citations_found))
        citations_found = [c for c in citations_found if len(c.split()) >= 3]  # Filter malformed

        print(f"✅ Found {len(citations_found)} unique citations")
        if citations_found:
            print("Sample citations:")
            for i, cite in enumerate(citations_found[:8]):
                print(f"  {i+1}. {cite}")
        print()

        # Step 3: Test case name extraction (simplified)
        print("🎯 Testing case name extraction...")
        from unified_case_name_extractor_v2 import UnifiedCaseNameExtractorV2

        extractor = UnifiedCaseNameExtractorV2()
        extraction_results = []

        print("Testing on first 5 citations:")
        for i, citation in enumerate(citations_found[:5]):
            # Find citation in text and get context
            cite_pos = text.find(citation)
            if cite_pos >= 0:
                # Get broader context
                start = max(0, cite_pos - 300)
                end = min(len(text), cite_pos + len(citation) + 100)
                context = text[start:end]

                # Extract case name
                result = extractor.extract_case_name_and_date(context, citation=citation)

                case_name = result.case_name or "N/A"
                confidence = result.confidence
                method = result.method

                print(f"  {i+1}. '{citation}' → '{case_name}' (conf: {confidence:.2f})")

                if case_name != "N/A":
                    extraction_results.append({
                        'citation': citation,
                        'case_name': case_name,
                        'confidence': confidence,
                        'method': method
                    })

        print()

        # Step 4: Simple clustering test
        print("🔗 Testing citation clustering...")

        if len(extraction_results) >= 2:
            # Group by case name
            clusters = {}
            for result in extraction_results:
                case_name = result['case_name']
                if case_name not in clusters:
                    clusters[case_name] = []
                clusters[case_name].append(result['citation'])

            print(f"✅ Created {len(clusters)} clusters:")
            for case_name, citations in clusters.items():
                print(f"  📁 '{case_name}': {len(citations)} citations")
                for cite in citations[:3]:  # Show first 3
                    print(f"    • {cite}")
                if len(citations) > 3:
                    print(f"    ... and {len(citations) - 3} more")
        else:
            print("❌ Need more case names for clustering test")

        print()

        # Step 5: Assessment
        print("📊 ASSESSMENT")
        print("-" * 30)

        url_success = len(text) > 1000
        citation_success = len(citations_found) > 0
        name_success = len(extraction_results) > 0
        cluster_success = len(clusters) > 1 if 'clusters' in locals() else False

        scores = {
            'URL Processing': 10 if url_success else 0,
            'Citation Finding': min(10, len(citations_found)),
            'Case Name Extraction': min(10, len(extraction_results) * 2),
            'Clustering': 10 if cluster_success else (5 if len(extraction_results) >= 2 else 0)
        }

        total = sum(scores.values())
        print(f"URL Processing: {scores['URL Processing']}/10 ({'✅' if url_success else '❌'})")
        print(f"Citation Finding: {scores['Citation Finding']}/10 ({len(citations_found)} found)")
        print(f"Case Name Extraction: {scores['Case Name Extraction']}/10 ({len(extraction_results)} extracted)")
        print(f"Clustering: {scores['Clustering']}/10 ({'✅' if cluster_success else '❌'})")
        print()
        print(f"🏆 TOTAL SCORE: {total}/40")

        if total >= 30:
            print("🎉 EXCELLENT: All core functionality working!")
        elif total >= 20:
            print("👍 GOOD: Core functionality operational")
        elif total >= 10:
            print("⚠️ FAIR: Basic functionality working")
        else:
            print("❌ POOR: Major issues detected")

        # Save results
        results = {
            'url': url,
            'success': {
                'url_processing': url_success,
                'citation_finding': citation_success,
                'case_name_extraction': name_success,
                'clustering': cluster_success
            },
            'counts': {
                'text_chars': len(text),
                'citations': len(citations_found),
                'case_names': len(extraction_results),
                'clusters': len(clusters) if 'clusters' in locals() else 0
            },
            'sample_citations': citations_found[:10],
            'extraction_results': extraction_results,
            'clusters': clusters if 'clusters' in locals() else {},
            'total_score': total
        }

        with open('focused_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Detailed results saved to: focused_test_results.json")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    url = "https://www.courthousenews.com/wp-content/uploads/2025/09/g-ross-intelligence-redacted-brief-thomson-reuters-interlocutory-appeal-third-circuit.pdf"
    focused_url_test(url)
