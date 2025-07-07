#!/usr/bin/env python3
import os
import sys
import requests
import json
import time
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from src.pdf_handler import PDFHandler

def process_pdf_file(pdf_path):
    """Process a PDF file through the citation analysis system."""
    
    print(f"=== PROCESSING PDF: {pdf_path} ===")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} does not exist")
        return None
    
    # Extract text from PDF
    print("Extracting text from PDF...")
    pdf_handler = PDFHandler()
    try:
        extracted_text = pdf_handler.extract_text(pdf_path)
        if not extracted_text:
            print("Error: No text extracted from PDF")
            return None
        
        print(f"Successfully extracted {len(extracted_text)} characters")
        print(f"Sample text: {extracted_text[:200]}...")
        
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None
    
    # Send to API for analysis
    print("\nSending to API for citation analysis...")
    url = "http://127.0.0.1:5000/casestrainer/api/analyze"
    
    try:
        # Make the API request
        response = requests.post(url, json={"text": extracted_text}, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"Task ID: {task_id}")
            
            # Wait for processing to complete
            print("Waiting for processing to complete...")
            for i in range(120):  # Wait up to 2 minutes
                time.sleep(2)
                try:
                    status_response = requests.get(f"http://127.0.0.1:5000/casestrainer/api/task_status/{task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('status') == 'completed':
                            print("Processing completed!")
                            results = status_data.get('results', {})
                            
                            # Handle different result structures
                            if isinstance(results, list):
                                citations = results
                            else:
                                citations = results.get('citations', [])
                            
                            print(f"\n=== RESULTS ===")
                            print(f"Total citations found: {len(citations)}")
                            
                            # Count verification statuses
                            true_count = 0
                            false_count = 0
                            true_by_parallel_count = 0
                            
                            for citation in citations:
                                verified = citation.get('verified', False)
                                if verified == True:
                                    true_count += 1
                                elif verified == False:
                                    false_count += 1
                                elif verified == 'true_by_parallel':
                                    true_by_parallel_count += 1
                            
                            print(f"Verified: {true_count}")
                            print(f"Not verified: {false_count}")
                            print(f"Verified by parallel: {true_by_parallel_count}")
                            
                            # Show all citations with details
                            print(f"\n=== ALL CITATIONS ===")
                            for i, citation in enumerate(citations):
                                print(f"{i+1}. Citation: {citation.get('citation', 'N/A')}")
                                print(f"   Case Name: {citation.get('case_name', 'N/A')}")
                                print(f"   Verified: {citation.get('verified', 'N/A')}")
                                print(f"   Source: {citation.get('source', 'N/A')}")
                                if citation.get('url'):
                                    print(f"   URL: {citation.get('url', 'N/A')}")
                                if citation.get('context'):
                                    print(f"   Context: {citation.get('context', 'N/A')[:100]}...")
                                print("---")
                            
                            return results
                        elif status_data.get('status') == 'failed':
                            print(f"Processing failed: {status_data.get('error', 'Unknown error')}")
                            return None
                        else:
                            print(f"Status: {status_data.get('status', 'Unknown')}")
                    else:
                        print(f"Status check failed: {status_response.status_code}")
                except Exception as e:
                    print(f"Error checking status: {e}")
                    continue
            
            print("Processing timed out")
            return None
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    pdf_path = r"C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\1029764.pdf"
    results = process_pdf_file(pdf_path)
    
    if results:
        print("\n=== PROCESSING COMPLETE ===")
        print("Results saved successfully")
    else:
        print("\n=== PROCESSING FAILED ===") 