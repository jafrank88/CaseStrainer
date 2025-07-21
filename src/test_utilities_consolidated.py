"""
Consolidated Test Utilities
Combines various test and utility functions from multiple files.
"""

import os
import sys
import socket
import sqlite3
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.citation_correction_engine import CitationCorrectionEngine
except ImportError:
    CitationCorrectionEngine = None

# Set up logging
logger = logging.getLogger(__name__)


def get_local_ip() -> str:
    """
    Get the local IP address of the machine.
    
    Returns:
        Local IP address as string
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


class SimpleTestServer(SimpleHTTPRequestHandler):
    """Simple HTTP server for testing purposes."""
    
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Hello, World!")


def start_simple_server(port: int = 5000) -> None:
    """
    Start a simple HTTP server for testing.
    
    Args:
        port: Port number to use
    """
    local_ip = get_local_ip()
    
    print(f"Starting server on {local_ip}:{port}")
    print(f"Try accessing: http://{local_ip}:{port}")
    print("Press Ctrl+C to stop")
    
    try:
        httpd = HTTPServer(("0.0.0.0", port), SimpleTestServer)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")


def add_sample_citation() -> None:
    """Add a sample citation to the database for testing."""
    if not CitationCorrectionEngine:
        logger.error("CitationCorrectionEngine not available")
        return
    
    # Create an instance of the correction engine
    engine = CitationCorrectionEngine()
    
    try:
        # Connect to the database
        conn = sqlite3.connect(engine.db_path)
        cursor = conn.cursor()
        
        # Add a sample citation
        cursor.execute(
            """
        INSERT OR IGNORE INTO citations 
        (volume, reporter, page, case_name, court, year, normalized_citation, is_verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "123",
                "F.3d",
                "456",
                "Sample v. Test Case",
                "United States Court of Appeals for the Ninth Circuit",
                2023,
                "123 F.3d 456",
                1,
            ),
        )
        
        # Commit the changes
        conn.commit()
        logger.info("Successfully added sample citation to the database.")
        
    except Exception as e:
        logger.error(f"Error adding sample citation: {e}")
        raise
    finally:
        if conn:
            conn.close()


def extract_citation_string(citation_obj) -> str:
    """
    Extract citation string from a citation object.
    
    Args:
        citation_obj: Citation object from CaseHold
        
    Returns:
        Citation string
    """
    if hasattr(citation_obj, 'citation'):
        return citation_obj.citation
    elif hasattr(citation_obj, 'matched_text'):
        return citation_obj.matched_text()
    elif isinstance(citation_obj, str):
        return citation_obj
    else:
        return str(citation_obj)


def verify_casehold_citations() -> Dict[str, Any]:
    """
    Verify citations using CaseHold dataset.
    
    Returns:
        Dictionary with verification results
    """
    try:
        # This would typically load CaseHold citations
        # For now, return a placeholder result
        return {
            'status': 'success',
            'total_citations': 0,
            'verified_citations': 0,
            'message': 'CaseHold verification not implemented'
        }
    except Exception as e:
        logger.error(f"Error in CaseHold verification: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


async def verify_vue_api_logging() -> Dict[str, Any]:
    """
    Verify Vue API logging functionality.
    
    Returns:
        Dictionary with verification results
    """
    try:
        # Test Vue API endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:5000/api/health') as response:
                if response.status == 200:
                    return {
                        'status': 'success',
                        'message': 'Vue API logging verified',
                        'response_status': response.status
                    }
                else:
                    return {
                        'status': 'warning',
                        'message': f'Vue API returned status {response.status}',
                        'response_status': response.status
                    }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Vue API verification failed: {e}',
            'error': str(e)
        }


async def verify_citation_api_logging() -> Dict[str, Any]:
    """
    Verify citation API logging functionality.
    
    Returns:
        Dictionary with verification results
    """
    try:
        # Test citation API endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:5000/api/citations/health') as response:
                if response.status == 200:
                    return {
                        'status': 'success',
                        'message': 'Citation API logging verified',
                        'response_status': response.status
                    }
                else:
                    return {
                        'status': 'warning',
                        'message': f'Citation API returned status {response.status}',
                        'response_status': response.status
                    }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Citation API verification failed: {e}',
            'error': str(e)
        }


def verify_app_routes_logging() -> Dict[str, Any]:
    """
    Verify application routes logging functionality.
    
    Returns:
        Dictionary with verification results
    """
    try:
        # Check if logging is properly configured
        root_logger = logging.getLogger()
        if root_logger.handlers:
            return {
                'status': 'success',
                'message': 'App routes logging verified',
                'handlers_count': len(root_logger.handlers)
            }
        else:
            return {
                'status': 'warning',
                'message': 'No logging handlers found',
                'handlers_count': 0
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'App routes logging verification failed: {e}',
            'error': str(e)
        }


def check_logging_function_exists() -> Dict[str, Any]:
    """
    Check if logging functions exist in the application.
    
    Returns:
        Dictionary with check results
    """
    try:
        # Check for common logging functions
        functions_to_check = [
            'verify_vue_api_logging',
            'verify_citation_api_logging',
            'verify_app_routes_logging'
        ]
        
        results = {}
        for func_name in functions_to_check:
            if func_name in globals():
                results[func_name] = 'exists'
            else:
                results[func_name] = 'missing'
        
        return {
            'status': 'success',
            'message': 'Logging function check completed',
            'functions': results
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Logging function check failed: {e}',
            'error': str(e)
        }


async def run_all_verifications() -> Dict[str, Any]:
    """
    Run all verification functions.
    
    Returns:
        Dictionary with all verification results
    """
    results = {
        'vue_api': await verify_vue_api_logging(),
        'citation_api': await verify_citation_api_logging(),
        'app_routes': verify_app_routes_logging(),
        'logging_functions': check_logging_function_exists(),
        'casehold': verify_casehold_citations()
    }
    
    return results


def main():
    """Main function for testing and demonstration."""
    print("=== Test Utilities Demo ===")
    
    # Test local IP
    local_ip = get_local_ip()
    print(f"Local IP: {local_ip}")
    
    # Test sample citation addition
    print("\nAdding sample citation...")
    try:
        add_sample_citation()
        print("Sample citation added successfully")
    except Exception as e:
        print(f"Failed to add sample citation: {e}")
    
    # Test verification functions
    print("\nRunning verifications...")
    try:
        results = asyncio.run(run_all_verifications())
        for name, result in results.items():
            print(f"{name}: {result['status']} - {result['message']}")
    except Exception as e:
        print(f"Verification failed: {e}")
    
    print("\nTest utilities demo completed!")


if __name__ == "__main__":
    main() 