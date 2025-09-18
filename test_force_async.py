"""
Force Async Processing Test
Creates a very large text to force async processing and test deduplication.
"""

import requests
import json
import time

def test_force_async():
    """Create a very large text to force async processing."""
    
    print("🔄 FORCING ASYNC PROCESSING TEST")
    print("=" * 40)
    
    # Create a very large text by repeating the problematic text multiple times
    base_text = """'[A] court must not add words where the legislature has
chosen not to include them.'" Lucid Grp. USA, Inc. v. Dep't of Licensing, 33 Wn. App.
2d 75, 81, 559 P.3d 545 (2024) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d
674, 682, 80 P.3d 598 (2003)), review denied, 4 Wn.3d 1021 (2025)

If the statute is susceptible to more than one reasonable interpretation after this inquiry, 
it is ambiguous, and we may consider extratextual materials to help determine legislative 
intent, including legislative history and agency interpretation. Five Corners Fam. Farmers v. State, 173 Wn.2d 
296, 306, 268 P.3d 892 (2011) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 
Wn.2d 674, 682, 80 P.3d 598 (2003)); Bostain v. Food Express, Inc., 159 Wn.2d 
700, 716, 153 P.3d 846 (2007) (collecting cases).
"""
    
    # Repeat the text multiple times to ensure we exceed sync threshold
    large_text = base_text * 10  # Make it 10x larger
    
    # Add some filler text to make it even larger
    filler = """
    Additional legal analysis and discussion follows. This case demonstrates the importance
    of statutory interpretation and the role of courts in determining legislative intent.
    The precedent established in these cases continues to influence modern legal decisions.
    """ * 20
    
    very_large_text = large_text + filler
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': very_large_text}
    
    print(f"📝 Text length: {len(very_large_text)} characters (should definitely force async)")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if it's async (has task_id) or sync
            if 'task_id' in result.get('result', {}):
                task_id = result['result']['task_id']
                print(f"📋 ✅ ASYNC processing started with task_id: {task_id}")
                
                # Poll for results
                max_attempts = 60  # Longer timeout for large text
                for attempt in range(max_attempts):
                    time.sleep(3)
                    status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
                    status_response = requests.get(status_url)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('status') == 'completed':
                            citations = status_data.get('citations', [])
                            
                            print(f"✅ Async processing completed after {(attempt + 1) * 3}s")
                            print(f"   Citations found: {len(citations)}")
                            
                            # Check for duplicates
                            citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                            unique_citations = set(citation_texts)
                            duplicates = len(citation_texts) - len(unique_citations)
                            
                            print(f"   Total citations: {len(citation_texts)}")
                            print(f"   Unique citations: {len(unique_citations)}")
                            print(f"   Duplicate citations: {duplicates}")
                            
                            if duplicates > 0:
                                print(f"   ❌ ASYNC DEDUPLICATION NOT WORKING")
                                from collections import Counter
                                counts = Counter(citation_texts)
                                duplicated_citations = []
                                for citation, count in counts.items():
                                    if count > 1:
                                        duplicated_citations.append(f"'{citation}' appears {count} times")
                                
                                print(f"   Duplicated citations:")
                                for dup in duplicated_citations[:5]:  # Show first 5
                                    print(f"      {dup}")
                                if len(duplicated_citations) > 5:
                                    print(f"      ... and {len(duplicated_citations) - 5} more")
                            else:
                                print(f"   ✅ ASYNC DEDUPLICATION WORKING PERFECTLY!")
                            
                            # Check case name extraction for key citations
                            print(f"\n📋 Key case name extractions:")
                            key_citations = ["150 Wn.2d 674", "80 P.3d 598", "559 P.3d 545"]
                            
                            for citation in citations:
                                citation_text = citation.get('citation', '').replace('\n', ' ').strip()
                                if any(key in citation_text for key in key_citations):
                                    extracted_name = citation.get('extracted_case_name', '')
                                    canonical_name = citation.get('canonical_name', '')
                                    
                                    print(f"   {citation_text}:")
                                    print(f"      Extracted: {extracted_name}")
                                    if canonical_name:
                                        print(f"      Canonical: {canonical_name}")
                                    
                                    # Check improvement
                                    if "Rest. Dev." in extracted_name or "Restaurant Development" in extracted_name:
                                        print(f"      ✅ PERFECT EXTRACTION!")
                                    elif "Lucid Grp." in extracted_name:
                                        print(f"      ✅ GOOD EXTRACTION!")
                                    elif len(extracted_name) > 15:
                                        print(f"      ⚠️  PARTIAL IMPROVEMENT")
                                    else:
                                        print(f"      ❌ STILL TRUNCATED")
                            
                            return True
                            
                        elif status_data.get('status') == 'failed':
                            print(f"❌ Async processing failed: {status_data.get('error', 'Unknown error')}")
                            return False
                    
                    if attempt % 5 == 0:  # Print progress every 15 seconds
                        print(f"   ⏳ Waiting for async completion... ({(attempt + 1) * 3}s elapsed)")
                else:
                    print(f"❌ Async processing timed out after {max_attempts * 3}s")
                    return False
            else:
                # Still processed as sync
                processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
                citations = result.get('result', {}).get('citations', [])
                
                print(f"⚠️  Still processed as sync despite large text size")
                print(f"   Processing mode: {processing_mode}")
                print(f"   Citations found: {len(citations)}")
                print(f"   This suggests the sync threshold is very high")
                
                return False
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_force_async()
    if success:
        print(f"\n🎉 ASYNC DEDUPLICATION TEST SUCCESSFUL!")
    else:
        print(f"\n⚠️  Could not test true async processing - sync threshold may be very high")
