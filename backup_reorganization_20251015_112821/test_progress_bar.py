"""
Test that progress bar updates are working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import PyPDF2
from src.unified_input_processor import UnifiedInputProcessor, get_progress_manager
import uuid
import time

def extract_pdf_text(pdf_path, max_pages=3):
    """Extract text from first few pages of PDF."""
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ''
        pages = reader.pages[:max_pages]
        for page in pages:
            text += page.extract_text()
        return text

def test_progress_updates():
    """Test that progress updates are being captured."""
    
    print("=" * 80)
    print("PROGRESS BAR TEST")
    print("=" * 80)
    
    # Extract sample text from PDF
    pdf_path = '1028814.pdf'
    text = extract_pdf_text(pdf_path, max_pages=3)
    
    print(f"\n1. Extracted {len(text)} characters from first 3 pages")
    
    # Initialize processor
    processor = UnifiedInputProcessor()
    progress_manager = get_progress_manager()
    
    request_id = str(uuid.uuid4())
    print(f"2. Request ID: {request_id}")
    
    # Process with sync mode
    print("\n3. Starting sync processing...")
    input_data = {
        'type': 'text',
        'text': text
    }
    
    result = processor.process_any_input(
        input_data=input_data,
        input_type='text',
        request_id=request_id,
        source_name='pdf_progress_test',
        force_mode='sync'
    )
    
    print(f"\n4. Processing completed")
    print(f"   Success: {result.get('success')}")
    print(f"   Citations: {len(result.get('citations', []))}")
    
    # Check if progress was tracked
    print(f"\n5. Checking progress tracking...")
    
    if request_id in progress_manager.active_tasks:
        progress_data = progress_manager.get_progress(request_id)
        print(f"   ✓ Progress tracking ACTIVE")
        print(f"   Progress: {progress_data.get('progress')}%")
        print(f"   Status: {progress_data.get('status')}")
        print(f"   Message: {progress_data.get('message')}")
        print(f"   Current step: {progress_data.get('current_step')}")
        print(f"   Total steps: {progress_data.get('total_steps')}")
    else:
        print(f"   ✗ No progress tracking found for request_id: {request_id}")
        print(f"   Active tasks: {list(progress_manager.active_tasks.keys())}")
    
    # Test progress endpoint simulation
    print(f"\n6. Simulating progress endpoint calls...")
    for i in range(3):
        time.sleep(0.1)
        progress_data = progress_manager.get_progress(request_id)
        if progress_data and 'error' not in progress_data:
            print(f"   Call {i+1}: {progress_data.get('progress')}% - {progress_data.get('message')}")
        else:
            print(f"   Call {i+1}: No data or error")
    
    print("\n" + "=" * 80)
    print("PROGRESS BAR TEST COMPLETE")
    print("=" * 80)
    
    # Summary
    if request_id in progress_manager.active_tasks:
        print("\n✅ SUCCESS: Progress tracking is working!")
        print("   The progress bar should now display correctly in the frontend.")
    else:
        print("\n❌ ISSUE: Progress tracking not found")
        print("   The progress bar may still show NaN%")

if __name__ == "__main__":
    test_progress_updates()
