# CaseStrainer

A web application for extracting and validating legal citations from documents.

## Features

- Extract citations from PDF, DOCX, and text files
- Validate citations against CourtListener API
- Support for multiple users
- Real-time citation verification
- Modern Vue.js frontend

## Requirements

- Python 3.8 or higher
- Windows 10 or higher
- Internet connection for API access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/CaseStrainer.git
cd CaseStrainer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Windows

The application can be started in two modes:

#### Development Mode (Default)
```bash
start_casestrainer.bat
```
This runs the Flask development server with debug mode enabled, which is ideal for development and testing.

#### Production Mode
```bash
start_casestrainer.bat production
```
This runs the application using Waitress WSGI server, which is suitable for production deployment.

### Manual Start

#### Development Mode
1. Set environment variables:
```bash
set FLASK_ENV=development
set FLASK_APP=src/app_final_vue.py
set FLASK_DEBUG=1
```

2. Run the development server:
```bash
python -m flask run --host=0.0.0.0 --port=5000
```

#### Production Mode
1. Set environment variables:
```bash
set FLASK_ENV=production
set FLASK_APP=src/app_final_vue.py
```

2. Run the production server:
```bash
python run_production.py
```

The application will be available at:
- Local: http://localhost:5000
- Network: http://your-ip-address:5000

## Development vs Production

### Development Mode
- Uses Flask's built-in development server
- Enables debug mode for detailed error messages
- Auto-reloads on code changes
- Not suitable for production use

### Production Mode
- Uses Waitress WSGI server
- Disables debug mode for security
- Handles multiple users efficiently
- Includes proper logging and error handling
- Suitable for production deployment

## Configuration

The application can be configured through environment variables:

- `FLASK_ENV`: Set to 'production' or 'development'
- `FLASK_APP`: Path to the main application file (src/app_final_vue.py)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 5000)
- `THREADS`: Number of worker threads (default: 10)
- `COURTLISTENER_API_KEY`: Your CourtListener API key

## Directory Structure

- `src/`: Source code
  - `app_final_vue.py`: Main application file
  - `run_production.py`: Production server script
- `logs/`: Application logs
- `uploads/`: Temporary file storage
- `casestrainer_sessions/`: User session data

## Troubleshooting

1. If you get a "port already in use" error:
   - Change the PORT environment variable
   - Or close the application using the port

2. If the application doesn't start:
   - Check the logs in the `logs` directory
   - Ensure all dependencies are installed
   - Verify your CourtListener API key

3. Development Mode Issues:
   - Make sure FLASK_DEBUG=1 is set
   - Check for syntax errors in the code
   - Verify all imports are working

4. Production Mode Issues:
   - Check the production logs
   - Verify all environment variables are set
   - Ensure proper permissions on directories

## Support

For issues and feature requests, please create an issue in the GitHub repository. 