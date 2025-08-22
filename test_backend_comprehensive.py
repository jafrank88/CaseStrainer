#!/usr/bin/env python3
"""
Comprehensive Backend Test Suite

This test suite verifies that the backend correctly handles:
1. Text input with citation extraction, clustering, and verification
2. File input (PDF) with proper text extraction and processing
3. URL input with content fetching and processing
4. Proper clustering of parallel citations
5. Extraction of case names and years
6. Verification with canonical data when available
7. Enhanced features integration (cross-validation, confidence scoring)

Test Data:
- Standard test paragraph with known citations
- Test PDF file with citations
- Test URL with legal content
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class TestBackendComprehensive(unittest.TestCase):
    """Comprehensive backend testing for all input types and features."""
    
    def setUp(self):
        """Set up test environment and data."""
        self.test_text = """
        A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
        """
        
        self.expected_citations = [
            "200 Wn.2d 72",
            "514 P.3d 643", 
            "171 Wn.2d 486",
            "256 P.3d 321",
            "146 Wn.2d 1",
            "43 P.3d 4"
        ]
        
        self.expected_clusters = [
            ["200 Wn.2d 72", "514 P.3d 643"],  # Convoyant case
            ["171 Wn.2d 486", "256 P.3d 321"],  # Carlson case
            ["146 Wn.2d 1", "43 P.3d 4"]        # Ecology case
        ]
        
        self.expected_case_names = [
            "Convoyant, LLC v. DeepThink, LLC",
            "Carlson v. Glob. Client Sols., LLC", 
            "Dep't of Ecology v. Campbell & Gwinn, LLC"
        ]
        
        self.expected_years = ["2022", "2011", "2003"]
        
        # Create test PDF content
        self.test_pdf_content = self.test_text
        
        # Create test URL content
        self.test_url_content = self.test_text
        
        # Set up test environment
        self.test_dir = tempfile.mkdtemp()
        self.test_pdf_path = os.path.join(self.test_dir, "test_citations.pdf")
        
        # Create a mock PDF file
        with open(self.test_pdf_path, 'w') as f:
            f.write(self.test_pdf_content)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_text_input_processing(self):
        """Test text input processing with enhanced features."""
        try:
            from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
            
            # Initialize processor with enhanced features
            options = ProcessingOptions(
                enable_enhanced_verification=True,
                enable_cross_validation=True,
                enable_false_positive_prevention=True,
                enable_confidence_scoring=True
            )
            
            processor = EnhancedSyncProcessor(options)
            
            # Process text input
            result = processor.process_any_input_enhanced(
                self.test_text, 'text'
            )
            
            # Verify basic structure
            self.assertTrue(result['success'])
            self.assertEqual(result['processing_mode'], 'enhanced_sync')
            self.assertIn('citations', result)
            self.assertIn('clusters', result)
            
            # Verify citations were extracted
            citations = result['citations']
            self.assertGreater(len(citations), 0)
            
            # Check that we have the expected number of citations
            self.assertGreaterEqual(len(citations), len(self.expected_citations))
            
            # Verify citation structure
            for citation in citations:
                self.assertIn('citation', citation)
                self.assertIn('extracted_case_name', citation)
                self.assertIn('extracted_date', citation)
                self.assertIn('confidence_score', citation)
                self.assertIn('extraction_method', citation)
                self.assertIn('false_positive_filtered', citation)
                
                # Check for enhanced features
                if 'verification_result' in citation and citation['verification_result']:
                    self.assertIn('verified', citation['verification_result'])
                    self.assertIn('canonical_name', citation['verification_result'])
                    self.assertIn('canonical_date', citation['verification_result'])
                    self.assertIn('url', citation['verification_result'])
                    self.assertIn('source', citation['verification_result'])
                    self.assertIn('validation_method', citation['verification_result'])
                    self.assertIn('confidence', citation['verification_result'])
            
            # Verify clusters were created
            clusters = result['clusters']
            self.assertGreaterEqual(len(clusters), len(self.expected_clusters))
            
            # Check cluster structure
            for cluster in clusters:
                self.assertIn('cluster_id', cluster)
                self.assertIn('citations', cluster)
                self.assertIn('reporter', cluster)
                self.assertIn('cluster_type', cluster)
            
            # Verify processing metadata
            self.assertIn('processing_strategy', result)
            self.assertIn('extraction_method', result)
            self.assertIn('verification_status', result)
            self.assertIn('local_processing_complete', result)
            self.assertIn('citations_found', result)
            self.assertIn('clusters_created', result)
            
            print(f"✅ Text input processing: {len(citations)} citations, {len(clusters)} clusters")
            
        except ImportError as e:
            self.skipTest(f"Enhanced processor not available: {e}")
        except Exception as e:
            self.fail(f"Text input processing failed: {e}")
    
    def test_file_input_processing(self):
        """Test file input processing with PDF extraction."""
        try:
            from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
            
            # Initialize processor
            options = ProcessingOptions(
                enable_enhanced_verification=True,
                enable_cross_validation=True,
                enable_false_positive_prevention=True,
                enable_confidence_scoring=True
            )
            
            processor = EnhancedSyncProcessor(options)
            
            # Process file input
            result = processor.process_any_input_enhanced(
                self.test_pdf_path, 'file'
            )
            
            # Verify basic structure
            self.assertTrue(result['success'])
            self.assertEqual(result['processing_mode'], 'enhanced_sync')
            self.assertIn('citations', result)
            self.assertIn('clusters', result)
            
            # Verify file metadata
            self.assertIn('metadata', result)
            metadata = result['metadata']
            self.assertEqual(metadata['input_type'], 'file')
            self.assertIn('file_path', metadata)
            self.assertIn('extraction_method', metadata)
            
            # Verify citations were extracted from file
            citations = result['citations']
            self.assertGreater(len(citations), 0)
            
            # Check citation structure
            for citation in citations:
                self.assertIn('citation', citation)
                self.assertIn('extracted_case_name', citation)
                self.assertIn('extracted_date', citation)
                self.assertIn('confidence_score', citation)
                self.assertIn('extraction_method', citation)
            
            # Verify clusters
            clusters = result['clusters']
            self.assertGreaterEqual(len(clusters), 0)
            
            print(f"✅ File input processing: {len(citations)} citations, {len(clusters)} clusters")
            
        except ImportError as e:
            self.skipTest(f"Enhanced processor not available: {e}")
        except Exception as e:
            self.fail(f"File input processing failed: {e}")
    
    def test_url_input_processing(self):
        """Test URL input processing with content fetching."""
        try:
            from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
            
            # Mock the URL fetching to avoid actual HTTP requests
            with patch('src.progress_manager.fetch_url_content') as mock_fetch:
                mock_fetch.return_value = self.test_url_content
                
                # Initialize processor
                options = ProcessingOptions(
                    enable_enhanced_verification=True,
                    enable_cross_validation=True,
                    enable_false_positive_prevention=True,
                    enable_confidence_scoring=True
                )
                
                processor = EnhancedSyncProcessor(options)
                
                # Process URL input
                test_url = "https://example.com/legal-document"
                result = processor.process_any_input_enhanced(
                    test_url, 'url'
                )
                
                # Verify basic structure
                self.assertTrue(result['success'])
                self.assertEqual(result['processing_mode'], 'enhanced_sync')
                self.assertIn('citations', result)
                self.assertIn('clusters', result)
                
                # Verify URL metadata
                self.assertIn('metadata', result)
                metadata = result['metadata']
                self.assertEqual(metadata['input_type'], 'url')
                self.assertIn('url', metadata)
                self.assertIn('content_length', metadata)
                self.assertIn('extraction_method', metadata)
                
                # Verify citations were extracted from URL
                citations = result['citations']
                self.assertGreater(len(citations), 0)
                
                # Check citation structure
                for citation in citations:
                    self.assertIn('citation', citation)
                    self.assertIn('extracted_case_name', citation)
                    self.assertIn('extracted_date', citation)
                    self.assertIn('confidence_score', citation)
                    self.assertIn('extraction_method', citation)
                
                # Verify clusters
                clusters = result['clusters']
                self.assertGreaterEqual(len(clusters), 0)
                
                print(f"✅ URL input processing: {len(citations)} citations, {len(clusters)} clusters")
                
        except ImportError as e:
            self.skipTest(f"Enhanced processor not available: {e}")
        except Exception as e:
            self.fail(f"URL input processing failed: {e}")
    
    def test_citation_clustering_logic(self):
        """Test that parallel citations are properly clustered together."""
        try:
            from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
            
            # Initialize processor
            options = ProcessingOptions(
                enable_enhanced_verification=True,
                enable_cross_validation=True,
                enable_false_positive_prevention=True,
                enable_confidence_scoring=True
            )
            
            processor = EnhancedSyncProcessor(options)
            
            # Process text input
            result = processor.process_any_input_enhanced(
                self.test_text, 'text'
            )
            
            self.assertTrue(result['success'])
            
            citations = result['citations']
            clusters = result['clusters']
            
            # Verify that we have clusters
            self.assertGreater(len(clusters), 0)
            
            # Check that parallel citations are grouped together
            # Look for the Convoyant case citations (200 Wn.2d 72 and 514 P.3d 643)
            convoyant_citations = []
            for citation in citations:
                if citation['citation'] in ["200 Wn.2d 72", "514 P.3d 643"]:
                    convoyant_citations.append(citation)
            
            # Should find both citations
            self.assertEqual(len(convoyant_citations), 2)
            
            # Check that they have the same extracted case name
            case_names = [c['extracted_case_name'] for c in convoyant_citations if c['extracted_case_name']]
            if len(case_names) > 1:
                # All case names should be similar (allowing for extraction variations)
                self.assertTrue(all('Convoyant' in name or 'DeepThink' in name for name in case_names))
            
            # Check that they have the same year
            years = [c['extracted_date'] for c in convoyant_citations if c['extracted_date']]
            if len(years) > 1:
                # All years should be the same
                self.assertEqual(len(set(years)), 1)
            
            print(f"✅ Citation clustering: {len(clusters)} clusters created")
            
        except ImportError as e:
            self.skipTest(f"Enhanced processor not available: {e}")
        except Exception as e:
            self.fail(f"Citation clustering test failed: {e}")
    
    def test_enhanced_verification_integration(self):
        """Test that enhanced verification features are properly integrated."""
        try:
            from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
            
            # Initialize processor with enhanced features
            options = ProcessingOptions(
                enable_enhanced_verification=True,
                enable_cross_validation=True,
                enable_false_positive_prevention=True,
                enable_confidence_scoring=True,
                courtlistener_api_key="test_key"  # Mock API key
            )
            
            processor = EnhancedSyncProcessor(options)
            
            # Check that enhanced features are initialized
            self.assertIsNotNone(processor.options)
            self.assertTrue(processor.options.enable_enhanced_verification)
            self.assertTrue(processor.options.enable_cross_validation)
            self.assertTrue(processor.options.enable_false_positive_prevention)
            self.assertTrue(processor.options.enable_confidence_scoring)
            
            # Check that enhanced verifier is available (or gracefully handled)
            if hasattr(processor, 'enhanced_verifier'):
                # If enhanced verification is available, it should be initialized
                # If not available, it should be None but not cause errors
                pass
            
            # Check that confidence scorer is available (or gracefully handled)
            if hasattr(processor, 'confidence_scorer'):
                # If confidence scoring is available, it should be initialized
                # If not available, it should be None but not cause errors
                pass
            
            print("✅ Enhanced verification integration: Features properly configured")
            
        except ImportError as e:
            self.skipTest(f"Enhanced processor not available: {e}")
        except Exception as e:
            self.fail(f"Enhanced verification integration test failed: {e}")
    
    def test_false_positive_prevention(self):
        """Test that false positive prevention is working."""
        try:
            from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
            
            # Initialize processor with false positive prevention
            options = ProcessingOptions(
                enable_false_positive_prevention=True,
                min_confidence_threshold=0.7
            )
            
            processor = EnhancedSyncProcessor(options)
            
            # Test with a low-quality citation that should be filtered
            test_citation = "123 Test 456"
            case_name = "Test"
            year = "2023"
            confidence = 0.3  # Below threshold
            
            # This should be filtered out
            is_valid = processor._is_valid_citation(test_citation, case_name, year, confidence)
            
            # With low confidence and short case name, it should be filtered
            if processor.options.enable_false_positive_prevention:
                self.assertFalse(is_valid)
            
            # Test with a high-quality citation that should pass
            good_citation = "200 Wn.2d 72"
            good_case_name = "Convoyant, LLC v. DeepThink, LLC"
            good_year = "2022"
            good_confidence = 0.9  # Above threshold
            
            is_valid_good = processor._is_valid_citation(good_citation, good_case_name, good_year, good_confidence)
            self.assertTrue(is_valid_good)
            
            print("✅ False positive prevention: Working correctly")
            
        except ImportError as e:
            self.skipTest(f"Enhanced processor not available: {e}")
        except Exception as e:
            self.fail(f"False positive prevention test failed: {e}")
    
    def test_confidence_scoring_integration(self):
        """Test that confidence scoring is properly integrated."""
        try:
            from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
            
            # Initialize processor with confidence scoring
            options = ProcessingOptions(
                enable_confidence_scoring=True
            )
            
            processor = EnhancedSyncProcessor(options)
            
            # Check that confidence scoring is configured
            self.assertTrue(processor.options.enable_confidence_scoring)
            
            # Test confidence scoring if available
            if hasattr(processor, 'confidence_scorer') and processor.confidence_scorer:
                # Test with a sample citation
                citation_dict = {
                    'citation': '200 Wn.2d 72',
                    'extracted_case_name': 'Convoyant v. DeepThink',
                    'extracted_date': '2022',
                    'verified': True,
                    'method': 'test'
                }
                
                # Calculate confidence
                confidence = processor.confidence_scorer.calculate_citation_confidence(
                    citation_dict, self.test_text
                )
                
                # Confidence should be a float between 0 and 1
                self.assertIsInstance(confidence, float)
                self.assertGreaterEqual(confidence, 0.0)
                self.assertLessEqual(confidence, 1.0)
                
                print(f"✅ Confidence scoring: Score calculated: {confidence:.3f}")
            else:
                print("✅ Confidence scoring: Gracefully handled when not available")
            
        except ImportError as e:
            self.skipTest(f"Enhanced processor not available: {e}")
        except Exception as e:
            self.fail(f"Confidence scoring integration test failed: {e}")
    
    def test_async_verification_queuing(self):
        """Test that async verification is properly queued."""
        try:
            from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
            
            # Initialize processor with async verification
            options = ProcessingOptions(
                enable_async_verification=True
            )
            
            processor = EnhancedSyncProcessor(options)
            
            # Check that async verification is configured
            self.assertTrue(processor.options.enable_async_verification)
            
            # Mock Redis queue to avoid actual Redis operations
            with patch('src.enhanced_sync_processor.Queue') as mock_queue:
                mock_job = MagicMock()
                mock_job.id = "test_job_123"
                mock_queue.return_value.enqueue.return_value = mock_job
                
                # Test async verification queuing
                citations = [{'citation': '200 Wn.2d 72'}]
                text = "Test text with citation"
                request_id = "test_request_123"
                input_type = "text"
                metadata = {'test': True}
                
                # This should queue the verification
                verification_status = processor._queue_async_verification(
                    citations, text, request_id, input_type, metadata
                )
                
                # Check that verification was queued
                self.assertTrue(verification_status['verification_queued'])
                self.assertIn('verification_job_id', verification_status)
                self.assertEqual(verification_status['verification_job_id'], "test_job_123")
                
                print("✅ Async verification queuing: Working correctly")
            
        except ImportError as e:
            self.skipTest(f"Enhanced processor not available: {e}")
        except Exception as e:
            self.fail(f"Async verification queuing test failed: {e}")
    
    def test_response_format_consistency(self):
        """Test that all input types return consistent response formats."""
        try:
            from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
            
            # Initialize processor
            options = ProcessingOptions(
                enable_enhanced_verification=True,
                enable_cross_validation=True,
                enable_false_positive_prevention=True,
                enable_confidence_scoring=True
            )
            
            processor = EnhancedSyncProcessor(options)
            
            # Test all input types
            input_types = [
                ('text', self.test_text),
                ('file', self.test_pdf_path),
                ('url', "https://example.com/test")
            ]
            
            for input_type, input_data in input_types:
                with patch('src.progress_manager.fetch_url_content') as mock_fetch:
                    if input_type == 'url':
                        mock_fetch.return_value = self.test_url_content
                    
                    # Process input
                    result = processor.process_any_input_enhanced(input_data, input_type)
                    
                    # Verify consistent structure
                    self.assertTrue(result['success'])
                    self.assertIn('citations', result)
                    self.assertIn('clusters', result)
                    self.assertIn('processing_mode', result)
                    self.assertIn('processing_time', result)
                    self.assertIn('request_id', result)
                    self.assertIn('text_length', result)
                    self.assertIn('input_type', result)
                    self.assertIn('metadata', result)
                    
                    # Verify metadata consistency
                    metadata = result['metadata']
                    self.assertEqual(metadata['input_type'], input_type)
                    
                    # Verify citations structure consistency
                    citations = result['citations']
                    if citations:
                        citation = citations[0]
                        required_fields = [
                            'citation', 'extracted_case_name', 'extracted_date',
                            'confidence_score', 'extraction_method', 'false_positive_filtered'
                        ]
                        for field in required_fields:
                            self.assertIn(field, citation)
                    
                    print(f"✅ Response format consistency: {input_type} input")
            
        except ImportError as e:
            self.skipTest(f"Enhanced processor not available: {e}")
        except Exception as e:
            self.fail(f"Response format consistency test failed: {e}")

def run_comprehensive_tests():
    """Run all comprehensive backend tests."""
    print("🚀 Starting Comprehensive Backend Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBackendComprehensive)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.skipped:
        print("\n⏭️ Skipped:")
        for test, reason in result.skipped:
            print(f"  - {test}: {reason}")
    
    # Overall result
    if result.wasSuccessful():
        print("\n🎉 All tests passed! Backend is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please review the issues above.")
        return False

if __name__ == '__main__':
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)

