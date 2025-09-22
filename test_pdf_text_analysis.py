#!/usr/bin/env python3

import requests
import json
import time

def test_pdf_text_analysis():
    """Test the extracted PDF text for contamination analysis."""
    
    print("📄 PDF TEXT CONTAMINATION ANALYSIS")
    print("=" * 60)
    
    # Read the extracted text
    try:
        with open("extracted_pdf_text.txt", "r", encoding="utf-8") as f:
            pdf_text = f.read()
    except FileNotFoundError:
        print("❌ extracted_pdf_text.txt not found. Run extract_pdf_text.py first.")
        return
    
    print(f"📊 Text size: {len(pdf_text):,} characters")
    print(f"📊 Expected routing: {'SYNC' if len(pdf_text) < 5120 else 'ASYNC'}")
    print()
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # Test with the full text
    data = {"text": pdf_text, "type": "text"}
    
    print("🔄 Sending text for analysis...")
    
    try:
        start_time = time.time()
        response = requests.post(url, data=data, timeout=60)
        response_time = time.time() - start_time
        
        print(f"⏱️  Initial response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check processing mode
            task_id = result.get('task_id')
            processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
            
            if task_id:
                print(f"📊 Processing Mode: ASYNC (Task ID: {task_id})")
                print("⏳ Waiting for async processing to complete...")
                
                # Poll for completion
                for attempt in range(60):  # Wait up to 10 minutes
                    time.sleep(10)
                    status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
                    status_response = requests.get(status_url, timeout=30)
                    
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        status = status_result.get('status', 'unknown')
                        
                        print(f"   Attempt {attempt + 1}: Status = {status}")
                        
                        if status == 'completed':
                            result = status_result
                            print("✅ Processing completed!")
                            break
                        elif status == 'failed':
                            print(f"   ❌ Processing failed: {status_result.get('error', 'unknown error')}")
                            return
                        elif attempt % 6 == 0:  # Every minute, show progress
                            progress = status_result.get('progress_data', {})
                            overall_progress = progress.get('overall_progress', 0)
                            current_step = progress.get('current_step_name', 'Processing...')
                            print(f"   Progress: {overall_progress}% - {current_step}")
                    else:
                        print(f"   ❌ Status check failed: {status_response.status_code}")
                        return
                else:
                    print("   ⏰ Timeout waiting for processing to complete")
                    return
            else:
                print(f"📊 Processing Mode: SYNC ({processing_mode})")
            
            # Analyze the results
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"\n📋 PROCESSING RESULTS:")
            print(f"   Citations found: {len(citations)}")
            print(f"   Clusters found: {len(clusters)}")
            print()
            
            if not citations:
                print("❌ No citations found - cannot analyze contamination")
                return
            
            print("🔍 CONTAMINATION ANALYSIS:")
            print("=" * 50)
            
            contamination_stats = {
                'total_citations': len(citations),
                'extracted_only': 0,
                'canonical_only': 0,
                'both_same': 0,
                'both_different': 0,
                'neither': 0,
                'verified_count': 0
            }
            
            contamination_examples = []
            clean_examples = []
            
            for i, citation in enumerate(citations):
                citation_text = citation.get('citation', '')
                extracted_name = citation.get('extracted_case_name', '')
                canonical_name = citation.get('canonical_name', '')
                cluster_name = citation.get('cluster_case_name', '')
                verified = citation.get('verified', False)
                
                if verified:
                    contamination_stats['verified_count'] += 1
                
                # Normalize for comparison
                extracted_clean = extracted_name.strip() if extracted_name and extracted_name != 'N/A' else ''
                canonical_clean = canonical_name.strip() if canonical_name and canonical_name != 'N/A' else ''
                
                has_extracted = bool(extracted_clean)
                has_canonical = bool(canonical_clean)
                
                if has_extracted and has_canonical:
                    if extracted_clean == canonical_clean:
                        contamination_stats['both_same'] += 1
                        contamination_examples.append({
                            'citation': citation_text,
                            'name': extracted_clean,
                            'verified': verified,
                            'index': i + 1
                        })
                    else:
                        contamination_stats['both_different'] += 1
                        clean_examples.append({
                            'citation': citation_text,
                            'extracted': extracted_clean,
                            'canonical': canonical_clean,
                            'verified': verified,
                            'index': i + 1
                        })
                elif has_extracted and not has_canonical:
                    contamination_stats['extracted_only'] += 1
                elif not has_extracted and has_canonical:
                    contamination_stats['canonical_only'] += 1
                else:
                    contamination_stats['neither'] += 1
            
            # Calculate contamination rate
            total_with_both = contamination_stats['both_same'] + contamination_stats['both_different']
            contamination_rate = (contamination_stats['both_same'] / total_with_both * 100) if total_with_both > 0 else 0
            
            print(f"📊 CONTAMINATION STATISTICS:")
            print("-" * 35)
            total = contamination_stats['total_citations']
            
            for key, value in contamination_stats.items():
                if key != 'total_citations':
                    percentage = (value / total * 100) if total > 0 else 0
                    print(f"   {key.replace('_', ' ').title()}: {value} ({percentage:.1f}%)")
            
            print(f"\n🎯 CONTAMINATION ASSESSMENT:")
            print("-" * 35)
            
            if contamination_rate > 80:
                assessment = "🚨 SEVERE CONTAMINATION"
                color = "RED"
            elif contamination_rate > 60:
                assessment = "⚠️  HIGH CONTAMINATION"
                color = "ORANGE"
            elif contamination_rate > 40:
                assessment = "🟡 MODERATE CONTAMINATION"
                color = "YELLOW"
            elif contamination_rate > 20:
                assessment = "🟢 LOW CONTAMINATION"
                color = "GREEN"
            else:
                assessment = "✅ MINIMAL CONTAMINATION"
                color = "GREEN"
            
            print(f"   Status: {assessment}")
            print(f"   Rate: {contamination_rate:.1f}% of citations with both names have identical values")
            print()
            
            # Show examples
            if contamination_examples:
                print(f"🚨 CONTAMINATION EXAMPLES (showing first 5):")
                print("-" * 45)
                for example in contamination_examples[:5]:
                    print(f"   #{example['index']}: {example['citation']}")
                    print(f"      Name: '{example['name']}'")
                    print(f"      Verified: {example['verified']}")
                    print()
            
            if clean_examples:
                print(f"✅ CLEAN SEPARATION EXAMPLES (showing first 3):")
                print("-" * 45)
                for example in clean_examples[:3]:
                    print(f"   #{example['index']}: {example['citation']}")
                    print(f"      Extracted: '{example['extracted']}'")
                    print(f"      Canonical: '{example['canonical']}'")
                    print(f"      Verified: {example['verified']}")
                    print()
            
            # Verification analysis
            verified_rate = (contamination_stats['verified_count'] / total * 100) if total > 0 else 0
            print(f"📊 VERIFICATION ANALYSIS:")
            print("-" * 30)
            print(f"   Verified citations: {contamination_stats['verified_count']}/{total} ({verified_rate:.1f}%)")
            
            if verified_rate > 50:
                print("   ✅ Good verification rate - canonical names are being populated")
            elif verified_rate > 20:
                print("   ⚠️  Moderate verification rate")
            else:
                print("   ❌ Low verification rate - most citations unverified")
            
            print(f"\n🎯 ROOT CAUSE ANALYSIS:")
            print("=" * 30)
            
            if contamination_rate > 70:
                print("🚨 LIKELY CAUSES:")
                print("   1. Extracted names are being overwritten with canonical names")
                print("   2. Verification process is contaminating extracted data")
                print("   3. Case name extraction is using canonical sources")
                print("   4. Fallback logic is using canonical names for extracted names")
                
                print("\n🔧 RECOMMENDED FIXES:")
                print("   1. Check case name extraction logic in unified_citation_processor_v2.py")
                print("   2. Verify no fallback from canonical to extracted names")
                print("   3. Ensure verification doesn't overwrite extracted names")
                print("   4. Add logging to track where names are being set")
            else:
                print("✅ Data separation appears to be working correctly")
                print("   The identical names may be legitimate matches")
        
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
    
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_text_analysis()
