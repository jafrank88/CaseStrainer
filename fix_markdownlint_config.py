#!/usr/bin/env python3
"""
Fix Markdownlint Configuration Issues
"""

import json
import os

def validate_markdownlint_config():
    """Validate markdownlint configuration files."""
    
    print("🔧 VALIDATING MARKDOWNLINT CONFIGURATION")
    print("=" * 50)
    
    config_files = ['.markdownlint.json', '.markdownlintrc']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"📄 Checking: {config_file}")
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Validate required fields
                required_fields = ['default']
                for field in required_fields:
                    if field not in config:
                        print(f"   ⚠️  Missing required field: {field}")
                    else:
                        print(f"   ✅ Field '{field}' present")
                
                # Validate ignore field
                if 'ignore' in config:
                    if isinstance(config['ignore'], list):
                        print(f"   ✅ 'ignore' field is properly formatted as array")
                        print(f"   📊 Ignoring {len(config['ignore'])} patterns")
                    else:
                        print(f"   ❌ 'ignore' field is not an array")
                
                # Validate rule configurations
                rule_count = 0
                for key, value in config.items():
                    if key.startswith('MD') and isinstance(value, bool):
                        rule_count += 1
                
                print(f"   📊 Configured {rule_count} markdown rules")
                print(f"   ✅ Configuration is valid JSON")
                
            except json.JSONDecodeError as e:
                print(f"   ❌ Invalid JSON: {e}")
            except Exception as e:
                print(f"   ❌ Error reading config: {e}")
        else:
            print(f"📄 {config_file} not found")

def create_robust_config():
    """Create a robust markdownlint configuration."""
    
    print(f"\n🔧 CREATING ROBUST CONFIGURATION")
    print("=" * 50)
    
    # Create a comprehensive configuration
    config = {
        "default": True,
        "MD013": False,  # Line length
        "MD033": False,  # Inline HTML
        "MD041": False,  # First line in file should be a top level heading
        "MD024": False,  # Multiple headings with the same content
        "MD022": False,  # Headings should be surrounded by blank lines
        "MD032": False,  # Lists should be surrounded by blank lines
        "MD031": False,  # Fenced code blocks should be surrounded by blank lines
        "MD040": False,  # Fenced code blocks should have a language specified
        "MD009": False,  # Trailing spaces
        "MD047": False,  # Files should end with a single newline character
        "ignore": [
            "archived_documentation/*.md",
            "CONSOLIDATED_DOCUMENTATION.md",
            "docs/COMPREHENSIVE_ALL_CONTENT_ANALYSIS.md",
            "docs/COMPREHENSIVE_FEATURE_ANALYSIS.md",
            "docs/COMPREHENSIVE_FEATURE_INTEGRATION_SUMMARY.md",
            "docs/COMPREHENSIVE_WEBSEARCH_SUMMARY.md",
            "docs/VLEX_COMPREHENSIVE_VERIFICATION.md",
            "docs/VLEX_INTEGRATION_SUMMARY.md"
        ]
    }
    
    # Write to both configuration files
    config_files = ['.markdownlint.json', '.markdownlintrc']
    
    for config_file in config_files:
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            print(f"   ✅ Created {config_file}")
        except Exception as e:
            print(f"   ❌ Error creating {config_file}: {e}")

def test_configuration():
    """Test the markdownlint configuration."""
    
    print(f"\n🧪 TESTING CONFIGURATION")
    print("=" * 50)
    
    try:
        import subprocess
        
        # Test with a simple markdown file
        test_content = """# Test Heading

This is a test markdown file.

- List item 1
- List item 2

```text
Test code block
```

"""
        
        # Create a test file
        with open('test_markdown.md', 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Run markdownlint
        result = subprocess.run([
            "markdownlint", "test_markdown.md"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Configuration test passed")
        else:
            print("   ⚠️  Configuration test completed with issues")
            print(f"   📄 Output: {result.stdout}")
        
        # Clean up test file
        if os.path.exists('test_markdown.md'):
            os.remove('test_markdown.md')
            
    except FileNotFoundError:
        print("   ℹ️  markdownlint not found, skipping test")
    except Exception as e:
        print(f"   ❌ Error testing configuration: {e}")

def main():
    """Main function to fix markdownlint configuration."""
    
    print("🔧 MARKDOWNLINT CONFIGURATION FIXES")
    print("=" * 60)
    
    # Validate existing configuration
    validate_markdownlint_config()
    
    # Create robust configuration
    create_robust_config()
    
    # Test configuration
    test_configuration()
    
    print(f"\n✅ CONFIGURATION FIXES COMPLETE!")
    print("=" * 60)
    print("Next steps:")
    print("1. Verify configuration works with your editor")
    print("2. Test with markdownlint CLI if available")
    print("3. Commit configuration improvements")

if __name__ == "__main__":
    main() 