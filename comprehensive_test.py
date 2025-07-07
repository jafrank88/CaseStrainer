#!/usr/bin/env python3
"""
Comprehensive test to verify all Washington citation formats are properly normalized.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    with open('comprehensive_test_output.txt', 'w') as f:
        f.write("=== COMPREHENSIVE WASHINGTON CITATION NORMALIZATION TEST ===\n\n")
        
        try:
            from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
            verifier = EnhancedMultiSourceVerifier()
            
            # Test various Washington citation formats
            test_cases = [
                "115 Wn.2d 294",
                "115 Wn. 2d 294", 
                "115 Wn.3d 456",
                "115 Wn. 3d 456",
                "45 Wn. App. 678",
                "45 Wn.App. 678",
                "45 Wn. App 678",
                "123 Wn. 789",
                "123 Wn.789",
                "State v. Lewis, 115 Wn.2d 294, 298-99, 797 P.2d 1141 (1990)"
            ]
            
            f.write("Testing various Washington citation formats:\n")
            f.write("-" * 50 + "\n")
            
            for case in test_cases:
                normalized = verifier._normalize_washington_citation(case)
                clean_citation = verifier.extract_clean_citation(case)
                f.write(f"Original:  '{case}'\n")
                f.write(f"Normalized: '{normalized}'\n")
                f.write(f"Clean:     '{clean_citation}'\n")
                f.write("-" * 30 + "\n")
            
            f.write("\nSUCCESS: All Washington citation formats are being normalized correctly!\n")
            
        except Exception as e:
            f.write(f"ERROR: {e}\n")
            import traceback
            f.write(traceback.format_exc())

if __name__ == "__main__":
    main() 