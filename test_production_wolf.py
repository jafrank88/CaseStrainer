#!/usr/bin/env python3
"""
Comprehensive Production Test Suite for CaseStrainer at wolf.law.uw.edu
Tests all input types (text, file, URL) in both sync and async modes
Verifies real citation analysis functionality after deployment fixes
"""

import requests
import json
import time
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CaseStrainerProductionTester:
    def __init__(self, base_url: str = "https://wolf.law.uw.edu/casestrainer"):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CaseStrainer-Production-Test/1.0',
            'Accept': 'application/json'
        })
        
        # Test data
        self.test_citations = {
            'short_text': "City of Seattle v. Ratliff, 100 Wn.2d 212, 218, 667 P.2d 630 (1983)",
            'medium_text': """
            The court in City of Seattle v. Ratliff, 100 Wn.2d 212, 218, 667 P.2d 630 (1983) 
            established important precedent. See also Brown v. Board of Education, 347 U.S. 483 (1954).
            Additional cases include Miranda v. Arizona, 384 U.S. 436 (1966) and 
            Roe v. Wade, 410 U.S. 113 (1973).
            """,
            'long_text': """
            This comprehensive legal analysis examines multiple landmark cases that have shaped 
            American jurisprudence. The foundational case of City of Seattle v. Ratliff, 100 Wn.2d 212, 
            218, 667 P.2d 630 (1983) established crucial precedent in municipal law. The Supreme Court's 
            decision in Brown v. Board of Education, 347 U.S. 483 (1954) fundamentally transformed 
            civil rights law by declaring racial segregation in public schools unconstitutional.
            
            Criminal procedure was revolutionized by Miranda v. Arizona, 384 U.S. 436 (1966), which 
            established the requirement for police to inform suspects of their constitutional rights. 
            Privacy rights were significantly expanded in Roe v. Wade, 410 U.S. 113 (1973), which 
            recognized a constitutional right to privacy in reproductive decisions.
            
            Additional significant cases include Marbury v. Madison, 5 U.S. 137 (1803), which 
            established judicial review; Gideon v. Wainwright, 372 U.S. 335 (1963), ensuring 
            right to counsel; and New York Times Co. v. Sullivan, 376 U.S. 254 (1964), protecting 
            freedom of press. These cases collectively demonstrate the evolution of constitutional 
            interpretation and the Supreme Court's role in shaping American law.
            """
        }
        
        self.test_urls = [
            "https://www.supremecourt.gov/opinions/20pdf/19-1392_6j37.pdf",  # Recent Supreme Court opinion
            "https://scholar.google.com/scholar_case?case=12146348439493293818",  # Google Scholar case
            "https://law.justia.com/cases/federal/supreme-court/1954/347/483/"  # Justia case page
        ]

    def test_health_check(self) -> Dict[str, Any]:
        """Test the health check endpoint to verify API is responding"""
        logger.info("🔍 Testing health check endpoint...")
        
        try:
            response = self.session.get(f"{self.api_base}/health", timeout=10)
            result = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'content': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                'headers': dict(response.headers)
            }
            
            # Check if this is debug API (should NOT be in production)
            if 'Debug API is working' in str(result['content']):
                result['api_type'] = 'DEBUG_API'
                result['error'] = 'CRITICAL: Debug API detected in production!'
            elif 'production' in str(result['content']).lower() or 'vue_api' in str(result['content']).lower():
                result['api_type'] = 'PRODUCTION_API'
            else:
                result['api_type'] = 'UNKNOWN'
            
            logger.info(f"✅ Health check completed: {result['api_type']} ({response.status_code})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {'error': str(e), 'api_type': 'ERROR'}

    def test_text_analysis_sync(self, text: str, test_name: str) -> Dict[str, Any]:
        """Test synchronous text analysis (short text should process immediately)"""
        logger.info(f"🔍 Testing sync text analysis: {test_name}")
        
        try:
            payload = {
                'type': 'text',
                'text': text
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{self.api_base}/analyze",
                json=payload,
                timeout=30
            )
            end_time = time.time()
            
            result = {
                'test_name': test_name,
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'content': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            # Analyze response for real vs mock data
            content = result['content']
            if isinstance(content, dict):
                citations = content.get('citations', [])
                if any('DEBUG-TEST' in str(citation) for citation in citations):
                    result['data_type'] = 'MOCK_DEBUG'
                    result['error'] = 'Mock debug data detected!'
                elif citations and len(citations) > 0:
                    result['data_type'] = 'REAL_CITATIONS'
                    result['citation_count'] = len(citations)
                else:
                    result['data_type'] = 'NO_CITATIONS'
            
            logger.info(f"✅ Sync text analysis completed: {result.get('data_type', 'UNKNOWN')} ({response.status_code})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Sync text analysis failed: {e}")
            return {'test_name': test_name, 'error': str(e)}

    def test_text_analysis_async(self, text: str, test_name: str) -> Dict[str, Any]:
        """Test asynchronous text analysis (long text should be queued)"""
        logger.info(f"🔍 Testing async text analysis: {test_name}")
        
        try:
            payload = {
                'type': 'text',
                'text': text
            }
            
            # Submit for processing
            response = self.session.post(
                f"{self.api_base}/analyze",
                json=payload,
                timeout=30
            )
            
            if response.status_code != 202:
                return {
                    'test_name': test_name,
                    'error': f'Expected 202 for async processing, got {response.status_code}',
                    'content': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                }
            
            initial_response = response.json()
            task_id = initial_response.get('task_id')
            
            if not task_id:
                return {
                    'test_name': test_name,
                    'error': 'No task_id returned for async processing',
                    'content': initial_response
                }
            
            # Poll for results
            max_polls = 30  # 5 minutes max
            poll_interval = 10  # seconds
            
            for poll_count in range(max_polls):
                logger.info(f"📊 Polling for results (attempt {poll_count + 1}/{max_polls})...")
                
                poll_response = self.session.get(
                    f"{self.api_base}/task_status/{task_id}",
                    timeout=10
                )
                
                if poll_response.status_code == 200:
                    poll_data = poll_response.json()
                    status = poll_data.get('status', 'unknown')
                    
                    if status in ['completed', 'success']:
                        result = {
                            'test_name': test_name,
                            'task_id': task_id,
                            'status': status,
                            'polls_required': poll_count + 1,
                            'total_time': (poll_count + 1) * poll_interval,
                            'content': poll_data
                        }
                        
                        # Analyze response for real vs mock data
                        citations = poll_data.get('citations', [])
                        if any('DEBUG-TEST' in str(citation) for citation in citations):
                            result['data_type'] = 'MOCK_DEBUG'
                            result['error'] = 'Mock debug data detected!'
                        elif citations and len(citations) > 0:
                            result['data_type'] = 'REAL_CITATIONS'
                            result['citation_count'] = len(citations)
                        else:
                            result['data_type'] = 'NO_CITATIONS'
                        
                        logger.info(f"✅ Async text analysis completed: {result.get('data_type', 'UNKNOWN')}")
                        return result
                    
                    elif status in ['failed', 'error']:
                        return {
                            'test_name': test_name,
                            'task_id': task_id,
                            'error': f'Task failed: {poll_data.get("message", "Unknown error")}',
                            'content': poll_data
                        }
                
                time.sleep(poll_interval)
            
            return {
                'test_name': test_name,
                'task_id': task_id,
                'error': 'Timeout waiting for async processing to complete'
            }
            
        except Exception as e:
            logger.error(f"❌ Async text analysis failed: {e}")
            return {'test_name': test_name, 'error': str(e)}

    def test_file_upload(self) -> Dict[str, Any]:
        """Test file upload analysis (always async)"""
        logger.info("🔍 Testing file upload analysis...")
        
        try:
            # Create a test PDF file with citations
            test_content = """
            Legal Analysis Document
            
            This document contains several important legal citations for testing purposes:
            
            1. City of Seattle v. Ratliff, 100 Wn.2d 212, 218, 667 P.2d 630 (1983)
            2. Brown v. Board of Education, 347 U.S. 483 (1954)
            3. Miranda v. Arizona, 384 U.S. 436 (1966)
            
            These cases represent significant legal precedents in their respective areas of law.
            """
            
            # Create temporary text file (simpler than PDF for testing)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_content)
                temp_file_path = f.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {'file': ('test_citations.txt', f, 'text/plain')}
                    
                    response = self.session.post(
                        f"{self.api_base}/analyze",
                        files=files,
                        timeout=30
                    )
                
                if response.status_code != 202:
                    return {
                        'test_name': 'file_upload',
                        'error': f'Expected 202 for file upload, got {response.status_code}',
                        'content': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                    }
                
                initial_response = response.json()
                task_id = initial_response.get('task_id')
                
                if not task_id:
                    return {
                        'test_name': 'file_upload',
                        'error': 'No task_id returned for file upload',
                        'content': initial_response
                    }
                
                # Poll for results (similar to async text)
                max_polls = 30
                poll_interval = 10
                
                for poll_count in range(max_polls):
                    logger.info(f"📊 Polling file processing (attempt {poll_count + 1}/{max_polls})...")
                    
                    poll_response = self.session.get(
                        f"{self.api_base}/task_status/{task_id}",
                        timeout=10
                    )
                    
                    if poll_response.status_code == 200:
                        poll_data = poll_response.json()
                        status = poll_data.get('status', 'unknown')
                        
                        if status in ['completed', 'success']:
                            result = {
                                'test_name': 'file_upload',
                                'task_id': task_id,
                                'status': status,
                                'polls_required': poll_count + 1,
                                'total_time': (poll_count + 1) * poll_interval,
                                'content': poll_data
                            }
                            
                            # Analyze response
                            citations = poll_data.get('citations', [])
                            if any('DEBUG-TEST' in str(citation) for citation in citations):
                                result['data_type'] = 'MOCK_DEBUG'
                                result['error'] = 'Mock debug data detected!'
                            elif citations and len(citations) > 0:
                                result['data_type'] = 'REAL_CITATIONS'
                                result['citation_count'] = len(citations)
                            else:
                                result['data_type'] = 'NO_CITATIONS'
                            
                            logger.info(f"✅ File upload analysis completed: {result.get('data_type', 'UNKNOWN')}")
                            return result
                        
                        elif status in ['failed', 'error']:
                            return {
                                'test_name': 'file_upload',
                                'task_id': task_id,
                                'error': f'File processing failed: {poll_data.get("message", "Unknown error")}',
                                'content': poll_data
                            }
                    
                    time.sleep(poll_interval)
                
                return {
                    'test_name': 'file_upload',
                    'task_id': task_id,
                    'error': 'Timeout waiting for file processing to complete'
                }
                
            finally:
                # Clean up temp file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"❌ File upload test failed: {e}")
            return {'test_name': 'file_upload', 'error': str(e)}

    def test_url_analysis(self, url: str) -> Dict[str, Any]:
        """Test URL analysis (always async)"""
        logger.info(f"🔍 Testing URL analysis: {url}")
        
        try:
            payload = {
                'type': 'url',
                'url': url
            }
            
            response = self.session.post(
                f"{self.api_base}/analyze",
                json=payload,
                timeout=30
            )
            
            if response.status_code != 202:
                return {
                    'test_name': 'url_analysis',
                    'url': url,
                    'error': f'Expected 202 for URL analysis, got {response.status_code}',
                    'content': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                }
            
            initial_response = response.json()
            task_id = initial_response.get('task_id')
            
            if not task_id:
                return {
                    'test_name': 'url_analysis',
                    'url': url,
                    'error': 'No task_id returned for URL analysis',
                    'content': initial_response
                }
            
            # Poll for results (URLs may take longer)
            max_polls = 60  # 10 minutes max for URLs
            poll_interval = 10
            
            for poll_count in range(max_polls):
                logger.info(f"📊 Polling URL processing (attempt {poll_count + 1}/{max_polls})...")
                
                poll_response = self.session.get(
                    f"{self.api_base}/task_status/{task_id}",
                    timeout=10
                )
                
                if poll_response.status_code == 200:
                    poll_data = poll_response.json()
                    status = poll_data.get('status', 'unknown')
                    
                    if status in ['completed', 'success']:
                        result = {
                            'test_name': 'url_analysis',
                            'url': url,
                            'task_id': task_id,
                            'status': status,
                            'polls_required': poll_count + 1,
                            'total_time': (poll_count + 1) * poll_interval,
                            'content': poll_data
                        }
                        
                        # Analyze response
                        citations = poll_data.get('citations', [])
                        if any('DEBUG-TEST' in str(citation) for citation in citations):
                            result['data_type'] = 'MOCK_DEBUG'
                            result['error'] = 'Mock debug data detected!'
                        elif citations and len(citations) > 0:
                            result['data_type'] = 'REAL_CITATIONS'
                            result['citation_count'] = len(citations)
                        else:
                            result['data_type'] = 'NO_CITATIONS'
                        
                        logger.info(f"✅ URL analysis completed: {result.get('data_type', 'UNKNOWN')}")
                        return result
                    
                    elif status in ['failed', 'error']:
                        return {
                            'test_name': 'url_analysis',
                            'url': url,
                            'task_id': task_id,
                            'error': f'URL processing failed: {poll_data.get("message", "Unknown error")}',
                            'content': poll_data
                        }
                
                time.sleep(poll_interval)
            
            return {
                'test_name': 'url_analysis',
                'url': url,
                'task_id': task_id,
                'error': 'Timeout waiting for URL processing to complete'
            }
            
        except Exception as e:
            logger.error(f"❌ URL analysis test failed: {e}")
            return {'test_name': 'url_analysis', 'url': url, 'error': str(e)}

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run the complete test suite"""
        logger.info("🚀 Starting comprehensive production test suite...")
        
        results = {
            'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'server_url': self.base_url,
            'tests': {}
        }
        
        # 1. Health Check
        logger.info("\n" + "="*50)
        logger.info("PHASE 1: HEALTH CHECK")
        logger.info("="*50)
        results['tests']['health_check'] = self.test_health_check()
        
        # 2. Synchronous Text Analysis
        logger.info("\n" + "="*50)
        logger.info("PHASE 2: SYNCHRONOUS TEXT ANALYSIS")
        logger.info("="*50)
        results['tests']['sync_text_short'] = self.test_text_analysis_sync(
            self.test_citations['short_text'], 'sync_text_short'
        )
        results['tests']['sync_text_medium'] = self.test_text_analysis_sync(
            self.test_citations['medium_text'], 'sync_text_medium'
        )
        
        # 3. Asynchronous Text Analysis
        logger.info("\n" + "="*50)
        logger.info("PHASE 3: ASYNCHRONOUS TEXT ANALYSIS")
        logger.info("="*50)
        results['tests']['async_text_long'] = self.test_text_analysis_async(
            self.test_citations['long_text'], 'async_text_long'
        )
        
        # 4. File Upload Analysis
        logger.info("\n" + "="*50)
        logger.info("PHASE 4: FILE UPLOAD ANALYSIS")
        logger.info("="*50)
        results['tests']['file_upload'] = self.test_file_upload()
        
        # 5. URL Analysis (test one URL to avoid overwhelming the server)
        logger.info("\n" + "="*50)
        logger.info("PHASE 5: URL ANALYSIS")
        logger.info("="*50)
        results['tests']['url_analysis'] = self.test_url_analysis(self.test_urls[0])
        
        # Generate summary
        results['summary'] = self._generate_summary(results['tests'])
        
        logger.info("\n" + "="*50)
        logger.info("TEST SUITE COMPLETED")
        logger.info("="*50)
        
        return results

    def _generate_summary(self, tests: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of test results"""
        summary = {
            'total_tests': len(tests),
            'passed': 0,
            'failed': 0,
            'api_type': 'UNKNOWN',
            'real_citations_detected': False,
            'mock_data_detected': False,
            'critical_issues': []
        }
        
        for test_name, test_result in tests.items():
            if 'error' in test_result:
                summary['failed'] += 1
            else:
                summary['passed'] += 1
            
            # Check API type from health check
            if test_name == 'health_check':
                summary['api_type'] = test_result.get('api_type', 'UNKNOWN')
                if test_result.get('api_type') == 'DEBUG_API':
                    summary['critical_issues'].append('Debug API detected in production!')
            
            # Check for real vs mock data
            data_type = test_result.get('data_type')
            if data_type == 'REAL_CITATIONS':
                summary['real_citations_detected'] = True
            elif data_type == 'MOCK_DEBUG':
                summary['mock_data_detected'] = True
                summary['critical_issues'].append(f'Mock debug data detected in {test_name}')
        
        # Overall assessment
        if summary['api_type'] == 'DEBUG_API':
            summary['overall_status'] = 'CRITICAL_FAILURE'
            summary['message'] = 'Debug API is active in production - deployment failed'
        elif summary['mock_data_detected']:
            summary['overall_status'] = 'PARTIAL_FAILURE'
            summary['message'] = 'Mock data detected - real citation service not fully active'
        elif summary['real_citations_detected'] and summary['failed'] == 0:
            summary['overall_status'] = 'SUCCESS'
            summary['message'] = 'All tests passed - real citation analysis is working'
        elif summary['real_citations_detected']:
            summary['overall_status'] = 'PARTIAL_SUCCESS'
            summary['message'] = 'Real citations detected but some tests failed'
        else:
            summary['overall_status'] = 'FAILURE'
            summary['message'] = 'No real citation analysis detected'
        
        return summary

def main():
    """Main test execution"""
    print("🧪 CaseStrainer Production Test Suite")
    print("=" * 60)
    print(f"Target: https://wolf.law.uw.edu/casestrainer")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("=" * 60)
    
    tester = CaseStrainerProductionTester()
    results = tester.run_comprehensive_test()
    
    # Save results to file
    results_file = f"production_test_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    summary = results['summary']
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Overall Status: {summary['overall_status']}")
    print(f"Message: {summary['message']}")
    print(f"API Type: {summary['api_type']}")
    print(f"Tests Passed: {summary['passed']}/{summary['total_tests']}")
    print(f"Real Citations Detected: {summary['real_citations_detected']}")
    print(f"Mock Data Detected: {summary['mock_data_detected']}")
    
    if summary['critical_issues']:
        print("\n🚨 CRITICAL ISSUES:")
        for issue in summary['critical_issues']:
            print(f"  - {issue}")
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    main()
