"""
Test production extraction with the 1033940.pdf file
"""
import requests
import json
import time

# Production URL
BASE_URL = "https://wolf.law.uw.edu/casestrainer/api"

def test_pdf_upload():
    """Test PDF upload and extraction"""
    
    # Upload PDF
    print("Uploading PDF to production...")
    with open('1033940.pdf', 'rb') as f:
        files = {'file': ('1033940.pdf', f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/analyze", files=files)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    task_id = result.get('task_id') or result.get('metadata', {}).get('job_id') or result.get('request_id')
    
    if not task_id:
        print("No task_id received")
        print(json.dumps(result, indent=2))
        return
    
    print(f"Task ID: {task_id}")
    print("Waiting for processing...")
    
    # Poll for results
    max_attempts = 60
    for i in range(max_attempts):
        time.sleep(2)
        status_response = requests.get(f"{BASE_URL}/task/{task_id}")
        
        if status_response.status_code != 200:
            print(f"Status check failed: {status_response.status_code}")
            continue
        
        status_data = status_response.json()
        state = status_data.get('state', 'UNKNOWN')
        
        print(f"Attempt {i+1}/{max_attempts}: State = {state}")
        
        if state == 'SUCCESS':
            print("\n" + "="*80)
            print("EXTRACTION COMPLETE!")
            print("="*80)
            
            citations = status_data.get('result', {}).get('citations', [])
            print(f"\nTotal citations: {len(citations)}")
            
            # Analyze extraction success
            with_names = 0
            without_names = 0
            examples_with = []
            examples_without = []
            
            for cit in citations:
                case_name = cit.get('extracted_case_name', '')
                citation_text = cit.get('citation', '')
                
                if case_name and case_name != 'N/A' and case_name.strip():
                    with_names += 1
                    if len(examples_with) < 5:
                        examples_with.append({
                            'citation': citation_text,
                            'name': case_name
                        })
                else:
                    without_names += 1
                    if len(examples_without) < 5:
                        examples_without.append({
                            'citation': citation_text,
                            'name': case_name if case_name else '(empty)'
                        })
            
            total = len(citations)
            success_rate = (with_names / total * 100) if total > 0 else 0
            
            print("\n" + "="*80)
            print("EXTRACTION STATISTICS")
            print("="*80)
            print(f"Citations WITH case names: {with_names} ({success_rate:.1f}%)")
            print(f"Citations WITHOUT case names: {without_names} ({100-success_rate:.1f}%)")
            
            print("\n" + "="*80)
            print("SUCCESSFUL EXTRACTIONS (First 5)")
            print("="*80)
            for ex in examples_with:
                print(f"\n{ex['citation']}")
                print(f"  → {ex['name']}")
            
            print("\n" + "="*80)
            print("FAILED EXTRACTIONS (First 5)")
            print("="*80)
            for ex in examples_without:
                print(f"\n{ex['citation']}")
                print(f"  → {ex['name']}")
            
            # Save full results
            with open('production_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
            print("\n\nFull results saved to: production_test_results.json")
            
            return
        
        elif state in ['FAILURE', 'REVOKED']:
            print(f"\nTask failed with state: {state}")
            print(json.dumps(status_data, indent=2))
            return
    
    print("\nTimeout waiting for results")

if __name__ == "__main__":
    test_pdf_upload()
