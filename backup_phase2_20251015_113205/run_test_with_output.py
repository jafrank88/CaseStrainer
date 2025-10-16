#!/usr/bin/env python3

def run_test_with_full_output():
    """Run tests and capture full output to files."""
    
    import subprocess
    import sys
    from datetime import datetime
    
    # Test files to run
    test_files = [
        'test_sync_async_focused.py',
        'test_async_path_validation.py', 
        'test_comprehensive_sync_async.py'
    ]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for test_file in test_files:
        print(f"🔍 Running {test_file}...")
        
        # Output file for this test
        output_file = f"test_output_{test_file.replace('.py', '')}_{timestamp}.txt"
        
        try:
            # Run the test and capture all output
            with open(output_file, 'w', encoding='utf-8') as f:
                result = subprocess.run(
                    [sys.executable, test_file],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd='.',
                    timeout=300  # 5 minute timeout
                )
            
            print(f"✅ {test_file} completed - output saved to {output_file}")
            print(f"   Exit code: {result.returncode}")
            
            # Show first few lines of output
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print(f"   Output lines: {len(lines)}")
                    print(f"   First few lines:")
                    for i, line in enumerate(lines[:5]):
                        print(f"      {i+1}: {line.strip()}")
                    if len(lines) > 5:
                        print(f"      ... ({len(lines)-5} more lines in file)")
            except Exception as e:
                print(f"   Could not preview output: {e}")
                
        except subprocess.TimeoutExpired:
            print(f"❌ {test_file} timed out after 5 minutes")
        except Exception as e:
            print(f"❌ Error running {test_file}: {e}")
    
    print(f"\n📁 All output files saved with timestamp: {timestamp}")
    print(f"   You can read the full output from the generated .txt files")

if __name__ == "__main__":
    run_test_with_full_output()
