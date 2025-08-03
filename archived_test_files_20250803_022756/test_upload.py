import json
import sys
import os
import PyPDF2
import requests
import argparse
from urllib.parse import urlparse
from requests_toolbelt.multipart.encoder import MultipartEncoder

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def upload_text(text: str) -> dict:
    """Upload text directly to the API."""
    url = "http://localhost:5000/casestrainer/api/analyze"
    headers = {"Content-Type": "application/json"}
    
    try:
        print("Testing direct text upload...")
        response = requests.post(
            url,
            headers=headers,
            json={"text": text}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

def upload_file(file_path: str) -> dict:
    """Upload a file to the API."""
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    try:
        print("Testing file upload...")
        with open(file_path, 'rb') as f:
            m = MultipartEncoder(
                fields={'file': (os.path.basename(file_path), f, 'application/pdf')}
            )
            
            response = requests.post(
                url,
                data=m,
                headers={'Content-Type': m.content_type}
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error making API request: {e}")
        return None

def upload_url(url: str) -> dict:
    """Test URL upload functionality."""
    api_url = "http://localhost:5000/casestrainer/api/analyze"
    headers = {"Content-Type": "application/json"}
    
    try:
        print(f"Testing URL upload: {url}")
        response = requests.post(
            api_url,
            headers=headers,
            json={"url": url}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

def print_result(result):
    """Print the API response in a formatted way."""
    if result:
        print("\nAPI Response:")
        print(json.dumps(result, indent=2))
        
        if 'task_id' in result:
            print(f"\nTo check progress, visit:")
            print(f"http://localhost:5000/casestrainer/api/analyze/progress/{result['task_id']}")
            print(f"\nTo get results, visit:")
            print(f"http://localhost:5000/casestrainer/api/analyze/results/{result['task_id']}")
    else:
        print("Failed to process document")

def main():
    parser = argparse.ArgumentParser(description='Test CaseStrainer upload functionality')
    parser.add_argument('--file', help='Path to PDF file for upload testing')
    parser.add_argument('--url', help='URL to test URL upload functionality', 
                       default='https://www.courts.wa.gov/opinions/pdf/1035420.pdf')
    
    args = parser.parse_args()
    
    if args.file:
        print(f"Extracting text from: {args.file}")
        text = extract_text_from_pdf(args.file)
        
        if not text:
            print("Failed to extract text from PDF")
            sys.exit(1)
        
        print(f"Extracted {len(text)} characters of text")
        
        # Test direct text upload
        print("\n=== Testing Direct Text Upload ===")
        result = upload_text(text)
        print_result(result)
        
        # Test file upload
        print("\n=== Testing File Upload ===")
        result = upload_file(args.file)
        print_result(result)
    
    # Always test URL upload
    print("\n=== Testing URL Upload ===")
    result = upload_url(args.url)
    print_result(result)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_upload.py [--file <path_to_pdf>] [--url <url>]")
        print("At least one of --file or --url must be provided")
        sys.exit(1)
    
    main()


