# CaseStrainer API Tests

This directory contains automated tests for the CaseStrainer API.

## Test Suite Overview

The test suite includes the following test cases:

1. **Health Check** - Verifies the API is running and responsive
2. **Citation Verification** - Tests individual citation validation
3. **Text Analysis** - Tests citation extraction from text
4. **File Upload** - Tests document upload and citation extraction
5. **Batch Validation** - Tests validation of multiple citations at once
6. **Error Handling** - Tests error responses for invalid requests

## Prerequisites

- Python 3.8+
- `requests` library
- CaseStrainer API server running locally on port 5000

## Running the Tests

1. First, ensure the CaseStrainer API server is running:
   ```bash
   python src/app_final_vue.py
   ```

2. Run the test suite:
   ```bash
   # Run all tests with default settings
   python -m tests.test_case_strainer_api
   
   # Run with verbose output
   python -m tests.test_case_strainer_api -v
   
   # Test against a different API URL
   python -m tests.test_case_strainer_api --url http://localhost:5000/casestrainer/api
   ```

## Test Files

- `test_case_strainer_api.py`: Main test suite
- `test_files/`: Directory containing test files used in the tests

## Adding New Tests

1. Add new test methods to the `TestCaseStrainerAPI` class in `test_case_strainer_api.py`
2. Follow the naming convention `test_*` for test methods
3. Use `self.assert*` methods to verify expected behavior
4. Add descriptive docstrings to explain what each test verifies

## Troubleshooting

- If tests fail, check that the API server is running and accessible
- Enable verbose output with `-v` for more detailed error messages
- Check the API server logs for any errors that might occur during testing
