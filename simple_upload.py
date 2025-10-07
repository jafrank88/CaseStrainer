#!/usr/bin/env python3
"""
Simple script to upload a PDF and extract citations.
"""

import os
import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

def check_task_status(task_id, max_attempts=30, delay=2):
    """Check the status of a task until it's complete."""
    import time
    
    url = f"https://wolf.law.uw.edu/casestrainer/api/analyze/status/{task_id}"
    
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"\n🔄 Checking status (attempt {attempt}/{max_attempts})...")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Save the latest response
                with open('api_response.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                
                # Check if processing is complete
                if result.get('status') == 'completed':
                    print("✅ Processing complete!")
                    return result
                elif result.get('status') == 'failed':
                    print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                    return None
                else:
                    # Show progress
                    progress = result.get('progress_data', {})
                    print(f"Status: {result.get('status', 'processing')}")
                    print(f"Progress: {progress.get('overall_progress', 0)}% - {progress.get('current_message', 'Processing')}")
            else:
                print(f"⚠️  Status check failed: {response.status_code}")
                print(f"Response: {response.text[:500]}")
            
            # Wait before next check
            if attempt < max_attempts:
                time.sleep(delay)
                
        except Exception as e:
            print(f"⚠️  Error checking status: {e}")
            if attempt < max_attempts:
                time.sleep(delay)
    
    print(f"❌ Max attempts reached. Task may still be processing.")
    return None

def upload_and_extract(pdf_path):
    """Upload a PDF and extract citations."""
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    # Prepare the file upload
    with open(pdf_path, 'rb') as f:
        multipart_data = MultipartEncoder(
            fields={
                'file': (os.path.basename(pdf_path), f, 'application/pdf'),
                'options': json.dumps({
                    'convert_pdf_to_md': True,
                    'is_binary': True,
                    'file_type': 'application/pdf',
                    'file_ext': 'pdf',
                    'track_progress': True
                })
            }
        )
        
        headers = {
            'Content-Type': multipart_data.content_type,
            'Accept': 'application/json',
        }
        
        try:
            print(f"📤 Uploading {os.path.basename(pdf_path)}...")
            response = requests.post(url, data=multipart_data, headers=headers, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                
                # Save the initial response
                with open('api_response_initial.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                
                print("✅ Upload successful!")
                
                # Check if we have a task ID for async processing
                task_id = result.get('request_id')
                if task_id:
                    print(f"🆔 Task ID: {task_id}")
                    print("⏳ Processing document (this may take a few minutes)...")
                    
                    # Wait for processing to complete
                    final_result = check_task_status(task_id)
                    
                    if final_result:
                        # Save the final result
                        with open('api_response_final.json', 'w', encoding='utf-8') as f:
                            json.dump(final_result, f, indent=2)
                        
                        # Show citations if available
                        if 'citations' in final_result and final_result['citations']:
                            print("\n📚 Extracted Citations:")
                            for i, cite in enumerate(final_result['citations'][:10], 1):
                                print(f"  {i}. {cite.get('citation')} - {cite.get('case_name', 'N/A')}")
                            
                            if len(final_result['citations']) > 10:
                                print(f"  ... and {len(final_result['citations']) - 10} more")
                        else:
                            print("\nℹ️ No citations found in the document.")
                        
                        return True
                    else:
                        return False
                else:
                    print("❌ No task ID received in the response.")
                    return False
                
            else:
                print(f"❌ Error! Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    # Try to find the PDF file
    pdf_path = os.path.join(os.path.dirname(__file__), "1033940.pdf")
    
    if not os.path.exists(pdf_path):
        print("❌ PDF file not found. Please place your PDF in the same directory as this script.")
        return
    
    print(f"🔍 Processing: {pdf_path}")
    print(f"📄 File size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
    
    # Process the PDF
    success = upload_and_extract(pdf_path)
    
    if success:
        print("\n✅ Processing complete!")
    else:
        print("\n❌ Processing failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
