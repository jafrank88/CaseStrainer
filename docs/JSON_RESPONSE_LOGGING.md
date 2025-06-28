# JSON Response Logging System

## Overview

The CaseStrainer backend now includes a comprehensive JSON response logging system that automatically logs all JSON responses before they are sent to the frontend. This system helps with debugging, monitoring, and understanding the data flow between the backend and frontend.

## How It Works

### Flask After Request Handlers

The logging system uses Flask's `after_request` handlers to intercept all responses before they are sent to the client. This ensures that:

1. **All JSON responses are captured** regardless of which endpoint generates them
2. **No performance impact** on the actual response time
3. **Comprehensive logging** with context information
4. **Pretty-printed JSON** for easy reading

### Implementation Details

The logging system is implemented in three main files:

1. **`src/vue_api_endpoints.py`** - Main API endpoints
2. **`src/citation_api.py`** - Citation-specific API endpoints  
3. **`app/routes.py`** - Legacy API routes

Each file includes:

```python
def log_json_responses(response):
    """
    Flask after_request handler to log all JSON responses before they are sent to the frontend.
    """
    try:
        # Only log JSON responses
        if response.content_type == 'application/json':
            # Get the response data
            response_data = response.get_data(as_text=True)
            
            # Try to parse and pretty-print the JSON for better logging
            try:
                import json
                parsed_data = json.loads(response_data)
                formatted_json = json.dumps(parsed_data, indent=2, ensure_ascii=False)
                
                # Log the response with context
                logger.info("=" * 80)
                logger.info("JSON RESPONSE BEING SENT TO FRONTEND")
                logger.info("=" * 80)
                logger.info(f"Endpoint: {request.endpoint}")
                logger.info(f"Method: {request.method}")
                logger.info(f"URL: {request.url}")
                logger.info(f"Status Code: {response.status_code}")
                logger.info(f"Content-Type: {response.content_type}")
                logger.info(f"Response Size: {len(response_data)} characters")
                logger.info("-" * 80)
                logger.info("RESPONSE BODY:")
                logger.info(formatted_json)
                logger.info("=" * 80)
                
            except json.JSONDecodeError:
                # If JSON parsing fails, log the raw response
                logger.warning("Failed to parse JSON response, logging raw data:")
                logger.info(f"Raw response: {response_data}")
                
        return response
        
    except Exception as e:
        logger.error(f"Error in log_json_responses: {str(e)}")
        return response
```

## Log Output Format

When a JSON response is sent to the frontend, you'll see log entries like this:

```
================================================================================
JSON RESPONSE BEING SENT TO FRONTEND
================================================================================
Endpoint: vue_api.health_check
Method: GET
URL: http://localhost:5000/casestrainer/api/health
Status Code: 200
Content-Type: application/json
Response Size: 245 characters
--------------------------------------------------------------------------------
RESPONSE BODY:
{
  "status": "healthy",
  "service": "CaseStrainer Vue API",
  "timestamp": "2024-01-15T10:30:45.123456",
  "redis": "ok",
  "database": "ok",
  "rq_worker": "ok",
  "environment": "production",
  "version": "2.0.0"
}
================================================================================
```

## Log File Locations

The JSON response logs are written to the same log files as the rest of the application:

- **Main application logs**: `logs/app.log`
- **Citation verification logs**: `logs/citation_verification_*.log`
- **Console output**: If running in development mode

## Testing the Logging System

### Using the Test Script

A test script is provided to verify that the logging system is working correctly:

```bash
python test_json_logging.py
```

This script will:
1. Make requests to various API endpoints
2. Display the responses
3. Instruct you to check the logs for the JSON response entries

### Manual Testing

You can also test manually by:

1. **Starting the application**:
   ```bash
   python src/app_final_vue.py
   ```

2. **Making API requests** using curl, Postman, or your browser:
   ```bash
   curl http://localhost:5000/casestrainer/api/health
   ```

3. **Checking the logs** for entries starting with "JSON RESPONSE BEING SENT TO FRONTEND"

## Configuration

### Enabling/Disabling Logging

To disable JSON response logging, you can comment out the `after_request` registration in each file:

```python
# Comment out this line to disable logging
# vue_api.after_request(log_json_responses)
```

### Log Level Control

The logging level is controlled by the main application logging configuration in `src/config.py`. To reduce verbosity, you can:

1. Change the log level to WARNING or ERROR
2. Filter out specific log messages
3. Use a separate log file for JSON responses

### Performance Considerations

The logging system is designed to have minimal performance impact:

- **Non-blocking**: Logging happens after the response is generated
- **Conditional**: Only JSON responses are logged
- **Efficient**: Uses built-in Flask mechanisms
- **Error-safe**: Exceptions in logging don't affect the response

## Troubleshooting

### Common Issues

1. **No logs appearing**:
   - Check that the application is running
   - Verify log file permissions
   - Ensure logging is configured correctly

2. **JSON parsing errors**:
   - The system will log raw response data if JSON parsing fails
   - Check for malformed JSON responses

3. **Missing context information**:
   - Ensure Flask request context is available
   - Check that the after_request handler is properly registered

### Debug Mode

For additional debugging, you can enable debug logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Integration with Existing Logging

The JSON response logging integrates seamlessly with the existing logging system:

- **Same log files**: Uses existing log handlers
- **Consistent format**: Follows the same logging patterns
- **Configurable**: Respects existing log levels and configurations
- **Non-intrusive**: Doesn't interfere with other logging

## Future Enhancements

Potential improvements to the logging system:

1. **Response filtering**: Log only specific endpoints or response types
2. **Performance metrics**: Track response times and sizes
3. **Structured logging**: Use JSON format for logs
4. **Log rotation**: Implement automatic log file rotation
5. **Remote logging**: Send logs to external logging services

## Support

If you encounter issues with the JSON response logging system:

1. Check the application logs for error messages
2. Verify that all blueprints have the after_request handler registered
3. Test with the provided test script
4. Review the Flask documentation on after_request handlers 