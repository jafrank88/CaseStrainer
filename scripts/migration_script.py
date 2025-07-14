
#!/usr/bin/env python3
"""
Migration Script: Update Existing Citations with Enhanced Extraction
===================================================================

This script updates existing citation data with enhanced extraction results.
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from enhanced_extraction_improvements import EnhancedExtractionProcessor

def migrate_existing_citations():
    """Migrate existing citations to enhanced format."""
    
    enhanced_processor = EnhancedExtractionProcessor()
    
    # Load existing citations (example)
    existing_file = "data/existing_citations.json"
    if os.path.exists(existing_file):
        with open(existing_file, 'r') as f:
            existing_data = json.load(f)
        
        migrated_results = []
        
        for item in existing_data:
            text = item.get('text', '')
            if text:
                # Process with enhanced extraction
                enhanced_result = enhanced_processor.process_text_enhanced(text)
                
                # Merge with existing data
                migrated_item = {
                    **item,
                    'enhanced_citations': enhanced_result.get('citations', []),
                    'enhanced_case_names': enhanced_result.get('case_names', []),
                    'enhanced_dates': enhanced_result.get('dates', []),
                    'enhanced_clusters': enhanced_result.get('clusters', [])
                }
                
                migrated_results.append(migrated_item)
        
        # Save migrated data
        output_file = "data/migrated_citations.json"
        with open(output_file, 'w') as f:
            json.dump(migrated_results, f, indent=2)
        
        print(f"Migration complete. Results saved to {output_file}")
        print(f"Migrated {len(migrated_results)} documents")

if __name__ == '__main__':
    migrate_existing_citations()
