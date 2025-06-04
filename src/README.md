# Enhanced Citation Validator with CitationProcessor

This module provides enhanced citation validation functionality using the `CitationProcessor` class, which integrates with the eyecite library and provides additional features like caching, batching, and error handling.

## Features

- **Citation Extraction**: Extract legal citations from text using the eyecite library
- **Citation Validation**: Validate citations against the CourtListener API
- **Caching**: Built-in caching to reduce API calls and improve performance
- **Batching**: Process multiple citations in parallel for better performance
- **Error Handling**: Comprehensive error handling and logging
- **Metrics**: Track processing metrics and performance

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables (if needed):

```bash
export COURTLISTENER_API_KEY=your_api_key_here
```

## Usage

### Basic Usage

```python
from citation_processor import CitationProcessor

# Initialize the processor
with CitationProcessor() as processor:
    # Extract citations from text
    text = "The case of Brown v. Board of Education, 347 U.S. 483 (1954) was a landmark decision."
    citations = processor.extract_citations(text)
    
    # Validate a single citation
    result = processor.validate_citation("347 U.S. 483")
    print(f"Citation is {'valid' if result['valid'] else 'invalid'}")
    
    # Process multiple citations in a batch
    citations_to_validate = ["347 U.S. 483", "358 U.S. 1"]
    results = processor.process_batch(citations_to_validate)
    for result in results:
        print(f"{result['citation']}: {'Valid' if result['valid'] else 'Invalid'}")
```

### Integration with Flask

The `enhanced_validator_production.py` file provides a Flask blueprint that can be integrated into your Flask application:

```python
from flask import Flask
from enhanced_validator_production import register_enhanced_validator

app = Flask(__name__)

# Register the enhanced validator blueprint
register_enhanced_validator(app)

if __name__ == "__main__":
    app.run(debug=True)
```

### API Endpoints

- `POST /enhanced-validator/api/analyze`: Analyze text for legal citations

  **Request Body:**
  ```json
  {
    "text": "The case of Brown v. Board of Education, 347 U.S. 483 (1954) was a landmark decision.",
    "batch_process": false
  }
  ```

  **Response:**
  ```json
  {
    "status": "success",
    "data": {
      "citations": [
        {
          "citation": "347 U.S. 483",
          "valid": true,
          "results": [...],
          "cached": false,
          "error": null
        }
      ],
      "stats": {
        "total_citations": 1,
        "valid_citations": 1,
        "processing_time": 0.45,
        "extraction_time": 0.12,
        "validation_time": 0.33
      }
    }
  }
  ```

## Configuration

The `CitationProcessor` class can be configured with the following parameters:

- `api_key` (str): API key for the citation validation service
- `max_workers` (int): Maximum number of worker threads for parallel processing (default: 5)
- `cache_size` (int): Maximum number of items to cache (default: 1000)

## Error Handling

The module provides comprehensive error handling. All functions that interact with external services will raise appropriate exceptions that can be caught and handled by the calling code.

## Performance Considerations

- The `process_batch` method is optimized for processing multiple citations efficiently.
- Caching is enabled by default to reduce the number of API calls.
- The circuit breaker pattern is used to handle API failures gracefully.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
