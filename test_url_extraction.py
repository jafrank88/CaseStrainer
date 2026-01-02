#!/usr/bin/env python3
"""Test script for URL endpoint - no verification for faster results"""
import requests
import json
import time

def check_task_status(task_id):
    """Poll task status until complete"""
    url = f'http://localhost:5000/casestrainer/api/task_status/{task_id}'
    max_wait = 120  # Wait up to 120 seconds for large document
    start = time.time()
    
    while time.time() - start < max_wait:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                print(f'  Task status: {status}')
                
                if status == 'completed':
                    return data
                elif status == 'failed':
                    print(f'  Task failed: {data.get("error", "Unknown error")}')
                    return data
            elif response.status_code == 404:
                print(f'  Task not found (may still be processing)...')
            else:
                print(f'  Unexpected status: {response.status_code}')
            
            time.sleep(3)  # Wait 3 seconds before checking again
        except Exception as e:
            print(f'  Error checking status: {e}')
            time.sleep(3)
    
    print(f'  Timeout waiting for task completion')
    return None

def analyze_results(data):
    """Analyze and display citation/cluster results"""
    citations = data.get('citations', [])
    clusters = data.get('clusters', [])
    
    print(f'\n{"="*80}')
    print(f'RESULTS ANALYSIS')
    print(f'{"="*80}')
    print(f'Total Citations: {len(citations)}')
    print(f'Total Clusters: {len(clusters)}')
    
    if citations:
        print(f'\n📋 Citation Analysis:')
        # Group by citation type
        citation_types = {}
        for cit in citations:
            cit_text = cit.get('citation', cit.get('text', 'Unknown'))
            # Extract reporter type
            if 'Wn.' in cit_text or 'Wash.' in cit_text:
                reporter = 'Washington'
            elif 'P.' in cit_text or 'P.2d' in cit_text or 'P.3d' in cit_text:
                reporter = 'Pacific Reporter'
            elif 'F.' in cit_text or 'F.2d' in cit_text or 'F.3d' in cit_text:
                reporter = 'Federal Reporter'
            elif 'S.Ct.' in cit_text or 'U.S.' in cit_text:
                reporter = 'US Supreme Court'
            else:
                reporter = 'Other'
            
            citation_types[reporter] = citation_types.get(reporter, 0) + 1
        
        for reporter, count in sorted(citation_types.items(), key=lambda x: x[1], reverse=True):
            print(f'  - {reporter}: {count} citations')
        
        print(f'\n✅ Sample Citations (first 5):')
        for i, cit in enumerate(citations[:5], 1):
            cit_text = cit.get('citation', cit.get('text', 'N/A'))
            extracted_name = cit.get('extracted_case_name', 'N/A')
            canonical_name = cit.get('canonical_name', 'N/A')
            print(f'  {i}. {cit_text}')
            print(f'     Extracted Name: {extracted_name}')
            print(f'     Canonical Name: {canonical_name if canonical_name != "N/A" else "Not verified"}')
    else:
        print(f'\n⚠️  No citations found!')
    
    if clusters:
        print(f'\n📊 Cluster Analysis:')
        print(f'  Average citations per cluster: {len(citations) / len(clusters):.2f}' if citations else 'N/A')
        
        # Analyze cluster sizes
        cluster_sizes = [len(cluster.get('citations', cluster.get('cluster_members', []))) for cluster in clusters]
        if cluster_sizes:
            print(f'  Smallest cluster: {min(cluster_sizes)} citation(s)')
            print(f'  Largest cluster: {max(cluster_sizes)} citation(s)')
            print(f'  Clusters with 1 citation: {sum(1 for s in cluster_sizes if s == 1)}')
            print(f'  Clusters with 2+ citations: {sum(1 for s in cluster_sizes if s >= 2)}')
        
        print(f'\n✅ Sample Clusters (first 3):')
        for i, cluster in enumerate(clusters[:3], 1):
            cluster_citations = cluster.get('citations', [])
            cluster_members = cluster.get('cluster_members', [])
            members = cluster_citations if cluster_citations else cluster_members
            
            print(f'  Cluster {i}: {len(members)} citation(s)')
            canonical_name = cluster.get('canonical_name', 'N/A')
            canonical_date = cluster.get('canonical_date', 'N/A')
            extracted_name = cluster.get('extracted_case_name', 'N/A')
            extracted_date = cluster.get('extracted_date', 'N/A')
            
            print(f'    Canonical: {canonical_name} ({canonical_date if canonical_date != "N/A" else "N/A"})')
            print(f'    Extracted: {extracted_name} ({extracted_date if extracted_date != "N/A" else "N/A"})')
            
            if members:
                print(f'    Citations: {", ".join([str(m) if isinstance(m, str) else m.get("citation", m.get("text", "N/A")) for m in members[:3]])}...')
    else:
        print(f'\n⚠️  No clusters found!')
    
    return len(citations), len(clusters)

def test_url_endpoint():
    url = 'http://localhost:5000/casestrainer/api/analyze'
    payload = {
        'type': 'url',
        'url': 'https://www.courts.wa.gov/opinions/pdf/1031351.pdf',
        'client_request_id': f'test-url-noverify-{int(time.time())}',
        'enable_verification': False  # Disable verification for faster results
    }
    
    print('Testing URL endpoint (no verification for faster results)...')
    print(f'URL: {payload["url"]}')
    print('Sending request...')
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=120
        )
        
        print(f'\nStatus Code: {response.status_code}')
        
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
        else:
            data = {'raw_response': response.text[:500]}
        
        print(f'Response Keys: {list(data.keys())}')
        print(f'Status: {data.get("status", "unknown")}')
        print(f'Task ID: {data.get("task_id", "None")}')
        
        # If async, poll for results
        if data.get('status') == 'processing' or data.get('task_id'):
            task_id = data.get('task_id') or data.get('request_id')
            print(f'\n📋 Polling for async task results (task_id: {task_id})...')
            result = check_task_status(task_id)
            
            if result:
                data = result
        
        # Analyze results
        citations_count, clusters_count = analyze_results(data)
        
        if citations_count == 0:
            print(f'\n❌ ERROR: No citations extracted from document!')
            print(f'Full response: {json.dumps(data, indent=2)[:2000]}')
        elif clusters_count == 0:
            print(f'\n⚠️  WARNING: Citations found but no clusters created!')
        else:
            print(f'\n✅ SUCCESS: {citations_count} citations organized into {clusters_count} clusters')
            
    except requests.exceptions.Timeout:
        print('ERROR: Request timed out after 120 seconds')
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_url_endpoint()
