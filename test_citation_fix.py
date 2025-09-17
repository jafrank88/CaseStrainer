"""
Focused test script for citation verification fix with enhanced output.
"""
import os
import sys
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from pprint import pprint

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from enhanced_courtlistener_verification import EnhancedCourtListenerVerifier

# Set up logging
log_file = f'citation_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ANSI color codes for console output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def format_result(result: Dict[str, Any], color: bool = True) -> str:
    """Format a verification result for display with optional color."""
    if not result:
        return f"{Colors.RED}No result{Colors.ENDC}" if color else "No result"
    
    verified = result.get('verified', False)
    confidence = result.get('confidence', 0.0)
    method = result.get('validation_method', 'unknown')
    
    # Determine status color
    status_color = Colors.GREEN if verified else Colors.RED
    confidence_color = (
        Colors.GREEN if confidence >= 0.9 else
        Colors.YELLOW if confidence >= 0.7 else
        Colors.RED
    )
    
    # Build output lines
    lines = []
    
    # Status line
    status = f"Status: {status_color}{'VERIFIED' if verified else 'NOT VERIFIED'}{Colors.ENDC if color else ''}"
    lines.append(status)
    
    # Confidence line with color based on level
    conf_str = f"Confidence: {confidence_color}{confidence:.0%}{Colors.ENDC if color else ''}"
    lines.append(conf_str)
    
    # Method line
    method_str = f"Method: {Colors.CYAN if color else ''}{method}{Colors.ENDC if color else ''}"
    lines.append(method_str)
    
    # Additional fields
    fields = [
        ('Case', 'canonical_name'),
        ('Date', 'canonical_date'),
        ('URL', 'url'),
        ('Error', 'error')
    ]
    
    for label, key in fields:
        if key in result and result[key]:
            value = result[key]
            if key == 'url' and color:
                value = f"{Colors.BLUE}{value}{Colors.ENDC}"
            elif key == 'error' and color:
                value = f"{Colors.RED}{value}{Colors.ENDC}"
            lines.append(f"{label}: {value}")
    
    # Parallel citations if available
    if 'parallel_citations' in result and result['parallel_citations']:
        lines.append("\n  Parallel Citations:")
        for i, cite in enumerate(result['parallel_citations'][:3], 1):  # Show max 3
            cite_str = f"{cite.get('volume', '?')} {cite.get('reporter', '?')} {cite.get('page', '?')}"
            lines.append(f"    {i}. {cite_str}")
        if len(result['parallel_citations']) > 3:
            lines.append(f"    ... and {len(result['parallel_citations']) - 3} more")
    
    # Raw data for debugging
    if 'raw' in result and result['raw']:
        lines.append("\n  Raw data available (set verbose=True to view)")
    
    # Join with proper indentation
    return "\n  " + "\n  ".join(lines)

def test_citation(verifier: EnhancedCourtListenerVerifier, 
                 citation: str, 
                 extracted_case_name: Optional[str] = None,
                 verbose: bool = False) -> Dict[str, Any]:
    """
    Test verification of a single citation with detailed output.
    
    Args:
        verifier: The verifier instance
        citation: The citation to test
        extracted_case_name: Optional extracted case name
        verbose: Whether to show verbose output including raw data
        
    Returns:
        Dict with test results
    """
    print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}TESTING CITATION:{Colors.ENDC} {Colors.CYAN}{citation}{Colors.ENDC}")
    if extracted_case_name:
        print(f"{Colors.BOLD}EXTRACTED CASE:{Colors.ENDC} {extracted_case_name}")
    
    start_time = time.time()
    result = {'single': {}, 'batch': {}, 'citation': citation, 'extracted_case_name': extracted_case_name}
    
    try:
        # Test single citation verification
        print(f"\n{Colors.BOLD}SINGLE CITATION VERIFICATION:{Colors.ENDC}")
        single_start = time.time()
        single_result = verifier.verify_citation_enhanced(citation, extracted_case_name)
        single_elapsed = time.time() - single_start
        
        if verbose and 'raw' in single_result:
            print(f"\n{Colors.YELLOW}Raw API Response (Single):{Colors.ENDC}")
            pprint(single_result['raw'])
            
        print(format_result(single_result))
        print(f"{Colors.YELLOW}Time: {single_elapsed:.2f}s{Colors.ENDC}")
        
        # Test batch verification
        print(f"\n{Colors.BOLD}BATCH VERIFICATION:{Colors.ENDC}")
        batch_start = time.time()
        batch_results = verifier.verify_citations_batch(
            [citation], 
            [extracted_case_name] if extracted_case_name else None
        )
        batch_elapsed = time.time() - batch_start
        
        batch_result = batch_results.get(citation, {}) if batch_results else {}
        
        if verbose and 'raw' in batch_result:
            print(f"\n{Colors.YELLOW}Raw API Response (Batch):{Colors.ENDC}")
            pprint(batch_result['raw'])
            
        print(format_result(batch_result))
        print(f"{Colors.YELLOW}Time: {batch_elapsed:.2f}s{Colors.ENDC}")
        
        # Compare single vs batch results
        print(f"\n{Colors.BOLD}COMPARISON:{Colors.ENDC}")
        if single_result.get('verified') == batch_result.get('verified'):
            print(f"  {Colors.GREEN}✓ Results match between single and batch verification{Colors.ENDC}")
        else:
            print(f"  {Colors.RED}✗ Results differ between single and batch verification{Colors.ENDC}")
        
        # Store results
        result.update({
            'single': single_result,
            'batch': batch_result,
            'single_time': single_elapsed,
            'batch_time': batch_elapsed,
            'total_time': time.time() - start_time
        })
        
    except Exception as e:
        error_msg = f"Error testing citation {citation}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        result['error'] = error_msg
        print(f"{Colors.RED}ERROR: {error_msg}{Colors.ENDC}")
    
    print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    return result

