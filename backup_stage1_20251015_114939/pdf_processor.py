#!/usr/bin/env python3
import requests
import time
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder

def upload_pdf(pdf_path, api_base_url):
    """Upload PDF and return task ID for async processing"""
    base_url = api_base_url.rstrip('/')
    if '/api' in base_url:
        base_url = base_url.split('/api')[0]
    
    upload_url = f"{base_url}/casestrainer/api/analyze"
    
    # Create form data with file and options
    form_data = {
        'file': (pdf_path.split('\\')[-1], open(pdf_path, 'rb'), 'application/pdf'),
        'options': json.dumps({
            'convert_pdf_to_md': True,
            'is_binary': True,
            'file_type': 'application/pdf',
            'file_ext': 'pdf',
            'track_progress': True
        })
    }
    
    multipart_data = MultipartEncoder(fields=form_data)
    
    headers = {
        'Content-Type': multipart_data.content_type,
        'Accept': 'application/json',
    }
    
    try:
        print(f"Uploading {pdf_path} to {upload_url}...")
        print(f"Request headers: {headers}")
        print(f"Request data size: {len(multipart_data.to_string())} bytes")
        
        # Increase timeout to 5 minutes (300 seconds) and add streaming upload
        print("Starting file upload (this may take a while for large files)...")
        response = requests.post(
            upload_url, 
            data=multipart_data, 
            headers=headers, 
            timeout=300,  # 5 minute timeout
            stream=True
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        try:
            response_json = response.json()
            print(f"Response JSON: {json.dumps(response_json, indent=2)}")
            return response_json.get('request_id')
        except ValueError:
            print(f"Response is not JSON: {response.text[:500]}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response headers: {e.response.headers}")
            print(f"Response body: {e.response.text[:1000]}")
        return None
    except Exception as e:
        print(f"Unexpected error during upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_task_status(task_id, api_base_url):
    """Check status of an async task using SSE (Server-Sent Events)"""
    import sseclient
    import json
    
    base_url = api_base_url.rstrip('/')
    if '/api' in base_url:
        base_url = base_url.split('/api')[0]
    
    sse_url = f"{base_url}/casestrainer/api/analyze/progress-stream/{task_id}"
    
    try:
        print(f"Connecting to SSE stream at: {sse_url}")
        
        # Add debug headers to help diagnose CORS or other issues
        headers = {
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
        
        print(f"Sending SSE request with headers: {headers}")
        response = requests.get(sse_url, headers=headers, stream=True, timeout=30)
        print(f"SSE response status: {response.status_code}")
        print(f"SSE response headers: {dict(response.headers)}")
        
        # Check if this is actually an SSE stream
        content_type = response.headers.get('content-type', '').lower()
        if 'text/event-stream' not in content_type:
            print(f"Unexpected content type: {content_type}")
            print(f"Response content: {response.text[:1000]}")
            return None
            
        response.raise_for_status()
        
        client = sseclient.SSEClient(response)
        print("SSE client created, waiting for events...")
        
        try:
            for event in client.events():
                try:
                    print(f"Received SSE event: {event.event} - {event.data}")
                    data = json.loads(event.data)
                    print(f"Progress: {data.get('progress', 0)}% - {data.get('status', 'Processing')}")
                    
                    if data.get('complete'):
                        if data.get('error'):
                            print(f"Error: {data.get('error')}")
                            if 'traceback' in data:
                                print(f"Server traceback: {data['traceback']}")
                            return None
                        return data.get('result')
                        
                except json.JSONDecodeError as e:
                    print(f"Error decoding SSE data: {e}")
                    print(f"Raw event data: {event.data}")
                except Exception as e:
                    print(f"Error processing SSE event: {e}")
                    import traceback
                    traceback.print_exc()
                    return None
                    
        except Exception as e:
            print(f"Error in SSE event loop: {e}")
            import traceback
            traceback.print_exc()
            return None
                
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error connecting to SSE stream: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:500]}")
    except Exception as e:
        print(f"Unexpected error with SSE stream: {e}")
    
    return None

def main():
    # Install required packages if not already installed
    try:
        import sseclient
    except ImportError:
        print("Installing required packages...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "sseclient-py", "requests_toolbelt"])
        import sseclient
    
    # Configuration
    import os
    
    # Get the absolute path to the PDF file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(current_dir, "1033940.pdf")
    
    # Check if the PDF exists, if not, use a test file
    test_pdf_path = os.path.join(current_dir, "test.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"Warning: PDF file not found at {pdf_path}")
        
        # Create a test PDF if it doesn't exist
        if not os.path.exists(test_pdf_path):
            print("Creating a test PDF file...")
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                
                c = canvas.Canvas(test_pdf_path, pagesize=letter)
                width, height = letter
                c.drawString(100, height - 100, "Test PDF for CaseStrainer API")
                c.drawString(100, height - 120, "This is a test document containing a citation: Roe v. Wade, 410 U.S. 113 (1973)")
                c.save()
                print(f"Created test PDF at {test_pdf_path}")
            except Exception as e:
                print(f"Error creating test PDF: {e}")
                return
        
        pdf_path = test_pdf_path
    
    print(f"Using PDF file: {pdf_path}")
    print(f"File size: {os.path.getsize(pdf_path) / 1024:.2f} KB")
    
    api_base_url = "https://wolf.law.uw.edu"  # Base URL without /api
    
    try:
        # Step 1: Upload PDF and get task ID
        print("Starting PDF upload...")
        task_id = upload_pdf(pdf_path, api_base_url)
        if not task_id:
            print("Failed to upload PDF or get task ID")
            return
        
        print(f"\nTask ID: {task_id}")
        print("Processing PDF... (this may take a moment)")
        
        # Step 2: Get results via SSE
        print("\nConnecting to progress stream...")
        result = get_task_status(task_id, api_base_url)
        
        if result is None:
            print("Failed to get results from the server.")
            return
            
        if result:
            print("\n✅ Processing complete!")
            
            # Save full results
            with open('api_results.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            
            # Show citation summary
            citations = result.get('citations', [])
            print(f"\n📄 Found {len(citations)} citations:")
            for i, cite in enumerate(citations[:10], 1):  # Show first 10 citations
                print(f"{i}. {cite.get('citation')} - {cite.get('case_name', 'N/A')}")
            
            if len(citations) > 10:
                print(f"... and {len(citations) - 10} more")
            
            print("\n💾 Full results saved to api_results.json")
        else:
            print("\n❌ Processing failed or was incomplete.")
        
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user.")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
