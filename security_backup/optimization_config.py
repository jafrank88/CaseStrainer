"""
Optimization Configuration
Controls which performance optimizations are enabled.
"""

import os
from typing import Dict, Any

class OptimizationConfig:
    """
    Configuration for performance optimizations.
    """
    
    def __init__(self):
        # PDF Extraction Optimizations
        self.USE_ULTRA_FAST_PDF_EXTRACTION: bool = True
        self.SKIP_OCR_DETECTION: bool = True
        self.MINIMAL_TEXT_CLEANING: bool = True
        
        # Citation Verification Optimizations
        self.SKIP_CITATION_VERIFICATION: bool = True
        self.REDUCE_API_TIMEOUTS: bool = True
        self.USE_LOCAL_CITATION_EXTRACTION: bool = True
        
        # Processing Optimizations
        self.USE_FAST_PROCESSING_PIPELINE: bool = True
        self.SKIP_COMPREHENSIVE_CLEANING: bool = True
        self.ENABLE_PROGRESSIVE_CLEANING: bool = True
        
        # Load from environment variables if available
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_mappings = {
            'USE_ULTRA_FAST_PDF_EXTRACTION': 'CASE_TRAINER_ULTRA_FAST_PDF',
            'SKIP_OCR_DETECTION': 'CASE_TRAINER_SKIP_OCR',
            'MINIMAL_TEXT_CLEANING': 'CASE_TRAINER_MINIMAL_CLEANING',
            'SKIP_CITATION_VERIFICATION': 'CASE_TRAINER_SKIP_VERIFICATION',
            'REDUCE_API_TIMEOUTS': 'CASE_TRAINER_REDUCE_TIMEOUTS',
            'USE_LOCAL_CITATION_EXTRACTION': 'CASE_TRAINER_LOCAL_CITATIONS',
            'USE_FAST_PROCESSING_PIPELINE': 'CASE_TRAINER_FAST_PIPELINE',
            'SKIP_COMPREHENSIVE_CLEANING': 'CASE_TRAINER_SKIP_CLEANING',
            'ENABLE_PROGRESSIVE_CLEANING': 'CASE_TRAINER_PROGRESSIVE_CLEANING'
        }
        
        for attr, env_var in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string to boolean
                if env_value.lower() in ['true', '1', 'yes', 'on']:
                    setattr(self, attr, True)
                elif env_value.lower() in ['false', '0', 'no', 'off']:
                    setattr(self, attr, False)
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get a summary of current optimization settings."""
        return {
            'pdf_extraction': {
                'ultra_fast': self.USE_ULTRA_FAST_PDF_EXTRACTION,
                'skip_ocr': self.SKIP_OCR_DETECTION,
                'minimal_cleaning': self.MINIMAL_TEXT_CLEANING
            },
            'citation_verification': {
                'skip_verification': self.SKIP_CITATION_VERIFICATION,
                'reduce_timeouts': self.REDUCE_API_TIMEOUTS,
                'local_extraction': self.USE_LOCAL_CITATION_EXTRACTION
            },
            'processing': {
                'fast_pipeline': self.USE_FAST_PROCESSING_PIPELINE,
                'skip_comprehensive_cleaning': self.SKIP_COMPREHENSIVE_CLEANING,
                'progressive_cleaning': self.ENABLE_PROGRESSIVE_CLEANING
            }
        }
    
    def is_optimized_mode(self) -> bool:
        """Check if optimized mode is enabled."""
        return (self.USE_ULTRA_FAST_PDF_EXTRACTION and 
                self.SKIP_CITATION_VERIFICATION and 
                self.USE_FAST_PROCESSING_PIPELINE)


# Global configuration instance
config = OptimizationConfig()


def enable_optimized_mode():
    """Enable all performance optimizations."""
    config.USE_ULTRA_FAST_PDF_EXTRACTION = True
    config.SKIP_OCR_DETECTION = True
    config.MINIMAL_TEXT_CLEANING = True
    config.SKIP_CITATION_VERIFICATION = True
    config.REDUCE_API_TIMEOUTS = True
    config.USE_LOCAL_CITATION_EXTRACTION = True
    config.USE_FAST_PROCESSING_PIPELINE = True
    config.SKIP_COMPREHENSIVE_CLEANING = True
    config.ENABLE_PROGRESSIVE_CLEANING = True


def disable_optimized_mode():
    """Disable all performance optimizations."""
    config.USE_ULTRA_FAST_PDF_EXTRACTION = False
    config.SKIP_OCR_DETECTION = False
    config.MINIMAL_TEXT_CLEANING = False
    config.SKIP_CITATION_VERIFICATION = False
    config.REDUCE_API_TIMEOUTS = False
    config.USE_LOCAL_CITATION_EXTRACTION = False
    config.USE_FAST_PROCESSING_PIPELINE = False
    config.SKIP_COMPREHENSIVE_CLEANING = False
    config.ENABLE_PROGRESSIVE_CLEANING = False


if __name__ == "__main__":
    # Print current optimization settings
    print("=== Optimization Configuration ===")
    summary = config.get_optimization_summary()
    
    for category, settings in summary.items():
        print(f"\n{category.upper()}:")
        for setting, value in settings.items():
            status = "✅ ENABLED" if value else "❌ DISABLED"
            print(f"  {setting}: {status}")
    
    print(f"\nOptimized Mode: {'✅ ENABLED' if config.is_optimized_mode() else '❌ DISABLED'}")
    
    # Show environment variable usage
    print(f"\nEnvironment Variables:")
    print("  CASE_TRAINER_ULTRA_FAST_PDF=true")
    print("  CASE_TRAINER_SKIP_VERIFICATION=true")
    print("  CASE_TRAINER_FAST_PIPELINE=true") 