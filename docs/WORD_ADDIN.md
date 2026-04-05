# CaseStrainer Word Add-In (BriefCheck)

## Overview

The CaseStrainer Word Add-In, branded as **BriefCheck**, allows legal professionals to analyze and verify citations directly within Microsoft Word documents. This tool helps detect hallucinated or incorrect legal citations in briefs, memos, and other legal documents.

## Status

**✅ AVAILABLE** - The Word Add-In is currently available and functional.

## Features

### Citation Analysis
- **Document-Wide Analysis**: Analyze all citations in your entire Word document
- **Selection Analysis**: Analyze only selected text for quick verification
- **Real-Time Processing**: Citations are analyzed in real-time using the CaseStrainer API
- **Confidence Scoring**: Each citation receives a confidence score indicating likelihood of authenticity

### Verification Methods
- **API Lookup**: Direct verification against CourtListener database
- **Summary Comparison**: Advanced verification using document context and case summaries
- **Multi-Iteration Analysis**: Configurable number of summary iterations (2-5) for increased accuracy
- **Similarity Threshold**: Adjustable threshold (0.5-0.9) for controlling verification strictness

### Visual Feedback
- **Color-Coded Results**: 
  - ✅ Green: Verified citations (likely real)
  - ⚠️ Yellow/Red: Unverified citations (potentially hallucinated)
- **Detailed Accordion View**: Expandable panels for each citation with detailed information
- **Confidence Bars**: Visual representation of confidence levels
- **Case Summaries**: Toggle-able case summary displays

### Advanced Features
- **Local PDF Search**: Option to search local PDF folders instead of using API
- **Batch Processing**: Analyze entire documents with one click
- **Export Options**: Results can be reviewed and exported
- **Customizable Settings**: Adjust verification parameters to match your needs

## Installation

### Prerequisites
- Microsoft Word 2016 or later (Windows or Mac)
- Office 365 subscription or standalone Office installation
- Internet connection for API access

### Installation Steps

1. **Download the manifest**
   - **Production (hosted with the web app):**  
     `https://wolf.law.uw.edu/casestrainer/word-addin/manifest.xml`
   - **From source:**  
     `casestrainer-vue-new/public/word-addin/manifest.xml` (same content as production after deploy)
   - **Local dev with Vite:** use `manifest.local.xml` in that folder (points at `http://localhost:5173/casestrainer/word-addin/`)

2. **Add to Word**
   
   **Windows:**
   ```powershell
   # Create the Word WebExtensions folder if it doesn't exist
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\AppData\Local\Microsoft\Office\16.0\Wef"
   
   # Copy the manifest file
   Copy-Item manifest.xml "$env:USERPROFILE\AppData\Local\Microsoft\Office\16.0\Wef\"
   ```
   
   **Mac:**
   ```bash
   # Copy to the Word addins folder
   cp manifest.xml ~/Library/Containers/com.microsoft.Word/Data/Documents/wef/
   ```

3. **Enable the Add-In**
   - Open Microsoft Word
   - Go to **Insert** → **Add-ins** → **My Add-ins**
   - Select **BriefCheck** from the list
   - Click **Add** to enable the add-in

### Alternative: Sideload for Development

1. **Enable Developer Mode**
   - In Word, go to **File** → **Options** → **Trust Center** → **Trust Center Settings**
   - Click **Trusted Add-in Catalogs**
   - Add your local directory as a trusted catalog

2. **Sideload the Add-In**
   - Open Word
   - Go to **Insert** → **Add-ins** → **My Add-ins**
   - Select **Shared Folder** tab
   - Select **BriefCheck**

## Usage

### Basic Analysis

1. **Open BriefCheck**
   - Click the **BriefCheck** button in the Word ribbon (Home tab)
   - The task pane will open on the right side of your document

