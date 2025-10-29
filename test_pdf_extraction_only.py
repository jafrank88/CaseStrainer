#!/usr/bin/env python
"""Test PDF extraction without verification to assess accuracy."""

import requests
import time
import os

# Use the same PDF
file_path = "d:\\dev\\casestrainer\\Lavery v. The Department of Financial and Professional Regulation 2025 IL 130033.pdf"

print("=" * 80)
print("PDF EXTRACTION ACCURACY ASSESSMENT")
print("=" * 80)
print(f"PDF: {os.path.basename(file_path)}")
print(f"Expected citations: 34 (from manual analysis)")

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
files = {'file': open(file_path, 'rb')}
data = {
    "enable_verification": False,  # Skip verification for speed
    "client_request_id": f"pdf_extract_{int(time.time())}"
}

try:
    response = requests.post(url, files=files, data=data, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    print(f"\n✅ PDF submitted for extraction!")
    print(f"Status: {result.get('status')}")
    print(f"Processing mode: {result.get('metadata', {}).get('processing_mode')}")
    
    task_id = result.get('task_id')
    if task_id:
        print(f"✅ Async processing - Task ID: {task_id}")
        
        # Monitor progress
        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
        print(f"\nMonitoring extraction progress...")
        
        for i in range(30):  # 30 second timeout
            try:
                status_response = requests.get(status_url, timeout=5)
                status = status_response.json()
                
                progress = status.get('verification_status', {}).get('progress_percent', 0)
                message = status.get('verification_status', {}).get('current_message', '')
                
                if progress > 0:
                    print(f"  Progress: {progress}% - {message}")
                
                if status.get('status') == 'completed':
                    print(f"\n✅ EXTRACTION COMPLETED!")
                    
                    if 'result' in status:
                        result = status['result']
                        citations = result.get('citations', [])
                        clusters = result.get('clusters', [])
                        
                        print("\n" + "=" * 80)
                        print("EXTRACTION ACCURACY ANALYSIS")
                        print("=" * 80)
                        
                        print(f"\n📊 RESULTS:")
                        print(f"Citations extracted by CaseStrainer: {len(citations)}")
                        print(f"Expected citations (manual): 34")
                        
                        # Show all extracted citations
                        print(f"\n📋 Citations Extracted by CaseStrainer:")
                        for i, cit in enumerate(citations):
                            print(f"  {i+1}. {cit.get('citation', 'N/A')}")
                            if cit.get('extracted_case_name'):
                                case_name = cit.get('extracted_case_name')
                                if len(case_name) > 70:
                                    case_name = case_name[:67] + "..."
                                print(f"     Case: {case_name}")
                        
                        # Check accuracy
                        extracted_cits = set(c.get('citation') for c in citations)
                        expected_cits = {
                            '72 Ill. 2d 485', '376 Ill. 346', '241 Ill. 2d 281', '377 Ill. 255',
                            '148 Ill. 2d 151', '367 Ill. 436', '235 Ill. 2d', '61 Ill. 2d',
                            '85 Ill. 516', '249 Ill. 554', '198 Ill. 2d', '137 Ill. 2d',
                            '366 Ill. 216', '201 Ill. 2d', '216 Ill. 2d', '239 Ill. 2d',
                            '104 Ill. 2d', '82 Ill. 2d', '67 Ill. 2d', '131 Ill. 2d',
                            '93 Ill. 2d', '68 Ill. 2d', '347 Ill. App. 3d', '201 Ill. App. 3d',
                            '4 Ill. App. 2d', '118 Ill. App. 3d', '115 Ill. App. 3d',
                            '306 Ill. App. 3d', '340 U.S. 135', '205 U.S. 349',
                            '437 U.S. 678', '601 U.S. 42', '491 U.S. 274'
                        }
                        
                        print(f"\n🎯 ACCURACY ASSESSMENT:")
                        print(f"Expected: 34 citations")
                        print(f"Extracted: {len(citations)} citations")
                        print(f"Accuracy rate: {len(citations)/34*100:.1f}%")
                        
                        # Check for matches
                        matches = 0
                        for cit in extracted_cits:
                            for exp in expected_cits:
                                if cit in exp or exp in cit:
                                    matches += 1
                                    break
                        
                        print(f"Citations matching expected patterns: {matches}")
                        print(f"Match accuracy: {matches/34*100:.1f}%")
                        
                        # Case name extraction quality
                        with_names = sum(1 for c in citations if c.get('extracted_case_name'))
                        print(f"\n🏛️  Case Name Extraction:")
                        print(f"With case names: {with_names}/{len(citations)} ({with_names/len(citations)*100:.1f}%)")
                        
                        # Clustering analysis
                        print(f"\n🔗 Clustering:")
                        print(f"Clusters created: {len(clusters)}")
                        if len(clusters) > 0:
                            avg_cluster_size = sum(len(c.get('citations', [])) for c in clusters) / len(clusters)
                            print(f"Average cluster size: {avg_cluster_size:.1f}")
                        
                        print(f"\n🎉 ASSESSMENT COMPLETE:")
                        if len(citations) >= 30:
                            print("✅ EXTRACTION: Excellent (>90% of expected)")
                        elif len(citations) >= 25:
                            print("✅ EXTRACTION: Good (>70% of expected)")
                        elif len(citations) >= 17:
                            print("⚠️  EXTRACTION: Fair (>50% of expected)")
                        else:
                            print("❌ EXTRACTION: Poor (<50% of expected)")
                    
                    break
                elif status.get('status') == 'failed':
                    print(f"\n❌ Processing failed: {status.get('error', 'Unknown error')}")
                    break
                    
                time.sleep(1)
                
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(1)
        else:
            print(f"\n⏰ Timeout: Extraction took too long")
    else:
        print(f"❌ Unexpected: Processed synchronously")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    files['file'].close()