def run_test_cases(verifier: EnhancedCourtListenerVerifier, 
                  test_cases: List[Tuple[str, str]]) -> Dict[str, Dict[str, Any]]:
    """Run all test cases and return results."""
    results = {}
    
    for citation, case_name in test_cases:
        results[citation] = test_citation(verifier, citation, case_name)
        
    return results

def print_summary(results: Dict[str, Dict[str, Any]]) -> None:
    """
    Print a detailed summary of test results with statistics and color coding.
    
    Args:
        results: Dictionary of test results from run_test_cases()
    """
    if not results:
        print(f"{Colors.RED}No test results to summarize{Colors.ENDC}")
        return
    
    # Calculate statistics
    total = len(results)
    single_verified = sum(1 for r in results.values() if r.get('single', {}).get('verified', False))
    batch_verified = sum(1 for r in results.values() if r.get('batch', {}).get('verified', False))
    
    # Calculate average times
    single_times = [r.get('single_time', 0) for r in results.values() if 'single_time' in r]
    batch_times = [r.get('batch_time', 0) for r in results.values() if 'batch_time' in r]
    
    avg_single_time = sum(single_times) / len(single_times) if single_times else 0
    avg_batch_time = sum(batch_times) / len(batch_times) if batch_times else 0
    
    # Print header
    print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}TEST SUMMARY{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    
    # Print statistics
    print(f"\n{Colors.BOLD}Statistics:{Colors.ENDC}")
    print(f"  Total citations tested: {total}")
    print(f"  Successfully verified (single): {single_verified}/{total} ({single_verified/max(1,total):.0%})")
    print(f"  Successfully verified (batch):  {batch_verified}/{total} ({batch_verified/max(1,total):.0%})")
    print(f"  Avg. single verification time: {avg_single_time:.2f}s")
    print(f"  Avg. batch verification time:  {avg_batch_time:.2f}s")
    
    # Print detailed results
    print(f"\n{Colors.BOLD}Detailed Results:{Colors.ENDC}")
    for citation, result in results.items():
        single = result.get('single', {})
        batch = result.get('batch', {})
        
        # Status indicators
        single_status = f"{Colors.GREEN}✓{Colors.ENDC}" if single.get('verified') else f"{Colors.RED}✗{Colors.ENDC}"
        batch_status = f"{Colors.GREEN}✓{Colors.ENDC}" if batch.get('verified') else f"{Colors.RED}✗{Colors.ENDC}"
        
        # Get case names if available
        single_case = single.get('canonical_name', single.get('extracted_case_name', 'N/A'))
        batch_case = batch.get('canonical_name', batch.get('extracted_case_name', 'N/A'))
        
        print(f"\n{Colors.BOLD}Citation: {citation}{Colors.ENDC}")
        print(f"  Single: {single_status} {single_case}")
        print(f"  Batch:  {batch_status} {batch_case}")
        
        # Show any errors
        if 'error' in result:
            print(f"  {Colors.RED}Error: {result['error']}{Colors.ENDC}")
    
    # Print footer
    print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Log file: {os.path.abspath(log_file)}")
    print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}")