2. **Configure Settings**
   - **Number of Iterations**: Set between 2-5 (default: 3)
     - More iterations = higher accuracy but slower processing
   - **Similarity Threshold**: Adjust slider from 0.5 to 0.9 (default: 0.7)
     - Higher threshold = stricter verification
   - **Local PDF Search**: Enable to search local PDF folders instead of API

3. **Analyze Citations**
   - Click **Analyze Document** to analyze all citations
   - Or select specific text and then click **Analyze Document**
   - Wait for processing to complete (progress indicator will show)

4. **Review Results**
   - View the summary showing total citations and potentially hallucinated citations
   - Expand individual citations to see detailed information
   - Review confidence scores and verification methods
   - Check case summaries if available

5. **Clear Results**
   - Click **Clear** to reset the interface and prepare for a new analysis

### Understanding Results

#### Result Display
Each citation shows:
- **Citation Text**: The exact citation found in your document
- **Status Badge**: Green (likely real) or Red (potentially hallucinated)
- **Detection Method**: API Lookup or Summary Comparison
- **Raw API Result**: Shows whether the citation exists in the database
- **Verification Result**: Clear indication of citation existence
- **Confidence Score**: Percentage indicating confidence level
- **Similarity Score**: (If applicable) Similarity between generated and actual summaries

#### Case Summary Sections
- **Show/Hide Case Summary**: Toggle button to view the official case summary
- **Show/Hide Generated Summaries**: View AI-generated summaries from multiple iterations

### Advanced Settings

#### Iterations
- **2 iterations**: Fastest, less accurate (good for quick checks)
- **3 iterations**: Balanced (recommended for most uses)
- **4-5 iterations**: Slowest, most accurate (for critical documents)

#### Similarity Threshold
- **0.5-0.6**: Lenient (flags fewer citations)
- **0.7**: Balanced (recommended)
- **0.8-0.9**: Strict (flags more citations)

#### Local PDF Search
- Enable if you have local PDF repositories of legal cases
- Requires proper folder configuration
- Significantly longer processing time
- More comprehensive for specialized legal databases

## Configuration

### API Endpoint
The add-in connects to:
```
https://wolf.law.uw.edu:5000/api/analyze
```

### Timeout Settings
- **Standard API**: 60 seconds
- **Local PDF Search**: 120 seconds

### Security
- All communication uses HTTPS encryption
- API keys (if required) should be configured server-side
- No citation data is stored locally or transmitted to third parties

## Files structure

```
casestrainer-vue-new/public/word-addin/
├── manifest.xml          # Production — points at wolf.law.uw.edu task pane URLs
├── manifest.local.xml    # Local sideload — Vite dev server (port 5173)
├── index.html            # Task pane shell
├── app.js                # UI + Word.run text extraction / highlighting
├── api-client.js         # POST /analyze + task_status polling
├── commands.html         # Ribbon function file (minimal)
├── styles.css
└── icons/                # PNG icons referenced by the manifest
```

### Key files

#### manifest.xml
- Add-in metadata, HTTPS `SourceLocation` on the deployed site, ribbon button → task pane
- Version in-repo: **1.1.0.0**

#### index.html / app.js
- Office Fabric–styled task pane
- `Word.run` for full-document or selection text and optional highlighting
- Settings persisted with `Office.context.roamingSettings`

## API integration

The add-in uses the same contract as the web app.

### Request (JSON)
```json
{
  "type": "text",
  "text": "Pasted or extracted document text…",
  "force_mode": "sync"
}
```

### Response
- Immediate `citations` / `clusters` when the server completes synchronously, **or**
- `task_id` + `status: "processing"` — poll `GET /casestrainer/api/task_status/{task_id}` until `completed`.

Citation objects use fields such as `citation`, `verified`, `found`, `confidence`, `canonical_name` (see [API docs](API_DOCUMENTATION.md)).

## Troubleshooting

### Common Issues

#### Add-In Not Appearing
- **Solution**: Ensure manifest.xml is in the correct directory
- Restart Microsoft Word
- Check Office 365 subscription status

