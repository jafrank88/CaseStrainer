#!/usr/bin/env python3

def test_problematic_citations():
    """Investigate specific citations with missing or short case names."""
    
    print("🔍 PROBLEMATIC CITATIONS INVESTIGATION")
    print("=" * 60)
    
    # Target citations with issues
    target_citations = [
        "9 P.3d 655",
        "101 Wash.2d 270", 
        "567 P.3d 1128"
    ]
    
    try:
        # Load the large PDF text
        pdf_text_file = "d:/dev/casestrainer/extracted_pdf_text.txt"
        try:
            with open(pdf_text_file, 'r', encoding='utf-8') as f:
                full_text = f.read()
        except FileNotFoundError:
            print(f"❌ PDF text file not found: {pdf_text_file}")
            return
        
        print(f"📊 Full text size: {len(full_text)} characters")
        
        # Find context around each problematic citation
        for citation in target_citations:
            print(f"\n🔍 ANALYZING: {citation}")
            print("=" * 40)
            
            # Find all occurrences of this citation
            import re
            
            # Create a flexible pattern for the citation
            citation_pattern = citation.replace(".", r"\.").replace(" ", r"\s+")
            matches = list(re.finditer(citation_pattern, full_text, re.IGNORECASE))
            
            print(f"   Found {len(matches)} occurrences in text")
            
            for i, match in enumerate(matches):
                start_pos = match.start()
                end_pos = match.end()
                
                # Get context around the citation (500 chars before and after)
                context_start = max(0, start_pos - 500)
                context_end = min(len(full_text), end_pos + 500)
                context = full_text[context_start:context_end]
                
                print(f"\n   📖 Occurrence {i+1} (position {start_pos}-{end_pos}):")
                print(f"   Context (±500 chars):")
                print(f"   {'='*50}")
                
                # Highlight the citation in the context
                relative_start = start_pos - context_start
                relative_end = end_pos - context_start
                
                before_citation = context[:relative_start]
                citation_text = context[relative_start:relative_end]
                after_citation = context[relative_end:]
                
                print(f"   ...{before_citation}[{citation_text}]{after_citation}...")
                
                # Look for potential case names in the context
                print(f"\n   🔍 Potential case names in context:")
                
                # Common case name patterns
                case_patterns = [
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)',  # Smith v. Jones
                    r'In\s+re\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)',  # In re Smith
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)\s+v\.\s+([A-Z][A-Z\s&,.]+)',  # Smith v. STATE
                    r'([A-Z][A-Z\s&,.]+)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)',  # STATE v. Smith
                ]
                
                found_names = []
                for pattern in case_patterns:
                    matches_in_context = re.findall(pattern, context)
                    for match in matches_in_context:
                        if isinstance(match, tuple):
                            case_name = f"{match[0]} v. {match[1]}"
                        else:
                            case_name = match
                        found_names.append(case_name)
                
                if found_names:
                    for name in found_names[:3]:  # Show first 3 potential names
                        print(f"      - {name}")
                else:
                    print(f"      - No clear case name patterns found")
                
                # Look for years near the citation
                year_pattern = r'\b(19|20)\d{2}\b'
                years_in_context = re.findall(year_pattern, context)
                if years_in_context:
                    print(f"   📅 Years found: {list(set(years_in_context))}")
        
        # Test direct extraction with UnifiedCitationProcessorV2
        print(f"\n🔧 TESTING DIRECT EXTRACTION")
        print("=" * 40)
        
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        import asyncio
        
        processor = UnifiedCitationProcessorV2()
        
        # Test with a smaller sample containing our target citations
        for citation in target_citations:
            print(f"\n   Testing extraction for: {citation}")
            
            # Find the citation in text and extract a reasonable sample around it
            citation_pattern = citation.replace(".", r"\.").replace(" ", r"\s+")
            match = re.search(citation_pattern, full_text, re.IGNORECASE)
            
            if match:
                start_pos = match.start()
                # Get 2000 chars around the citation for context
                sample_start = max(0, start_pos - 1000)
                sample_end = min(len(full_text), start_pos + 1000)
                sample_text = full_text[sample_start:sample_end]
                
                print(f"      Sample size: {len(sample_text)} chars")
                
                try:
                    result = asyncio.run(processor.process_text(sample_text))
                    citations_found = result.get('citations', [])
                    
                    # Find our target citation in the results
                    target_found = None
                    for cit in citations_found:
                        if citation.replace(" ", "").replace(".", "") in cit.citation.replace(" ", "").replace(".", ""):
                            target_found = cit
                            break
                    
                    if target_found:
                        print(f"      ✅ Found: {target_found.citation}")
                        print(f"      Extracted name: '{getattr(target_found, 'extracted_case_name', 'N/A')}'")
                        print(f"      Canonical name: '{getattr(target_found, 'canonical_name', 'N/A')}'")
                        print(f"      Cluster name: '{getattr(target_found, 'cluster_case_name', 'N/A')}'")
                    else:
                        print(f"      ❌ Citation not found in extraction results")
                        print(f"      Found {len(citations_found)} other citations")
                        
                except Exception as e:
                    print(f"      ❌ Extraction error: {e}")
            else:
                print(f"      ❌ Citation not found in full text")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_problematic_citations()
