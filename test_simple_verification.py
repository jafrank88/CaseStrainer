#!/usr/bin/env python3
"""
Simple test to check if verification is enabled
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_verification_config():
    """Test if verification is enabled in config"""
    
    print("🔍 Testing Verification Configuration")
    print("=" * 50)
    
    try:
        from models import ProcessingConfig
        
        # Create default config
        config = ProcessingConfig()
        
        print("📋 Default Configuration:")
        print(f"   enable_verification: {config.enable_verification}")
        print(f"   enable_clustering: {config.enable_clustering}")
        print(f"   extract_case_names: {config.extract_case_names}")
        print(f"   extract_dates: {config.extract_dates}")
        print(f"   use_eyecite: {config.use_eyecite}")
        print(f"   use_regex: {config.use_regex}")
        print()
        
        if config.enable_verification:
            print("✅ Verification is ENABLED in configuration")
        else:
            print("❌ Verification is DISABLED in configuration")
            
        # Test CourtListener API key
        try:
            from config import get_config_value
            api_key = get_config_value("COURTLISTENER_API_KEY", "")
            if api_key:
                print("✅ CourtListener API key is configured")
            else:
                print("❌ CourtListener API key is NOT configured")
        except Exception as e:
            print(f"⚠️ Could not check API key: {e}")
            
        # Test if we can import the processor
        try:
            from unified_citation_processor_v2 import UnifiedCitationProcessorV2
            processor = UnifiedCitationProcessorV2(config=config)
            print("✅ UnifiedCitationProcessorV2 can be instantiated")
            print(f"   Processor config.enable_verification: {processor.config.enable_verification}")
        except Exception as e:
            print(f"❌ Could not instantiate processor: {e}")
            
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main execution"""
    test_verification_config()

if __name__ == "__main__":
    main()
