import requests
import json
import os
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from pathlib import Path
import logging

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create console handler with a higher log level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create formatter and add it to the handlers
log_format = '%(asctime)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)
console_handler.setFormatter(formatter)

# Remove any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Add the console handler to the logger
logger.addHandler(console_handler)

# Disable requests/urllib3 debug logs
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger.info("Logging initialized")

# Constants
BASE_URL = "http://localhost:5000/casestrainer/api"
TIMEOUT = 60  # Increased timeout to 60 seconds for longer operations

# Type aliases
JsonDict = Dict[str, Any]

@dataclass
class TestResult:
    success: bool
    status_code: int
    data: Optional[JsonDict] = None
    duration: float = 0
    error: Optional[str] = None

class CitationTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.timeout = TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CaseStrainer-Test/1.0',
            'Accept': 'application/json'
        })

    def _make_request(self, endpoint: str, method: str = "POST", timeout: int = 30, **kwargs) -> TestResult:
        """Generic method to make HTTP requests with error handling and retries"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        start_time = time.time()
        
        # Log request details
        logger.info(f"Making {method.upper()} request to: {url}")
        if 'json' in kwargs:
            logger.debug(f"Request JSON: {kwargs['json']}")
        
        # Create a session with retry strategy
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        try:
            # Set a default timeout if not provided
            if 'timeout' not in kwargs:
                kwargs['timeout'] = timeout
                
            # Add detailed logging for API key verification
            if 'headers' in kwargs and 'Authorization' in kwargs['headers']:
                auth_header = kwargs['headers']['Authorization']
                logger.info(f"Using Authorization header: {auth_header.split()[0]} {auth_header.split()[1][:6]}...")
            
            response = session.request(method, url, **kwargs)
            response_time = int((time.time() - start_time) * 1000)  # ms
            
            # Log response details
            logger.info(f"Response status: {response.status_code} ({response_time}ms)")
            if response.status_code != 200:
                logger.error(f"Error response: {response.text[:500]}")
            
            return TestResult(
                success=True,
                status_code=response.status_code,
                data=response.json(),
                duration=response_time,
                error=None
            )
        except requests.exceptions.Timeout:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                success=False,
                status_code=0,
                data={},
                duration=duration,
                error=f"Request timed out after {duration/1000:.1f}s (timeout={kwargs.get('timeout', self.timeout)}s)"
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                success=False,
                status_code=0,
                data={},
                duration=duration,
                error=f"{type(e).__name__}: {str(e)}"
            )

    def test_single_citation(self, citation: str) -> TestResult:
        print(f"\n🔍 Testing citation: {citation}")
        logger.info(f"Testing single citation: {citation}")
        
        # First, check if we have an API key
        api_key = os.environ.get("COURTLISTENER_API_KEY")
        if not api_key:
            logger.warning("No COURTLISTENER_API_KEY environment variable found")
            print("⚠️  WARNING: No COURTLISTENER_API_KEY environment variable found")
        else:
            logger.info(f"Using CourtListener API key: {api_key[:6]}...")
        
        # Make the request with the API key in the header
        headers = {
            "Authorization": f"Token {api_key}" if api_key else "",
            "Content-Type": "application/json"
        }
        
        return self._make_request(
            "verify_citation",
            method="POST",
            json={"citation": citation},
            headers=headers,
            timeout=10  # Shorter timeout for single citation
        )

    def test_text_analysis(self, text: str) -> TestResult:
        print("\n📝 Testing text analysis...")
        logger.info(f"Testing text analysis with {len(text)} characters")
        
        # Add API key to headers if available
        api_key = os.environ.get("COURTLISTENER_API_KEY")
        headers = {
            "Authorization": f"Token {api_key}" if api_key else "",
            "Content-Type": "application/json"
        }
        
        return self._make_request(
            "analyze",
            method="POST",
            json={"text": text, "source_type": "text"},
            headers=headers,
            timeout=30  # Medium timeout for text analysis
        )

    def test_url_analysis(self, url: str) -> TestResult:
        print(f"\n🌐 Testing URL: {url}")
        return self._make_request("analyze", "POST",
                               json={"url": url, "source_type": "url"},
                               timeout=60)  # Longer timeout for URL analysis

    def test_file_upload(self, file_path: Union[str, Path]) -> TestResult:
        print(f"\n📂 Testing file upload: {file_path}")
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f, 'application/pdf')}
                return self._make_request("analyze", "POST",
                                       files=files,
                                       data={"source_type": "file"},
                                       timeout=60)  # Longer timeout for file upload
        except FileNotFoundError as e:
            return TestResult(
                success=False,
                status_code=0,
                data={},
                duration=0,
                error=f"File not found: {file_path}"
            )

def print_result(result: TestResult):
    print("\n" + "="*80)
    if result.success:
        print(f"✅ Status: {result.status_code} ({result.duration/1000:.1f}s)")
        
        # Handle single citation response
        if 'case_name' in result.data:
            print(f"\n📄 Case: {result.data.get('case_name', 'Unknown')}")
            if 'url' in result.data:
                print(f"🔗 URL: {result.data['url']}")
        # Handle analysis response
        elif 'citations' in result.data:
            citations = result.data['citations']
            confirmed = sum(1 for c in citations if c.get('status') == 'confirmed')
            possible = len(citations) - confirmed
            
            print(f"\n📊 Found {len(citations)} citations ({confirmed} confirmed, {possible} possible)")
            
            if citations:
                print("\n🔍 Sample Citations:")
                for i, cite in enumerate(citations[:2], 1):
                    print(f"   {i}. {cite.get('citation', 'N/A')}")
                if len(citations) > 2:
                    print(f"   ... and {len(citations) - 2} more")
    else:
        print(f"❌ Status: {result.status_code} ({result.duration/1000:.1f}s)")
        print(f"\n❌ {result.error}")
    print("="*80)

def load_config():
    """Load configuration from environment variables or config.json"""
    config = {}
    
    # Try to load from config.json
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            logger.info("Successfully loaded config.json")
    except FileNotFoundError:
        logger.warning("config.json not found")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config.json: {e}")
    
    # Check for API key in environment or config
    if not os.environ.get("COURTLISTENER_API_KEY"):
        if "COURTLISTENER_API_KEY" in config:
            os.environ["COURTLISTENER_API_KEY"] = config["COURTLISTENER_API_KEY"]
            logger.info("Using API key from config.json")
        elif "courtlistener_api_key" in config and config["courtlistener_api_key"] != "YOUR_API_KEY_HERE":
            os.environ["COURTLISTENER_API_KEY"] = config["courtlistener_api_key"]
            logger.info("Using API key from config.json (legacy key name)")
    
    # Verify we have the API key
    if not os.environ.get("COURTLISTENER_API_KEY"):
        print("\n❌ ERROR: No CourtListener API key found.")
        print("Please either:")
        print("1. Set the COURTLISTENER_API_KEY environment variable, or")
        print("2. Add it to config.json as 'COURTLISTENER_API_KEY'")
        print("\nYou can get an API key from: https://www.courtlistener.com/api/")
        return False
        
    return True

def main():
    print("=== Starting test_api.py ===")
    print("Current working directory:", os.getcwd())
    
    # Load configuration and check for API key
    print("\n[1/5] Loading configuration...")
    if not load_config():
        print("❌ Failed to load configuration")
        return
    print("✅ Configuration loaded successfully")
    
    # Check for API key
    api_key = os.environ.get("COURTLISTENER_API_KEY")
    if not api_key:
        print("❌ No COURTLISTENER_API_KEY found in environment")
        return
    print(f"✅ Found API key: {api_key[:6]}...")
    
    # Initialize tester
    print("\n[2/5] Initializing tester...")
    try:
        tester = CitationTester()
        print("✅ Tester initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize tester: {e}")
        return
    
    # Log start of testing
    print("\n[3/5] Starting API tests...")
    
    # Test single citation with a recent case
    print("\n" + "="*80)
    print("1. SINGLE CITATION VALIDATION")
    print("="*80)
    
    # Test with a well-known case first to verify the API is working
    print("\n🔍 Testing with landmark case (should be in database):")
    result = tester.test_single_citation("347 U.S. 483")  # Brown v. Board of Education
    print_result(result)
    
    # Then test with a recent case
    print("\n🔍 Testing with recent case (may not be in database):")
    result = tester.test_single_citation("591 U.S. ___")  # Recent case
    print_result(result)
    
    # Test text analysis with mixed citations
    print("\n" + "="*80)
    print("2. TEXT ANALYSIS")
    print("="*80)
    sample_text = """
    In recent years, the Supreme Court has decided several important cases. 
    In Bostock v. Clayton County, 590 U.S. ___ (2020), the Court held that 
    Title VII protects employees against discrimination based on sexual 
    orientation or gender identity. Another significant case is McGirt v. 
    Oklahoma, 591 U.S. ___ (2020), which affirmed Native American 
    sovereignty over much of eastern Oklahoma.
    """
    result = tester.test_text_analysis(sample_text)
    print_result(result)
    
    # Test URL analysis
    print("\n" + "="*80)
    print("3. URL ANALYSIS")
    print("="*80)
    try:
        result = tester.test_url_analysis("https://en.wikipedia.org/wiki/Brown_v._Board_of_Education")
        print_result(result)
    except KeyboardInterrupt:
        print("\n⚠️  URL analysis was interrupted by user")
        print("="*80)
    
    # Test file upload
    print("\n" + "="*80)
    print("4. FILE UPLOAD")
    print("="*80)
    test_file = Path("test_files") / "test.pdf"
    if not test_file.exists():
        print(f"\n⚠️  Test file not found: {test_file}")
        print("   Please create a test PDF in the test_files directory.")
    else:
        result = tester.test_file_upload(test_file)
        print_result(result)

if __name__ == "__main__":
    main()