def print_citation_result(citation: str, result: Dict, verbose: bool = False) -> None:
    """Print the result of a single citation verification."""
    print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}Citation:{Colors.ENDC} {Colors.CYAN}{citation}{Colors.ENDC}")
    
    # Print single verification result
    single = result.get('single', {})
    print(f"\n{Colors.BOLD}Single Verification:{Colors.ENDC}")
    print(format_result(single))
    
    if verbose and 'raw' in single:
        print(f"\n{Colors.YELLOW}Raw API Response (Single):{Colors.ENDC}")
        pprint(single['raw'])
    
    # Print batch verification result
    batch = result.get('batch', {})
    print(f"\n{Colors.BOLD}Batch Verification:{Colors.ENDC}")
    print(format_result(batch))
    
    if verbose and 'raw' in batch:
        print(f"\n{Colors.YELLOW}Raw API Response (Batch):{Colors.ENDC}")
        pprint(batch['raw'])
    
    # Print timing information
    if 'single_time' in result and 'batch_time' in result:
        print(f"\n{Colors.BOLD}Timing:{Colors.ENDC}")
        print(f"  Single: {result['single_time']:.2f}s")
        print(f"  Batch:  {result['batch_time']:.2f}s")
    
    print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}")


def main():
    """Main function to run the test script."""
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Test citation verification with CourtListener API')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--api-key', help='CourtListener API key (overrides environment variable)')
    parser.add_argument('--summary-only', action='store_true', help='Only show the summary, not individual results')
    parser.add_argument('citations', nargs='*', help='Citations to test (format: "CITATION" or "CITATION|CASE_NAME"')
    
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or os.getenv("COURTLISTENER_API_KEY")
    if not api_key:
        print(f"{Colors.RED}ERROR: No CourtListener API key provided. Set COURTLISTENER_API_KEY environment variable or use --api-key argument.{Colors.ENDC}")
        sys.exit(1)
    
    # Prepare test cases
    test_cases = []
    
    # Add default test cases if none provided
    if not args.citations:
        test_cases = [
            ("578 U.S. 5", "Luis v. United States"),
            ("194 L. Ed. 2d 256", "Luis v. United States"),
            ("200 Wn.2d 72", "Convoyant, LLC v. DeepThink, LLC"),
            ("150 Wn.2d 135", "State v. Smith"),
            ("123 F.3d 456", "Test v. Invalid Case"),
        ]
        print(f"{Colors.YELLOW}No citations provided, using default test cases{Colors.ENDC}")
    else:
        for citation in args.citations:
            if '|' in citation:
                cite, name = citation.split('|', 1)
                test_cases.append((cite.strip(), name.strip()))
            else:
                test_cases.append((citation.strip(), None))
    
    # Initialize verifier
    verifier = EnhancedCourtListenerVerifier(api_key)
    
    # Print test header
    print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}RUNNING CITATION VERIFICATION TESTS{Colors.ENDC}")
    print(f"  API Key: {'*' * 8}{api_key[-4:] if len(api_key) > 8 else ''}")
    print(f"  Citations to test: {len(test_cases)}")
    print(f"  Verbose mode: {'ON' if args.verbose else 'OFF'}")
    print(f"  Summary only: {'YES' if args.summary_only else 'NO'}")
    print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    
    # Run tests
    results = {}
    for citation, case_name in test_cases:
        print(f"\n{Colors.BLUE}Processing: {citation}{' - ' + case_name if case_name else ''}{Colors.ENDC}")
        results[citation] = test_citation(verifier, citation, case_name, verbose=args.verbose)
        
        # Print individual results unless in summary-only mode
        if not args.summary_only:
            print_citation_result(citation, results[citation], args.verbose)
    
    # Print summary
    print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}TEST SUMMARY{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print_summary(results)
    
    # Print log file location
    print(f"\n{Colors.YELLOW}Detailed logs available in: {os.path.abspath(log_file)}{Colors.ENDC}")
    
    # Return non-zero exit code if any tests had errors
    if any('error' in r for r in results.values()):
        print(f"{Colors.RED}\nSome tests failed with errors. See logs for details.{Colors.ENDC}")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
