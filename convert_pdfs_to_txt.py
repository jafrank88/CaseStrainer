import fitz  # PyMuPDF
import os
import glob
from pathlib import Path

def convert_pdf_to_text(pdf_path, output_dir):
    """Convert a PDF file to text and save it to the output directory."""
    doc = None
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        # Extract text from all pages
        all_text = ""
        page_count = len(doc)
        
        for page_num in range(page_count):
            page = doc[page_num]
            text = page.get_text()
            all_text += f"\n--- Page {page_num + 1} ---\n{text}"
        
        # Create output filename
        pdf_filename = os.path.basename(pdf_path)
        txt_filename = os.path.splitext(pdf_filename)[0] + ".txt"
        output_path = os.path.join(output_dir, txt_filename)
        
        # Save text to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(all_text)
        
        return {
            'success': True,
            'input_file': pdf_path,
            'output_file': output_path,
            'text_length': len(all_text),
            'page_count': page_count
        }
        
    except Exception as e:
        return {
            'success': False,
            'input_file': pdf_path,
            'error': str(e),
            'error_type': type(e).__name__
        }
    finally:
        # Always close the document
        if doc:
            doc.close()

def convert_all_pdfs_in_folder(input_folder, output_folder):
    """Convert all PDF files in the input folder to text files in the output folder."""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Find all PDF files in the input folder
    pdf_pattern = os.path.join(input_folder, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print(f"No PDF files found in {input_folder}")
        return []
    
    print(f"Found {len(pdf_files)} PDF files to convert")
    
    results = []
    successful = 0
    failed = 0
    
    for pdf_file in pdf_files:
        print(f"Converting: {os.path.basename(pdf_file)}")
        result = convert_pdf_to_text(pdf_file, output_folder)
        results.append(result)
        
        if result['success']:
            successful += 1
            print(f"  ✓ Success: {result['text_length']} characters, {result['page_count']} pages")
        else:
            failed += 1
            print(f"  ✗ Failed: {result['error']}")
    
    print(f"\nConversion complete:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Output directory: {output_folder}")
    
    return results

if __name__ == "__main__":
    # Define input and output folders
    input_folder = "wa_briefs"
    output_folder = "wa_briefs_txt"
    
    # Convert all PDFs
    results = convert_all_pdfs_in_folder(input_folder, output_folder)
    
    # Print summary
    if results:
        print(f"\nDetailed results:")
        for result in results:
            if result['success']:
                print(f"✓ {os.path.basename(result['input_file'])} -> {os.path.basename(result['output_file'])}")
            else:
                print(f"✗ {os.path.basename(result['input_file'])}: {result['error']}") 