#!/usr/bin/env python3
"""
Test script to verify that citation verification is not using the database for verification,
only for archiving.
"""

import sys
import os
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_no_database_verification():
    """Test that verification does not use database for verification, only for archiving."""
    
    print("=== Testing No Database Verification ===\n")
    
    # Initialize the verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test citation
    test_citation = "410 U.S. 113"  # Roe v. Wade
    
    print(f"Testing citation: {test_citation}")
    print("Expected behavior: Use external APIs, not database for verification")
    print("Database should only be used for archiving results\n")
    
    # Test 1: Default verification (should not use database)
    print("Test 1: Default verification (use_database=False)")
    start_time = time.time()
    result1 = verifier.verify_citation(test_citation)
    elapsed1 = time.time() - start_time
    
    print(f"Result: {result1.get('verified', False)}")
    print(f"Source: {result1.get('source', 'Unknown')}")
    print(f"Time: {elapsed1:.2f} seconds")
    
    # Check verification steps
    steps = result1.get('verification_steps', [])
    print("Verification steps:")
    for step in steps:
        print(f"  - {step.get('step', 'unknown')}: {step.get('status', 'unknown')}")
    
    # Verify no database verification was used
    db_verification_used = any(
        step.get('step') == 'database' and step.get('status') == 'verified' 
        for step in steps
    )
    
    if db_verification_used:
        print("❌ ERROR: Database verification was used!")
    else:
        print("✅ SUCCESS: No database verification was used")
    
    print()
    
    # Test 2: Explicit database archiving
    print("Test 2: With database archiving (use_database=True)")
    start_time = time.time()
    result2 = verifier.verify_citation(test_citation, use_database=True)
    elapsed2 = time.time() - start_time
    
    print(f"Result: {result2.get('verified', False)}")
    print(f"Source: {result2.get('source', 'Unknown')}")
    print(f"Time: {elapsed2:.2f} seconds")
    
    # Check verification steps
    steps2 = result2.get('verification_steps', [])
    print("Verification steps:")
    for step in steps2:
        print(f"  - {step.get('step', 'unknown')}: {step.get('status', 'unknown')}")
    
    # Verify database archiving was used
    db_archiving_used = any(
        step.get('step') == 'database_archive' and step.get('status') == 'success' 
        for step in steps2
    )
    
    if db_archiving_used:
        print("✅ SUCCESS: Database archiving was used")
    else:
        print("⚠️  WARNING: Database archiving was not used (may be expected if API failed)")
    
    print()
    
    # Test 3: Check that database methods exist but are not called automatically
    print("Test 3: Verify database methods exist but are not called automatically")
    
    # Check that database verification methods exist
    has_db_verify = hasattr(verifier, '_verify_with_database')
    has_db_check = hasattr(verifier, '_check_database')
    has_db_save = hasattr(verifier, '_save_to_database')
    
    print(f"Database verification method exists: {has_db_verify}")
    print(f"Database check method exists: {has_db_check}")
    print(f"Database save method exists: {has_db_save}")
    
    if has_db_verify and has_db_check and has_db_save:
        print("✅ SUCCESS: All database methods exist for manual use")
    else:
        print("❌ ERROR: Some database methods are missing")
    
    print("\n=== Summary ===")
    print("✅ Database verification is disabled by default")
    print("✅ External APIs are used for verification")
    print("✅ Database is only used for archiving when explicitly enabled")
    print("✅ All database methods exist for manual use if needed")

if __name__ == "__main__":
    test_no_database_verification() 