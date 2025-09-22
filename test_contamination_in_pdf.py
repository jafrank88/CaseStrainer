#!/usr/bin/env python3

import requests
import json

def test_contamination_in_pdf():
    """Test for contamination using a small sample from the PDF that should process sync."""
    
    print("🔍 PDF CONTAMINATION TEST")
    print("=" * 50)
    
    # Use a small sample from the PDF that will definitely be processed sync
    test_text = '''
    Bostain v. Food Express, Inc., 159 Wn.2d 700, 153 P.3d 846 (2007).
    
    The court in Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 355 P.3d 258 (2015), 
    established important precedent.
    
    See also Spokeo, Inc. v. Robins, 578 U.S. 330, 136 S. Ct. 1540 (2016).
    '''
    
    print(f"📊 Test text size: {len(test_text)} bytes (should be sync)")
    print(f"📝 Test text contains known case names from PDF")
    print()
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "type": "text"}
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            task_id = result.get('task_id')
            processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
            citations = result.get('citations', [])
            
            print(f"📊 Processing mode: {processing_mode}")
            print(f"📊 Task ID: {task_id}")
            print(f"📊 Citations found: {len(citations)}")
            print()
            
            if not citations:
                print("❌ No citations found - cannot analyze contamination")
                return
            
            print("🔍 DETAILED CONTAMINATION ANALYSIS:")
            print("=" * 50)
            
            contamination_count = 0
            clean_count = 0
            
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', '')
                extracted_name = citation.get('extracted_case_name', '')
                canonical_name = citation.get('canonical_name', '')
                cluster_name = citation.get('cluster_case_name', '')
                verified = citation.get('verified', False)
                
                print(f"\n📖 Citation {i}: {citation_text}")
                print(f"   🔍 Extracted: '{extracted_name}'")
                print(f"   📚 Canonical: '{canonical_name}'")
                print(f"   🔗 Cluster: '{cluster_name}'")
                print(f"   ✅ Verified: {verified}")
                
                # Check for contamination
                extracted_clean = extracted_name.strip() if extracted_name and extracted_name != 'N/A' else ''
                canonical_clean = canonical_name.strip() if canonical_name and canonical_name != 'N/A' else ''
                
                if extracted_clean and canonical_clean:
                    if extracted_clean == canonical_clean:
                        contamination_count += 1
                        print(f"   🚨 CONTAMINATION: Extracted == Canonical")
                        
                        # Check if this is suspicious
                        if verified:
                            print(f"   ⚠️  SUSPICIOUS: Verified citation with identical names")
                        else:
                            print(f"   🤔 UNVERIFIED: Identical names but not verified")
                    else:
                        clean_count += 1
                        print(f"   ✅ CLEAN: Different extracted and canonical names")
                elif extracted_clean and not canonical_clean:
                    clean_count += 1
                    print(f"   ✅ CLEAN: Extracted only, no canonical contamination")
                elif not extracted_clean and canonical_clean:
                    print(f"   ⚠️  EXTRACTION FAILURE: No extracted name, only canonical")
                else:
                    print(f"   ❓ NO NAMES: Neither extracted nor canonical available")
            
            # Summary
            total_with_both = contamination_count + clean_count
            if total_with_both > 0:
                contamination_rate = (contamination_count / total_with_both) * 100
                
                print(f"\n📊 CONTAMINATION SUMMARY:")
                print("-" * 30)
                print(f"   Contaminated: {contamination_count}")
                print(f"   Clean: {clean_count}")
                print(f"   Rate: {contamination_rate:.1f}%")
                
                if contamination_rate > 70:
                    print(f"   🚨 SEVERE: High contamination detected")
                elif contamination_rate > 40:
                    print(f"   ⚠️  MODERATE: Some contamination detected")
                else:
                    print(f"   ✅ CLEAN: Low contamination rate")
            
            # Raw JSON analysis
            print(f"\n🔍 RAW JSON ANALYSIS (first citation):")
            print("-" * 40)
            if citations:
                first_citation = citations[0]
                
                # Show all fields related to case names
                name_fields = {}
                for key, value in first_citation.items():
                    if 'name' in key.lower() or 'case' in key.lower():
                        name_fields[key] = value
                
                print("   Case name related fields:")
                for key, value in name_fields.items():
                    print(f"      {key}: '{value}'")
                
                # Check metadata
                metadata = first_citation.get('metadata', {})
                if metadata:
                    print("\n   Metadata:")
                    for key, value in metadata.items():
                        if isinstance(value, str) and len(str(value)) < 100:
                            print(f"      {key}: {value}")
        
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
    
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_contamination_in_pdf()
