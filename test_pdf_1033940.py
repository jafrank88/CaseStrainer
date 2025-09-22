#!/usr/bin/env python3

import requests
import json
import time

def test_pdf_1033940():
    """Test the 1033940.pdf file for sync processing and name extraction analysis."""
    
    print("📄 PDF 1033940 END-TO-END TEST")
    print("=" * 60)
    
    pdf_path = "D:\\dev\\casestrainer\\1033940.pdf"
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    print(f"📁 Testing PDF: {pdf_path}")
    print()
    
    try:
        # Upload the PDF file
        with open(pdf_path, 'rb') as pdf_file:
            files = {'file': ('1033940.pdf', pdf_file, 'application/pdf')}
            data = {'type': 'file'}
            
            print("📤 Uploading PDF file...")
            start_time = time.time()
            response = requests.post(url, files=files, data=data, timeout=60)
            response_time = time.time() - start_time
            
            print(f"⏱️  Upload and processing time: {response_time:.2f}s")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if it was processed sync or async
                task_id = result.get('task_id')
                processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
                
                if task_id:
                    print(f"📊 Processing Mode: ASYNC (Task ID: {task_id})")
                    print("⏳ Waiting for async processing to complete...")
                    
                    # Poll for completion
                    for attempt in range(30):  # Wait up to 5 minutes
                        time.sleep(10)
                        status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
                        status_response = requests.get(status_url, timeout=30)
                        
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            status = status_result.get('status', 'unknown')
                            
                            print(f"   Attempt {attempt + 1}: Status = {status}")
                            
                            if status == 'completed':
                                result = status_result
                                break
                            elif status == 'failed':
                                print(f"   ❌ Processing failed: {status_result.get('error', 'unknown error')}")
                                return
                        else:
                            print(f"   ❌ Status check failed: {status_response.status_code}")
                            return
                    else:
                        print("   ⏰ Timeout waiting for processing to complete")
                        return
                else:
                    print(f"📊 Processing Mode: SYNC ({processing_mode})")
                
                # Analyze results
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                
                print(f"\n📋 RESULTS SUMMARY:")
                print(f"   Citations found: {len(citations)}")
                print(f"   Clusters found: {len(clusters)}")
                print()
                
                if citations:
                    print("🔍 CITATION ANALYSIS:")
                    print("-" * 50)
                    
                    name_analysis = {
                        'extracted_only': 0,
                        'canonical_only': 0,
                        'both_same': 0,
                        'both_different': 0,
                        'neither': 0
                    }
                    
                    contamination_cases = []
                    
                    for i, citation in enumerate(citations[:10], 1):  # Analyze first 10
                        citation_text = citation.get('citation', '')
                        extracted_name = citation.get('extracted_case_name', 'N/A')
                        canonical_name = citation.get('canonical_name', 'N/A')
                        cluster_name = citation.get('cluster_case_name', 'N/A')
                        verified = citation.get('verified', False)
                        
                        print(f"\n📖 Citation {i}: {citation_text}")
                        print(f"   🔍 Extracted: '{extracted_name}'")
                        print(f"   📚 Canonical: '{canonical_name}'")
                        print(f"   🔗 Cluster: '{cluster_name}'")
                        print(f"   ✅ Verified: {verified}")
                        
                        # Analyze name relationships
                        has_extracted = extracted_name not in ['N/A', None, '']
                        has_canonical = canonical_name not in ['N/A', None, '']
                        
                        if has_extracted and has_canonical:
                            if extracted_name == canonical_name:
                                name_analysis['both_same'] += 1
                                print(f"   🟡 SAME: Extracted == Canonical")
                                
                                # Check if this might be contamination
                                if verified and canonical_name != 'N/A':
                                    contamination_cases.append({
                                        'citation': citation_text,
                                        'name': canonical_name,
                                        'reason': 'Extracted matches canonical exactly'
                                    })
                            else:
                                name_analysis['both_different'] += 1
                                print(f"   🟢 DIFFERENT: Extracted ≠ Canonical")
                        elif has_extracted and not has_canonical:
                            name_analysis['extracted_only'] += 1
                            print(f"   🔵 EXTRACTED ONLY")
                        elif not has_extracted and has_canonical:
                            name_analysis['canonical_only'] += 1
                            print(f"   🔴 CANONICAL ONLY (potential contamination)")
                        else:
                            name_analysis['neither'] += 1
                            print(f"   ⚫ NO NAMES")
                    
                    print(f"\n📊 NAME ANALYSIS SUMMARY:")
                    print("-" * 30)
                    total = sum(name_analysis.values())
                    for category, count in name_analysis.items():
                        percentage = (count / total * 100) if total > 0 else 0
                        print(f"   {category.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
                    
                    # Contamination analysis
                    if contamination_cases:
                        print(f"\n🚨 POTENTIAL CONTAMINATION CASES:")
                        print("-" * 40)
                        for case in contamination_cases[:5]:  # Show first 5
                            print(f"   📖 {case['citation']}")
                            print(f"      Name: {case['name']}")
                            print(f"      Reason: {case['reason']}")
                            print()
                    
                    # Check for patterns
                    same_percentage = (name_analysis['both_same'] / total * 100) if total > 0 else 0
                    
                    print(f"\n🎯 CONTAMINATION ASSESSMENT:")
                    print("-" * 35)
                    
                    if same_percentage > 80:
                        print(f"   🚨 HIGH CONTAMINATION RISK: {same_percentage:.1f}% of citations have identical extracted/canonical names")
                        print("   This suggests extracted names may be contaminated with canonical data")
                    elif same_percentage > 50:
                        print(f"   ⚠️  MODERATE CONTAMINATION RISK: {same_percentage:.1f}% identical names")
                        print("   Some contamination may be occurring")
                    elif same_percentage > 20:
                        print(f"   🟡 LOW CONTAMINATION RISK: {same_percentage:.1f}% identical names")
                        print("   This could be normal for well-formatted citations")
                    else:
                        print(f"   ✅ MINIMAL CONTAMINATION: {same_percentage:.1f}% identical names")
                        print("   Extracted and canonical names appear properly separated")
                
                # Cluster analysis
                if clusters:
                    print(f"\n🔗 CLUSTER ANALYSIS:")
                    print("-" * 30)
                    
                    for i, cluster in enumerate(clusters[:5], 1):  # Analyze first 5
                        cluster_id = cluster.get('cluster_id', 'N/A')
                        cluster_extracted = cluster.get('extracted_case_name', 'N/A')
                        cluster_canonical = cluster.get('canonical_name', 'N/A')
                        cluster_size = cluster.get('size', 0)
                        cluster_citations = cluster.get('citations', [])
                        
                        print(f"\n   Cluster {i} ({cluster_id}):")
                        print(f"      Size: {cluster_size} citations")
                        print(f"      Extracted: '{cluster_extracted}'")
                        print(f"      Canonical: '{cluster_canonical}'")
                        print(f"      Citations: {cluster_citations[:3]}{'...' if len(cluster_citations) > 3 else ''}")
                
                print(f"\n🎯 OVERALL ASSESSMENT:")
                print("=" * 30)
                
                if len(citations) > 0:
                    print(f"✅ Citation extraction: {len(citations)} citations found")
                else:
                    print("❌ Citation extraction: No citations found")
                
                if len(clusters) > 0:
                    print(f"✅ Clustering: {len(clusters)} clusters found")
                else:
                    print("⚠️  Clustering: No clusters found")
                
                same_names = name_analysis.get('both_same', 0)
                total_with_both = same_names + name_analysis.get('both_different', 0)
                
                if total_with_both > 0:
                    contamination_rate = (same_names / total_with_both) * 100
                    if contamination_rate > 70:
                        print(f"🚨 Data separation: LIKELY CONTAMINATED ({contamination_rate:.1f}%)")
                    elif contamination_rate > 40:
                        print(f"⚠️  Data separation: POSSIBLY CONTAMINATED ({contamination_rate:.1f}%)")
                    else:
                        print(f"✅ Data separation: APPEARS CLEAN ({contamination_rate:.1f}%)")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text[:500]}...")
                
    except FileNotFoundError:
        print(f"❌ PDF file not found: {pdf_path}")
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_1033940()
