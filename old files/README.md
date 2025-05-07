# CaseStrainer

A tool to detect and highlight potentially hallucinated legal case citations in briefs and legal documents.

## Overview

CaseStrainer analyzes legal documents to identify case citations that may be hallucinated (i.e., non-existent or fabricated). It uses multiple methods to verify citations:

1. **CourtListener API integration**: Checks citations against the CourtListener database for accurate verification
2. **Automatic citation extraction**: Identifies and extracts legal citations from documents using pattern matching
3. **Local PDF search**: Searches for citations in local PDF folders
4. **Summary comparison**: Generates and compares multiple summaries of each citation using LangSearch or OpenAI APIs to detect inconsistencies

## Features

- Web interface for uploading and analyzing documents
- CourtListener API integration for accurate citation verification
- Automatic extraction of legal citations from documents
- Support for multiple file formats (DOCX, PDF, TXT)
- Batch processing of multiple citations in a single document
- Configurable analysis parameters
- Detailed results with confidence scores and similarity metrics
- Collapsible summaries for each citation
- Local PDF search option for offline use
- Real-time progress updates during analysis

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/CaseStrainer.git
   cd CaseStrainer
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up API keys (optional but recommended):
   See [API Setup Guide](API_SETUP.md) for detailed instructions.

## Usage

### Running the Web Interface

```
python -m waitress --host=0.0.0.0 --port=5001 app:app
```

Then open a web browser and navigate to `http://localhost:5001`.

### Using the CourtListener API

1. Sign up for a CourtListener account at [courtlistener.com](https://www.courtlistener.com/)
2. Get your API key from your account settings page
3. Enter your API key in the designated field in the CaseStrainer web interface
4. Upload a document or enter text containing legal citations
5. Click "Analyze Brief" to start the analysis

### Document Processing

CaseStrainer can process documents in several ways:

1. **Text Input**: Paste text directly into the text area
2. **File Upload**: Upload DOCX, PDF, or TXT files
3. **Batch Processing**: The application automatically extracts and analyzes all citations found in the document

### Command Line Options

CaseStrainer supports several command line options:

- `--courtlistener-key KEY`: Provide your CourtListener API key
- `--openai-key KEY`: Provide your OpenAI API key
- `--langsearch-key KEY`: Provide your LangSearch API key
- `--port PORT`: Specify the port to run the server on (default: 5000)
- `--host HOST`: Specify the host to run the server on (default: 0.0.0.0)
- `--debug`: Run in debug mode

Example:
```
python app.py --courtlistener-key YOUR_CL_KEY --langsearch-key YOUR_LS_KEY --port 8080
```

For more details on API setup, see the [API Setup Guide](API_SETUP.md).

### Local PDF Search

CaseStrainer can search for citations in local PDF folders instead of using the CourtListener API. This is useful for offline use or when you have a collection of PDF documents that contain the cases you're interested in.

The default PDF folders are:
- D:\WOLF Processing Folder\Wash 2d\Wash2d full vol pdfs
- D:\WOLF Processing Folder\Wash\Wash Full Vol pdfs
- D:\WOLF Processing Folder\Wash App\wash-app full vol pdfs

To use this feature, check the "Search local PDF folders instead of using API" option in the web interface or Word add-in.

## Word Add-in

CaseStrainer includes a Word add-in that allows you to analyze documents directly from Microsoft Word. To use the add-in:

1. Make sure the CaseStrainer server is running
2. In Word, go to the Insert tab and click on "My Add-ins"
3. Browse for the add-in manifest file (located in the `word_addin` folder)
4. Click "Install"

## License

This project is licensed under the terms of the license included in the repository.
