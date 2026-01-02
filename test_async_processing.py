#!/usr/bin/env python3
"""
Test async processing to diagnose the "unknown" status issue
"""

import requests
import time
import tempfile
import os

def test_async_processing():
    """Test async processing with a file upload"""
    
    print("TESTING ASYNC PROCESSING")
    print("=" * 35)
    
    base_url = "https://wolf.law.uw.edu/casestrainer"
    
    # Create a temporary PDF-like file (larger content to trigger async)
    test_content = """
    This is a longer legal document that should trigger async processing.
    In the case of Smith v. Johnson, 123 F.3d 456 (9th Cir. 2023), the court
    considered important precedent. This decision built upon earlier rulings
    in cases like Brown v. Board of Education, 347 U.S. 483 (1954) and
    more recent decisions in the Ninth Circuit.
    
    The legal principle established in Smith v. Johnson has been cited
    in numerous subsequent cases, including Jones v. Smith, 456 F.4d 789 (9th Cir. 2024)
    and Anderson v. Wilson, 567 F.5d 123 (9th Cir. 2024). These cases
    demonstrate the ongoing importance of the original decision.
    
    Furthermore, the Supreme Court has addressed related issues in
    recent terms, as seen in cases like United States v. Martinez, 987 U.S. 123 (2024)
    and Federal Trade Commission v. Amazon, 876 F.3d 234 (D.C. Cir. 2023).
    """ * 10  # Repeat to make it larger
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        print(f"\n1. Created test file: {os.path.basename(temp_file)}")
        print(f"   File size: {os.path.getsize(temp_file)} bytes")
        
        # Upload the file
        print("\n2. Uploading file for processing...")
        with open(temp_file, 'rb') as f:
            files = {'file': (os.path.basename(temp_file), f, 'text/plain')}
            data = {'type': 'file'}
            
            response = requests.post(
                f"{base_url}/api/analyze",
                files=files,
                data=data,
                timeout=30
            )
        
        print(f"   Upload status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Response type: {'Immediate' if 'citations' in result else 'Async'}")
            
            if 'task_id' in result:
                # Async processing - this is what we want to test
                task_id = result['task_id']
                print(f"   Task ID: {task_id}")
                
                # Monitor task status
                print("\n3. Monitoring task status...")
                unknown_count = 0
                
                for i in range(30):  # Check for 60 seconds
                    status_response = requests.get(
                        f"{base_url}/api/task_status/{task_id}",
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        progress = status_data.get('progress', 0)
                        error = status_data.get('error')
                        
                        print(f"   Check {i+1:2d}: Status={status:12s} Progress={progress:3d}%")
                        
                        if status == 'completed':
                            print("   SUCCESS: Task completed!")
                            result = status_data.get('result', {})
                            citations = result.get('citations', [])
                            clusters = result.get('clusters', [])
                            print(f"   Results: {len(citations)} citations, {len(clusters)} clusters")
                            break
                        elif status == 'failed':
                            print(f"   ERROR: Task failed - {error}")
                            break
                        elif status == 'unknown':
                            unknown_count += 1
                            if unknown_count == 1:
                                print("   WARNING: First 'unknown' status detected")
                                print("   This may indicate a worker communication issue")
                            elif unknown_count > 5:
                                print("   ERROR: Multiple 'unknown' statuses - likely stuck")
                                break
                        elif status == 'queued':
                            print("   INFO: Task is queued waiting for worker")
                        elif status == 'started':
                            print("   INFO: Task is being processed")
                        
                        time.sleep(2)
                    else:
                        print(f"   ERROR: Status check failed - {status_response.status_code}")
                        break
                else:
                    print("   TIMEOUT: Task did not complete in 60 seconds")
                    print(f"   Final unknown count: {unknown_count}")
            
            elif 'citations' in result:
                print("   Immediate processing (file too small for async)")
            
        else:
            print(f"   ERROR: Upload failed - {response.text}")
    
    except Exception as e:
        print(f"   ERROR: {e}")
    
    finally:
        # Clean up
        os.unlink(temp_file)
        print(f"\n4. Cleaned up temporary file")
    
    print("\nDIAGNOSIS:")
    print("- If status goes to 'unknown' and stays there: worker communication issue")
    print("- If status stays 'queued': workers may not be processing")
    print("- If status stays 'started' but no progress: worker may be stuck")

if __name__ == "__main__":
    test_async_processing()
