#!/usr/bin/env python3
"""
Debug script to help identify file upload issues
Run this script to check if your file meets all the requirements
"""

import os
import sys
import mimetypes
from pathlib import Path

def check_file_upload_requirements(file_path):
    """Check if a file meets all upload requirements."""
    
    print("=== CaseStrainer File Upload Debug ===")
    print(f"Checking file: {file_path}")
    print()
    
    # Check if file exists
    if not os.path.exists(file_path):
        print("❌ ERROR: File does not exist")
        return False
    
    # Get file info
    file_stat = os.stat(file_path)
    file_size = file_stat.st_size
    file_name = os.path.basename(file_path)
    
    print(f"📁 Filename: {file_name}")
    print(f"📏 File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    print()
    
    # Check file size
    max_size = 50 * 1024 * 1024  # 50MB
    if file_size == 0:
        print("❌ ERROR: File is empty")
        return False
    elif file_size > max_size:
        print(f"❌ ERROR: File too large ({file_size / (1024*1024):.2f} MB > 50 MB)")
        return False
    else:
        print(f"✅ File size OK ({file_size / (1024*1024):.2f} MB <= 50 MB)")
    
    # Check file extension
    allowed_extensions = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'html', 'htm'}
    file_ext = Path(file_name).suffix.lower().lstrip('.')
    
    if not file_ext:
        print("❌ ERROR: No file extension found")
        return False
    elif file_ext not in allowed_extensions:
        print(f"❌ ERROR: Invalid file extension '{file_ext}'")
        print(f"   Allowed extensions: {', '.join(allowed_extensions)}")
        return False
    else:
        print(f"✅ File extension OK ({file_ext})")
    
    # Check filename for suspicious characters
    suspicious_chars = ['..', '\\', '/', ':', '*', '?', '"', '<', '>', '|']
    filename_issues = []
    
    for char in suspicious_chars:
        if char in file_name:
            filename_issues.append(char)
    
    if filename_issues:
        print(f"❌ ERROR: Filename contains suspicious characters: {', '.join(filename_issues)}")
        return False
    else:
        print("✅ Filename OK (no suspicious characters)")
    
    # Check for multiple extensions
    if file_name.count('.') > 1:
        print("❌ ERROR: Multiple extensions detected (e.g., file.pdf.exe)")
        return False
    else:
        print("✅ Single extension OK")
    
    # Check MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    expected_mime_types = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain'
    }
    
    expected_mime = expected_mime_types.get(file_ext)
    if mime_type and expected_mime and mime_type != expected_mime:
        print(f"⚠️  WARNING: MIME type mismatch")
        print(f"   Expected: {expected_mime}")
        print(f"   Detected: {mime_type}")
        print("   (This is usually OK, but may cause issues)")
    else:
        print(f"✅ MIME type OK ({mime_type or 'unknown'})")
    
    # Check if file is readable
    try:
        with open(file_path, 'rb') as f:
            f.read(1024)  # Read first 1KB
        print("✅ File is readable")
    except Exception as e:
        print(f"❌ ERROR: Cannot read file: {e}")
        return False
    
    print()
    print("=== Summary ===")
    print("✅ File appears to meet all upload requirements!")
    print()
    print("If you're still getting a 400 error, the issue might be:")
    print("1. Network connectivity problems")
    print("2. Server-side validation issues")
    print("3. Browser-specific problems")
    print("4. File corruption (try opening in native application)")
    print()
    print("Try these steps:")
    print("1. Use a different browser")
    print("2. Try uploading a smaller file first")
    print("3. Check your internet connection")
    print("4. Wait a few minutes and try again")
    
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_file_upload.py <file_path>")
        print("Example: python debug_file_upload.py document.pdf")
        sys.exit(1)
    
    file_path = sys.argv[1]
    check_file_upload_requirements(file_path)

if __name__ == "__main__":
    main() 