#### Connection Errors
- **Solution**: Verify internet connection
- Check firewall settings for https://wolf.law.uw.edu
- Ensure the CaseStrainer server is online

#### Slow Performance
- **Solution**: Reduce number of iterations (use 2 instead of 3-5)
- Disable local PDF search if not needed
- Analyze smaller sections of text instead of entire document

#### Timeout Errors
- **Solution**: Split large documents into smaller sections
- Increase timeout in settings (requires code modification)
- Check server load at https://wolf.law.uw.edu/casestrainer/api/health

### Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| "Request timed out" | Processing took too long | Reduce document size or iterations |
| "Server returned 500" | Server error | Check server status, try again later |
| "Error getting document text" | Word API error | Restart Word, check permissions |
| "No citations to analyze" | No citations detected | Verify document contains legal citations |

## Development

### Local development

1. **Clone the repository** and open `casestrainer-vue-new/`.
2. **Run the Vue dev server:** `npm install` then `npm run dev` (default `http://localhost:5173/casestrainer/`).
3. **Sideload `public/word-addin/manifest.local.xml`** in Word (shared folder or Insert → Add-ins → Upload My Add-in).
4. **Run the CaseStrainer backend** separately if you are not using the production API; set the task pane **Analyze URL** to your `…/casestrainer/api/analyze` endpoint (e.g. `http://127.0.0.1:5001/casestrainer/api/analyze`).

Refresh the task pane after editing static files under `public/word-addin/`.

### Making Changes

#### UI Changes
- Edit `taskpane.html` for UI modifications
- Uses Bootstrap 5 for styling
- Modify inline styles in `<style>` section

#### Functionality Changes
- Edit JavaScript in `<script>` section of taskpane.html
- Key functions:
  - `analyzeText()`: Main analysis logic
  - `displayResults()`: Results rendering
  - `highlightHallucinatedCitations()`: Document highlighting

#### API Changes
- Modify fetch URL in `analyzeText()` function
- Adjust request/response handling
- Update timeout values

### Testing
1. Test with various document types
2. Verify citation detection accuracy
3. Check error handling
4. Test timeout scenarios
5. Validate UI responsiveness

## Support & Contributing

### Getting Help
- **Documentation**: https://github.com/jafrank88/casestrainer/tree/main/docs
- **Issues**: https://github.com/jafrank88/casestrainer/issues
- **Discussions**: https://github.com/jafrank88/casestrainer/discussions

### Contributing
We welcome contributions! Please:
1. Fork the repository: https://github.com/jafrank88/casestrainer
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Reporting Bugs
- Use GitHub Issues: https://github.com/jafrank88/casestrainer/issues
- Include Word version, OS, and error messages
- Provide sample documents if possible (redact sensitive info)

## Roadmap

### Current Version (1.0)
- ✅ Basic citation detection
- ✅ CourtListener API integration
- ✅ Confidence scoring
- ✅ Summary comparison
- ✅ Local PDF search option

### Planned Features (v1.1)
- [ ] Batch document processing
- [ ] Citation export to BibTeX/EndNote
- [ ] Custom verification rules
- [ ] Team collaboration features
- [ ] Citation correction suggestions

### Future enhancements
- [ ] Machine learning citation classifier
- [ ] Real-time verification as you type
- [ ] Integration with citation management tools
- [ ] Advanced reporting and analytics

## License

The CaseStrainer Word Add-In is part of the CaseStrainer project. See the LICENSE file in the repository for details.

**Repository**: https://github.com/jafrank88/casestrainer

## Acknowledgments

- **Microsoft Office Add-ins Team**: For the Office.js framework
- **CourtListener**: For providing the citation verification API
- **Legal Community**: For testing and feedback
- **Contributors**: Everyone who has contributed to CaseStrainer

---

**Last Updated**: 2025-01-20  
**Status**: Available  
**Version**: 1.0.0.0  
**Repository**: https://github.com/jafrank88/casestrainer
