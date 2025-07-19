# File Upload Troubleshooting Guide

## 400 Bad Request Error - Common Causes and Solutions

When you encounter a `POST https://wolf.law.uw.edu/casestrainer/api/analyze 400 (BAD REQUEST)` error when uploading a file, here are the most likely causes and solutions:

## 1. File Type Validation

### Allowed File Extensions

The system only accepts these file types:

- **PDF**: `.pdf`
- **Word Documents**: `.doc`, `.docx`
- **Text Files**: `.txt`

### Solution

- Ensure your file has one of the allowed extensions
- If your file has a different extension, convert it to one of the supported formats
- Check that the file extension is lowercase (e.g., `.PDF` should be `.pdf`)

## 2. File Size Limits

### Current Limits

- **Maximum file size**: 50MB (50,000,000 bytes)
- **Minimum file size**: 1 byte (file cannot be empty)

### Solution (2)

- Check your file size: Right-click the file → Properties
- If the file is larger than 50MB:
  - Split the document into smaller parts
  - Compress the PDF if possible
  - Convert to a more efficient format

## 3. File Content Validation

### Security Checks

The system performs several security validations:

#### Filename Validation

- **Invalid characters**: `..`, `\`, `/`, `:`, `*`, `?`, `"`, `<`, `>`, `|`
- **Multiple extensions**: Files like `document.pdf.exe` are rejected
- **Empty filename**: Files without names are rejected

#### Content Type Validation

- **PDF**: Must be `application/pdf`
- **DOC**: Must be `application/msword`
- **DOCX**: Must be `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **TXT**: Must be `text/plain`

### Solution (3)

- Ensure your filename doesn't contain special characters
- Use a simple filename like `document.pdf` instead of `My Document (v2).pdf`
- Make sure the file is actually the type it claims to be (not a renamed file)

## 4. Frontend Validation

### Browser-Side Checks

The frontend also validates files before upload:

```javascript
// File size check
if (file.size > 50 * 1024 * 1024) {
  throw new Error('File is too large. Maximum size is 50MB.');
}

// File type check
const allowedTypes = {
  'application/pdf': ['.pdf'],
  'application/msword': ['.doc'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt']
};

```text

### Solution (4)

- Check the browser console for any JavaScript errors
- Ensure the file type is correctly detected by the browser

## 5. Network and Server Issues

### Common Network Problems

- **Timeout**: Large files may timeout during upload
- **Connection issues**: Unstable internet connection
- **Server overload**: Server may be temporarily unavailable

### Solution (5)

- Try uploading a smaller file first to test
- Check your internet connection
- Wait a few minutes and try again
- Try uploading during off-peak hours

## 6. Debugging Steps

### Step 1: Check File Properties

```bash

# On Windows

dir filename.pdf

# On Mac/Linux

ls -la filename.pdf

```text

### Step 2: Test with Different Files

1. Try uploading a simple text file first
2. Try uploading a small PDF (under 1MB)
3. Try uploading a Word document

### Step 3: Check Browser Console

1. Open Developer Tools (F12)
2. Go to Console tab
3. Look for any error messages
4. Check Network tab for detailed request/response

### Step 4: Verify File Format

```bash

# Check file type (Mac/Linux)

file filename.pdf

# Check file size

du -h filename.pdf

```text

## 7. Common Error Messages

### "File too large"

- **Cause**: File exceeds 50MB limit
- **Solution**: Reduce file size or split document

### "Invalid file type"

- **Cause**: File extension not in allowed list
- **Solution**: Convert to supported format

### "File is empty"

- **Cause**: File has 0 bytes
- **Solution**: Ensure file contains content

### "Invalid filename"

- **Cause**: Filename contains special characters
- **Solution**: Use simple filename without special characters

### "No file provided"

- **Cause**: File not properly selected or uploaded
- **Solution**: Ensure file is selected before clicking upload

## 8. Advanced Troubleshooting

### Check Server Logs

If you have access to server logs, look for:

- File validation errors
- File size violations
- Content type mismatches
- Security violations

### Test API Directly

You can test the API endpoint directly using curl:

```bash
curl -X POST \
  -F "file=@your_document.pdf" \
  https://wolf.law.uw.edu/casestrainer/api/analyze

```text

### Check File Integrity

- Ensure the file isn't corrupted
- Try opening the file in its native application
- Re-save the file if possible

## 9. Prevention Tips

### Best Practices

1. **Use simple filenames**: `document.pdf` instead of `My Document (v2).pdf`
2. **Keep files under 10MB**: Smaller files upload faster and are less likely to fail
3. **Use standard formats**: PDF, DOC, DOCX, or TXT
4. **Check file before upload**: Ensure it opens correctly in its native application
5. **Use stable internet**: Avoid uploading on slow or unstable connections

### File Preparation

- **PDFs**: Use standard PDF format, avoid scanned images if possible
- **Word documents**: Save as .docx for better compatibility
- **Text files**: Use UTF-8 encoding for international characters

## 10. Getting Help

If you continue to experience issues:

1. **Note the exact error message** from the browser console
2. **Record the file details**: name, size, type, extension
3. **Try with a different file** to isolate the issue
4. **Check if the issue is consistent** across different browsers
5. **Contact support** with the specific error details

### Information to Provide

- Exact error message
- File name and extension
- File size
- Browser and version
- Operating system
- Steps to reproduce the issue
