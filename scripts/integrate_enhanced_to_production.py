#!/usr/bin/env python3
"""
Production Integration Script for Enhanced Extraction
====================================================

This script shows how to integrate the enhanced extraction system
into the main production application.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from enhanced_extraction_improvements import EnhancedExtractionProcessor
from unified_citation_processor_v2 import UnifiedCitationProcessorV2


class ProductionEnhancedExtractor:
    """
    Production-ready enhanced extraction system.
    
    This class provides a drop-in replacement for the current extraction
    system with enhanced capabilities for case names, dates, and clustering.
    """
    
    def __init__(self, config: dict = None):
        """Initialize the enhanced extraction system."""
        self.config = config or {}
        self.base_processor = UnifiedCitationProcessorV2()
        self.enhanced_processor = EnhancedExtractionProcessor()
        
        # Performance tracking
        self.stats = {
            'total_documents': 0,
            'total_citations': 0,
            'total_case_names': 0,
            'total_dates': 0,
            'total_clusters': 0,
            'processing_times': []
        }
    
    def process_document(self, text: str, document_id: str = None) -> dict:
        """
        Process a document with enhanced extraction.
        
        Args:
            text: Document text to process
            document_id: Optional document identifier
            
        Returns:
            Dictionary with extraction results
        """
        import time
        start_time = time.time()
        
        try:
            # Process with enhanced extraction
            enhanced_result = self.enhanced_processor.process_text_enhanced(text)
            
            # Extract statistics and convert CitationResult objects to dicts
            citations = enhanced_result.get('citations', [])
            case_names = enhanced_result.get('case_names', [])
            dates = enhanced_result.get('dates', [])
            clusters = enhanced_result.get('clusters', [])
            
            # Convert CitationResult objects to dictionaries for JSON serialization
            citations_dict = []
            for citation in citations:
                if hasattr(citation, '__dict__'):
                    citations_dict.append(citation.__dict__)
                else:
                    citations_dict.append(str(citation))
            
            case_names_dict = []
            for case_name in case_names:
                if hasattr(case_name, '__dict__'):
                    case_names_dict.append(case_name.__dict__)
                else:
                    case_names_dict.append(str(case_name))
            
            dates_dict = []
            for date in dates:
                if hasattr(date, '__dict__'):
                    dates_dict.append(date.__dict__)
                else:
                    dates_dict.append(str(date))
            
            clusters_dict = []
            for cluster in clusters:
                if isinstance(cluster, dict):
                    clusters_dict.append(cluster)
                else:
                    clusters_dict.append(str(cluster))
            
            processing_time = time.time() - start_time
            
            # Update statistics
            self.stats['total_documents'] += 1
            self.stats['total_citations'] += len(citations)
            self.stats['total_case_names'] += len(case_names)
            self.stats['total_dates'] += len(dates)
            self.stats['total_clusters'] += len(clusters)
            self.stats['processing_times'].append(processing_time)
            
            result = {
                'document_id': document_id,
                'processing_time': processing_time,
                'text_length': len(text),
                'citations': citations_dict,
                'case_names': case_names_dict,
                'dates': dates_dict,
                'clusters': clusters_dict,
                'enhanced_features': {
                    'case_name_extraction': len(case_names) > 0,
                    'date_extraction': len(dates) > 0,
                    'clustering': len(clusters) > 0,
                    'confidence_scoring': True
                },
                'statistics': {
                    'citation_count': len(citations),
                    'case_name_count': len(case_names),
                    'date_count': len(dates),
                    'cluster_count': len(clusters)
                }
            }
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                'document_id': document_id,
                'processing_time': processing_time,
                'error': str(e),
                'success': False
            }
    
    def get_statistics(self) -> dict:
        """Get processing statistics."""
        if not self.stats['processing_times']:
            return self.stats
        
        avg_time = sum(self.stats['processing_times']) / len(self.stats['processing_times'])
        
        return {
            **self.stats,
            'average_processing_time': avg_time,
            'min_processing_time': min(self.stats['processing_times']),
            'max_processing_time': max(self.stats['processing_times'])
        }
    
    def export_results(self, results: list, output_file: str = None) -> str:
        """Export results to JSON file."""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"enhanced_extraction_results_{timestamp}.json"
        
        export_data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'total_documents': len(results),
                'enhanced_extraction_version': '1.0'
            },
            'statistics': self.get_statistics(),
            'results': results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return output_file


def integrate_with_flask_app():
    """
    Example of how to integrate with Flask app.
    
    Replace the current extraction in your Flask routes with this enhanced version.
    """
    
    # Example Flask route integration
    flask_integration_code = '''
# In your Flask app (e.g., app.py or routes.py)

from scripts.enhanced_extraction_improvements import EnhancedExtractionProcessor

# Initialize the enhanced processor
enhanced_processor = EnhancedExtractionProcessor()

@app.route('/api/process_document', methods=['POST'])
def process_document():
    """Enhanced document processing endpoint."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Process with enhanced extraction
        result = enhanced_processor.process_text_enhanced(text)
        
        return jsonify({
            'success': True,
            'citations': result.get('citations', []),
            'case_names': result.get('case_names', []),
            'dates': result.get('dates', []),
            'clusters': result.get('clusters', []),
            'enhanced_features': {
                'case_name_extraction': len(result.get('case_names', [])) > 0,
                'date_extraction': len(result.get('dates', [])) > 0,
                'clustering': len(result.get('clusters', [])) > 0
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
'''
    
    return flask_integration_code


def create_migration_script():
    """
    Create a migration script to update existing data.
    """
    
    migration_script = '''
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
'''
    
    return migration_script


def main():
    """Main function to demonstrate production integration."""
    
    print("🚀 PRODUCTION INTEGRATION FOR ENHANCED EXTRACTION")
    print("=" * 60)
    
    # Create production extractor
    extractor = ProductionEnhancedExtractor()
    
    # Example usage
    sample_text = """
    The court's analysis in this matter requires consideration of multiple authorities.
    
    First, we examine the framework established in Convoyant, LLC v. DeepThink, LLC, 
    200 Wn.2d 72, 514 P.3d 643 (2022). This case provides the foundational principles.
    
    Second, we consider the Department of Transportation v. State Highway Commission, 
    123 Wn.2d 456 (1990), which provides additional guidance on administrative procedures.
    
    Finally, we review the recent decision in In re Estate of Johnson, 234 Wn.2d 567 (2018).
    """
    
    print("📋 Processing sample document...")
    result = extractor.process_document(sample_text, "sample_doc_001")
    
    print(f"✅ Processing completed in {result['processing_time']:.2f} seconds")
    print(f"📊 Results:")
    print(f"   Citations: {result['statistics']['citation_count']}")
    print(f"   Case names: {result['statistics']['case_name_count']}")
    print(f"   Dates: {result['statistics']['date_count']}")
    print(f"   Clusters: {result['statistics']['cluster_count']}")
    
    # Export results
    output_file = extractor.export_results([result])
    print(f"💾 Results exported to: {output_file}")
    
    # Show statistics
    stats = extractor.get_statistics()
    print(f"\n📈 Overall Statistics:")
    print(f"   Documents processed: {stats['total_documents']}")
    print(f"   Total citations: {stats['total_citations']}")
    print(f"   Total case names: {stats['total_case_names']}")
    print(f"   Total dates: {stats['total_dates']}")
    print(f"   Total clusters: {stats['total_clusters']}")
    
    print(f"\n🔧 Integration Options:")
    print(f"   1. Flask App Integration: Use the provided code snippet")
    print(f"   2. Migration Script: Run the migration script for existing data")
    print(f"   3. Direct Integration: Use ProductionEnhancedExtractor class")
    
    # Save integration examples
    with open("flask_integration_example.py", "w") as f:
        f.write(integrate_with_flask_app())
    
    with open("migration_script.py", "w") as f:
        f.write(create_migration_script())
    
    print(f"\n💡 Integration examples saved to:")
    print(f"   - scripts/flask_integration_example.py")
    print(f"   - scripts/migration_script.py")


if __name__ == '__main__':
    main() 