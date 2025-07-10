# ⚠️ Important: File and URL Re-upload Behavior

## Overview

**CaseTrainer does NOT cache or deduplicate uploads.** Each time you upload a file, submit a URL, or paste text, it will be processed as a completely new request, regardless of whether you've submitted the same content before.

## What This Means

### 🔄 **Files Are Always Re-uploaded**
- Every file upload creates a new unique filename
- No duplicate detection based on file content
- No caching of file processing results
- Each upload triggers fresh citation extraction and verification

### 🌐 **URLs Are Always Re-processed**
- Every URL submission triggers fresh web scraping
- No caching of web content or results
- 10-minute timeout for URL processing
- Each submission gets fresh citation verification

### 📝 **Text Is Always Re-processed**
- Every text submission triggers fresh analysis
- No caching of text content or results
- Each submission gets fresh citation extraction

## Why This Matters

### ✅ **Benefits:**
- **Always up-to-date results** - No stale cached data
- **Fresh web scraping** - Gets latest content from legal databases
- **No storage concerns** - Results aren't permanently stored
- **Privacy** - No long-term retention of your documents

### ⚠️ **Considerations:**
- **Processing time** - Each submission takes full processing time
- **API usage** - Each submission uses fresh API calls to legal databases
- **No incremental updates** - Can't build on previous results
- **Resource usage** - Each submission uses full computational resources

## Common Scenarios

### 📄 **Document Editing Workflow**
If you:
1. Upload a document and get results
2. Edit the document 
3. Upload the edited version

**Result:** The edited version will be processed as a completely new document, even if only minor changes were made.

### 🔄 **Iterative Analysis**
If you:
1. Submit a URL for analysis
2. Make changes to the web page
3. Submit the same URL again

**Result:** The updated web page content will be scraped and analyzed fresh.

### 📝 **Text Refinement**
If you:
1. Paste text and get results
2. Edit the text slightly
3. Submit the edited text

**Result:** The edited text will be processed as completely new content.

## Best Practices

### 💡 **For Document Workflows:**
- **Finalize your document** before uploading to avoid multiple uploads
- **Save your results** locally if you need to reference them later
- **Use batch processing** for multiple documents to minimize uploads

### 💡 **For URL Analysis:**
- **Ensure the URL is stable** before submission
- **Check that the content is final** before analysis
- **Consider downloading content** if you need to analyze it multiple times

### 💡 **For Text Analysis:**
- **Review and finalize text** before submission
- **Save results locally** for future reference
- **Use the copy/paste feature** to reuse results in other documents

## Technical Details

### 🔧 **File Processing:**
- Files are saved with UUID-based names: `{uuid}.{extension}`
- No content hashing or duplicate detection
- Files are processed immediately or queued based on size
- Results are not cached between sessions

### 🔧 **URL Processing:**
- URLs are scraped fresh each time
- No content caching or result caching
- 10-minute timeout for complex web pages
- Web scraping uses enhanced legal database search

### 🔧 **Text Processing:**
- Text is processed fresh each time
- No content hashing or duplicate detection
- Immediate processing for short text
- Queued processing for longer documents

## Future Considerations

The development team is considering adding:
- **Optional result caching** for repeated submissions
- **Content-based deduplication** for identical files
- **Incremental processing** for document updates
- **User preference settings** for caching behavior

## Support

If you have questions about upload behavior or need help optimizing your workflow:
- Check the [API Documentation](API_DOCUMENTATION.md)
- Review the [Migration Guide](WEB_SEARCH_MIGRATION.md)
- Contact the development team for specific use cases

---

**Note:** This behavior is by design to ensure fresh, accurate results and maintain user privacy. Plan your workflows accordingly to minimize unnecessary re-processing. 