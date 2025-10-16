#!/usr/bin/env python3
"""
Comprehensive Update Script for Step 4: Update Existing Workflows
Updates all old extraction function calls to use the new streamlined API
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Tuple

class ExtractionFunctionUpdater:
    """Updates old extraction function calls to use new streamlined API"""
    
    def __init__(self):
        self.project_root = Path(".")
        self.src_dir = self.project_root / "src"
        self.backup_dir = self.project_root / "backup_before_update"
        
        # Function mapping: old -> new
        self.function_mappings = {
            # Import statements
            "from src.case_name_extraction_core import extract_case_name_triple": 
                "from src.case_name_extraction_core import extract_case_name_and_date",
            "from case_name_extraction_core import extract_case_name_triple": 
                "from case_name_extraction_core import extract_case_name_and_date",
            "from src.case_name_extraction_core import extract_case_name_triple_comprehensive": 
                "from src.case_name_extraction_core import extract_case_name_and_date",
            "from case_name_extraction_core import extract_case_name_triple_comprehensive": 
                "from case_name_extraction_core import extract_case_name_and_date",
            
            # Function calls
            "extract_case_name_triple(": "extract_case_name_and_date(",
            "extract_case_name_triple_comprehensive(": "extract_case_name_and_date(",
            "extract_case_name_fixed_comprehensive(": "extract_case_name_only(",
            "extract_year_fixed_comprehensive(": "extract_year_only(",
        }
        
        # Critical files to update (in order of priority)
        self.critical_files = [
            "src/app_final_vue.py",
            "src/unified_citation_processor_v2.py", 
            "src/document_processing.py",
            "src/citation_extractor.py",
            "src/extract_case_name.py",
            "src/legal_case_extractor_enhanced.py"
        ]
        
        # Result handling patterns to update
        self.result_patterns = [
            # Old triple return pattern
            (r'case_name,\s*date,\s*confidence\s*=\s*extract_case_name_and_date\(', 
             r'result = extract_case_name_and_date('),
            
            # Old dict access patterns
            (r'extraction_result\.get\("extracted_name"\)', r'extraction_result.get("case_name")'),
            (r'extraction_result\.get\("extracted_date"\)', r'extraction_result.get("year")'),
            (r'extraction_result\.get\("case_name_confidence"\)', r'extraction_result.get("confidence")'),
        ]
    
    def create_backup(self):
        """Create backup of critical files before updating"""
        print("🔒 Creating backup of critical files...")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        for file_path in self.critical_files:
            if Path(file_path).exists():
                backup_path = self.backup_dir / Path(file_path).name
                shutil.copy2(file_path, backup_path)
                print(f"  ✅ Backed up: {file_path}")
            else:
                print(f"  ⚠️  File not found: {file_path}")
        
        print(f"📁 Backup created in: {self.backup_dir}")
    
    def update_file(self, file_path: str) -> Dict[str, any]:
        """Update a single file with new extraction functions"""
        file_path = Path(file_path)
        if not file_path.exists():
            return {"status": "not_found", "changes": 0}
        
        print(f"\n🔄 Updating: {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Update imports and function calls
        for old_pattern, new_pattern in self.function_mappings.items():
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                changes_made += content.count(new_pattern) - original_content.count(new_pattern)
                print(f"  ✅ Updated: {old_pattern} -> {new_pattern}")
        
        # Update result handling patterns
        for pattern, replacement in self.result_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made += 1
                print(f"  ✅ Updated result handling pattern")
        
        # Update specific function call signatures
        content = self._update_function_signatures(content)
        
        # Write updated content
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  💾 Saved {changes_made} changes")
            return {"status": "updated", "changes": changes_made}
        else:
            print(f"  ℹ️  No changes needed")
            return {"status": "no_changes", "changes": 0}
    
    def _update_function_signatures(self, content: str) -> str:
        """Update function call signatures to match new API"""
        
        # Update extract_case_name_triple calls to extract_case_name_and_date
        # Remove api_key and context_window parameters (not supported in new API)
        pattern = r'extract_case_name_and_date\(\s*([^)]+)\)'
        
        def update_signature(match):
            params = match.group(1)
            
            # Remove unsupported parameters
            params = re.sub(r',\s*api_key\s*=\s*[^,)]+', '', params)
            params = re.sub(r',\s*context_window\s*=\s*[^,)]+', '', params)
            
            # Ensure we have the right parameter names
            if 'text=' not in params and 'citation=' not in params:
                # Convert positional to keyword arguments
                parts = [p.strip() for p in params.split(',')]
                if len(parts) >= 2:
                    params = f"text={parts[0]}, citation={parts[1]}"
            
            return f"extract_case_name_and_date({params})"
        
        content = re.sub(pattern, update_signature, content)
        return content
    
    def update_result_handling(self, file_path: str):
        """Update result handling to work with new API structure"""
        file_path = Path(file_path)
        if not file_path.exists():
            return
        
        print(f"\n🔧 Updating result handling in: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update result access patterns
        replacements = [
            # Old triple unpacking
            (r'(\w+),\s*(\w+),\s*(\w+)\s*=\s*extract_case_name_and_date\(', 
             r'result = extract_case_name_and_date('),
            
            # Update result field access
            (r'\1\s*=\s*result\.get\("case_name"\)', r'case_name = result.get("case_name")'),
            (r'\2\s*=\s*result\.get\("year"\)', r'year = result.get("year")'),
            (r'\3\s*=\s*result\.get\("confidence"\)', r'confidence = result.get("confidence")'),
        ]
        
        for pattern, replacement in replacements:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                print(f"  ✅ Updated result handling")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def run_comprehensive_update(self):
        """Run the complete update process"""
        print("🚀 Starting Step 4: Update Existing Workflows")
        print("=" * 60)
        
        # Step 1: Create backup
        self.create_backup()
        
        # Step 2: Update critical files
        print(f"\n📝 Updating {len(self.critical_files)} critical files...")
        
        results = []
        for file_path in self.critical_files:
            result = self.update_file(file_path)
            results.append({"file": file_path, **result})
        
        # Step 3: Update result handling
        print(f"\n🔧 Updating result handling patterns...")
        for file_path in self.critical_files:
            self.update_result_handling(file_path)
        
        # Step 4: Generate report
        self._generate_update_report(results)
        
        print(f"\n✅ Step 4 Complete!")
        print(f"📁 Backup available in: {self.backup_dir}")
        print(f"🔄 To rollback: copy files from {self.backup_dir} back to src/")
    
    def _generate_update_report(self, results: List[Dict]):
        """Generate a summary report of the update"""
        print(f"\n📊 Update Report:")
        print("-" * 40)
        
        total_changes = 0
        files_updated = 0
        
        for result in results:
            status = result["status"]
            changes = result["changes"]
            file_name = Path(result["file"]).name
            
            if status == "updated":
                print(f"✅ {file_name}: {changes} changes")
                total_changes += changes
                files_updated += 1
            elif status == "no_changes":
                print(f"ℹ️  {file_name}: No changes needed")
            else:
                print(f"❌ {file_name}: File not found")
        
        print("-" * 40)
        print(f"📈 Summary:")
        print(f"  Files updated: {files_updated}/{len(results)}")
        print(f"  Total changes: {total_changes}")
        print(f"  Backup location: {self.backup_dir}")

def main():
    """Main execution function"""
    updater = ExtractionFunctionUpdater()
    
    try:
        updater.run_comprehensive_update()
    except Exception as e:
        print(f"❌ Error during update: {e}")
        print(f"🔄 To rollback, copy files from {updater.backup_dir} back to src/")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 